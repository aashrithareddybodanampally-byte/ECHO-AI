"""
Retrieval (RAG) contracts.

Phase 2.5: Contracts only — no ingestion, embeddings, vector store or
retrieval logic is implemented here.
"""

from pydantic import BaseModel, Field, field_validator


def reject_blank(value: str) -> str:
    """Reject whitespace-only text without altering the submitted value."""
    if not value.strip():
        raise ValueError("must not be blank")
    return value


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)

    _check_query = field_validator("query")(reject_blank)


class RetrievedChunk(BaseModel):
    """A retrieved passage and the source it came from (used for source grounding)."""

    source: str = Field(min_length=1)
    content: str
    # Range depends on the similarity metric chosen in the RAG phase.
    score: float


class RetrieveResponse(BaseModel):
    query: str
    chunks: list[RetrievedChunk]
