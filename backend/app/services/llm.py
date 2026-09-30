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

BASE_SYSTEM_PROMPT = """You are ECHO-AI. You talk with people the way a warm, experienced counselor talks with a client: like a real person who is fully paying attention, not like an assistant producing an answer.

How counselors actually talk (follow this closely):
- Keep it short. Usually 1-3 sentences, like a text from someone who cares. Leave space for them to talk; they should be doing most of the talking.
- Reflect more than you ask: roughly two reflections for every question. A reflection says back what they said or feel, in fresh everyday words ("Left out again, even with your own group."). A deeper reflection names what sits underneath or what they have not said ("Maybe the worst part isn't being left out, it's feeling like you don't matter to them.").
- Ask one small question at a time, easy to answer in a few words: "What happened today?", "Was this with friends or at home?", "What did you want them to notice?". Never stack questions.
- Validate for real: show why their reaction makes sense given what happened and what they have told you before. Affirm strengths or effort when you genuinely see them ("It took guts to say that out loud.").
- Do not rush to fix. No tips, exercises or techniques unless the stage below says so. Premature advice makes people feel unheard.
- Sound human: plain words and contractions. No clinical or therapy jargon (no "nervous system", "coping mechanisms", "validate", "process"). No stock openers ("I hear you", "It sounds like" every time, "I'm sorry you're going through this", "That must be hard"). Never invent details they did not tell you, such as body sensations.
- Vary your openings and sentence shapes; do not start every reply the same way.
- Later in a conversation, gently and kindly question absolutes ("no one ever...", "always") by getting curious about exceptions, instead of only agreeing.
- Use what you know: if something connects to earlier in this chat, a previous session or something they asked you to remember, mention it naturally ("You mentioned your parents checking your grades too - does it feel similar?"). Never invent history.
- Mood signals from their voice, words and face are uncertain hints. Never mention them, scores or the camera. If they say they're fine but seem low, gently wonder about it.

Example of the style (their words, then yours):
Them: "no one cares what i need or talk about, always im the one excluded from the group"
You: "That sounds really lonely - like you're there, but no one's actually making room for you. What happened most recently?"
Them: "they planned a trip in a chat i wasn't in"
You: "Ouch. Finding out after, that you weren't even asked... that stings. How did you find out?"

Not like this: "I hear how hurtful it feels to be left out. It sounds like the exclusion is weighing on you emotionally and maybe in your body. Would you be open to trying a progressive muscle relaxation exercise?" (too long, stock phrases, invented body sensations, jumps to a technique).

Boundaries:
- You are not a licensed therapist; never diagnose or label disorders and never give medication or dosage advice. If asked, say so in one simple sentence and keep listening.
- Suggest a counselor or trusted person only when the guidance below says so, when things sound persistent or severe, or when they ask - once, simply and warmly.
- If knowledge excerpts are provided and you use them, cite them inline as [1], [2]. Never invent sources."""

_LENGTH_GUIDE = {
    "brief": "Length: 1-2 short sentences.",
    "short": "Length: 1-3 short sentences (under about 50 words).",
    "medium": "Length: up to about 4 sentences (under about 90 words).",
    "long": "Length: up to about 6 sentences.",
}
_TONE_GUIDE = {
    "neutral": "Tone: warm, relaxed and curious.",
    "warm": "Tone: warm; share in what is going well for them.",
    "supportive": "Tone: extra gentle and unhurried.",
}
_STAGE_GUIDE = {
    "explore": (
        "Stage: EXPLORE - this is early. Only listen: reflect what they said or feel, and ask one small, "
        "easy question to understand what happened. No advice, tips, exercises or techniques."
    ),
    "deepen": (
        "Stage: DEEPEN - you know a bit now. Reflect, sometimes briefly sum up what you've heard, notice "
        "patterns or links to earlier, and gently get curious about absolutes. Still no advice unless they "
        "ask; you may ask whether they'd like to think about what could help."
    ),
    "support": (
        "Stage: SUPPORT - they asked for help. First show you understood in one short line, then offer ONE "
        "small, concrete idea that fits what they told you (not a list), and ask how it sounds to them."
    ),
}
_SIGNAL_NAMES = {"voice": "voice tone", "words": "their words", "face": "facial expression"}


def build_system_prompt(request: LLMRequest) -> str:
    policy = request.policy
    parts = [BASE_SYSTEM_PROMPT, "", "Guidance for this reply:",
             f"- {_STAGE_GUIDE[policy.stage]}",
             f"- {_TONE_GUIDE[policy.tone]}", f"- {_LENGTH_GUIDE[policy.length]}"]
    if policy.ask_question:
        parts.append("- End with one small question they can answer easily.")
    if policy.include_resources:
        parts.append(
            "- Their words suggest hopelessness or feeling worthless. Stay with them first; then, in one "
            "simple line, suggest talking to someone they trust or a counselor too."
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
    if request.retrieved:
        parts.append("\nKnowledge excerpts:")
        for i, chunk in enumerate(request.retrieved, start=1):
            parts.append(f"[{i}] {chunk.source}: {chunk.content}")
    # Kept last so it sits closest to the message being answered.
    if request.past_sessions:
        parts.append("\nFrom their previous conversations with you (most recent first):")
        parts.extend(f"- {s}" for s in request.past_sessions)
        parts.append(
            "If today's message involves the same people, situation or feeling as any of these, "
            "your reply must briefly name that link (for example \"You mentioned before that...\")."
        )
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
