"""Add vector embeddings support

Revision ID: 002_add_embeddings
Revises: 001_initial_schema
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_add_embeddings"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create embeddings table for semantic search and similarity
    op.create_table(
        "embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("entity_type", sa.String(50), nullable=False),  # model, evaluation, document
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),  # description, result, documentation
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", sa.Column("vector(1536)")),  # OpenAI ada-002 dimension
        sa.Column("model_name", sa.String(100), server_default="'text-embedding-ada-002'"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    # Use raw SQL for vector column since SQLAlchemy doesn't natively support it
    op.execute("""
        ALTER TABLE embeddings 
        ADD COLUMN IF NOT EXISTS embedding vector(1536)
    """)
    
    # Create indexes
    op.create_index("idx_embeddings_entity", "embeddings", ["entity_type", "entity_id"])
    op.create_index("idx_embeddings_content_hash", "embeddings", ["content_hash"])
    
    # Create vector similarity index (IVFFlat for approximate nearest neighbor)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_embeddings_vector 
        ON embeddings 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)
    
    # Create model_documentation table for RAG
    op.create_table(
        "model_documentation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("doc_type", sa.String(50)),  # readme, api_doc, changelog, license
        sa.Column("source_url", sa.String(500)),
        sa.Column("version", sa.String(50)),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_model_documentation_model_id", "model_documentation", ["model_id"])
    
    # Create trigger for updated_at
    op.execute("""
        CREATE TRIGGER update_model_documentation_updated_at
            BEFORE UPDATE ON model_documentation
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create evaluation_artifacts table for storing test datasets, outputs
    op.create_table(
        "evaluation_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("evaluation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_type", sa.String(50), nullable=False),  # dataset, output, log, report
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),  # S3/MinIO path
        sa.Column("size_bytes", sa.BigInteger),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("checksum", sa.String(64)),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_evaluation_artifacts_evaluation_id", "evaluation_artifacts", ["evaluation_id"])
    op.create_index("idx_evaluation_artifacts_type", "evaluation_artifacts", ["artifact_type"])


def downgrade() -> None:
    op.drop_table("evaluation_artifacts")
    op.execute("DROP TRIGGER IF EXISTS update_model_documentation_updated_at ON model_documentation")
    op.drop_table("model_documentation")
    op.execute("DROP INDEX IF EXISTS idx_embeddings_vector")
    op.drop_table("embeddings")
