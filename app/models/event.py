from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opennms_event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id"), nullable=True)
    uei: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    log_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    raw_xml: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    node = relationship("Node")


Index("ix_events_node_time", Event.node_id, Event.event_time)
Index("ix_events_severity_time", Event.severity, Event.event_time)
