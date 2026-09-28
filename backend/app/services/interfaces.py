"""
Service boundary interfaces.

The backend depends only on these Protocols. Implementations (ML, RAG,
LLM, safety, persistence) are supplied in later phases and must satisfy
them structurally — they do not need to import backend modules.

Phase 2.5: Interfaces only — no implementations exist yet.

Ownership rule for user-scoped services: implementations must only read
or write data belonging to the given user, and must treat another user's
conversation or message exactly like a nonexistent one.
"""

from typing import Protocol

from app.models.user import User
from app.schemas.analytics import AnalyticsResponse
from app.schemas.chat import ChatRequest, ChatResponse, HistoryResponse
from app.schemas.emotion import (
    FusionRequest,
    FusionResult,
    TextAnalysisResult,
    TranscriptionResult,
    VoiceEmotionResult,
)
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.schemas.llm import LLMRequest, LLMResponse
from app.schemas.rag import RetrievedChunk
from app.schemas.safety import InputSafetyAssessment, OutputSafetyAssessment


class ServiceError(Exception):
    """Base error raised by service implementations."""


class InvalidInputError(ServiceError):
    """Input is well-formed but cannot be processed (e.g. unusable audio). Maps to 422."""


class ResourceNotFoundError(ServiceError):
    """Resource does not exist or is not owned by the user. Maps to 404."""


class VoiceEmotionService(Protocol):
    def analyze(self, audio: bytes, content_type: str) -> VoiceEmotionResult:
        """Predict emotion from audio. Raises InvalidInputError for unusable audio."""
        ...


class SpeechToTextService(Protocol):
    def transcribe(self, audio: bytes, content_type: str) -> TranscriptionResult:
        ...


class TextAnalysisService(Protocol):
    def analyze(self, text: str) -> TextAnalysisResult:
        ...


class FusionService(Protocol):
    def fuse(self, request: FusionRequest) -> FusionResult:
        ...


class RetrievalService(Protocol):
    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        ...


class LLMService(Protocol):
    def generate(self, request: LLMRequest) -> LLMResponse:
        ...


class SafetyService(Protocol):
    def check_input(self, text: str) -> InputSafetyAssessment:
        ...

    def check_output(self, text: str) -> OutputSafetyAssessment:
        ...


class ChatService(Protocol):
    def respond(self, user: User, request: ChatRequest) -> ChatResponse:
        """Raises ResourceNotFoundError if conversation_id is not the user's."""
        ...


class FeedbackService(Protocol):
    def submit(self, user: User, request: FeedbackRequest) -> FeedbackResponse:
        """Raises ResourceNotFoundError if message_id is not in the user's conversations."""
        ...


class HistoryService(Protocol):
    def list_conversations(self, user: User, limit: int, offset: int) -> HistoryResponse:
        ...


class AnalyticsService(Protocol):
    def summarize(self, user: User) -> AnalyticsResponse:
        ...
