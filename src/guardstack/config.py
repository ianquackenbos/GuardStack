"""
GuardStack Configuration

Application settings loaded from environment variables.
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1
    environment: str = "development"
    
    # CORS
    cors_origins: List[str] = ["*"]
    
    # Database
    database_url: str = "postgresql+asyncpg://guardstack:guardstack@localhost:5432/guardstack"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # MinIO/S3
    s3_endpoint: str = "localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "guardstack"
    s3_secure: bool = False
    
    # Argo Workflows
    argo_namespace: str = "argo"
    argo_server: str = "argo-server.argo.svc:2746"
    
    # Model Connectors
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    huggingface_api_key: str = ""
    ollama_endpoint: str = "http://localhost:11434"
    
    # Guardrails
    guardrails_config_path: str = "/etc/guardstack/guardrails"
    
    # Scoring Thresholds
    score_pass_threshold: float = 80.0
    score_warn_threshold: float = 50.0
    
    class Config:
        env_prefix = "GUARDSTACK_"
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
