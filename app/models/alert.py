from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AlertLifecycleStatus
from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opennms_alarm_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id"), nullable=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    lifecycle_status: Mapped[str] = mapped_column(
        String(32),
        default=AlertLifecycleStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )
    uei: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    log_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    node = relationship("Node", back_populates="alerts")
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="alert")
    chat_messages = relationship("ChatMessage", back_populates="alert")
    llm_responses = relationship("LLMResponse", back_populates="alert")
    ai_recommendation = relationship(
        "AIRecommendation",
        back_populates="alert",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_event_xml: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    alert = relationship("Alert", back_populates="history")


Index("ix_alerts_severity_status", Alert.severity, Alert.lifecycle_status)
Index("ix_alerts_node_status", Alert.node_id, Alert.lifecycle_status)
