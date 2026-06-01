from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opennms_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    raw_label: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    operator: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    circle: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    server_type: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    raw_xml: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    alerts = relationship("Alert", back_populates="node")


Index("ix_nodes_operator_circle", Node.operator, Node.circle)
Index("ix_nodes_ip_server_type", Node.ip_address, Node.server_type)
