import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.concurrency import run_in_threadpool

from app.api.deps import get_current_user
from app.api.v1.emotion import AUDIO_REQUEST_BODY, read_audio_body
from app.config import settings
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.emotion import FaceExpressionSignal
from app.services.chat_service import ChatPipeline
from app.services.components import preprocess_audio
from app.services.interfaces import ChatService, InvalidInputError
from app.services.providers import (
    get_chat_service,
    get_speech_to_text_service,
    get_voice_emotion_service,
)

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


def _voice_turn(audio: bytes, content_type: str, conversation_id, face, user, service, stt, voice_model):
    started = time.perf_counter()
    preprocessed = preprocess_audio(audio, content_type)
    transcript = stt.transcribe_preprocessed(preprocessed)
    if not transcript.text.strip():
        raise InvalidInputError("No speech could be transcribed from the audio")
    # Voice emotion is optional: the turn still works if the model is not trained.
    voice = voice_model.analyze_preprocessed(preprocessed) if voice_model.available else None
    audio_ms = round((time.perf_counter() - started) * 1000, 2)
    return service.respond(
        user,
        ChatRequest(message=transcript.text, conversation_id=conversation_id, face=face),
        voice=voice,
        transcript=transcript.text,
        timings={"audio_ms": audio_ms},
    )


@router.post("/chat/voice", response_model=ChatResponse, openapi_extra=AUDIO_REQUEST_BODY)
async def chat_voice(
    request: Request,
    conversation_id: int | None = Query(None, gt=0),
    face_emotion: str | None = Query(None, min_length=1, max_length=50),
    face_confidence: float | None = Query(None, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    service: ChatPipeline = Depends(get_chat_service),
    stt=Depends(get_speech_to_text_service),
    voice_model=Depends(get_voice_emotion_service),
):
    """
    Voice turn: raw WAV/FLAC body -> preprocessing -> speech-to-text + voice
    emotion -> the same pipeline as /chat. Returns the transcript with the reply.
    Optional face_emotion + face_confidence carry the browser's facial-expression estimate.
    """
    if (face_emotion is None) != (face_confidence is None):
        raise HTTPException(status_code=422, detail="face_emotion and face_confidence must be sent together")
    face = (
        FaceExpressionSignal(emotion=face_emotion, confidence=face_confidence)
        if face_emotion is not None else None
    )
    content_type = request.headers.get("content-type", "")
    if not content_type.lower().startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type must be an audio/* media type",
        )
    audio = await read_audio_body(request, settings.MAX_AUDIO_UPLOAD_BYTES)
    if not audio:
        raise HTTPException(status_code=422, detail="Audio body must not be empty")
    return await run_in_threadpool(
        _voice_turn, audio, content_type, conversation_id, face, current_user, service, stt, voice_model
    )
