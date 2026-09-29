"""
LLM service contracts (internal; no public endpoint).

Phase 2.5: Contracts only — no provider is selected and no LLM is called.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.models.message import MessageRole
from app.schemas.emotion import FusionResult
from app.schemas.rag import RetrievedChunk
from app.schemas.safety import SafetyLevel


class ChatTurn(BaseModel):
    role: MessageRole
    content: str


class ResponsePolicy(BaseModel):
    """Deterministic style decisions made before generation."""

    tone: Literal["neutral", "warm", "supportive"] = "neutral"
    length: Literal["brief", "short", "medium", "long"] = "short"
    ask_question: bool = False
    include_resources: bool = False
    # Counseling stage: "explore" (listen, reflect, small questions; no advice),
    # "deepen" (summarize, notice patterns, gently question absolutes),
    # "support" (they asked for help: offer one small, concrete idea).
    stage: Literal["explore", "deepen", "support"] = "explore"


class LLMRequest(BaseModel):
    message: str = Field(min_length=1)
    # Chronological conversation context selected by the context engine.
    history: list[ChatTurn] = Field(default_factory=list)
    emotion: FusionResult | None = None
    retrieved: list[RetrievedChunk] = Field(default_factory=list)
    safety_level: SafetyLevel = SafetyLevel.NORMAL
    policy: ResponsePolicy = Field(default_factory=ResponsePolicy)
    # User-approved long-term memories (empty when memory is disabled).
    memories: list[str] = Field(default_factory=list)
    # Per-modality mood labels for this turn, e.g. {"voice": "sad", "words": "neutral", "face": "sad"}.
    modality_labels: dict[str, str] = Field(default_factory=dict)
    # Short summaries of the user's previous conversations (empty when memory is disabled).
    past_sessions: list[str] = Field(default_factory=list)
    # Summary of recent fused mood estimates (only when the user saves emotion statistics).
    mood_history: str | None = None


class LLMResponse(BaseModel):
    content: str
    # Identifies which provider/model produced the response.
    model: str = Field(min_length=1)
