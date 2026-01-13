"""Add agentic AI evaluation tables

Revision ID: 003_add_agentic_tables
Revises: 002_add_embeddings
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_add_agentic_tables"
down_revision: Union[str, None] = "002_add_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum for tool categories
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tool_category AS ENUM (
                'file_system', 'network', 'database', 'api', 
                'code_execution', 'shell', 'browser', 'other'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create enum for permission levels
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE permission_level AS ENUM ('allow', 'deny', 'ask', 'audit');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create agent_tools table for registering tools available to agents
    op.create_table(
        "agent_tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("category", postgresql.ENUM("file_system", "network", "database", "api", "code_execution", "shell", "browser", "other", name="tool_category", create_type=False)),
        sa.Column("schema", postgresql.JSONB, nullable=False),  # JSON Schema for parameters
        sa.Column("risk_level", postgresql.ENUM("critical", "high", "medium", "low", "minimal", name="risk_level", create_type=False)),
        sa.Column("requires_approval", sa.Boolean, server_default="false"),
        sa.Column("allowed_parameters", postgresql.JSONB, server_default="{}"),
        sa.Column("blocked_parameters", postgresql.JSONB, server_default="{}"),
        sa.Column("rate_limit", sa.Integer),  # calls per minute
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_agent_tools_category", "agent_tools", ["category"])
    op.create_index("idx_agent_tools_risk_level", "agent_tools", ["risk_level"])
    
    # Create agent_sessions table for tracking agent execution sessions
    op.create_table(
        "agent_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("models.id", ondelete="CASCADE")),
        sa.Column("connector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("connectors.id", ondelete="SET NULL")),
        sa.Column("session_type", sa.String(50)),  # interactive, batch, evaluation
        sa.Column("status", sa.String(50), nullable=False, server_default="'active'"),
        sa.Column("config", postgresql.JSONB, server_default="{}"),
        sa.Column("sandbox_config", postgresql.JSONB, server_default="{}"),
        sa.Column("total_steps", sa.Integer, server_default="0"),
        sa.Column("total_tool_calls", sa.Integer, server_default="0"),
        sa.Column("total_tokens", sa.Integer, server_default="0"),
        sa.Column("error_count", sa.Integer, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(255)),
    )
    
    op.create_index("idx_agent_sessions_model_id", "agent_sessions", ["model_id"])
    op.create_index("idx_agent_sessions_status", "agent_sessions", ["status"])
    op.create_index("idx_agent_sessions_started_at", "agent_sessions", ["started_at"])
    
    # Create agent_tool_calls table for logging all tool invocations
    op.create_table(
        "agent_tool_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_tools.id", ondelete="SET NULL")),
        sa.Column("tool_name", sa.String(255), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("input_parameters", postgresql.JSONB),
        sa.Column("output_result", postgresql.JSONB),
        sa.Column("permission", postgresql.ENUM("allow", "deny", "ask", "audit", name="permission_level", create_type=False)),
        sa.Column("was_blocked", sa.Boolean, server_default="false"),
        sa.Column("block_reason", sa.Text),
        sa.Column("execution_time_ms", sa.Float),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_agent_tool_calls_session_id", "agent_tool_calls", ["session_id"])
    op.create_index("idx_agent_tool_calls_tool_id", "agent_tool_calls", ["tool_id"])
    op.create_index("idx_agent_tool_calls_was_blocked", "agent_tool_calls", ["was_blocked"])
    
    # Create agent_policies table for defining security policies for agents
    op.create_table(
        "agent_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("tool_permissions", postgresql.JSONB, server_default="{}"),  # tool_name -> permission
        sa.Column("resource_limits", postgresql.JSONB, server_default="{}"),  # max_steps, max_time, etc.
        sa.Column("sandbox_rules", postgresql.JSONB, server_default="{}"),
        sa.Column("allowed_domains", postgresql.ARRAY(sa.String(255)), server_default="{}"),
        sa.Column("blocked_domains", postgresql.ARRAY(sa.String(255)), server_default="{}"),
        sa.Column("allowed_paths", postgresql.ARRAY(sa.String(500)), server_default="{}"),
        sa.Column("blocked_paths", postgresql.ARRAY(sa.String(500)), server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.String(255)),
    )
    
    op.create_index("idx_agent_policies_is_active", "agent_policies", ["is_active"])
    
    # Link models to policies (many-to-many)
    op.create_table(
        "model_agent_policies",
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("models.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_policies.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    # Create triggers for updated_at
    for table in ["agent_tools", "agent_policies"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers
    for table in ["agent_tools", "agent_policies"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")
    
    # Drop tables
    op.drop_table("model_agent_policies")
    op.drop_table("agent_policies")
    op.drop_table("agent_tool_calls")
    op.drop_table("agent_sessions")
    op.drop_table("agent_tools")
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS permission_level")
    op.execute("DROP TYPE IF EXISTS tool_category")
