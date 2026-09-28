"""
FastAPI dependencies that supply service implementations to routes.

Phase 2.5: No implementations exist, so every provider responds with
501 Not Implemented. A later phase replaces the body of the relevant
provider to return a real implementation; tests substitute fakes via
app.dependency_overrides.
"""

from typing import NoReturn

from fastapi import HTTPException, status

from app.services.interfaces import (
    AnalyticsService,
    ChatService,
    FeedbackService,
    FusionService,
    HistoryService,
    RetrievalService,
    VoiceEmotionService,
)


def _not_implemented(name: str) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"{name} is not implemented yet",
    )


def get_voice_emotion_service() -> VoiceEmotionService:
    _not_implemented("Voice emotion analysis")


def get_fusion_service() -> FusionService:
    _not_implemented("Multimodal fusion")


def get_retrieval_service() -> RetrievalService:
    _not_implemented("Retrieval")


def get_chat_service() -> ChatService:
    _not_implemented("Chat")


def get_feedback_service() -> FeedbackService:
    _not_implemented("Feedback")


def get_history_service() -> HistoryService:
    _not_implemented("Conversation history")


def get_analytics_service() -> AnalyticsService:
    _not_implemented("Analytics")
