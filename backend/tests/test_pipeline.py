"""
End-to-end tests for the conversation pipeline with real components
(text analysis, fusion, retrieval, safety, response policy) on SQLite.

The LLM is always replaced (offline template or a capturing fake) so tests
never call a paid API, even when ANTHROPIC_API_KEY is configured.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.dependencies import get_db
from app.main import app
from app.models.analysis_result import AnalysisResult
from app.models.user import User
from app.schemas.emotion import TranscriptionResult, VoiceEmotionResult
from app.schemas.llm import LLMResponse
from app.services import components, providers
from app.services.components import VoiceEmotionAdapter
from app.services.llm import OFFLINE_MODEL, OfflineLLMService
from safety.guardrails import CRISIS_RESPONSE, SAFE_FALLBACK_RESPONSE

client = TestClient(app)


class CapturingLLM:
    def __init__(self, content=None):
        self.requests = []
        self.content = content

    def generate(self, request):
        self.requests.append(request)
        if self.content is not None:
            return LLMResponse(content=self.content, model="fake-llm")
        return OfflineLLMService().generate(request)


@pytest.fixture
def db_session_factory():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override
    yield factory
    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous
    engine.dispose()


@pytest.fixture
def llm(monkeypatch):
    fake = CapturingLLM()
    monkeypatch.setattr(components, "llm", lambda: fake)
    return fake


def _user(factory, email, **prefs) -> dict:
    db = factory()
    user = User(email=email, hashed_password=get_password_hash("password123"), **prefs)
    db.add(user)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    db.close()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice(db_session_factory):
    return _user(db_session_factory, "alice@example.com")


@pytest.fixture
def bob(db_session_factory):
    return _user(db_session_factory, "bob@example.com")


def _chat(headers, message, conversation_id=None):
    body = {"message": message}
    if conversation_id is not None:
        body["conversation_id"] = conversation_id
    return client.post("/api/v1/chat", json=body, headers=headers)


# ---------------------------------------------------------------------------
# Conversation flow
# ---------------------------------------------------------------------------

def test_chat_creates_conversation_with_grounded_reply(alice, llm):
    response = _chat(alice, "How should I take study breaks when revising for exams?")
    assert response.status_code == 200
    body = response.json()
    assert body["reply"]["role"] == "assistant"
    assert body["llm_model"] == OFFLINE_MODEL
    assert body["sources"], "retrieval should return knowledge-base sources"
    assert body["sources"][0]["source"].startswith("Study Techniques")
    assert body["emotion"]["state"]
    assert body["safety_level"] == "normal"
    assert {"context_ms", "text_analysis_ms", "fusion_ms", "retrieval_ms", "llm_ms", "total_ms"} <= set(body["timings_ms"])


def test_follow_up_turn_receives_prior_context(alice, llm):
    first = _chat(alice, "My exams are next month.").json()
    second = _chat(alice, "I'm really tired.", first["conversation_id"])
    assert second.status_code == 200
    assert second.json()["conversation_id"] == first["conversation_id"]
    history = llm.requests[-1].history
    assert [t.content for t in history][:1] == ["My exams are next month."]
    assert [t.role.value for t in history] == ["user", "assistant"]


def test_history_lists_messages_chronologically(alice, llm):
    first = _chat(alice, "Hello there").json()
    _chat(alice, "Tell me about sleep", first["conversation_id"])
    history = client.get("/api/v1/history", headers=alice).json()
    messages = history["conversations"][0]["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]
    assert messages[0]["content"] == "Hello there"


def test_delete_conversation(alice, bob, llm):
    conversation_id = _chat(alice, "Hello").json()["conversation_id"]
    assert client.delete(f"/api/v1/history/{conversation_id}", headers=bob).status_code == 404
    assert client.delete(f"/api/v1/history/{conversation_id}", headers=alice).status_code == 204
    assert client.get("/api/v1/history", headers=alice).json()["conversations"] == []


# ---------------------------------------------------------------------------
# Ownership isolation
# ---------------------------------------------------------------------------

def test_user_cannot_continue_another_users_conversation(alice, bob, llm):
    conversation_id = _chat(alice, "Private thoughts").json()["conversation_id"]
    response = _chat(bob, "Let me in", conversation_id)
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


def test_history_is_isolated_per_user(alice, bob, llm):
    _chat(alice, "Alice's conversation")
    assert client.get("/api/v1/history", headers=bob).json()["conversations"] == []


def test_feedback_on_another_users_message_is_not_found(alice, bob, llm):
    reply_id = _chat(alice, "Hi").json()["reply"]["id"]
    response = client.post("/api/v1/feedback", json={"message_id": reply_id, "helpful": True}, headers=bob)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------

def test_high_risk_message_uses_crisis_protocol_without_llm(alice, llm):
    response = _chat(alice, "I want to end my life")
    body = response.json()
    assert response.status_code == 200
    assert body["safety_level"] == "high_risk"
    assert body["reply"]["content"] == CRISIS_RESPONSE
    assert body["llm_model"] == "safety-protocol"
    assert llm.requests == []


def test_distress_message_gets_supportive_policy(alice, llm):
    body = _chat(alice, "I'm so overwhelmed and I can't handle this anymore").json()
    assert body["safety_level"] == "distress"
    policy = llm.requests[-1].policy
    assert policy.tone == "supportive"
    assert policy.include_resources is True


def test_output_guardrail_replaces_unsafe_reply(alice, monkeypatch):
    unsafe = CapturingLLM(content="You have clinical depression. Take 50 mg of something.")
    monkeypatch.setattr(components, "llm", lambda: unsafe)
    body = _chat(alice, "I feel low lately").json()
    assert body["reply"]["content"] == SAFE_FALLBACK_RESPONSE
    assert body["sources"] == []


# ---------------------------------------------------------------------------
# Feedback, analytics and privacy
# ---------------------------------------------------------------------------

def test_feedback_and_analytics(alice, llm):
    reply = _chat(alice, "Hi").json()["reply"]
    ok = client.post("/api/v1/feedback", json={"message_id": reply["id"], "helpful": False}, headers=alice)
    assert ok.status_code == 201
    # Updating feedback replaces the previous value.
    client.post("/api/v1/feedback", json={"message_id": reply["id"], "helpful": True}, headers=alice)
    analytics = client.get("/api/v1/analytics", headers=alice).json()
    assert analytics["feedback"] == {"helpful": 1, "not_helpful": 0}


def test_feedback_rejected_on_user_message(alice, llm):
    user_message_id = _chat(alice, "Hi").json()["reply"]["id"] - 1
    response = client.post("/api/v1/feedback", json={"message_id": user_message_id, "helpful": True}, headers=alice)
    assert response.status_code == 422


def test_emotion_stats_not_saved_by_default(alice, llm, db_session_factory):
    _chat(alice, "I'm so happy today!")
    db = db_session_factory()
    assert db.query(AnalysisResult).count() == 0
    db.close()
    assert client.get("/api/v1/analytics", headers=alice).json()["emotion_distribution"] == {}


def test_emotion_stats_saved_when_opted_in(alice, llm):
    assert client.patch("/api/v1/settings", json={"save_emotion_stats": True}, headers=alice).status_code == 200
    body = _chat(alice, "I'm so happy today, this is wonderful!").json()
    distribution = client.get("/api/v1/analytics", headers=alice).json()["emotion_distribution"]
    assert distribution == {body["emotion"]["state"]: 1}


def test_previous_turn_state_becomes_fusion_context(alice, llm):
    client.patch("/api/v1/settings", json={"save_emotion_stats": True}, headers=alice)
    first = _chat(alice, "I'm so happy today, this is wonderful!").json()
    second = _chat(alice, "ok", first["conversation_id"]).json()
    assert second["emotion"]["signals"]["context"] is not None


# ---------------------------------------------------------------------------
# Memory and settings
# ---------------------------------------------------------------------------

def test_memory_lifecycle(alice, bob, llm):
    created = client.post("/api/v1/memory", json={"content": "I prefer short answers"}, headers=alice)
    assert created.status_code == 201
    memory_id = created.json()["id"]

    _chat(alice, "Hello")
    assert llm.requests[-1].memories == ["I prefer short answers"]

    assert client.delete(f"/api/v1/memory/{memory_id}", headers=bob).status_code == 404

    disabled = client.post("/api/v1/memory/disable", headers=alice).json()
    assert disabled["memory_enabled"] is False
    _chat(alice, "Hello again")
    assert llm.requests[-1].memories == []
    assert client.post("/api/v1/memory", json={"content": "x"}, headers=alice).status_code == 409

    listing = client.get("/api/v1/memory", headers=alice).json()
    assert listing["enabled"] is False and len(listing["items"]) == 1
    assert client.delete(f"/api/v1/memory/{memory_id}", headers=alice).status_code == 204
    assert client.get("/api/v1/memory", headers=alice).json()["items"] == []


def test_response_style_setting_drives_policy(alice, llm):
    assert client.patch("/api/v1/settings", json={"response_style": "concise"}, headers=alice).status_code == 200
    _chat(alice, "Tell me about sleep")
    assert llm.requests[-1].policy.length == "short"


def test_settings_reject_unknown_style(alice):
    response = client.patch("/api/v1/settings", json={"response_style": "poetic"}, headers=alice)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Voice
# ---------------------------------------------------------------------------

def _wav_bytes(seconds=1.0, sr=16000):
    import io

    import numpy as np
    import soundfile as sf

    t = np.arange(int(seconds * sr)) / sr
    buffer = io.BytesIO()
    sf.write(buffer, 0.5 * np.sin(2 * np.pi * 220 * t), sr, format="WAV")
    return buffer.getvalue()


class FakeSTT:
    def transcribe_preprocessed(self, audio):
        return TranscriptionResult(text="I'm really frustrated with my exams", language="en", confidence=0.9)


class FakeVoice:
    available = True

    def analyze_preprocessed(self, audio):
        return VoiceEmotionResult(
            emotion="angry", confidence=0.7,
            probabilities={"angry": 0.7, "neutral": 0.3}, model_version="fake",
        )


def test_voice_chat_uses_transcript_and_voice_emotion(alice, llm):
    app.dependency_overrides[providers.get_speech_to_text_service] = FakeSTT
    app.dependency_overrides[providers.get_voice_emotion_service] = FakeVoice
    try:
        response = client.post(
            "/api/v1/chat/voice", content=_wav_bytes(), headers={**alice, "Content-Type": "audio/wav"}
        )
    finally:
        app.dependency_overrides.pop(providers.get_speech_to_text_service, None)
        app.dependency_overrides.pop(providers.get_voice_emotion_service, None)
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "I'm really frustrated with my exams"
    assert body["emotion"]["state"] == "angry"
    assert body["emotion"]["signals"]["voice"] == 0.7
    assert "audio_ms" in body["timings_ms"]


def test_voice_chat_rejects_unsupported_format(alice, llm):
    app.dependency_overrides[providers.get_speech_to_text_service] = FakeSTT
    try:
        response = client.post(
            "/api/v1/chat/voice", content=b"ID3....", headers={**alice, "Content-Type": "audio/mpeg"}
        )
    finally:
        app.dependency_overrides.pop(providers.get_speech_to_text_service, None)
    assert response.status_code == 415


def test_analyze_returns_503_when_model_missing(alice, tmp_path):
    missing = VoiceEmotionAdapter(tmp_path / "missing.pkl")
    app.dependency_overrides[providers.get_voice_emotion_service] = lambda: missing
    try:
        response = client.post(
            "/api/v1/emotion/analyze", content=_wav_bytes(), headers={**alice, "Content-Type": "audio/wav"}
        )
    finally:
        app.dependency_overrides.pop(providers.get_voice_emotion_service, None)
    assert response.status_code == 503


def test_retrieve_endpoint_uses_knowledge_base(alice):
    response = client.post("/api/v1/rag/retrieve", json={"query": "trouble falling asleep", "top_k": 2}, headers=alice)
    assert response.status_code == 200
    chunks = response.json()["chunks"]
    assert chunks and chunks[0]["source"].startswith("Sleep Basics")
