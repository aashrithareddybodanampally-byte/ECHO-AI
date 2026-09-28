"""
Route-level tests for the Phase 2.5 API contracts.

Services are replaced with fakes through app.dependency_overrides so these
tests exercise only the HTTP contract (auth, validation, status codes,
response shape). End-to-end behavior is covered in test_pipeline.py.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.config import settings
from app.main import app
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse
from app.schemas.chat import ChatResponse, HistoryResponse
from app.schemas.emotion import FusionResult, VoiceEmotionResult
from app.schemas.feedback import FeedbackResponse
from app.schemas.rag import RetrievedChunk
from app.services import providers
from app.services.interfaces import InvalidInputError, ResourceNotFoundError

client = TestClient(app)

USER = User(id=1, email="owner@example.com", hashed_password="x")
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

VOICE = {
    "emotion": "sad",
    "confidence": 0.74,
    "probabilities": {"sad": 0.74, "neutral": 0.26},
    "model_version": "fake",
}
TEXT = {"sentiment": "negative", "emotion": "frustration", "confidence": 0.81, "model_version": "fake"}
REPLY = {"id": 2, "conversation_id": 1, "role": "assistant", "content": "ok", "created_at": NOW}

# (method, path, kwargs for a valid request)
ENDPOINTS = [
    ("post", "/api/v1/emotion/analyze", {"content": b"RIFF", "headers": {"Content-Type": "audio/wav"}}),
    ("post", "/api/v1/emotion/fusion", {"json": {"text": TEXT}}),
    ("post", "/api/v1/rag/retrieve", {"json": {"query": "study breaks"}}),
    ("post", "/api/v1/chat", {"json": {"message": "hello"}}),
    ("post", "/api/v1/feedback", {"json": {"message_id": 2, "helpful": True}}),
    ("get", "/api/v1/history", {}),
    ("get", "/api/v1/analytics", {}),
]


@pytest.fixture
def overrides():
    """Set dependency overrides for one test and remove only those afterwards."""
    added = []

    def _set(dependency, value):
        app.dependency_overrides[dependency] = value
        added.append(dependency)

    yield _set
    for dependency in added:
        app.dependency_overrides.pop(dependency, None)


@pytest.fixture
def authed(overrides):
    overrides(get_current_user, lambda: USER)
    return overrides


def _call(method, path, kwargs, headers=None):
    kwargs = dict(kwargs)
    merged = {**kwargs.pop("headers", {}), **(headers or {})}
    return getattr(client, method)(path, headers=merged, **kwargs)


# ---------------------------------------------------------------------------
# Authentication and not-implemented behavior
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method,path,kwargs", ENDPOINTS)
def test_requires_authentication(method, path, kwargs):
    response = _call(method, path, kwargs)
    assert response.status_code == 401


@pytest.mark.parametrize("method,path,kwargs", ENDPOINTS)
def test_rejects_invalid_token(method, path, kwargs):
    response = _call(method, path, kwargs, headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_openapi_documents_contract_paths():
    paths = client.get("/openapi.json").json()["paths"]
    for _, path, _ in ENDPOINTS:
        assert path in paths


# ---------------------------------------------------------------------------
# Emotion
# ---------------------------------------------------------------------------

class FakeVoiceEmotion:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def analyze(self, audio, content_type):
        self.calls.append((audio, content_type))
        if self.error:
            raise self.error
        return VoiceEmotionResult(**VOICE)


def test_analyze_passes_raw_audio_to_service(authed):
    fake = FakeVoiceEmotion()
    authed(providers.get_voice_emotion_service, lambda: fake)
    response = client.post(
        "/api/v1/emotion/analyze", content=b"RIFFdata", headers={"Content-Type": "audio/wav"}
    )
    assert response.status_code == 200
    assert response.json() == VOICE
    assert fake.calls == [(b"RIFFdata", "audio/wav")]


def test_analyze_rejects_non_audio_content_type(authed):
    authed(providers.get_voice_emotion_service, FakeVoiceEmotion)
    response = client.post(
        "/api/v1/emotion/analyze", content=b"data", headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 415


def test_analyze_rejects_empty_body(authed):
    authed(providers.get_voice_emotion_service, FakeVoiceEmotion)
    response = client.post(
        "/api/v1/emotion/analyze", content=b"", headers={"Content-Type": "audio/wav"}
    )
    assert response.status_code == 422


def test_analyze_unusable_audio_returns_422(authed):
    fake = FakeVoiceEmotion(error=InvalidInputError("No speech detected"))
    authed(providers.get_voice_emotion_service, lambda: fake)
    response = client.post(
        "/api/v1/emotion/analyze", content=b"RIFF", headers={"Content-Type": "audio/wav"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "No speech detected"}


def test_audio_upload_limit_default_is_25_mb():
    assert settings.MAX_AUDIO_UPLOAD_BYTES == 25 * 1024 * 1024


def test_analyze_accepts_body_at_limit(authed, monkeypatch):
    monkeypatch.setattr(settings, "MAX_AUDIO_UPLOAD_BYTES", 8)
    fake = FakeVoiceEmotion()
    authed(providers.get_voice_emotion_service, lambda: fake)
    response = client.post(
        "/api/v1/emotion/analyze", content=b"12345678", headers={"Content-Type": "audio/wav"}
    )
    assert response.status_code == 200
    assert fake.calls == [(b"12345678", "audio/wav")]


def test_analyze_rejects_oversized_content_length(authed, monkeypatch):
    monkeypatch.setattr(settings, "MAX_AUDIO_UPLOAD_BYTES", 8)
    fake = FakeVoiceEmotion()
    authed(providers.get_voice_emotion_service, lambda: fake)
    response = client.post(
        "/api/v1/emotion/analyze", content=b"123456789", headers={"Content-Type": "audio/wav"}
    )
    assert response.status_code == 413
    assert fake.calls == []


def test_analyze_rejects_oversized_stream_without_content_length(authed, monkeypatch):
    monkeypatch.setattr(settings, "MAX_AUDIO_UPLOAD_BYTES", 8)
    fake = FakeVoiceEmotion()
    authed(providers.get_voice_emotion_service, lambda: fake)

    def chunks():
        yield b"12345"
        yield b"67890"

    # A generator body is sent chunked, with no Content-Length header.
    response = client.post(
        "/api/v1/emotion/analyze", content=chunks(), headers={"Content-Type": "audio/wav"}
    )
    assert response.status_code == 413
    assert fake.calls == []


def test_analyze_authenticates_before_checking_size(monkeypatch):
    monkeypatch.setattr(settings, "MAX_AUDIO_UPLOAD_BYTES", 8)
    response = client.post(
        "/api/v1/emotion/analyze", content=b"x" * 100, headers={"Content-Type": "audio/wav"}
    )
    assert response.status_code == 401


class FakeFusion:
    def fuse(self, request):
        return FusionResult(
            state="stressed", confidence=0.79, signals={"text": request.text.confidence}
        )


def test_fusion_returns_result(authed):
    authed(providers.get_fusion_service, FakeFusion)
    response = client.post("/api/v1/emotion/fusion", json={"text": TEXT})
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "stressed"
    assert body["signals"] == {"voice": None, "text": 0.81, "context": None}


def test_fusion_requires_a_modality(authed):
    authed(providers.get_fusion_service, FakeFusion)
    response = client.post("/api/v1/emotion/fusion", json={"context": {"label": "x", "score": 0.5}})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------

class FakeRetrieval:
    def __init__(self):
        self.calls = []

    def retrieve(self, query, top_k):
        self.calls.append((query, top_k))
        return [RetrievedChunk(source="Study Resource A", content="Take breaks.", score=0.9)]


def test_retrieve_returns_chunks_with_sources(authed):
    fake = FakeRetrieval()
    authed(providers.get_retrieval_service, lambda: fake)
    response = client.post("/api/v1/rag/retrieve", json={"query": "study breaks"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "study breaks"
    assert body["chunks"][0]["source"] == "Study Resource A"
    assert fake.calls == [("study breaks", 5)]


def test_retrieve_validates_top_k(authed):
    authed(providers.get_retrieval_service, FakeRetrieval)
    response = client.post("/api/v1/rag/retrieve", json={"query": "q", "top_k": 0})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class FakeChat:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def respond(self, user, request):
        self.calls.append((user, request))
        if self.error:
            raise self.error
        return ChatResponse(conversation_id=1, reply=REPLY)


def test_chat_passes_authenticated_user(authed):
    fake = FakeChat()
    authed(providers.get_chat_service, lambda: fake)
    response = client.post("/api/v1/chat", json={"message": "hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["reply"]["role"] == "assistant"
    assert body["sources"] == []
    assert body["emotion"] is None
    user, request = fake.calls[0]
    assert user is USER
    assert request.conversation_id is None


def test_chat_rejects_empty_message(authed):
    authed(providers.get_chat_service, FakeChat)
    response = client.post("/api/v1/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_foreign_conversation_returns_404(authed):
    fake = FakeChat(error=ResourceNotFoundError("conversation 99 owned by user 2"))
    authed(providers.get_chat_service, lambda: fake)
    response = client.post("/api/v1/chat", json={"message": "hi", "conversation_id": 99})
    assert response.status_code == 404
    # Ownership details must not leak.
    assert response.json() == {"detail": "Not found"}


# ---------------------------------------------------------------------------
# Feedback / history / analytics
# ---------------------------------------------------------------------------

class FakeFeedback:
    def submit(self, user, request):
        return FeedbackResponse(message_id=request.message_id, helpful=request.helpful)


def test_feedback_created(authed):
    authed(providers.get_feedback_service, FakeFeedback)
    response = client.post("/api/v1/feedback", json={"message_id": 2, "helpful": False})
    assert response.status_code == 201
    assert response.json() == {"message_id": 2, "helpful": False}


def test_feedback_validates_message_id(authed):
    authed(providers.get_feedback_service, FakeFeedback)
    response = client.post("/api/v1/feedback", json={"message_id": 0, "helpful": True})
    assert response.status_code == 422


class FakeHistory:
    def __init__(self):
        self.calls = []

    def list_conversations(self, user, limit, offset):
        self.calls.append((user, limit, offset))
        return HistoryResponse(
            conversations=[
                {"id": 1, "title": None, "created_at": NOW, "updated_at": NOW, "messages": [REPLY]}
            ]
        )


def test_history_default_pagination(authed):
    fake = FakeHistory()
    authed(providers.get_history_service, lambda: fake)
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    assert response.json()["conversations"][0]["messages"][0]["id"] == 2
    assert fake.calls == [(USER, 20, 0)]


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_history_validates_pagination(authed, query):
    authed(providers.get_history_service, FakeHistory)
    response = client.get(f"/api/v1/history?{query}")
    assert response.status_code == 422


class FakeAnalytics:
    def summarize(self, user):
        return AnalyticsResponse(
            emotion_distribution={"neutral": 3, "sad": 1},
            feedback={"helpful": 2, "not_helpful": 1},
        )


def test_analytics_returns_summary(authed):
    authed(providers.get_analytics_service, FakeAnalytics)
    response = client.get("/api/v1/analytics")
    assert response.status_code == 200
    assert response.json() == {
        "emotion_distribution": {"neutral": 3, "sad": 1},
        "feedback": {"helpful": 2, "not_helpful": 1},
    }
