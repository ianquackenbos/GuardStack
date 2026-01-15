"""
Agentic AI Security Router

Endpoints for managing and monitoring autonomous AI agents,
including session tracking, tool governance, and A2A trust management.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user

router = APIRouter(prefix="/agentic", tags=["Agentic AI"])


# ============================================================================
# Pydantic Models
# ============================================================================

class AgentSessionBase(BaseModel):
    """Base model for agent sessions"""
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_name: str = Field(..., description="Human-readable agent name")
    agent_type: str = Field(..., description="Type: autonomous, semi-autonomous, supervised")
    model_id: Optional[str] = Field(None, description="Underlying model identifier")
    purpose: Optional[str] = Field(None, description="Agent's declared purpose")


class AgentSessionCreate(AgentSessionBase):
    """Model for creating a new agent session"""
    allowed_tools: Optional[list[str]] = Field(None, description="Pre-approved tools")
    constraints: Optional[dict] = Field(default_factory=dict, description="Operational constraints")


class AgentSessionResponse(AgentSessionBase):
    """Model for agent session response"""
    id: UUID
    status: str = Field("active", description="Session status: active, paused, terminated")
    risk_level: str = Field("medium", description="Current risk assessment")
    total_actions: int = Field(0, description="Total actions taken")
    tool_calls: int = Field(0, description="Number of tool invocations")
    tokens_used: int = Field(0, description="Total tokens consumed")
    started_at: datetime
    last_activity: datetime
    terminated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ToolDefinition(BaseModel):
    """Model for tool/capability definitions"""
    id: UUID
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    category: str = Field(..., description="Category: filesystem, network, code_execution, external_api")
    risk_level: str = Field(..., description="Risk: critical, high, medium, low")
    requires_approval: bool = Field(False, description="Requires human approval before use")
    allowed_agents: Optional[list[str]] = Field(None, description="Agents allowed to use this tool")
    parameters_schema: Optional[dict] = Field(None, description="JSON schema for tool parameters")
    created_at: datetime
    updated_at: datetime


class ToolApprovalRequest(BaseModel):
    """Model for tool approval requests"""
    tool_id: UUID
    agent_session_id: UUID
    parameters: Optional[dict] = Field(default_factory=dict, description="Requested parameters")
    justification: Optional[str] = Field(None, description="Reason for tool usage")


class ActionLog(BaseModel):
    """Model for agent action logs"""
    id: UUID
    session_id: UUID
    action_type: str = Field(..., description="Type: tool_call, api_request, decision, output")
    tool_name: Optional[str] = Field(None, description="Tool used if applicable")
    input_summary: Optional[str] = Field(None, description="Summarized input")
    output_summary: Optional[str] = Field(None, description="Summarized output")
    risk_flags: list[str] = Field(default_factory=list, description="Detected risk indicators")
    tokens_used: int = Field(0, description="Tokens for this action")
    latency_ms: int = Field(0, description="Action latency")
    status: str = Field("completed", description="Action status")
    timestamp: datetime


class A2ATrustPolicy(BaseModel):
    """Agent-to-Agent trust policy"""
    id: UUID
    source_agent: str = Field(..., description="Requesting agent")
    target_agent: str = Field(..., description="Target agent")
    trust_level: str = Field(..., description="Trust level: full, limited, none")
    allowed_operations: list[str] = Field(default_factory=list, description="Permitted operations")
    expires_at: Optional[datetime] = None
    created_at: datetime


# ============================================================================
# Agent Session Endpoints
# ============================================================================

@router.get("/sessions", response_model=list[AgentSessionResponse])
async def list_agent_sessions(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all agent sessions with filtering options.
    """
    from uuid import uuid4
    
    sessions = [
        AgentSessionResponse(
            id=uuid4(),
            agent_id="agent-research-001",
            agent_name="Research Assistant",
            agent_type="semi-autonomous",
            model_id="gpt-4-turbo",
            purpose="Research and summarize technical documents",
            status="active",
            risk_level="low",
            total_actions=145,
            tool_calls=23,
            tokens_used=45000,
            started_at=datetime.utcnow() - timedelta(hours=2),
            last_activity=datetime.utcnow() - timedelta(minutes=5),
            terminated_at=None,
        ),
        AgentSessionResponse(
            id=uuid4(),
            agent_id="agent-code-002",
            agent_name="Code Assistant",
            agent_type="supervised",
            model_id="claude-3-opus",
            purpose="Code review and generation",
            status="active",
            risk_level="medium",
            total_actions=89,
            tool_calls=56,
            tokens_used=120000,
            started_at=datetime.utcnow() - timedelta(hours=1),
            last_activity=datetime.utcnow() - timedelta(minutes=1),
            terminated_at=None,
        ),
        AgentSessionResponse(
            id=uuid4(),
            agent_id="agent-deploy-003",
            agent_name="Deployment Agent",
            agent_type="autonomous",
            model_id="gpt-4",
            purpose="Automated deployment orchestration",
            status="paused",
            risk_level="high",
            total_actions=234,
            tool_calls=89,
            tokens_used=87000,
            started_at=datetime.utcnow() - timedelta(hours=4),
            last_activity=datetime.utcnow() - timedelta(minutes=30),
            terminated_at=None,
        ),
    ]
    
    return sessions


