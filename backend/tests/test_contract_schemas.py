"""
Unit tests for Phase 2.5 contract schemas (validation rules only).
"""

import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.emotion import (
    ContextSignal,
    FusionRequest,
    FusionResult,
    TextAnalysisResult,
    TranscriptionResult,
    VoiceEmotionResult,
)
from app.schemas.feedback import FeedbackRequest
from app.schemas.llm import LLMRequest
from app.schemas.rag import RetrieveRequest
from app.schemas.safety import InputSafetyAssessment, SafetyLevel


def _voice(**overrides):
    data = {
        "emotion": "sad",
        "confidence": 0.74,
        "probabilities": {"sad": 0.74, "neutral": 0.16, "angry": 0.06, "happy": 0.04},
        "model_version": "test",
    }
    data.update(overrides)
    return VoiceEmotionResult(**data)


def _text():
    return TextAnalysisResult(
        sentiment="negative", emotion="frustration", confidence=0.81, model_version="test"
    )


# ---------------------------------------------------------------------------
# VoiceEmotionResult
# ---------------------------------------------------------------------------

def test_voice_result_valid():
    result = _voice()
    assert result.emotion == "sad"
    assert result.confidence == 0.74


def test_voice_result_emotion_must_be_in_probabilities():
    with pytest.raises(ValidationError):
        _voice(emotion="fear")


def test_voice_result_probabilities_must_sum_to_one():
    with pytest.raises(ValidationError):
        _voice(probabilities={"sad": 0.74, "neutral": 0.10})


def test_voice_result_confidence_must_match_emotion_probability():
    with pytest.raises(ValidationError):
        _voice(confidence=0.5)


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_voice_result_confidence_bounds(value):
    with pytest.raises(ValidationError):
        _voice(confidence=value)


def test_voice_result_requires_probabilities():
    with pytest.raises(ValidationError):
        _voice(probabilities={})


def test_voice_result_requires_model_version():
    with pytest.raises(ValidationError):
        _voice(model_version="")


# ---------------------------------------------------------------------------
# Text / transcription
# ---------------------------------------------------------------------------

def test_text_result_confidence_bounds():
    with pytest.raises(ValidationError):
        TextAnalysisResult(sentiment="negative", emotion="x", confidence=1.5, model_version="t")


def test_transcription_confidence_optional():
    result = TranscriptionResult(text="hello")
    assert result.confidence is None
    assert result.language is None


# ---------------------------------------------------------------------------
# Fusion
# ---------------------------------------------------------------------------

def test_fusion_request_requires_voice_or_text():
    with pytest.raises(ValidationError):
        FusionRequest(context=ContextSignal(label="exam stress", score=0.65))


def test_fusion_request_text_only_is_valid():
    request = FusionRequest(text=_text())
    assert request.voice is None


def test_fusion_request_all_signals():
    request = FusionRequest(
        voice=_voice(), text=_text(), context=ContextSignal(label="exam stress", score=0.65)
    )
    assert request.context.score == 0.65


def test_fusion_result_signal_bounds():
    with pytest.raises(ValidationError):
        FusionResult(state="stressed", confidence=0.79, signals={"voice": 1.2})


# ---------------------------------------------------------------------------
# RAG / chat / feedback
# ---------------------------------------------------------------------------

def test_retrieve_request_defaults():
    assert RetrieveRequest(query="study breaks").top_k == 5


@pytest.mark.parametrize("top_k", [0, 21])
def test_retrieve_request_top_k_bounds(top_k):
    with pytest.raises(ValidationError):
        RetrieveRequest(query="study breaks", top_k=top_k)


@pytest.mark.parametrize("query", ["", "   "])
def test_retrieve_request_rejects_blank_query(query):
    with pytest.raises(ValidationError):
        RetrieveRequest(query=query)


@pytest.mark.parametrize("message", ["", " \n\t"])
def test_chat_request_rejects_blank_message(message):
    with pytest.raises(ValidationError):
        ChatRequest(message=message)


def test_chat_request_rejects_non_positive_conversation_id():
    with pytest.raises(ValidationError):
        ChatRequest(message="hi", conversation_id=0)


def test_chat_response_sources_default_empty():
    response = ChatResponse(
        conversation_id=1,
        reply={
            "id": 1,
            "conversation_id": 1,
            "role": "assistant",
            "content": "hi",
            "created_at": "2026-01-01T00:00:00Z",
        },
    )
    assert response.sources == []
    assert response.emotion is None


def test_chat_response_rejects_invalid_role():
    with pytest.raises(ValidationError):
        ChatResponse(
            conversation_id=1,
            reply={
                "id": 1,
                "conversation_id": 1,
                "role": "robot",
                "content": "hi",
                "created_at": "2026-01-01T00:00:00Z",
            },
        )


def test_feedback_request_rejects_non_positive_message_id():
    with pytest.raises(ValidationError):
        FeedbackRequest(message_id=0, helpful=True)


# ---------------------------------------------------------------------------
# Safety / LLM
# ---------------------------------------------------------------------------

def test_safety_levels():
    assert {level.value for level in SafetyLevel} == {"normal", "distress", "high_risk"}


def test_input_safety_rejects_unknown_level():
    with pytest.raises(ValidationError):
        InputSafetyAssessment(level="unknown")


def test_llm_request_defaults():
    request = LLMRequest(message="hi")
    assert request.history == []
    assert request.retrieved == []
    assert request.emotion is None
    assert request.safety_level == SafetyLevel.NORMAL
