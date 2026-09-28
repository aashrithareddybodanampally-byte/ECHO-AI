"""
Chat and conversation-history contracts.

Phase 2.5: Contracts only — no context engine, memory, LLM orchestration
or persistence logic is implemented here.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.message import MessageRole
from app.schemas.emotion import FusionResult
from app.schemas.rag import RetrievedChunk, reject_blank


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime
    # Chronological order (oldest first).
    messages: list[MessageResponse]

    model_config = ConfigDict(from_attributes=True)


class HistoryResponse(BaseModel):
    conversations: list[ConversationResponse]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    # Omit to start a new conversation.
    conversation_id: int | None = Field(default=None, gt=0)

    _check_message = field_validator("message")(reject_blank)


class ChatResponse(BaseModel):
    conversation_id: int
    reply: MessageResponse
    # Sources that supported the reply; empty when retrieval was not used.
    sources: list[RetrievedChunk] = Field(default_factory=list)
    # Present only when emotion signals were available for this turn.
    emotion: FusionResult | None = None
