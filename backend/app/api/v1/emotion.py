from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool

from app.api.deps import get_current_user
from app.config import settings
from app.models.user import User
from app.schemas.emotion import FusionRequest, FusionResult, VoiceEmotionResult
from app.services.interfaces import FusionService, VoiceEmotionService
from app.services.providers import get_fusion_service, get_voice_emotion_service

router = APIRouter(prefix="/emotion", tags=["Emotion"])

# The body is read manually (not declared as a parameter) so that FastAPI does
# not buffer it before authentication runs, and so the size limit is enforced
# while streaming.
_AUDIO_REQUEST_BODY = {
    "requestBody": {
        "required": True,
        "content": {"audio/*": {"schema": {"type": "string", "format": "binary"}}},
    }
}


async def _read_audio_body(request: Request, max_bytes: int) -> bytes:
    too_large = HTTPException(
        status_code=413,
        detail=f"Audio upload exceeds the maximum size of {max_bytes} bytes",
    )
    content_length = request.headers.get("content-length")
    if content_length is not None and content_length.isdigit() and int(content_length) > max_bytes:
        raise too_large

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > max_bytes:
            raise too_large
    return bytes(body)


@router.post("/analyze", response_model=VoiceEmotionResult, openapi_extra=_AUDIO_REQUEST_BODY)
async def analyze_voice_emotion(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: VoiceEmotionService = Depends(get_voice_emotion_service),
):
    """
    Predict emotion from a raw audio request body (Content-Type: audio/*).
    The result is a model prediction, not a diagnosis.
    """
    content_type = request.headers.get("content-type", "")
    if not content_type.lower().startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type must be an audio/* media type",
        )
    audio = await _read_audio_body(request, settings.MAX_AUDIO_UPLOAD_BYTES)
    if not audio:
        raise HTTPException(
            status_code=422,
            detail="Audio body must not be empty",
        )
    return await run_in_threadpool(service.analyze, audio, content_type)


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
