"""phase 4 feedback chat learning

Revision ID: 0004_phase4_feedback_chat_learning
Revises: 0003_phase3_ai_recommendations
Create Date: 2026-06-01 12:54:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_phase4_feedback_chat_learning"
down_revision: str | Sequence[str] | None = "0003_phase3_ai_recommendations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("feedback", sa.Column("ai_recommendation_id", sa.Integer(), nullable=True))
    op.add_column("feedback", sa.Column("feedback_type", sa.String(length=32), nullable=True))
    op.add_column("feedback", sa.Column("resolution_status", sa.String(length=32), nullable=True))
    op.add_column("feedback", sa.Column("resolution_time", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "feedback",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_foreign_key(
        op.f("fk_feedback_ai_recommendation_id_ai_recommendations"),
        "feedback",
        "ai_recommendations",
        ["ai_recommendation_id"],
        ["id"],
    )
    op.create_index(op.f("ix_feedback_ai_recommendation_id"), "feedback", ["ai_recommendation_id"], unique=False)
    op.create_index("ix_feedback_alert_recommendation", "feedback", ["alert_id", "ai_recommendation_id"], unique=False)
    op.create_index(op.f("ix_feedback_feedback_type"), "feedback", ["feedback_type"], unique=False)
    op.create_index(op.f("ix_feedback_resolution_status"), "feedback", ["resolution_status"], unique=False)
    op.create_unique_constraint(
        "uq_feedback_alert_recommendation_user",
        "feedback",
        ["alert_id", "ai_recommendation_id", "user_id"],
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=256), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], name=op.f("fk_chat_sessions_alert_id_alerts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_sessions")),
    )
    op.create_index(op.f("ix_chat_sessions_alert_id"), "chat_sessions", ["alert_id"], unique=False)
    op.create_index("ix_chat_sessions_alert_user", "chat_sessions", ["alert_id", "user_id"], unique=False)
    op.create_index(op.f("ix_chat_sessions_created_at"), "chat_sessions", ["created_at"], unique=False)
    op.create_index(op.f("ix_chat_sessions_status"), "chat_sessions", ["status"], unique=False)
    op.create_index(op.f("ix_chat_sessions_user_id"), "chat_sessions", ["user_id"], unique=False)

    op.add_column("chat_messages", sa.Column("session_id", sa.Integer(), nullable=True))
    op.add_column("chat_messages", sa.Column("ai_recommendation_id", sa.Integer(), nullable=True))
    op.add_column("chat_messages", sa.Column("context_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("chat_messages", sa.Column("provider", sa.String(length=64), nullable=True))
    op.add_column("chat_messages", sa.Column("model_name", sa.String(length=128), nullable=True))
    op.add_column(
        "chat_messages",
        sa.Column("advisory_only", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.create_foreign_key(
        op.f("fk_chat_messages_session_id_chat_sessions"),
        "chat_messages",
        "chat_sessions",
        ["session_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_chat_messages_ai_recommendation_id_ai_recommendations"),
        "chat_messages",
        "ai_recommendations",
        ["ai_recommendation_id"],
        ["id"],
    )
    op.create_index(op.f("ix_chat_messages_ai_recommendation_id"), "chat_messages", ["ai_recommendation_id"], unique=False)
    op.create_index(op.f("ix_chat_messages_session_id"), "chat_messages", ["session_id"], unique=False)
    op.create_index("ix_chat_messages_session_created", "chat_messages", ["session_id", "created_at"], unique=False)

    op.create_table(
        "incident_learning_store",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("ai_recommendation_id", sa.Integer(), nullable=False),
        sa.Column("feedback_id", sa.Integer(), nullable=False),
        sa.Column("feedback_type", sa.String(length=32), nullable=False),
        sa.Column("resolution_status", sa.String(length=32), nullable=False),
        sa.Column("learning_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], name=op.f("fk_incident_learning_store_alert_id_alerts")),
        sa.ForeignKeyConstraint(
            ["ai_recommendation_id"],
            ["ai_recommendations.id"],
            name=op.f("fk_incident_learning_store_ai_recommendation_id_ai_recommendations"),
        ),
        sa.ForeignKeyConstraint(["feedback_id"], ["feedback.id"], name=op.f("fk_incident_learning_store_feedback_id_feedback")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incident_learning_store")),
        sa.UniqueConstraint("feedback_id", name="uq_incident_learning_store_feedback_id"),
    )
    op.create_index(op.f("ix_incident_learning_store_alert_id"), "incident_learning_store", ["alert_id"], unique=False)
    op.create_index(
        op.f("ix_incident_learning_store_ai_recommendation_id"),
        "incident_learning_store",
        ["ai_recommendation_id"],
        unique=False,
    )
    op.create_index(op.f("ix_incident_learning_store_created_at"), "incident_learning_store", ["created_at"], unique=False)
    op.create_index(op.f("ix_incident_learning_store_feedback_id"), "incident_learning_store", ["feedback_id"], unique=False)
    op.create_index(op.f("ix_incident_learning_store_feedback_type"), "incident_learning_store", ["feedback_type"], unique=False)
    op.create_index(
        "ix_learning_alert_resolution",
        "incident_learning_store",
        ["alert_id", "resolution_status"],
        unique=False,
    )
    op.create_index(
        "ix_learning_recommendation_feedback",
        "incident_learning_store",
        ["ai_recommendation_id", "feedback_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_learning_store_resolution_status"),
        "incident_learning_store",
        ["resolution_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_incident_learning_store_resolution_status"), table_name="incident_learning_store")
    op.drop_index("ix_learning_recommendation_feedback", table_name="incident_learning_store")
    op.drop_index("ix_learning_alert_resolution", table_name="incident_learning_store")
    op.drop_index(op.f("ix_incident_learning_store_feedback_type"), table_name="incident_learning_store")
    op.drop_index(op.f("ix_incident_learning_store_feedback_id"), table_name="incident_learning_store")
    op.drop_index(op.f("ix_incident_learning_store_created_at"), table_name="incident_learning_store")
    op.drop_index(op.f("ix_incident_learning_store_ai_recommendation_id"), table_name="incident_learning_store")
    op.drop_index(op.f("ix_incident_learning_store_alert_id"), table_name="incident_learning_store")
    op.drop_table("incident_learning_store")

    op.drop_index("ix_chat_messages_session_created", table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_session_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_ai_recommendation_id"), table_name="chat_messages")
    op.drop_constraint(op.f("fk_chat_messages_ai_recommendation_id_ai_recommendations"), "chat_messages", type_="foreignkey")
    op.drop_constraint(op.f("fk_chat_messages_session_id_chat_sessions"), "chat_messages", type_="foreignkey")
    op.drop_column("chat_messages", "advisory_only")
    op.drop_column("chat_messages", "model_name")
    op.drop_column("chat_messages", "provider")
    op.drop_column("chat_messages", "context_snapshot")
    op.drop_column("chat_messages", "ai_recommendation_id")
    op.drop_column("chat_messages", "session_id")

    op.drop_index(op.f("ix_chat_sessions_user_id"), table_name="chat_sessions")
    op.drop_index(op.f("ix_chat_sessions_status"), table_name="chat_sessions")
    op.drop_index(op.f("ix_chat_sessions_created_at"), table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_alert_user", table_name="chat_sessions")
    op.drop_index(op.f("ix_chat_sessions_alert_id"), table_name="chat_sessions")
    op.drop_table("chat_sessions")

    op.drop_constraint("uq_feedback_alert_recommendation_user", "feedback", type_="unique")
    op.drop_index(op.f("ix_feedback_resolution_status"), table_name="feedback")
    op.drop_index(op.f("ix_feedback_feedback_type"), table_name="feedback")
    op.drop_index("ix_feedback_alert_recommendation", table_name="feedback")
    op.drop_index(op.f("ix_feedback_ai_recommendation_id"), table_name="feedback")
    op.drop_constraint(op.f("fk_feedback_ai_recommendation_id_ai_recommendations"), "feedback", type_="foreignkey")
    op.drop_column("feedback", "updated_at")
    op.drop_column("feedback", "resolution_time")
    op.drop_column("feedback", "resolution_status")
    op.drop_column("feedback", "feedback_type")
    op.drop_column("feedback", "ai_recommendation_id")
