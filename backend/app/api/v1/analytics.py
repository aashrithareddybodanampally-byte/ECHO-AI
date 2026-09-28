from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse
from app.services.interfaces import AnalyticsService
from app.services.providers import get_analytics_service

router = APIRouter(tags=["Analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Summarize the current user's emotion predictions and feedback.
    """
    return service.summarize(current_user)
