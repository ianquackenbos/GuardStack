"""Add dashboard and analytics tables

Revision ID: 004_add_dashboard_tables
Revises: 003_add_agentic_tables
Create Date: 2024-01-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_add_dashboard_tables"
down_revision: Union[str, None] = "003_add_agentic_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create dashboard_metrics table for time-series metrics
    op.create_table(
        "dashboard_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_type", sa.String(50), nullable=False),  # counter, gauge, histogram
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("labels", postgresql.JSONB, server_default="{}"),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("models.id", ondelete="CASCADE")),
        sa.Column("connector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("connectors.id", ondelete="CASCADE")),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    
    # Create indexes for efficient time-series queries
    op.create_index("idx_dashboard_metrics_name_time", "dashboard_metrics", ["metric_name", "timestamp"])
    op.create_index("idx_dashboard_metrics_model_time", "dashboard_metrics", ["model_id", "timestamp"])
    op.create_index("idx_dashboard_metrics_timestamp", "dashboard_metrics", ["timestamp"])
    
    # Create partitioning by time for metrics (optional - for high-volume)
    # This would be done differently in production, potentially using TimescaleDB
    
    # Create aggregated_scores table for dashboard widgets
    op.create_table(
        "aggregated_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),  # hourly, daily, weekly, monthly
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("overall_score", sa.Float),
        sa.Column("pillar_scores", postgresql.JSONB, server_default="{}"),
        sa.Column("risk_distribution", postgresql.JSONB, server_default="{}"),
        sa.Column("evaluation_count", sa.Integer, server_default="0"),
        sa.Column("guardrail_block_count", sa.Integer, server_default="0"),
        sa.Column("guardrail_allow_count", sa.Integer, server_default="0"),
        sa.Column("compliance_status", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_aggregated_scores_model_period", "aggregated_scores", ["model_id", "period", "period_start"])
    op.create_unique_constraint("uq_aggregated_scores_model_period_start", "aggregated_scores", ["model_id", "period", "period_start"])
    
    # Create alerts table for threshold violations and anomalies
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("alert_type", sa.String(50), nullable=False),  # threshold_violation, anomaly, compliance_failure
        sa.Column("severity", postgresql.ENUM("critical", "high", "medium", "low", "minimal", name="risk_level", create_type=False), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("models.id", ondelete="CASCADE")),
        sa.Column("evaluation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluations.id", ondelete="CASCADE")),
        sa.Column("metric_name", sa.String(100)),
        sa.Column("metric_value", sa.Float),
        sa.Column("threshold_value", sa.Float),
        sa.Column("context", postgresql.JSONB, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="'open'"),  # open, acknowledged, resolved, dismissed
        sa.Column("acknowledged_by", sa.String(255)),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", sa.String(255)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("idx_alerts_severity_status", "alerts", ["severity", "status"])
    op.create_index("idx_alerts_model_id", "alerts", ["model_id"])
    op.create_index("idx_alerts_created_at", "alerts", ["created_at"])
    
    # Create alert_rules table for configuring alert conditions
    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("rule_type", sa.String(50), nullable=False),  # threshold, anomaly, pattern
        sa.Column("metric_name", sa.String(100)),
        sa.Column("condition", postgresql.JSONB, nullable=False),  # operator, value, duration
        sa.Column("severity", postgresql.ENUM("critical", "high", "medium", "low", "minimal", name="risk_level", create_type=False)),
        sa.Column("applies_to", postgresql.JSONB, server_default="{}"),  # model_ids, model_types, tags
        sa.Column("notification_channels", postgresql.ARRAY(sa.String(50)), server_default="{}"),  # email, slack, webhook
        sa.Column("cooldown_minutes", sa.Integer, server_default="60"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.String(255)),
    )
    
    op.create_index("idx_alert_rules_is_active", "alert_rules", ["is_active"])
    
    # Create user_preferences table for dashboard customization
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", sa.String(255), nullable=False, unique=True),
        sa.Column("dashboard_layout", postgresql.JSONB, server_default="{}"),
        sa.Column("default_filters", postgresql.JSONB, server_default="{}"),
        sa.Column("notification_settings", postgresql.JSONB, server_default="{}"),
        sa.Column("theme", sa.String(20), server_default="'light'"),
        sa.Column("timezone", sa.String(50), server_default="'UTC'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    # Create trigger for updated_at
    for table in ["alert_rules", "user_preferences"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
    
    # Insert default alert rules
    op.execute("""
        INSERT INTO alert_rules (name, description, rule_type, metric_name, condition, severity, is_active)
        VALUES 
        (
            'Critical Safety Score',
            'Alert when overall safety score drops below critical threshold',
            'threshold',
            'overall_score',
            '{"operator": "lt", "value": 0.3}',
            'critical',
            true
        ),
        (
            'High Guardrail Block Rate',
            'Alert when guardrail block rate exceeds threshold',
            'threshold',
            'guardrail_block_rate',
            '{"operator": "gt", "value": 0.3, "duration_minutes": 15}',
            'high',
            true
        ),
        (
            'Fairness Score Degradation',
            'Alert when fairness score drops significantly',
            'threshold',
            'fairness_score',
            '{"operator": "lt", "value": 0.5}',
            'high',
            true
        ),
        (
            'Privacy Score Warning',
            'Alert when privacy score is below acceptable level',
            'threshold',
            'privacy_score',
            '{"operator": "lt", "value": 0.6}',
            'medium',
            true
        );
    """)


def downgrade() -> None:
    # Drop triggers
    for table in ["alert_rules", "user_preferences"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")
    
    # Drop tables
    op.drop_table("user_preferences")
    op.drop_table("alert_rules")
    op.drop_table("alerts")
    op.drop_table("aggregated_scores")
    op.drop_table("dashboard_metrics")
