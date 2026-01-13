"""Initial schema creation

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"vector\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\"")
    
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE model_type AS ENUM ('predictive', 'generative', 'agentic');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE evaluation_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_level AS ENUM ('critical', 'high', 'medium', 'low', 'minimal');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE connector_type AS ENUM ('openai', 'anthropic', 'azure_openai', 'bedrock', 'vertex', 'huggingface', 'ollama', 'custom');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create models table
    op.create_table(
        "models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("type", postgresql.ENUM("predictive", "generative", "agentic", name="model_type", create_type=False), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("framework", sa.String(50)),
        sa.Column("task_type", sa.String(100)),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("tags", postgresql.ARRAY(sa.String(50)), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.String(255)),
    )
    
    op.create_index("idx_models_name", "models", ["name"])
    op.create_index("idx_models_type", "models", ["type"])
    op.create_index("idx_models_tags", "models", ["tags"], postgresql_using="gin")
    
    # Create evaluations table
    op.create_table(
        "evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", postgresql.ENUM("pending", "running", "completed", "failed", "cancelled", name="evaluation_status", create_type=False), nullable=False, server_default="pending"),
        sa.Column("pillars", postgresql.ARRAY(sa.String(50)), nullable=False),
        sa.Column("config", postgresql.JSONB, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.String(255)),
    )
    
    op.create_index("idx_evaluations_model_id", "evaluations", ["model_id"])
    op.create_index("idx_evaluations_status", "evaluations", ["status"])
    op.create_index("idx_evaluations_created_at", "evaluations", ["created_at"])
    
    # Create evaluation_results table
    op.create_table(
        "evaluation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("evaluation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pillar", sa.String(50), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("risk_level", postgresql.ENUM("critical", "high", "medium", "low", "minimal", name="risk_level", create_type=False)),
        sa.Column("metrics", postgresql.JSONB, server_default="{}"),
        sa.Column("details", postgresql.JSONB, server_default="{}"),
        sa.Column("recommendations", postgresql.ARRAY(sa.Text), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_evaluation_results_evaluation_id", "evaluation_results", ["evaluation_id"])
    op.create_index("idx_evaluation_results_pillar", "evaluation_results", ["pillar"])
    
    # Create connectors table
    op.create_table(
        "connectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("type", postgresql.ENUM("openai", "anthropic", "azure_openai", "bedrock", "vertex", "huggingface", "ollama", "custom", name="connector_type", create_type=False), nullable=False),
        sa.Column("config", postgresql.JSONB, server_default="{}"),
        sa.Column("credentials_encrypted", sa.LargeBinary),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("last_health_check", sa.DateTime(timezone=True)),
        sa.Column("health_status", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_connectors_type", "connectors", ["type"])
    op.create_index("idx_connectors_is_active", "connectors", ["is_active"])
    
    # Create guardrail_policies table
    op.create_table(
        "guardrail_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0"),
        sa.Column("rules", postgresql.JSONB, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.String(255)),
    )
    
    op.create_index("idx_guardrail_policies_is_active", "guardrail_policies", ["is_active"])
    
    # Create guardrail_events table
    op.create_table(
        "guardrail_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("guardrail_policies.id", ondelete="SET NULL")),
        sa.Column("connector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("connectors.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("input_hash", sa.String(64)),
        sa.Column("triggered_rules", postgresql.ARRAY(sa.String(100))),
        sa.Column("reasons", postgresql.ARRAY(sa.Text)),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_guardrail_events_policy_id", "guardrail_events", ["policy_id"])
    op.create_index("idx_guardrail_events_connector_id", "guardrail_events", ["connector_id"])
    op.create_index("idx_guardrail_events_action", "guardrail_events", ["action"])
    op.create_index("idx_guardrail_events_created_at", "guardrail_events", ["created_at"])
    
    # Create compliance_reports table
    op.create_table(
        "compliance_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("framework", sa.String(50), nullable=False),
        sa.Column("overall_score", sa.Float),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("controls_assessed", sa.Integer),
        sa.Column("controls_passed", sa.Integer),
        sa.Column("controls_failed", sa.Integer),
        sa.Column("findings", postgresql.JSONB, server_default="{}"),
        sa.Column("recommendations", postgresql.ARRAY(sa.Text)),
        sa.Column("report_data", postgresql.JSONB),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("generated_by", sa.String(255)),
    )
    
    op.create_index("idx_compliance_reports_model_id", "compliance_reports", ["model_id"])
    op.create_index("idx_compliance_reports_framework", "compliance_reports", ["framework"])
    
    # Create spm_inventory table (Software Product Model inventory)
    op.create_table(
        "spm_inventory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("model_type", sa.String(50)),
        sa.Column("source", sa.String(255)),
        sa.Column("license", sa.String(100)),
        sa.Column("risk_score", sa.Float),
        sa.Column("vulnerabilities", postgresql.JSONB, server_default="[]"),
        sa.Column("dependencies", postgresql.JSONB, server_default="[]"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_spm_inventory_name", "spm_inventory", ["name"])
    op.create_index("idx_spm_inventory_risk_score", "spm_inventory", ["risk_score"])
    
    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("actor", sa.String(255)),
        sa.Column("changes", postgresql.JSONB, server_default="{}"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_logs_actor", "audit_logs", ["actor"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
    
    # Create function for updated_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for updated_at
    for table in ["models", "connectors", "guardrail_policies", "spm_inventory"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers
    for table in ["models", "connectors", "guardrail_policies", "spm_inventory"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables in reverse order
    op.drop_table("audit_logs")
    op.drop_table("spm_inventory")
    op.drop_table("compliance_reports")
    op.drop_table("guardrail_events")
    op.drop_table("guardrail_policies")
    op.drop_table("connectors")
    op.drop_table("evaluation_results")
    op.drop_table("evaluations")
    op.drop_table("models")
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS connector_type")
    op.execute("DROP TYPE IF EXISTS risk_level")
    op.execute("DROP TYPE IF EXISTS evaluation_status")
    op.execute("DROP TYPE IF EXISTS model_type")
    
    # Drop extensions (optional - may be used by other databases)
    # op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    # op.execute("DROP EXTENSION IF EXISTS vector")
    # op.execute("DROP EXTENSION IF EXISTS \"uuid-ossp\"")
