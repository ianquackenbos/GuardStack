"""
GuardStack Services

Backend services for database, caching, storage, workflows, auth, and guardrails.
"""

from guardstack.services.database import (
    DatabaseService,
    VectorStore,
    get_database,
    init_database,
    close_database,
    AsyncSessionLocal,
    User,
)
from guardstack.services.cache import (
    RedisService,
    CacheConfig,
    get_redis,
    close_redis,
)
from guardstack.services.storage import (
    StorageService,
    StorageConfig,
    get_storage,
    init_storage,
)
from guardstack.services.connectors import (
    ConnectorService,
    BaseConnector,
    ConnectorTestResult,
    ConnectorHealthStatus,
    get_connector_service,
)
from guardstack.services.argo import (
    ArgoWorkflowService,
    EvaluationWorkflowService,
    WorkflowStatus,
    WorkflowSubmitResult,
    get_argo_service,
    get_evaluation_workflow_service,
)
from guardstack.services.auth import (
    JWTAuthService,
    APIKeyAuthService,
    TokenPayload,
    get_jwt_auth_service,
    get_api_key_auth_service,
)
from guardstack.services.guardrails import (
    GuardrailService,
    PIIDetector,
    ToxicityDetector,
    JailbreakDetector,
    GuardrailResult,
    Violation,
    get_guardrail_service,
)

__all__ = [
    # Database
    "DatabaseService",
    "VectorStore",
    "get_database",
    "init_database",
    "close_database",
    "AsyncSessionLocal",
    "User",
    # Cache
    "RedisService",
    "CacheConfig",
    "get_redis",
    "close_redis",
    # Storage
    "StorageService",
    "StorageConfig",
    "get_storage",
    "init_storage",
    # Connectors
    "ConnectorService",
    "BaseConnector",
    "ConnectorTestResult",
    "ConnectorHealthStatus",
    "get_connector_service",
    # Argo Workflows
    "ArgoWorkflowService",
    "EvaluationWorkflowService",
    "WorkflowStatus",
    "WorkflowSubmitResult",
    "get_argo_service",
    "get_evaluation_workflow_service",
    # Auth
    "JWTAuthService",
    "APIKeyAuthService",
    "TokenPayload",
    "get_jwt_auth_service",
    "get_api_key_auth_service",
    # Guardrails
    "GuardrailService",
    "PIIDetector",
    "ToxicityDetector",
    "JailbreakDetector",
    "GuardrailResult",
    "Violation",
    "get_guardrail_service",
]
