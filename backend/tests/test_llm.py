"""
LLM provider tests. No network calls: the provider SDK clients are replaced with fakes.
"""

from types import SimpleNamespace

import httpx
import pytest

from app.schemas.llm import ChatTurn, LLMRequest, ResponsePolicy
from app.services.llm import (
    OFFLINE_MODEL,
    AnthropicLLMService,
    GroqLLMService,
    OfflineLLMService,
    build_llm_service,
    build_messages,
)


class FakeCompletions:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.result


def _groq_service(result=None, error=None, model="openai/gpt-oss-120b") -> tuple[GroqLLMService, FakeCompletions]:
    service = GroqLLMService(api_key="test-key", model=model, max_tokens=512, timeout=5)
    completions = FakeCompletions(result, error)
    service._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return service, completions


def _completion(text, model="openai/gpt-oss-120b"):
    return SimpleNamespace(model=model, choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


REQUEST = LLMRequest(
    message="How do I plan study breaks?",
    history=[ChatTurn(role="user", content="My exams are next month."),
             ChatTurn(role="assistant", content="That's a lot to prepare for.")],
    policy=ResponsePolicy(tone="supportive", ask_question=True),
    memories=["I prefer short answers"],
)


def test_groq_sends_system_prompt_history_and_message():
    service, completions = _groq_service(_completion("Try 25-minute focus blocks. [1]"))
    response = service.generate(REQUEST)
    assert response.content == "Try 25-minute focus blocks. [1]"
    assert response.model == "openai/gpt-oss-120b"

    call = completions.calls[0]
    assert call["model"] == "openai/gpt-oss-120b"
    assert call["reasoning_effort"] == "low"
    assert call["max_tokens"] == 512
    roles = [m["role"] for m in call["messages"]]
    assert roles == ["system", "user", "assistant", "user"]
    system = call["messages"][0]["content"]
    assert "medication or dosage advice" in system.lower()
    assert "not a licensed therapist" in system.lower()
    assert "I prefer short answers" in system
    assert call["messages"][-1]["content"] == "How do I plan study breaks?"


@pytest.mark.parametrize("make_error", [
    lambda: __import__("groq").APIConnectionError(request=httpx.Request("POST", "https://api.groq.com")),
    lambda: __import__("groq").RateLimitError(
        "rate limited",
        response=httpx.Response(429, request=httpx.Request("POST", "https://api.groq.com")),
        body=None,
    ),
    lambda: __import__("groq").AuthenticationError(
        "bad key",
        response=httpx.Response(401, request=httpx.Request("POST", "https://api.groq.com")),
        body=None,
    ),
])
def test_groq_errors_fall_back_to_offline(make_error):
    service, _ = _groq_service(error=make_error())
    assert service.generate(REQUEST).model == OFFLINE_MODEL


@pytest.mark.parametrize("result", [_completion(""), _completion(None), SimpleNamespace(model="x", choices=[])])
def test_groq_empty_reply_falls_back_to_offline(result):
    service, _ = _groq_service(result)
    assert service.generate(REQUEST).model == OFFLINE_MODEL


def _settings(**overrides):
    base = dict(
        LLM_PROVIDER="auto", GROQ_API_KEY=None, GROQ_MODEL="openai/gpt-oss-120b", GROQ_REASONING_EFFORT="low",
        ANTHROPIC_API_KEY=None, LLM_MODEL="claude-opus-5-5", LLM_EFFORT="low",
        LLM_MAX_TOKENS=512, LLM_TIMEOUT_SECONDS=5.0,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_auto_prefers_groq_then_anthropic_then_offline():
    assert isinstance(build_llm_service(_settings(GROQ_API_KEY="g", ANTHROPIC_API_KEY="a")), GroqLLMService)
    assert isinstance(build_llm_service(_settings(ANTHROPIC_API_KEY="a")), AnthropicLLMService)
    assert isinstance(build_llm_service(_settings()), OfflineLLMService)
    # An empty value (e.g. "GROQ_API_KEY=" in .env) counts as unset.
    assert isinstance(build_llm_service(_settings(GROQ_API_KEY="")), OfflineLLMService)


def test_explicit_provider_requires_its_key():
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        build_llm_service(_settings(LLM_PROVIDER="groq"))
    with pytest.raises(RuntimeError, match="Unknown LLM_PROVIDER"):
        build_llm_service(_settings(LLM_PROVIDER="gemini"))


def test_build_messages_starts_with_user_and_merges_same_role():
    history = [ChatTurn(role="assistant", content="Hi!"), ChatTurn(role="user", content="first")]
    messages = build_messages(history, "second")
    assert messages == [{"role": "user", "content": "first\n\nsecond"}]


def test_reasoning_effort_only_sent_to_gpt_oss_models():
    service, completions = _groq_service(_completion("ok", model="qwen/qwen3.8-27b"), model="qwen/qwen3.8-27b")
    service.generate(REQUEST)
    assert "reasoning_effort" not in completions.calls[0]


def test_system_prompt_includes_counseling_context():
    from app.schemas.emotion import FusionResult
    from app.services.llm import build_system_prompt

    request = LLMRequest(
        message="I'm fine",
        emotion=FusionResult(state="sad", confidence=0.6, signals={}),
        modality_labels={"words": "neutral, calm", "voice": "sad", "face": "sad"},
        past_sessions=['2026-09-28, "Exams": they said "I\'m behind on chemistry"'],
        mood_history="sad x3, neutral x2 over the last 5 messages (most recent: sad)",
        policy=ResponsePolicy(tone="supportive", ask_question=True, include_resources=False),
    )
    prompt = build_system_prompt(request)
    assert "facial expression: sad" in prompt
    assert "voice tone: sad" in prompt
    assert "behind on chemistry" in prompt
    assert "sad x3" in prompt
    assert "check in" in prompt.lower()  # mismatch handling instruction
    assert "suggest talking to someone they trust or a counselor" not in prompt
