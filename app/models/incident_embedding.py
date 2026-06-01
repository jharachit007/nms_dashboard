from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UserDefinedType

from app.db.base import Base


class Vector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **kw) -> str:
        return f"VECTOR({self.dimensions})"


class IncidentEmbedding(Base):
    __tablename__ = "incident_embeddings"
    __table_args__ = (
        UniqueConstraint("alert_id", name="uq_incident_embeddings_alert_id"),
        Index("ix_incident_embeddings_alert_id", "alert_id"),
        Index("ix_incident_embeddings_node_id", "node_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False)
    node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id"), nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    alert = relationship("Alert")
    node = relationship("Node")
