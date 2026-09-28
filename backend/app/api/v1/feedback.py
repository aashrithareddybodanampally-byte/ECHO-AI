from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.interfaces import FeedbackService
from app.services.providers import get_feedback_service

router = APIRouter(tags=["Feedback"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    service: FeedbackService = Depends(get_feedback_service),
):
    """
    Record whether an assistant message was helpful.
    """
    return service.submit(current_user, request)
