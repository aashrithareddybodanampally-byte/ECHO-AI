from pydantic import BaseModel, Field


class FeedbackSummary(BaseModel):
    helpful: int = Field(ge=0)
    not_helpful: int = Field(ge=0)


class AnalyticsResponse(BaseModel):
    """
    Per-user analytics.

    emotion_distribution counts model predictions per label; these are
    predictions, not clinical measurements.
    """

    emotion_distribution: dict[str, int]
    feedback: FeedbackSummary
