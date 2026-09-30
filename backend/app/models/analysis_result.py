"""
AnalysisResult: emotion/safety analysis of a user message.

Stored only when the user has enabled "save emotional statistics".
Values are model predictions, not clinical measurements.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    __table_args__ = (UniqueConstraint("message_id", name="uq_analysis_results_message_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    voice_emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    voice_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    text_sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    text_emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    text_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    fused_state: Mapped[str] = mapped_column(String(50), nullable=False)
    fused_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    safety_level: Mapped[str] = mapped_column(String(20), nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
