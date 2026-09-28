"""
LLM providers behind the LLMService interface.

- AnthropicLLMService: Claude via the official Anthropic SDK.
- OfflineLLMService:   deterministic template responder used when no API key
                       is configured or the provider fails. Clearly labeled via
                       LLMResponse.model so it is never mistaken for an LLM.
"""

import logging
import re

from app.schemas.llm import ChatTurn, LLMRequest, LLMResponse
from app.schemas.safety import SafetyLevel

logger = logging.getLogger(__name__)

OFFLINE_MODEL = "offline-template-v1"

BASE_SYSTEM_PROMPT = """You are ECHO-AI, a supportive, context-aware conversational assistant.

Rules you must always follow:
- You are not a doctor or therapist. Never diagnose conditions, never give medication or dosage advice, and never claim certainty about someone's mental or medical state.
- Emotion signals you receive are uncertain model predictions from the user's voice and words. You may gently acknowledge how the user might be feeling, but never state it as a fact and never mention scores or models.
- When knowledge excerpts are provided and relevant, base factual suggestions on them and cite them inline as [1], [2], matching their numbers. Do not invent sources.
- If the user seems distressed, respond with warmth, keep it simple, and encourage reaching out to trusted people or a professional.
- Write in plain conversational prose without headings. Use a short list only when giving several concrete steps."""

_LENGTH_GUIDE = {
    "short": "Keep the reply to 2-3 sentences.",
    "medium": "Keep the reply to one or two short paragraphs.",
    "long": "You may give a fuller answer of up to four short paragraphs.",
}
_TONE_GUIDE = {
    "neutral": "Use a friendly, clear tone.",
    "warm": "Use a warm, upbeat tone.",
    "supportive": "Use a gentle, supportive and validating tone.",
}


def build_system_prompt(request: LLMRequest) -> str:
    policy = request.policy
    parts = [BASE_SYSTEM_PROMPT, "", "Guidance for this reply:",
             f"- {_TONE_GUIDE[policy.tone]}", f"- {_LENGTH_GUIDE[policy.length]}"]
    if policy.ask_question:
        parts.append("- End with one gentle, open question to understand the user better.")
    if policy.include_resources:
        parts.append("- Briefly mention that talking to someone they trust or a professional can help.")
    if request.safety_level == SafetyLevel.DISTRESS:
        parts.append("- The user's message shows signs of distress. Prioritize support over problem-solving.")
    if request.emotion:
        parts.append(
            f"- Possible emotional state (uncertain prediction): {request.emotion.state}."
        )
    if request.memories:
        parts.append("\nThings the user asked you to remember:")
        parts.extend(f"- {m}" for m in request.memories)
    if request.retrieved:
        parts.append("\nKnowledge excerpts:")
        for i, chunk in enumerate(request.retrieved, start=1):
            parts.append(f"[{i}] {chunk.source}: {chunk.content}")
    return "\n".join(parts)


def build_messages(history: list[ChatTurn], message: str) -> list[dict]:
    """Alternating user/assistant messages ending with the current user message."""
    turns = [t for t in history if t.role.value in ("user", "assistant")]
    turns.append(ChatTurn(role="user", content=message))
    messages: list[dict] = []
    for turn in turns:
        role = turn.role.value
        if messages and messages[-1]["role"] == role:
            messages[-1]["content"] += "\n\n" + turn.content
        else:
            messages.append({"role": role, "content": turn.content})
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    return messages


class OfflineLLMService:
    """Template-based responder. Not an LLM."""

    def generate(self, request: LLMRequest) -> LLMResponse:
        policy = request.policy
        parts = []
        if policy.tone == "supportive":
            parts.append("That sounds really hard, and it makes sense to feel this way.")
        elif policy.tone == "warm":
            parts.append("That's good to hear!")
        else:
            parts.append("Thanks for sharing that with me.")
        if request.retrieved:
            first = re.split(r"(?<=[.!?])\s", request.retrieved[0].content, maxsplit=1)[0]
            parts.append(f"One idea that may help: {first} [1]")
        if policy.include_resources:
            parts.append("Talking with someone you trust or a professional can also make a real difference.")
        if policy.ask_question:
            parts.append("What feels like the hardest part right now?")
        return LLMResponse(content=" ".join(parts), model=OFFLINE_MODEL)


class AnthropicLLMService:
    def __init__(self, api_key: str, model: str, effort: str, max_tokens: int, timeout: float):
        import anthropic

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=2)
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self._fallback = OfflineLLMService()

    def generate(self, request: LLMRequest) -> LLMResponse:
        anthropic = self._anthropic
        try:
            response = self._client.beta.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=build_system_prompt(request),
                messages=build_messages(request.history, request.message),
                output_config={"effort": self.effort},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            logger.error("Anthropic credentials rejected: %s", exc)
            return self._fallback.generate(request)
        except anthropic.RateLimitError as exc:
            logger.warning("Anthropic rate limited: %s", exc)
            return self._fallback.generate(request)
        except anthropic.APIStatusError as exc:
            logger.error("Anthropic API error %s: %s", exc.status_code, exc)
            return self._fallback.generate(request)
        except anthropic.APIConnectionError as exc:
            logger.error("Anthropic connection error: %s", exc)
            return self._fallback.generate(request)

        if response.stop_reason == "refusal":
            logger.warning("Anthropic refused the request")
            return self._fallback.generate(request)
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        if not text:
            return self._fallback.generate(request)
        return LLMResponse(content=text, model=response.model)


def build_llm_service(settings):
    provider = settings.LLM_PROVIDER.lower()
    if provider == "offline" or (provider == "auto" and not settings.ANTHROPIC_API_KEY):
        return OfflineLLMService()
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY")
    return AnthropicLLMService(
        api_key=settings.ANTHROPIC_API_KEY,
        model=settings.LLM_MODEL,
        effort=settings.LLM_EFFORT,
        max_tokens=settings.LLM_MAX_TOKENS,
        timeout=settings.LLM_TIMEOUT_SECONDS,
    )
