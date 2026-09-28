from fastapi import APIRouter, Body, Depends, Header, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.emotion import FusionRequest, FusionResult, VoiceEmotionResult
from app.services.interfaces import FusionService, VoiceEmotionService
from app.services.providers import get_fusion_service, get_voice_emotion_service

router = APIRouter(prefix="/emotion", tags=["Emotion"])


@router.post("/analyze", response_model=VoiceEmotionResult)
def analyze_voice_emotion(
    audio: bytes = Body(..., media_type="audio/*"),
    content_type: str = Header(...),
    current_user: User = Depends(get_current_user),
    service: VoiceEmotionService = Depends(get_voice_emotion_service),
):
    """
    Predict emotion from a raw audio request body (Content-Type: audio/*).
    The result is a model prediction, not a diagnosis.
    """
    if not content_type.lower().startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type must be an audio/* media type",
        )
    return service.analyze(audio, content_type)


@router.post("/fusion", response_model=FusionResult)
def fuse_emotion_signals(
    request: FusionRequest,
    current_user: User = Depends(get_current_user),
    service: FusionService = Depends(get_fusion_service),
):
    """
    Combine voice, text and context signals into a conversational state.
    """
    return service.fuse(request)
