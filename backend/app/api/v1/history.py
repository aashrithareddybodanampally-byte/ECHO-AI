from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.chat import HistoryResponse
from app.services.interfaces import HistoryService
from app.services.providers import get_history_service

router = APIRouter(tags=["History"])


@router.get("/history", response_model=HistoryResponse)
def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: HistoryService = Depends(get_history_service),
):
    """
    List the current user's conversations with their messages in chronological order.
    """
    return service.list_conversations(current_user, limit, offset)