@router.get("/sessions/{session_id}", response_model=AgentSessionResponse)
async def get_agent_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed information about a specific agent session.
    """
    return AgentSessionResponse(
        id=session_id,
        agent_id="agent-research-001",
        agent_name="Research Assistant",
        agent_type="semi-autonomous",
        model_id="gpt-4-turbo",
        purpose="Research and summarize technical documents",
        status="active",
        risk_level="low",
        total_actions=145,
        tool_calls=23,
        tokens_used=45000,
        started_at=datetime.utcnow() - timedelta(hours=2),
        last_activity=datetime.utcnow() - timedelta(minutes=5),
        terminated_at=None,
    )


@router.post("/sessions", response_model=AgentSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_session(
    session: AgentSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Register a new agent session for monitoring.
    """
    from uuid import uuid4
    
    return AgentSessionResponse(
        id=uuid4(),
        **session.model_dump(exclude={"allowed_tools", "constraints"}),
        status="active",
        risk_level="medium",
        total_actions=0,
        tool_calls=0,
        tokens_used=0,
        started_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        terminated_at=None,
    )


@router.post("/sessions/{session_id}/terminate")
async def terminate_agent_session(
    session_id: UUID,
    reason: Optional[str] = Query(None, description="Termination reason"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Terminate an active agent session.
    """
    return {
        "id": session_id,
        "status": "terminated",
        "reason": reason or "Manual termination by user",
        "terminated_at": datetime.utcnow(),
        "terminated_by": current_user.get("username", "unknown"),
    }


@router.post("/sessions/{session_id}/pause")
async def pause_agent_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Pause an active agent session.
    """
    return {
        "id": session_id,
        "status": "paused",
        "paused_at": datetime.utcnow(),
    }


@router.post("/sessions/{session_id}/resume")
async def resume_agent_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Resume a paused agent session.
    """
    return {
        "id": session_id,
        "status": "active",
        "resumed_at": datetime.utcnow(),
    }


# ============================================================================
# Tool Management Endpoints
# ============================================================================

@router.get("/tools", response_model=list[ToolDefinition])
async def list_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all registered tools/capabilities available to agents.
    """
    from uuid import uuid4
    
    tools = [
        ToolDefinition(
            id=uuid4(),
            name="file_read",
            description="Read contents of a file from the filesystem",
            category="filesystem",
            risk_level="medium",
            requires_approval=False,
            allowed_agents=None,
            parameters_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "required": ["path"]
            },
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow(),
        ),
        ToolDefinition(
            id=uuid4(),
            name="code_execute",
            description="Execute arbitrary code in a sandboxed environment",
            category="code_execution",
            risk_level="critical",
            requires_approval=True,
            allowed_agents=["agent-code-002"],
            parameters_schema={
                "type": "object",
                "properties": {
                    "language": {"type": "string", "enum": ["python", "javascript"]},
                    "code": {"type": "string", "description": "Code to execute"}
                },
                "required": ["language", "code"]
            },
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow(),
        ),
        ToolDefinition(
            id=uuid4(),
            name="http_request",
            description="Make HTTP requests to external APIs",
            category="network",
            risk_level="high",
            requires_approval=False,
            allowed_agents=None,
            parameters_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                    "body": {"type": "object"}
                },
                "required": ["url", "method"]
            },
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow(),
        ),
    ]
    
    return tools


