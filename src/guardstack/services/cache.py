"""
Redis Service

Caching, pub/sub, and job queue management.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from guardstack.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration."""
    
    default_ttl: int = 3600  # 1 hour
    key_prefix: str = "guardstack"
    serializer: str = "json"


class RedisService:
    """
    Redis service for caching, pub/sub, and queues.
    
    Provides:
    - Key-value caching
    - Pub/sub messaging
    - Job queues
    - Rate limiting
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        cache_config: Optional[CacheConfig] = None,
    ) -> None:
        self.settings = settings or Settings()
        self.cache_config = cache_config or CacheConfig()
        self._client: Optional[Redis] = None
        self._pubsub_client: Optional[Redis] = None
        self._subscriptions: dict[str, Callable] = {}
    
    @property
    def client(self) -> Redis:
        """Get or create the Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client
    
    def _make_key(self, key: str) -> str:
        """Create a prefixed key."""
        return f"{self.cache_config.key_prefix}:{key}"
    
    # ==================== Caching ====================
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value."""
        value = await self.client.get(self._make_key(key))
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set a cached value.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        
        Returns:
            True if successful
        """
        ttl = ttl or self.cache_config.default_ttl
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        await self.client.setex(
            self._make_key(key),
            ttl,
            value,
        )
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete a cached value."""
        result = await self.client.delete(self._make_key(key))
        return result > 0
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return await self.client.exists(self._make_key(key)) > 0
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None,
    ) -> Any:
        """
        Get a value from cache or compute and store it.
        
        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Time to live in seconds
        
        Returns:
            Cached or computed value
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        await self.set(key, value, ttl)
        return value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Glob pattern (e.g., "user:*")
        
        Returns:
            Number of keys deleted
        """
        full_pattern = self._make_key(pattern)
        keys = []
        
        async for key in self.client.scan_iter(match=full_pattern):
            keys.append(key)
        
        if keys:
            return await self.client.delete(*keys)
        return 0
    
    # ==================== Pub/Sub ====================
    
    async def publish(self, channel: str, message: Any) -> int:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel name
            message: Message to publish
        
        Returns:
            Number of subscribers that received the message
        """
        if isinstance(message, (dict, list)):
            message = json.dumps(message)
        
        return await self.client.publish(
            self._make_key(channel),
            message,
        )
    
    async def subscribe(
        self,
        channel: str,
        callback: Callable[[str, Any], None],
    ) -> None:
        """
        Subscribe to a channel.
        
        Args:
            channel: Channel name
            callback: Function to call when message received
        """
        if self._pubsub_client is None:
            self._pubsub_client = self.client.pubsub()
        
        full_channel = self._make_key(channel)
        self._subscriptions[full_channel] = callback
        
        await self._pubsub_client.subscribe(full_channel)
        logger.info(f"Subscribed to channel: {channel}")
    
    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel."""
        if self._pubsub_client is None:
            return
        
        full_channel = self._make_key(channel)
        await self._pubsub_client.unsubscribe(full_channel)
        self._subscriptions.pop(full_channel, None)
        logger.info(f"Unsubscribed from channel: {channel}")
    
    async def listen(self) -> None:
        """
        Listen for pub/sub messages.
        
        This should be run in a background task.
        """
        if self._pubsub_client is None:
            logger.warning("No subscriptions to listen for")
            return
        
        async for message in self._pubsub_client.listen():
            if message["type"] != "message":
                continue
            
            channel = message["channel"]
            callback = self._subscriptions.get(channel)
            
            if callback is None:
                continue
            
            try:
                data = json.loads(message["data"])
            except json.JSONDecodeError:
                data = message["data"]
            
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(channel, data)
                else:
                    callback(channel, data)
            except Exception as e:
                logger.error(f"Error in pub/sub callback: {e}")
    
    # ==================== Job Queues ====================
    
    async def enqueue(
        self,
        queue: str,
        job: dict[str, Any],
        priority: int = 0,
    ) -> str:
        """
        Add a job to a queue.
        
        Args:
            queue: Queue name
            job: Job data
            priority: Higher priority jobs processed first
        
        Returns:
            Job ID
        """
        import uuid
        
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "data": job,
            "status": "pending",
            "priority": priority,
            "created_at": asyncio.get_event_loop().time(),
        }
        
        # Use sorted set for priority queue
        await self.client.zadd(
            self._make_key(f"queue:{queue}"),
            {json.dumps(job_data): -priority},  # Negative for high-first
        )
        
        # Store job details
        await self.set(f"job:{job_id}", job_data, ttl=86400)
        
        return job_id
    
    async def dequeue(self, queue: str) -> Optional[dict[str, Any]]:
        """
        Get the next job from a queue.
        
        Args:
            queue: Queue name
        
        Returns:
            Job data or None if queue is empty
        """
        # Pop highest priority item
        result = await self.client.zpopmin(
            self._make_key(f"queue:{queue}"),
            count=1,
        )
        
        if not result:
            return None
        
        job_str, _ = result[0]
        job_data = json.loads(job_str)
        
        # Update job status
        job_data["status"] = "processing"
        await self.set(f"job:{job_data['id']}", job_data, ttl=86400)
        
        return job_data
    
    async def complete_job(
        self,
        job_id: str,
        result: Optional[Any] = None,
    ) -> None:
        """Mark a job as completed."""
        job_data = await self.get(f"job:{job_id}")
        if job_data:
            job_data["status"] = "completed"
            job_data["result"] = result
            await self.set(f"job:{job_id}", job_data, ttl=86400)
    
    async def fail_job(
        self,
        job_id: str,
        error: str,
    ) -> None:
        """Mark a job as failed."""
        job_data = await self.get(f"job:{job_id}")
        if job_data:
            job_data["status"] = "failed"
            job_data["error"] = error
            await self.set(f"job:{job_id}", job_data, ttl=86400)
    
    async def get_job_status(self, job_id: str) -> Optional[dict[str, Any]]:
        """Get job status."""
        return await self.get(f"job:{job_id}")
    
    async def get_queue_length(self, queue: str) -> int:
        """Get number of jobs in queue."""
        return await self.client.zcard(self._make_key(f"queue:{queue}"))
    
    # ==================== Rate Limiting ====================
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int = 60,
    ) -> tuple[bool, int]:
        """
        Check if rate limit is exceeded.
        
        Args:
            key: Rate limit key (e.g., "api:user:123")
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        full_key = self._make_key(f"ratelimit:{key}")
        
        # Increment counter
        current = await self.client.incr(full_key)
        
        # Set expiry on first request
        if current == 1:
            await self.client.expire(full_key, window)
        
        remaining = max(0, limit - current)
        is_allowed = current <= limit
        
        return is_allowed, remaining
    
    # ==================== Lifecycle ====================
    
    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close Redis connections."""
        if self._pubsub_client is not None:
            await self._pubsub_client.close()
            self._pubsub_client = None
        
        if self._client is not None:
            await self._client.close()
            self._client = None
        
        logger.info("Redis connections closed")


# Global Redis instance
_redis_service: Optional[RedisService] = None


def get_redis() -> RedisService:
    """Get the global Redis service."""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service


async def close_redis() -> None:
    """Close the Redis service."""
    global _redis_service
    if _redis_service is not None:
        await _redis_service.close()
        _redis_service = None


async def redis_client():
    """Get the raw Redis client for direct access."""
    service = get_redis()
    return service.client
