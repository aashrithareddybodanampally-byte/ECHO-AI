from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.rag import RetrieveRequest, RetrieveResponse
from app.services.interfaces import RetrievalService
from app.services.providers import get_retrieval_service

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(
    request: RetrieveRequest,
    current_user: User = Depends(get_current_user),
    service: RetrievalService = Depends(get_retrieval_service),
):
    """
    Return the top-k knowledge-base chunks relevant to the query, with sources.
    """
    chunks = service.retrieve(request.query, request.top_k)
    return RetrieveResponse(query=request.query, chunks=chunks)
