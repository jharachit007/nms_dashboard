"""phase 6 performance indexes

Revision ID: 0005_phase6_performance_indexes
Revises: 0004_phase4_feedback_chat_learning
Create Date: 2026-06-01 15:09:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0005_phase6_performance_indexes"
down_revision: str | Sequence[str] | None = "0004_phase4_feedback_chat_learning"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_alerts_severity_last_event_time "
        "ON alerts (severity, last_event_time DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_alerts_lifecycle_last_event_time "
        "ON alerts (lifecycle_status, last_event_time DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_alerts_node_last_event_time "
        "ON alerts (node_id, last_event_time DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_alerts_critical_active_time "
        "ON alerts (last_event_time DESC) "
        "WHERE severity = 'CRITICAL' AND lifecycle_status IN ('ACTIVE', 'ACKNOWLEDGED')"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_nodes_operator_circle_server_type "
        "ON nodes (operator, circle, server_type)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_events_node_severity_time "
        "ON events (node_id, severity, event_time DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_feedback_alert_created_at "
        "ON feedback (alert_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chat_messages_alert_created_at_desc "
        "ON chat_messages (alert_id, created_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chat_messages_alert_created_at_desc")
    op.execute("DROP INDEX IF EXISTS ix_feedback_alert_created_at")
    op.execute("DROP INDEX IF EXISTS ix_events_node_severity_time")
    op.execute("DROP INDEX IF EXISTS ix_nodes_operator_circle_server_type")
    op.execute("DROP INDEX IF EXISTS ix_alerts_critical_active_time")
    op.execute("DROP INDEX IF EXISTS ix_alerts_node_last_event_time")
    op.execute("DROP INDEX IF EXISTS ix_alerts_lifecycle_last_event_time")
    op.execute("DROP INDEX IF EXISTS ix_alerts_severity_last_event_time")
