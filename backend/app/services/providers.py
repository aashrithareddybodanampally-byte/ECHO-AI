"""
FastAPI dependencies that supply service implementations to routes.

Tests substitute fakes via app.dependency_overrides.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.services import components
from app.services.chat_service import (
    ChatPipeline,
    DatabaseAnalyticsService,
    DatabaseFeedbackService,
    DatabaseHistoryService,
)
from app.services.interfaces import (
    AnalyticsService,
    ChatService,
    FeedbackService,
    FusionService,
    HistoryService,
    RetrievalService,
    VoiceEmotionService,
)


def get_voice_emotion_service() -> VoiceEmotionService:
    return components.voice_emotion()


def get_speech_to_text_service():
    return components.speech_to_text()


def get_fusion_service() -> FusionService:
    return components.fusion()


def get_retrieval_service() -> RetrievalService:
    return components.retrieval()


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    return ChatPipeline(db)


def get_feedback_service(db: Session = Depends(get_db)) -> FeedbackService:
    return DatabaseFeedbackService(db)


def get_history_service(db: Session = Depends(get_db)) -> HistoryService:
    return DatabaseHistoryService(db)


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return DatabaseAnalyticsService(db)
