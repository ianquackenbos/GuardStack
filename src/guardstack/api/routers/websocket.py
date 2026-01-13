"""
WebSocket Router for Real-time Updates

Provides WebSocket endpoints for streaming evaluation progress,
live dashboard updates, and guardrail monitoring.
"""

import asyncio
import json
import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from redis.asyncio import Redis

from guardstack.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._redis: Optional[Redis] = None
    
    async def get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self._redis
    
    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        logger.info(f"WebSocket connected to channel: {channel}")
    
    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Remove a WebSocket connection."""
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        logger.info(f"WebSocket disconnected from channel: {channel}")
    
    async def send_personal_message(
        self,
        message: dict[str, Any],
        websocket: WebSocket
    ) -> None:
        """Send message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast(
        self,
        channel: str,
        message: dict[str, Any]
    ) -> None:
        """Broadcast message to all connections in a channel."""
        if channel in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # Clean up disconnected sockets
            for conn in disconnected:
                self.disconnect(conn, channel)
    
    async def publish_to_redis(
        self,
        channel: str,
        message: dict[str, Any]
    ) -> None:
        """Publish message to Redis for cross-pod distribution."""
        redis = await self.get_redis()
        await redis.publish(channel, json.dumps(message))
    
    async def subscribe_to_redis(self, channel: str) -> None:
        """Subscribe to Redis channel for cross-pod messages."""
        redis = await self.get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await self.broadcast(channel, data)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/evaluations/{evaluation_id}")
async def evaluation_progress_websocket(
    websocket: WebSocket,
    evaluation_id: UUID,
):
    """
    WebSocket endpoint for streaming evaluation progress.
    
    Sends real-time updates as each pillar completes:
    - pillar_started: When a pillar begins evaluation
    - pillar_completed: When a pillar finishes with score
    - evaluation_completed: When entire evaluation is done
    - error: On any errors
    """
    channel = f"evaluation:{evaluation_id}"
    await manager.connect(websocket, channel)
    
    try:
        # Send initial status
        await manager.send_personal_message({
            "type": "connected",
            "evaluation_id": str(evaluation_id),
            "message": "Connected to evaluation progress stream",
        }, websocket)
        
        # Listen for messages (keep connection alive)
        while True:
            try:
                # Wait for any client messages (heartbeat, etc.)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                if data == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                    }, websocket)
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await manager.send_personal_message({
                    "type": "heartbeat",
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, channel)


@router.websocket("/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    
    Streams:
    - score_update: When a model's score changes
    - evaluation_started: When new evaluation begins
    - evaluation_completed: When evaluation finishes
    - alert: On threshold violations
    """
    channel = "dashboard"
    await manager.connect(websocket, channel)
    
    try:
        await manager.send_personal_message({
            "type": "connected",
            "message": "Connected to dashboard updates",
        }, websocket)
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                if data == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                    }, websocket)
                    
            except asyncio.TimeoutError:
                await manager.send_personal_message({
                    "type": "heartbeat",
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@router.websocket("/guardrails/{guardrail_id}")
async def guardrail_monitoring_websocket(
    websocket: WebSocket,
    guardrail_id: str,
):
    """
    WebSocket endpoint for real-time guardrail monitoring.
    
    Streams:
    - triggered: When guardrail is triggered
    - blocked: When content is blocked
    - stats_update: Periodic statistics update
    """
    channel = f"guardrail:{guardrail_id}"
    await manager.connect(websocket, channel)
    
    try:
        await manager.send_personal_message({
            "type": "connected",
            "guardrail_id": guardrail_id,
            "message": "Connected to guardrail monitoring",
        }, websocket)
        
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                if data == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                    }, websocket)
                    
            except asyncio.TimeoutError:
                await manager.send_personal_message({
                    "type": "heartbeat",
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


# Helper functions for publishing updates (called from evaluation engine)

async def publish_pillar_started(
    evaluation_id: UUID,
    pillar: str,
) -> None:
    """Publish pillar started event."""
    await manager.publish_to_redis(
        f"evaluation:{evaluation_id}",
        {
            "type": "pillar_started",
            "evaluation_id": str(evaluation_id),
            "pillar": pillar,
            "timestamp": asyncio.get_event_loop().time(),
        }
    )


async def publish_pillar_completed(
    evaluation_id: UUID,
    pillar: str,
    score: float,
    findings_count: int,
) -> None:
    """Publish pillar completed event."""
    await manager.publish_to_redis(
        f"evaluation:{evaluation_id}",
        {
            "type": "pillar_completed",
            "evaluation_id": str(evaluation_id),
            "pillar": pillar,
            "score": score,
            "findings_count": findings_count,
            "timestamp": asyncio.get_event_loop().time(),
        }
    )


async def publish_evaluation_completed(
    evaluation_id: UUID,
    overall_score: float,
    risk_status: str,
) -> None:
    """Publish evaluation completed event."""
    await manager.publish_to_redis(
        f"evaluation:{evaluation_id}",
        {
            "type": "evaluation_completed",
            "evaluation_id": str(evaluation_id),
            "overall_score": overall_score,
            "risk_status": risk_status,
            "timestamp": asyncio.get_event_loop().time(),
        }
    )
    
    # Also publish to dashboard channel
    await manager.publish_to_redis(
        "dashboard",
        {
            "type": "evaluation_completed",
            "evaluation_id": str(evaluation_id),
            "overall_score": overall_score,
            "risk_status": risk_status,
        }
    )


async def publish_guardrail_triggered(
    guardrail_id: str,
    trigger_type: str,
    blocked: bool,
    details: dict[str, Any],
) -> None:
    """Publish guardrail triggered event."""
    await manager.publish_to_redis(
        f"guardrail:{guardrail_id}",
        {
            "type": "triggered",
            "guardrail_id": guardrail_id,
            "trigger_type": trigger_type,
            "blocked": blocked,
            "details": details,
            "timestamp": asyncio.get_event_loop().time(),
        }
    )
