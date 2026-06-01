from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), unique=True, nullable=False, index=True)
    input_context_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_sanitized: Mapped[str] = mapped_column(Text, nullable=False)
    sanitized_context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    recommendation: Mapped[dict] = mapped_column(JSONB, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    advisory_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    alert = relationship("Alert", back_populates="ai_recommendation")


Index("ix_ai_recommendations_alert_context", AIRecommendation.alert_id, AIRecommendation.input_context_hash)
Index("ix_ai_recommendations_provider_created", AIRecommendation.provider, AIRecommendation.created_at)
