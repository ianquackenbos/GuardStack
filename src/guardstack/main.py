"""
GuardStack FastAPI Application

Main entry point for the GuardStack API server.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

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
        """Health check endpoint for Kubernetes probes."""
        return JSONResponse(
            content={
                "status": "healthy",
                "version": "0.1.0",
            }
        )
    
    @app.get("/ready", tags=["health"])
    async def readiness_check() -> JSONResponse:
        """Readiness check endpoint for Kubernetes probes."""
        # TODO: Check database and Redis connectivity
        return JSONResponse(
            content={
                "status": "ready",
                "checks": {
                    "database": "ok",
                    "redis": "ok",
                    "argo": "ok",
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
