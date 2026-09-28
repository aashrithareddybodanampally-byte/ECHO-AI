"""
LLM service contracts (internal; no public endpoint).

Phase 2.5: Contracts only — no provider is selected and no LLM is called.
"""

from pydantic import BaseModel, Field

from app.models.message import MessageRole
from app.schemas.emotion import FusionResult
from app.schemas.rag import RetrievedChunk
from app.schemas.safety import SafetyLevel


class ChatTurn(BaseModel):
    role: MessageRole
    content: str


class LLMRequest(BaseModel):
    message: str = Field(min_length=1)
    # Chronological conversation context selected by the context engine.
    history: list[ChatTurn] = Field(default_factory=list)
    emotion: FusionResult | None = None
    retrieved: list[RetrievedChunk] = Field(default_factory=list)
    safety_level: SafetyLevel = SafetyLevel.NORMAL


class LLMResponse(BaseModel):
    content: str
    # Identifies which provider/model produced the response.
    model: str = Field(min_length=1)
