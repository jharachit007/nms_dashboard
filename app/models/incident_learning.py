from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentLearningStore(Base):
    __tablename__ = "incident_learning_store"
    __table_args__ = (
        UniqueConstraint("feedback_id", name="uq_incident_learning_store_feedback_id"),
        Index("ix_learning_alert_resolution", "alert_id", "resolution_status"),
        Index("ix_learning_recommendation_feedback", "ai_recommendation_id", "feedback_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False, index=True)
    ai_recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("ai_recommendations.id"),
        nullable=False,
        index=True,
    )
    feedback_id: Mapped[int] = mapped_column(ForeignKey("feedback.id"), nullable=False, index=True)
    feedback_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    resolution_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    learning_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    alert = relationship("Alert")
    ai_recommendation = relationship("AIRecommendation")
    feedback = relationship("Feedback")
