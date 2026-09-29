"""
Conversation pipeline and database-backed services.

Chat turn:
  ownership check -> context window -> save user message -> input safety
  -> text analysis (+ voice) -> fusion (+ previous-turn context)
  -> [high risk: crisis protocol, LLM bypassed]
  -> memory + retrieval -> response policy -> LLM -> output safety
  -> save reply (+ analysis when the user opted in)
"""

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.analysis_result import AnalysisResult
from app.models.conversation import Conversation
from app.models.feedback import Feedback
from app.models.memory import Memory
from app.models.message import Message, MessageRole
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse, FeedbackSummary
from app.schemas.chat import ChatRequest, ChatResponse, ConversationResponse, HistoryResponse
from app.schemas.emotion import ContextSignal, FusionRequest, VoiceEmotionResult
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.schemas.llm import ChatTurn, LLMRequest
from app.schemas.safety import SafetyLevel
from app.services import components
from app.services.interfaces import InvalidInputError, ResourceNotFoundError
from app.services.policy import asks_for_help, decide_policy, decide_stage

logger = logging.getLogger(__name__)

SAFETY_PROTOCOL_MODEL = "safety-protocol"
# Weight applied to the previous turn's fused confidence when used as context.
CONTEXT_DECAY = 0.8


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _owned_conversation(db: Session, user: User, conversation_id: int) -> Conversation:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if conversation is None:
        raise ResourceNotFoundError(f"conversation {conversation_id}")
    return conversation


def build_context(messages: list[Message], max_messages: int, max_chars: int) -> list[ChatTurn]:
    """Most recent messages (oldest first) within count and character budgets."""
    selected: list[ChatTurn] = []
    used = 0
    for message in reversed(messages[-max_messages:]):
        if used + len(message.content) > max_chars:
            break
        selected.append(ChatTurn(role=message.role, content=message.content))
        used += len(message.content)
    return list(reversed(selected))


PAST_SESSIONS = 3
PAST_SESSION_MESSAGES = 2
MOOD_HISTORY_TURNS = 12


def summarize_past_sessions(db: Session, user: User, exclude_id: int) -> list[str]:
    """Short summaries of the user's most recent other conversations (their own words only)."""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id, Conversation.id != exclude_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .limit(PAST_SESSIONS)
        .all()
    )
    summaries = []
    for conversation in conversations:
        said = (
            db.query(Message.content)
            .filter(Message.conversation_id == conversation.id, Message.role == MessageRole.USER.value)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(PAST_SESSION_MESSAGES)
            .all()
        )
        if not said:
            continue
        quotes = "; ".join(f'"{content[:160]}"' for (content,) in reversed(said))
        when = conversation.updated_at.strftime("%Y-%m-%d") if conversation.updated_at else "earlier"
        summaries.append(f"{when}, \"{conversation.title or 'Untitled'}\": they said {quotes}")
    return summaries


