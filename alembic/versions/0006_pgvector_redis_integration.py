"""pgvector semantic memory integration

Revision ID: 0006_pgvector_redis_integration
Revises: 0005_phase6_performance_indexes
Create Date: 2026-06-01 15:19:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006_pgvector_redis_integration"
down_revision: str | Sequence[str] | None = "0005_phase6_performance_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "incident_embeddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("node_id", sa.Integer(), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], name=op.f("fk_incident_embeddings_alert_id_alerts")),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], name=op.f("fk_incident_embeddings_node_id_nodes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incident_embeddings")),
        sa.UniqueConstraint("alert_id", name="uq_incident_embeddings_alert_id"),
    )
    op.execute("ALTER TABLE incident_embeddings ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")
    op.create_index(op.f("ix_incident_embeddings_alert_id"), "incident_embeddings", ["alert_id"], unique=False)
    op.create_index(op.f("ix_incident_embeddings_created_at"), "incident_embeddings", ["created_at"], unique=False)
    op.create_index(op.f("ix_incident_embeddings_node_id"), "incident_embeddings", ["node_id"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_incident_embeddings_embedding_ivfflat "
        "ON incident_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_incident_embeddings_embedding_ivfflat")
    op.drop_index(op.f("ix_incident_embeddings_node_id"), table_name="incident_embeddings")
    op.drop_index(op.f("ix_incident_embeddings_created_at"), table_name="incident_embeddings")
    op.drop_index(op.f("ix_incident_embeddings_alert_id"), table_name="incident_embeddings")
    op.drop_table("incident_embeddings")
