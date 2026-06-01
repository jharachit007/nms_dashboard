"""phase 1 foundation schema

Revision ID: 0001_phase1_foundation
Revises:
Create Date: 2026-06-01 12:02:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_phase1_foundation"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "nodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("opennms_id", sa.String(length=128), nullable=False),
        sa.Column("raw_label", sa.String(length=512), nullable=False),
        sa.Column("operator", sa.String(length=128), nullable=True),
        sa.Column("circle", sa.String(length=128), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("server_type", sa.String(length=128), nullable=True),
        sa.Column("raw_xml", sa.Text(), nullable=False),
        sa.Column("normalized_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nodes")),
        sa.UniqueConstraint("opennms_id", name=op.f("uq_nodes_opennms_id")),
    )
    op.create_index(op.f("ix_nodes_circle"), "nodes", ["circle"], unique=False)
    op.create_index(op.f("ix_nodes_ip_address"), "nodes", ["ip_address"], unique=False)
    op.create_index("ix_nodes_ip_server_type", "nodes", ["ip_address", "server_type"], unique=False)
    op.create_index(op.f("ix_nodes_operator"), "nodes", ["operator"], unique=False)
    op.create_index("ix_nodes_operator_circle", "nodes", ["operator", "circle"], unique=False)
    op.create_index(op.f("ix_nodes_raw_label"), "nodes", ["raw_label"], unique=False)
    op.create_index(op.f("ix_nodes_server_type"), "nodes", ["server_type"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("opennms_alarm_id", sa.String(length=128), nullable=False),
        sa.Column("node_id", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=32), nullable=False),
        sa.Column("uei", sa.String(length=512), nullable=True),
        sa.Column("log_message", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("first_event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.String(length=256), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_xml", sa.Text(), nullable=False),
        sa.Column("normalized_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], name=op.f("fk_alerts_node_id_nodes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
        sa.UniqueConstraint("opennms_alarm_id", name=op.f("uq_alerts_opennms_alarm_id")),
    )
    op.create_index("ix_alerts_node_status", "alerts", ["node_id", "lifecycle_status"], unique=False)
    op.create_index(op.f("ix_alerts_severity"), "alerts", ["severity"], unique=False)
    op.create_index("ix_alerts_severity_status", "alerts", ["severity", "lifecycle_status"], unique=False)
    op.create_index(op.f("ix_alerts_lifecycle_status"), "alerts", ["lifecycle_status"], unique=False)
    op.create_index(op.f("ix_alerts_uei"), "alerts", ["uei"], unique=False)

    op.create_table(
        "alert_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("changed_by", sa.String(length=256), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("raw_event_xml", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], name=op.f("fk_alert_history_alert_id_alerts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alert_history")),
    )
    op.create_index(op.f("ix_alert_history_alert_id"), "alert_history", ["alert_id"], unique=False)
    op.create_index(op.f("ix_alert_history_created_at"), "alert_history", ["created_at"], unique=False)

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=256), nullable=False),
        sa.Column("helpful", sa.Boolean(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], name=op.f("fk_feedback_alert_id_alerts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback")),
    )
    op.create_index(op.f("ix_feedback_alert_id"), "feedback", ["alert_id"], unique=False)
    op.create_index("ix_feedback_alert_user", "feedback", ["alert_id", "user_id"], unique=False)
    op.create_index(op.f("ix_feedback_created_at"), "feedback", ["created_at"], unique=False)
    op.create_index(op.f("ix_feedback_user_id"), "feedback", ["user_id"], unique=False)

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.String(length=256), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sanitized_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], name=op.f("fk_chat_messages_alert_id_alerts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_messages")),
    )
    op.create_index(op.f("ix_chat_messages_alert_id"), "chat_messages", ["alert_id"], unique=False)
    op.create_index("ix_chat_messages_alert_created", "chat_messages", ["alert_id", "created_at"], unique=False)
    op.create_index(op.f("ix_chat_messages_created_at"), "chat_messages", ["created_at"], unique=False)
    op.create_index(op.f("ix_chat_messages_user_id"), "chat_messages", ["user_id"], unique=False)

    op.create_table(
        "llm_responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_sanitized", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("advisory_only", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], name=op.f("fk_llm_responses_alert_id_alerts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_llm_responses")),
    )
    op.create_index(op.f("ix_llm_responses_alert_id"), "llm_responses", ["alert_id"], unique=False)
    op.create_index(op.f("ix_llm_responses_created_at"), "llm_responses", ["created_at"], unique=False)
    op.create_index("ix_llm_responses_provider_created", "llm_responses", ["provider", "created_at"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=256), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_type", sa.String(length=128), nullable=True),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_action_created", "audit_logs", ["action", "created_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_type"), "audit_logs", ["resource_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_index("ix_audit_logs_user_created", "audit_logs", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_user_created", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_created", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_llm_responses_provider_created", table_name="llm_responses")
    op.drop_index(op.f("ix_llm_responses_created_at"), table_name="llm_responses")
    op.drop_index(op.f("ix_llm_responses_alert_id"), table_name="llm_responses")
    op.drop_table("llm_responses")

    op.drop_index(op.f("ix_chat_messages_user_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_created_at"), table_name="chat_messages")
    op.drop_index("ix_chat_messages_alert_created", table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_alert_id"), table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index(op.f("ix_feedback_user_id"), table_name="feedback")
    op.drop_index(op.f("ix_feedback_created_at"), table_name="feedback")
    op.drop_index("ix_feedback_alert_user", table_name="feedback")
    op.drop_index(op.f("ix_feedback_alert_id"), table_name="feedback")
    op.drop_table("feedback")

    op.drop_index(op.f("ix_alert_history_created_at"), table_name="alert_history")
    op.drop_index(op.f("ix_alert_history_alert_id"), table_name="alert_history")
    op.drop_table("alert_history")

    op.drop_index(op.f("ix_alerts_uei"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_lifecycle_status"), table_name="alerts")
    op.drop_index("ix_alerts_severity_status", table_name="alerts")
    op.drop_index(op.f("ix_alerts_severity"), table_name="alerts")
    op.drop_index("ix_alerts_node_status", table_name="alerts")
    op.drop_table("alerts")

    op.drop_index(op.f("ix_nodes_server_type"), table_name="nodes")
    op.drop_index(op.f("ix_nodes_raw_label"), table_name="nodes")
    op.drop_index("ix_nodes_operator_circle", table_name="nodes")
    op.drop_index(op.f("ix_nodes_operator"), table_name="nodes")
    op.drop_index("ix_nodes_ip_server_type", table_name="nodes")
    op.drop_index(op.f("ix_nodes_ip_address"), table_name="nodes")
    op.drop_index(op.f("ix_nodes_circle"), table_name="nodes")
    op.drop_table("nodes")