def summarize_mood_history(db: Session, user: User) -> str | None:
    """Counts of recent fused mood estimates, only available when the user saves them."""
    states = [
        state for (state,) in db.query(AnalysisResult.fused_state)
        .filter(AnalysisResult.user_id == user.id)
        .order_by(AnalysisResult.id.desc())
        .limit(MOOD_HISTORY_TURNS)
        .all()
    ]
    if not states:
        return None
    counts: dict[str, int] = {}
    for state in states:
        counts[state] = counts.get(state, 0) + 1
    ordered = ", ".join(f"{k} x{v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
    return f"{ordered} over the last {len(states)} messages (most recent: {states[0]})"


class ChatPipeline:
    def __init__(self, db: Session):
        self.db = db

    def respond(
        self,
        user: User,
        request: ChatRequest,
        voice: VoiceEmotionResult | None = None,
        transcript: str | None = None,
        timings: dict[str, float] | None = None,
    ) -> ChatResponse:
        db = self.db
        timings = dict(timings or {})
        started = time.perf_counter()

        def mark(stage: str, since: float) -> float:
            now = time.perf_counter()
            timings[stage] = round((now - since) * 1000, 2)
            return now

        # Conversation + context window (built before the new message is saved).
        if request.conversation_id is not None:
            conversation = _owned_conversation(db, user, request.conversation_id)
        else:
            conversation = Conversation(user_id=user.id, title=request.message.strip()[:60])
            db.add(conversation)
            db.flush()
        previous = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(settings.CONTEXT_MAX_MESSAGES)
            .all()
        )
        history = build_context(
            list(reversed(previous)), settings.CONTEXT_MAX_MESSAGES, settings.CONTEXT_MAX_CHARS
        )
        user_message = Message(
            conversation_id=conversation.id, role=MessageRole.USER.value, content=request.message
        )
        db.add(user_message)
        db.flush()
        t = mark("context_ms", started)

        # Understanding.
        safety_in = components.safety().check_input(request.message)
        text = components.text_analysis().analyze(request.message)
        t = mark("text_analysis_ms", t)

        last_analysis = (
            db.query(AnalysisResult)
            .join(Message, Message.id == AnalysisResult.message_id)
            .filter(Message.conversation_id == conversation.id)
            .order_by(AnalysisResult.id.desc())
            .first()
        )
        context = (
            ContextSignal(
                label=last_analysis.fused_state,
                score=round(last_analysis.fused_confidence * CONTEXT_DECAY, 6),
            )
            if last_analysis
            else None
        )
        emotion = components.fusion().fuse(
            FusionRequest(voice=voice, text=text, face=request.face, context=context)
        )
        modality_labels = {"words": f"{text.sentiment}, {text.emotion}"}
        if voice:
            modality_labels["voice"] = voice.emotion
        if request.face:
            from ml.models.fusion import normalize_label

            modality_labels["face"] = normalize_label(request.face.emotion)
        t = mark("fusion_ms", t)

        sources = []
        if safety_in.level == SafetyLevel.HIGH_RISK:
            from safety.guardrails import CRISIS_RESPONSE

            reply_text, model = CRISIS_RESPONSE, SAFETY_PROTOCOL_MODEL
        else:
            memories, past_sessions = [], []
            if user.memory_enabled:
                memories = [
                    m.content for m in db.query(Memory)
                    .filter(Memory.user_id == user.id).order_by(Memory.id).all()
                ]
                past_sessions = summarize_past_sessions(db, user, conversation.id)
            mood_history = summarize_mood_history(db, user) if user.save_emotion_stats else None
            user_turns = sum(1 for turn in history if turn.role == MessageRole.USER) + 1
            wants_help = asks_for_help(request.message)
            # Knowledge-base tips only when the person asks for help; earlier they pull the
            # reply toward advice before the person feels heard.
            if decide_stage(user_turns, wants_help) == "support":
                sources = components.retrieval().retrieve(request.message, settings.RAG_TOP_K)
                t = mark("retrieval_ms", t)

            policy = decide_policy(
                emotion, user.response_style, safety_in.level, safety_in.reasons,
                user_turns=user_turns, wants_help=wants_help,
            )
            generated = components.llm().generate(LLMRequest(
                message=request.message, history=history, emotion=emotion,
                retrieved=sources, safety_level=safety_in.level,
                policy=policy, memories=memories, modality_labels=modality_labels,
                past_sessions=past_sessions, mood_history=mood_history,
            ))
            t = mark("llm_ms", t)
            reply_text, model = generated.content, generated.model

            safety_out = components.safety().check_output(reply_text)
            if not safety_out.approved:
                from safety.guardrails import SAFE_FALLBACK_RESPONSE

                logger.warning("Output guardrail replaced a reply: %s", safety_out.flags)
                reply_text = SAFE_FALLBACK_RESPONSE
                sources = []
            t = mark("output_safety_ms", t)

        reply = Message(
            conversation_id=conversation.id, role=MessageRole.ASSISTANT.value, content=reply_text
        )
        db.add(reply)
        conversation.updated_at = _now()
        timings["total_ms"] = round(
            (time.perf_counter() - started) * 1000 + timings.get("audio_ms", 0.0), 2
        )

        if user.save_emotion_stats:
            db.add(AnalysisResult(
                message_id=user_message.id, user_id=user.id,
                voice_emotion=voice.emotion if voice else None,
                voice_confidence=voice.confidence if voice else None,
                text_sentiment=text.sentiment, text_emotion=text.emotion,
                text_confidence=text.confidence,
                fused_state=emotion.state, fused_confidence=emotion.confidence,
                safety_level=safety_in.level.value, latency_ms=timings["total_ms"],
            ))
        db.commit()
        db.refresh(reply)

        return ChatResponse(
            conversation_id=conversation.id,
            reply=reply,
            sources=sources,
            emotion=emotion,
            safety_level=safety_in.level,
            transcript=transcript,
            llm_model=model,
            timings_ms=timings,
        )


class DatabaseHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def list_conversations(self, user: User, limit: int, offset: int) -> HistoryResponse:
        conversations = (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .offset(offset).limit(limit).all()
        )
        items = []
        for conversation in conversations:
            messages = sorted(conversation.messages, key=lambda m: (m.created_at, m.id))
            items.append(ConversationResponse(
                id=conversation.id, title=conversation.title,
                created_at=conversation.created_at, updated_at=conversation.updated_at,
                messages=messages,
            ))
        return HistoryResponse(conversations=items)

    def delete_conversation(self, user: User, conversation_id: int) -> None:
        conversation = _owned_conversation(self.db, user, conversation_id)
        self.db.delete(conversation)
        self.db.commit()


class DatabaseFeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def submit(self, user: User, request: FeedbackRequest) -> FeedbackResponse:
        message = (
            self.db.query(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .filter(Message.id == request.message_id, Conversation.user_id == user.id)
            .first()
        )
        if message is None:
            raise ResourceNotFoundError(f"message {request.message_id}")
        if message.role != MessageRole.ASSISTANT.value:
            raise InvalidInputError("Feedback can only be given on assistant messages")
        feedback = self.db.query(Feedback).filter(Feedback.message_id == message.id).first()
        if feedback is None:
            feedback = Feedback(message_id=message.id, user_id=user.id, helpful=request.helpful)
            self.db.add(feedback)
        else:
            feedback.helpful = request.helpful
        self.db.commit()
        return FeedbackResponse(message_id=message.id, helpful=request.helpful)


class DatabaseAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def summarize(self, user: User) -> AnalyticsResponse:
        distribution = dict(
            self.db.query(AnalysisResult.fused_state, func.count(AnalysisResult.id))
            .filter(AnalysisResult.user_id == user.id)
            .group_by(AnalysisResult.fused_state).all()
        )
        counts = dict(
            self.db.query(Feedback.helpful, func.count(Feedback.id))
            .filter(Feedback.user_id == user.id)
            .group_by(Feedback.helpful).all()
        )
        return AnalyticsResponse(
            emotion_distribution={k: int(v) for k, v in distribution.items()},
            feedback=FeedbackSummary(
                helpful=int(counts.get(True, 0)), not_helpful=int(counts.get(False, 0))
            ),
        )
