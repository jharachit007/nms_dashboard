from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        UniqueConstraint(
            "alert_id",
            "ai_recommendation_id",
            "user_id",
            name="uq_feedback_alert_recommendation_user",
        ),
        Index("ix_feedback_alert_user", "alert_id", "user_id"),
        Index("ix_feedback_alert_recommendation", "alert_id", "ai_recommendation_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False, index=True)
    ai_recommendation_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_recommendations.id"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    helpful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    resolved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    feedback_type: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    resolution_status: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    resolution_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    alert = relationship("Alert", back_populates="feedback")
    ai_recommendation = relationship("AIRecommendation", back_populates="feedback")
