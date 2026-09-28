from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.interfaces import ChatService
from app.services.providers import get_chat_service

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Send a message and receive the assistant's reply. Omit conversation_id
    to start a new conversation.
    """
    return service.respond(current_user, request)