@router.post("/tools/approve")
async def approve_tool_usage(
    request: ToolApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Approve a tool usage request from an agent.
    """
    from uuid import uuid4
    
    return {
        "approval_id": uuid4(),
        "tool_id": request.tool_id,
        "session_id": request.agent_session_id,
        "status": "approved",
        "approved_by": current_user.get("username", "unknown"),
        "approved_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=1),
    }


@router.post("/tools/deny")
async def deny_tool_usage(
    request: ToolApprovalRequest,
    reason: Optional[str] = Query(None, description="Denial reason"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Deny a tool usage request from an agent.
    """
    return {
        "tool_id": request.tool_id,
        "session_id": request.agent_session_id,
        "status": "denied",
        "reason": reason or "Request denied by administrator",
        "denied_by": current_user.get("username", "unknown"),
        "denied_at": datetime.utcnow(),
    }


# ============================================================================
# Action Logging Endpoints
# ============================================================================

@router.get("/sessions/{session_id}/actions", response_model=list[ActionLog])
async def get_session_actions(
    session_id: UUID,
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get action logs for a specific agent session.
    """
    from uuid import uuid4
    
    actions = [
        ActionLog(
            id=uuid4(),
            session_id=session_id,
            action_type="tool_call",
            tool_name="file_read",
            input_summary="Read config.yaml from /app/config/",
            output_summary="Successfully read 245 bytes",
            risk_flags=[],
            tokens_used=150,
            latency_ms=45,
            status="completed",
            timestamp=datetime.utcnow() - timedelta(minutes=10),
        ),
        ActionLog(
            id=uuid4(),
            session_id=session_id,
            action_type="decision",
            tool_name=None,
            input_summary="Analyzing configuration options",
            output_summary="Decided to update database connection settings",
            risk_flags=["configuration_change"],
            tokens_used=500,
            latency_ms=120,
            status="completed",
            timestamp=datetime.utcnow() - timedelta(minutes=8),
        ),
        ActionLog(
            id=uuid4(),
            session_id=session_id,
            action_type="api_request",
            tool_name="http_request",
            input_summary="GET https://api.internal/health",
            output_summary="200 OK - Service healthy",
            risk_flags=[],
            tokens_used=100,
            latency_ms=230,
            status="completed",
            timestamp=datetime.utcnow() - timedelta(minutes=5),
        ),
    ]
    
    return actions


@router.post("/actions/log", status_code=status.HTTP_201_CREATED)
async def log_agent_action(
    session_id: UUID,
    action_type: str,
    tool_name: Optional[str] = None,
    input_data: Optional[dict] = None,
    output_data: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Log an action taken by an agent (used by agent framework integration).
    """
    from uuid import uuid4
    
    return {
        "action_id": uuid4(),
        "session_id": session_id,
        "action_type": action_type,
        "logged_at": datetime.utcnow(),
    }


# ============================================================================
# A2A Trust Management Endpoints
# ============================================================================

@router.get("/a2a/policies", response_model=list[A2ATrustPolicy])
async def list_a2a_policies(
    source_agent: Optional[str] = Query(None, description="Filter by source agent"),
    target_agent: Optional[str] = Query(None, description="Filter by target agent"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List Agent-to-Agent trust policies.
    """
    from uuid import uuid4
    
    policies = [
        A2ATrustPolicy(
            id=uuid4(),
            source_agent="agent-research-001",
            target_agent="agent-code-002",
            trust_level="limited",
            allowed_operations=["read_context", "request_review"],
            expires_at=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow() - timedelta(days=7),
        ),
        A2ATrustPolicy(
            id=uuid4(),
            source_agent="agent-orchestrator-000",
            target_agent="agent-deploy-003",
            trust_level="full",
            allowed_operations=["delegate_task", "share_context", "execute_command"],
            expires_at=None,
            created_at=datetime.utcnow() - timedelta(days=30),
        ),
    ]
    
    return policies


@router.post("/a2a/policies", status_code=status.HTTP_201_CREATED)
async def create_a2a_policy(
    source_agent: str,
    target_agent: str,
    trust_level: str = Query(..., description="Trust level: full, limited, none"),
    allowed_operations: list[str] = Query(default=[]),
    expires_in_days: Optional[int] = Query(None, description="Policy expiration in days"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new Agent-to-Agent trust policy.
    """
    from uuid import uuid4
    
    valid_trust_levels = ["full", "limited", "none"]
    if trust_level not in valid_trust_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid trust level. Must be one of: {valid_trust_levels}"
        )
    
    return {
        "id": uuid4(),
        "source_agent": source_agent,
        "target_agent": target_agent,
        "trust_level": trust_level,
        "allowed_operations": allowed_operations,
        "expires_at": datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None,
        "created_at": datetime.utcnow(),
    }


@router.delete("/a2a/policies/{policy_id}")
async def delete_a2a_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete an Agent-to-Agent trust policy.
    """
    return {"id": policy_id, "status": "deleted", "deleted_at": datetime.utcnow()}


# ============================================================================
# Real-time Monitoring Endpoints
# ============================================================================

@router.get("/monitor/alerts")
async def get_agent_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get active alerts for agent activities.
    """
    from uuid import uuid4
    
    alerts = [
        {
            "id": uuid4(),
            "severity": "high",
            "title": "Unusual tool invocation pattern",
            "description": "Agent agent-code-002 made 50+ code_execute calls in 5 minutes",
            "session_id": uuid4(),
            "agent_id": "agent-code-002",
            "acknowledged": False,
            "created_at": datetime.utcnow() - timedelta(minutes=15),
        },
        {
            "id": uuid4(),
            "severity": "critical",
            "title": "Agent attempting unauthorized resource access",
            "description": "Agent agent-deploy-003 attempted to access production secrets",
            "session_id": uuid4(),
            "agent_id": "agent-deploy-003",
            "acknowledged": False,
            "created_at": datetime.utcnow() - timedelta(minutes=5),
        },
    ]
    
    return alerts


@router.post("/monitor/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Acknowledge an agent alert.
    """
    return {
        "id": alert_id,
        "acknowledged": True,
        "acknowledged_by": current_user.get("username", "unknown"),
        "acknowledged_at": datetime.utcnow(),
    }


@router.get("/monitor/metrics")
async def get_agent_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get aggregate metrics for agent activities.
    """
    return {
        "active_sessions": 3,
        "total_actions_24h": 1247,
        "tool_calls_24h": 456,
        "tokens_consumed_24h": 2500000,
        "alerts_triggered_24h": 12,
        "high_risk_sessions": 1,
        "pending_approvals": 2,
        "avg_session_duration_min": 45,
    }
