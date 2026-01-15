"""
GuardStack FastAPI Application

Main entry point for the GuardStack API server.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from guardstack.api.routers import (
    models,
    evaluations,
    dashboard,
    compliance,
    guardrails,
    connectors,
    websocket,
    spm,
    agentic,
    reports,
    workflows,
    inventory,
)
from guardstack.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("Starting GuardStack API server...")
    logger.info(f"Environment: {settings.environment}")
    
    # Initialize database connection pool
    # await init_db()
    
    # Initialize Redis connection
    # await init_redis()
    
    yield
    
    # Shutdown
    logger.info("Shutting down GuardStack API server...")
    # await close_db()
    # await close_redis()


async def check_postgres() -> tuple[bool, str]:
    """Check PostgreSQL database connectivity."""
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host=settings.database_host,
            port=settings.database_port,
            user=settings.database_user,
            password=settings.database_password,
            database=settings.database_name,
            timeout=5.0,
        )
        await conn.fetchval("SELECT 1")
        await conn.close()
        return True, "connected"
    except ImportError:
        # asyncpg not installed, skip check
        return True, "skipped (asyncpg not installed)"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return False, str(e)


async def check_redis() -> tuple[bool, str]:
    """Check Redis connectivity."""
    try:
        import redis.asyncio as aioredis
        client = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True,
        )
        await client.ping()
        await client.aclose()
        return True, "connected"
    except ImportError:
        return True, "skipped (redis not installed)"
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False, str(e)


async def check_argo() -> tuple[bool, str]:
    """Check Argo Workflows server connectivity."""
    try:
        argo_url = getattr(settings, "argo_server_url", "http://argo-server:2746")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{argo_url}/api/v1/version")
            if response.status_code == 200:
                return True, "connected"
            return False, f"status {response.status_code}"
    except Exception as e:
        logger.warning(f"Argo health check failed: {e}")
        return False, str(e)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="GuardStack API",
        description="AI Safety & Security Platform API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(
        models.router,
        prefix="/api/v1/models",
        tags=["models"],
    )
    app.include_router(
        evaluations.router,
        prefix="/api/v1/evaluations",
        tags=["evaluations"],
    )
    app.include_router(
        dashboard.router,
        prefix="/api/v1/dashboard",
        tags=["dashboard"],
    )
    app.include_router(
        compliance.router,
        prefix="/api/v1/compliance",
        tags=["compliance"],
    )
    app.include_router(
        guardrails.router,
        prefix="/api/v1/guardrails",
        tags=["guardrails"],
    )
    app.include_router(
        connectors.router,
        prefix="/api/v1/connectors",
        tags=["connectors"],
    )
    
    # New routers for AI-SPM, Agentic, Reports, Workflows, Inventory
    app.include_router(
        spm.router,
        prefix="/api/v1/spm",
        tags=["ai-spm"],
    )
    app.include_router(
        agentic.router,
        prefix="/api/v1/agentic",
        tags=["agentic"],
    )
    app.include_router(
        reports.router,
        prefix="/api/v1/reports",
        tags=["reports"],
    )
    app.include_router(
        workflows.router,
        prefix="/api/v1/workflows",
        tags=["workflows"],
    )
    app.include_router(
        inventory.router,
        prefix="/api/v1/inventory",
        tags=["inventory"],
    )
    
    # WebSocket router (no prefix, uses /ws)
    app.include_router(
        websocket.router,
        tags=["websocket"],
    )
    
    @app.get("/health", tags=["health"])
    async def health_check() -> JSONResponse:
        """Health check endpoint for Kubernetes liveness probes."""
        return JSONResponse(
            content={
                "status": "healthy",
                "version": "0.1.0",
            }
        )
    
    @app.get("/ready", tags=["health"])
    async def readiness_check() -> JSONResponse:
        """
        Readiness check endpoint for Kubernetes readiness probes.
        
        Checks connectivity to all backend services:
        - PostgreSQL database
        - Redis cache
        - Argo Workflows server
        """
        db_ok, db_msg = await check_postgres()
        redis_ok, redis_msg = await check_redis()
        argo_ok, argo_msg = await check_argo()
        
        all_ok = db_ok and redis_ok and argo_ok
        
        return JSONResponse(
            status_code=200 if all_ok else 503,
            content={
                "status": "ready" if all_ok else "degraded",
                "checks": {
                    "database": {"status": "ok" if db_ok else "error", "message": db_msg},
                    "redis": {"status": "ok" if redis_ok else "error", "message": redis_msg},
                    "argo": {"status": "ok" if argo_ok else "error", "message": argo_msg},
                }
            }
        )
    
    return app


# Create application instance
app = create_app()


def cli() -> None:
    """CLI entry point for running the server."""
    import uvicorn
    
    uvicorn.run(
        "guardstack.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers,
    )


if __name__ == "__main__":
    cli()
