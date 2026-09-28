from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    """'Was this helpful?' feedback on an assistant message."""

    message_id: int = Field(gt=0)
    helpful: bool


class FeedbackResponse(BaseModel):
    message_id: int
    helpful: bool
