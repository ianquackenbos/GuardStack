"""
Database Services

Async PostgreSQL with pgvector support.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from guardstack.config import Settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Async database service with connection pooling.
    
    Provides:
    - Connection management
    - Session factory
    - Migration support
    - pgvector initialization
    """
    
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings()
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
    
    @property
    def engine(self) -> AsyncEngine:
        """Get or create the async engine."""
        if self._engine is None:
            self._engine = create_async_engine(
                self.settings.database_url.replace(
                    "postgresql://", "postgresql+asyncpg://"
                ),
                echo=self.settings.debug,
                pool_size=20,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
            )
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session with automatic cleanup.
        
        Usage:
            async with db.session() as session:
                result = await session.execute(query)
        """
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def initialize(self) -> None:
        """
        Initialize database with required extensions.
        
        Creates pgvector extension and other required setup.
        """
        async with self.engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            # Enable trigram extension for text search
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            
            # Enable UUID extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            
            logger.info("Database extensions initialized")
    
    async def create_tables(self) -> None:
        """Create all tables from SQLModel metadata."""
        from guardstack.models.core import SQLModel
        
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        
        logger.info("Database tables created")
    
    async def drop_tables(self) -> None:
        """Drop all tables (use with caution)."""
        from guardstack.models.core import SQLModel
        
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        
        logger.warning("Database tables dropped")
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")


class VectorStore:
    """
    Vector storage using pgvector.
    
    Provides:
    - Embedding storage
    - Similarity search
    - Index management
    """
    
    def __init__(self, db: DatabaseService) -> None:
        self.db = db
    
    async def create_embedding_table(
        self,
        table_name: str,
        dimensions: int = 1536,
    ) -> None:
        """Create a table for storing embeddings."""
        async with self.db.session() as session:
            await session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    content TEXT NOT NULL,
                    embedding vector({dimensions}),
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            
            # Create index for similarity search
            await session.execute(text(f"""
                CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx
                ON {table_name}
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
    
    async def insert_embedding(
        self,
        table_name: str,
        content: str,
        embedding: list[float],
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Insert an embedding and return its ID."""
        import json
        
        async with self.db.session() as session:
            result = await session.execute(
                text(f"""
                    INSERT INTO {table_name} (content, embedding, metadata)
                    VALUES (:content, :embedding, :metadata)
                    RETURNING id
                """),
                {
                    "content": content,
                    "embedding": str(embedding),
                    "metadata": json.dumps(metadata or {}),
                },
            )
            row = result.fetchone()
            return str(row[0]) if row else ""
    
    async def similarity_search(
        self,
        table_name: str,
        query_embedding: list[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Search for similar embeddings.
        
        Args:
            table_name: Table to search
            query_embedding: Query vector
            limit: Maximum results
            threshold: Minimum similarity (0-1)
        
        Returns:
            List of matching documents with scores
        """
        async with self.db.session() as session:
            result = await session.execute(
                text(f"""
                    SELECT 
                        id,
                        content,
                        metadata,
                        1 - (embedding <=> :embedding) AS similarity
                    FROM {table_name}
                    WHERE 1 - (embedding <=> :embedding) > :threshold
                    ORDER BY embedding <=> :embedding
                    LIMIT :limit
                """),
                {
                    "embedding": str(query_embedding),
                    "threshold": threshold,
                    "limit": limit,
                },
            )
            
            rows = result.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "content": row[1],
                    "metadata": row[2],
                    "similarity": float(row[3]),
                }
                for row in rows
            ]


# Global database instance
_db_service: Optional[DatabaseService] = None


def get_database() -> DatabaseService:
    """Get the global database service."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


async def init_database() -> DatabaseService:
    """Initialize and return the database service."""
    db = get_database()
    await db.initialize()
    await db.create_tables()
    return db


async def close_database() -> None:
    """Close the database service."""
    global _db_service
    if _db_service is not None:
        await _db_service.close()
        _db_service = None


# Re-export User model for convenience
from guardstack.models.core import User

# Create AsyncSessionLocal alias for dependencies
def AsyncSessionLocal():
    """Get a session from the database service."""
    db = get_database()
    return db.session_factory()
