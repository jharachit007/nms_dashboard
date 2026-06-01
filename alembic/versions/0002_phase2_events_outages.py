"""phase 2 event and outage ingestion schema

Revision ID: 0002_phase2_events_outages
Revises: 0001_phase1_foundation
Create Date: 2026-06-01 12:30:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase2_events_outages"
down_revision: str | Sequence[str] | None = "0001_phase1_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("opennms_event_id", sa.String(length=128), nullable=False),
        sa.Column("node_id", sa.Integer(), nullable=True),
        sa.Column("uei", sa.String(length=512), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=True),
        sa.Column("log_message", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_xml", sa.Text(), nullable=False),
        sa.Column("normalized_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], name=op.f("fk_events_node_id_nodes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
        sa.UniqueConstraint("opennms_event_id", name=op.f("uq_events_opennms_event_id")),
    )
    op.create_index(op.f("ix_events_event_time"), "events", ["event_time"], unique=False)
    op.create_index("ix_events_node_time", "events", ["node_id", "event_time"], unique=False)
    op.create_index(op.f("ix_events_severity"), "events", ["severity"], unique=False)
    op.create_index("ix_events_severity_time", "events", ["severity", "event_time"], unique=False)
    op.create_index(op.f("ix_events_uei"), "events", ["uei"], unique=False)

    op.create_table(
        "outages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("opennms_outage_id", sa.String(length=128), nullable=False),
        sa.Column("node_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("service_name", sa.String(length=256), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("lost_service_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("regained_service_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_xml", sa.Text(), nullable=False),
        sa.Column("normalized_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], name=op.f("fk_outages_node_id_nodes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outages")),
        sa.UniqueConstraint("opennms_outage_id", name=op.f("uq_outages_opennms_outage_id")),
    )
    op.create_index(op.f("ix_outages_ip_address"), "outages", ["ip_address"], unique=False)
    op.create_index(op.f("ix_outages_lost_service_at"), "outages", ["lost_service_at"], unique=False)
    op.create_index("ix_outages_node_status", "outages", ["node_id", "status"], unique=False)
    op.create_index(op.f("ix_outages_service_name"), "outages", ["service_name"], unique=False)
    op.create_index("ix_outages_service_status", "outages", ["service_name", "status"], unique=False)
    op.create_index(op.f("ix_outages_status"), "outages", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_outages_status"), table_name="outages")
    op.drop_index("ix_outages_service_status", table_name="outages")
    op.drop_index(op.f("ix_outages_service_name"), table_name="outages")
    op.drop_index("ix_outages_node_status", table_name="outages")
    op.drop_index(op.f("ix_outages_lost_service_at"), table_name="outages")
    op.drop_index(op.f("ix_outages_ip_address"), table_name="outages")
    op.drop_table("outages")

    op.drop_index(op.f("ix_events_uei"), table_name="events")
    op.drop_index("ix_events_severity_time", table_name="events")
    op.drop_index(op.f("ix_events_severity"), table_name="events")
    op.drop_index("ix_events_node_time", table_name="events")
    op.drop_index(op.f("ix_events_event_time"), table_name="events")
    op.drop_table("events")
