"""phase 3 ai recommendations

Revision ID: 0003_phase3_ai_recommendations
Revises: 0002_phase2_events_outages
Create Date: 2026-06-01 12:45:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_phase3_ai_recommendations"
down_revision: str | Sequence[str] | None = "0002_phase2_events_outages"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("input_context_hash", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_sanitized", sa.Text(), nullable=False),
        sa.Column("sanitized_context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recommendation", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("advisory_only", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], name=op.f("fk_ai_recommendations_alert_id_alerts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_recommendations")),
        sa.UniqueConstraint("alert_id", name=op.f("uq_ai_recommendations_alert_id")),
    )
    op.create_index(
        "ix_ai_recommendations_alert_context",
        "ai_recommendations",
        ["alert_id", "input_context_hash"],
        unique=False,
    )
    op.create_index(op.f("ix_ai_recommendations_alert_id"), "ai_recommendations", ["alert_id"], unique=False)
    op.create_index(
        op.f("ix_ai_recommendations_created_at"),
        "ai_recommendations",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ai_recommendations_input_context_hash"),
        "ai_recommendations",
        ["input_context_hash"],
        unique=False,
    )
    op.create_index(op.f("ix_ai_recommendations_provider"), "ai_recommendations", ["provider"], unique=False)
    op.create_index(
        "ix_ai_recommendations_provider_created",
        "ai_recommendations",
        ["provider", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ai_recommendations_provider_created", table_name="ai_recommendations")
    op.drop_index(op.f("ix_ai_recommendations_provider"), table_name="ai_recommendations")
    op.drop_index(op.f("ix_ai_recommendations_input_context_hash"), table_name="ai_recommendations")
    op.drop_index(op.f("ix_ai_recommendations_created_at"), table_name="ai_recommendations")
    op.drop_index(op.f("ix_ai_recommendations_alert_id"), table_name="ai_recommendations")
    op.drop_index("ix_ai_recommendations_alert_context", table_name="ai_recommendations")
    op.drop_table("ai_recommendations")
