"""
LLM providers behind the LLMService interface.

- GroqLLMService:      open models (default Llama 3.3 70B) via the Groq SDK.
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

BASE_SYSTEM_PROMPT = """You are ECHO-AI, an emotionally attuned conversational companion. You talk with people the way a skilled, warm counselor does: you listen closely, you remember, and you help them understand and work through what they are feeling. You are not a generic advice bot.

How you work in every conversation:
1. Attune first. Reflect back what the person said and what they seem to be feeling, in your own specific words, tentatively ("It sounds like...", "I wonder if..."). Name the feeling and the situation behind it. Never open with stock phrases such as "I hear you", "It's important to", or "I'm sorry you're going through this".
2. Stay curious. Ask one focused, open question at a time that helps them go deeper: what happened, what went through their mind, how it felt in their body, what they need. Do not interrogate; one question per reply at most.
3. Use what you know. Weave in relevant details from earlier in this conversation, from previous sessions and from things they asked you to remember ("Last time you mentioned your exams...") so they feel known. Only use details listed below; never invent history.
4. Read the signals. You receive uncertain estimates of their mood from their voice, words and (if they turned the camera on) facial expression. Treat them as hints, never facts, and never mention scores, models or the camera analysis itself. If the signals and their words disagree (they say "I'm fine" but sound or look low), gently and curiously check in about it.
5. Offer something useful, tailored to them. When it fits, suggest one concrete, evidence-based technique chosen for their situation (for example: noticing and questioning an unhelpful thought, a short grounding or breathing exercise, breaking a task into a first small step, scheduling one small pleasant activity, self-compassionate reframing, sleep routines, problem-solving the next step). Explain it in a sentence or two and invite them to try it, adapted to what they told you. Do not give generic lists of tips.
6. Collaborate. When unsure what they want, ask whether they would like to vent, think it through together, or try a coping strategy.

Boundaries:
- You are not a licensed therapist and do not diagnose, label disorders, or give medication or dosage advice. If asked, say so briefly and warmly, then keep supporting them.
- Do not redirect people to professionals by reflex; stay with them and engage. Suggest professional support only when the guidance below says so, when difficulties sound persistent or severe, or when they ask. When you do, make it specific and caring, once, and keep engaging.
- If knowledge excerpts are provided and relevant, base factual suggestions on them and cite them inline as [1], [2], matching their numbers. Never invent sources.
- Write in natural conversational prose, like a person talking, without headings or bullet lists unless you are walking through steps of an exercise."""

_LENGTH_GUIDE = {
    "short": "Keep the reply to 2-4 sentences.",
    "medium": "Keep the reply to about one short paragraph (roughly 60-120 words).",
    "long": "You may write up to three short paragraphs.",
}
_TONE_GUIDE = {
    "neutral": "Be warm and conversational.",
    "warm": "Be warm and share in what is going well for them.",
    "supportive": "Be especially gentle, validating and unhurried.",
}
_SIGNAL_NAMES = {"voice": "voice tone", "words": "their words", "face": "facial expression"}


def build_system_prompt(request: LLMRequest) -> str:
    policy = request.policy
    parts = [BASE_SYSTEM_PROMPT, "", "Guidance for this reply:",
             f"- {_TONE_GUIDE[policy.tone]}", f"- {_LENGTH_GUIDE[policy.length]}"]
    if policy.ask_question:
        parts.append("- End with one open, specific question that helps them explore further.")
    if policy.include_resources:
        parts.append(
            "- Their words suggest hopelessness or feeling worthless. After engaging with what they said, "
            "gently and specifically suggest talking to someone they trust or a counselor, once."
        )
    if request.safety_level == SafetyLevel.DISTRESS:
        parts.append("- They seem distressed. Slow down: prioritize understanding and emotional support over solutions.")
    if request.emotion or request.modality_labels:
        parts.append("\nCurrent mood signals (uncertain estimates, never state them as facts):")
        if request.emotion:
            parts.append(f"- Overall impression: {request.emotion.state}")
        for key, label in request.modality_labels.items():
            parts.append(f"- {_SIGNAL_NAMES.get(key, key)}: {label}")
    if request.mood_history:
        parts.append(f"\nMood across recent messages (estimates): {request.mood_history}")
    if request.memories:
        parts.append("\nThings they asked you to remember:")
        parts.extend(f"- {m}" for m in request.memories)
    if request.past_sessions:
        parts.append("\nFrom their previous conversations with you (most recent first):")
        parts.extend(f"- {s}" for s in request.past_sessions)
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


class GroqLLMService:
    def __init__(
        self, api_key: str, model: str, max_tokens: int, timeout: float, reasoning_effort: str = "low"
    ):
        import groq

        self._groq = groq
        self._client = groq.Groq(api_key=api_key, timeout=timeout, max_retries=2)
        self.model = model
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self._fallback = OfflineLLMService()

    def _extra_params(self) -> dict:
        # gpt-oss models reason before answering; reasoning is returned separately from
        # message.content, and a low effort keeps chat replies fast.
        if self.model.startswith("openai/gpt-oss") and self.reasoning_effort:
            return {"reasoning_effort": self.reasoning_effort}
        return {}

    def generate(self, request: LLMRequest) -> LLMResponse:
        groq = self._groq
        messages = [{"role": "system", "content": build_system_prompt(request)}]
        messages += build_messages(request.history, request.message)
        try:
            completion = self._client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=self.max_tokens,
                **self._extra_params(),
            )
        except (groq.AuthenticationError, groq.PermissionDeniedError) as exc:
            logger.error("Groq credentials rejected: %s", exc)
            return self._fallback.generate(request)
        except groq.RateLimitError as exc:
            logger.warning("Groq rate limited: %s", exc)
            return self._fallback.generate(request)
        except groq.APIStatusError as exc:
            logger.error("Groq API error %s: %s", exc.status_code, exc)
            return self._fallback.generate(request)
        except groq.APIConnectionError as exc:
            logger.error("Groq connection error: %s", exc)
            return self._fallback.generate(request)

        text = (completion.choices[0].message.content or "").strip() if completion.choices else ""
        if not text:
            return self._fallback.generate(request)
        return LLMResponse(content=text, model=completion.model or self.model)


def build_llm_service(settings):
    """
    LLM_PROVIDER: "auto" (Groq if GROQ_API_KEY is set, else Anthropic if
    ANTHROPIC_API_KEY is set, else offline), "groq", "anthropic" or "offline".
    """
    provider = settings.LLM_PROVIDER.lower()
    if provider == "auto":
        if settings.GROQ_API_KEY:
            provider = "groq"
        elif settings.ANTHROPIC_API_KEY:
            provider = "anthropic"
        else:
            provider = "offline"
    if provider == "offline":
        return OfflineLLMService()
    if provider == "groq":
        if not settings.GROQ_API_KEY:
            raise RuntimeError("LLM_PROVIDER=groq requires GROQ_API_KEY")
        return GroqLLMService(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            reasoning_effort=settings.GROQ_REASONING_EFFORT,
        )
    if provider != "anthropic":
        raise RuntimeError(f"Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}'")
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY")
    return AnthropicLLMService(
        api_key=settings.ANTHROPIC_API_KEY,
        model=settings.LLM_MODEL,
        effort=settings.LLM_EFFORT,
        max_tokens=settings.LLM_MAX_TOKENS,
        timeout=settings.LLM_TIMEOUT_SECONDS,
    )
