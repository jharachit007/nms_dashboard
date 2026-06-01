from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Outage(Base):
    __tablename__ = "outages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opennms_outage_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id"), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    service_name: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    lost_service_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    regained_service_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


Index("ix_outages_node_status", Outage.node_id, Outage.status)
Index("ix_outages_service_status", Outage.service_name, Outage.status)
