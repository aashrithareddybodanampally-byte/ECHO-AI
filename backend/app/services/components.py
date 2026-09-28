"""
Process-wide singletons for heavy components, loaded lazily on first use.

Each adapter converts between the isolated ml/rag/safety packages (plain
dicts, their own exceptions) and backend schemas / service errors.
"""

import logging
from functools import lru_cache

from app.config import settings
from app.schemas.emotion import (
    FusionRequest,
    FusionResult,
    TextAnalysisResult,
    TranscriptionResult,
    VoiceEmotionResult,
)
from app.schemas.rag import RetrievedChunk
from app.schemas.safety import InputSafetyAssessment, OutputSafetyAssessment
from app.services.interfaces import (
    InvalidInputError,
    ServiceUnavailableError,
    UnsupportedMediaError,
)

logger = logging.getLogger(__name__)


def preprocess_audio(audio: bytes, content_type: str):
    from ml.audio.preprocessing import (
        DefaultAudioPreprocessor,
        InvalidAudioError,
        UnsupportedAudioFormatError,
    )

    try:
        return DefaultAudioPreprocessor().preprocess(audio, content_type)
    except UnsupportedAudioFormatError as exc:
        raise UnsupportedMediaError(str(exc)) from exc
    except InvalidAudioError as exc:
        raise InvalidInputError(str(exc)) from exc


class VoiceEmotionAdapter:
    def __init__(self, model_path):
        self.model_path = model_path
        self._model = None

    def _load(self):
        if self._model is None:
            from ml.inference.voice_emotion import ModelNotAvailableError, VoiceEmotionModel

            try:
                self._model = VoiceEmotionModel(self.model_path)
            except ModelNotAvailableError as exc:
                raise ServiceUnavailableError(
                    "Voice emotion model is not available. Train it with "
                    "`python -m ml.training.train_voice_emotion`."
                ) from exc
        return self._model

    @property
    def available(self) -> bool:
        try:
            self._load()
            return True
        except ServiceUnavailableError:
            return False

    def analyze_preprocessed(self, audio) -> VoiceEmotionResult:
        return VoiceEmotionResult(**self._load().predict_preprocessed(audio))

    def analyze(self, audio: bytes, content_type: str) -> VoiceEmotionResult:
        return self.analyze_preprocessed(preprocess_audio(audio, content_type))


class SpeechToTextAdapter:
    def __init__(self, enabled: bool, model_size: str):
        self.enabled = enabled
        self.model_size = model_size
        self._transcriber = None

    def transcribe_preprocessed(self, audio) -> TranscriptionResult:
        if not self.enabled:
            raise ServiceUnavailableError("Speech-to-text is disabled (STT_ENABLED=false)")
        from ml.audio.speech_to_text import SpeechToTextUnavailableError, WhisperTranscriber

        if self._transcriber is None:
            self._transcriber = WhisperTranscriber(self.model_size)
        try:
            return TranscriptionResult(
                **self._transcriber.transcribe(audio.samples, audio.sample_rate)
            )
        except SpeechToTextUnavailableError as exc:
            raise ServiceUnavailableError(f"Speech-to-text unavailable: {exc}") from exc

    def transcribe(self, audio: bytes, content_type: str) -> TranscriptionResult:
        return self.transcribe_preprocessed(preprocess_audio(audio, content_type))


class TextAnalysisAdapter:
    def __init__(self):
        from ml.nlp.text_emotion import TextEmotionAnalyzer

        self._analyzer = TextEmotionAnalyzer()

    def analyze(self, text: str) -> TextAnalysisResult:
        return TextAnalysisResult(**self._analyzer.analyze(text))


class FusionAdapter:
    def fuse(self, request: FusionRequest) -> FusionResult:
        from ml.models.fusion import fuse

        return FusionResult(**fuse(
            voice=request.voice.model_dump() if request.voice else None,
            text=request.text.model_dump() if request.text else None,
            context=request.context.model_dump() if request.context else None,
        ))


class RetrievalAdapter:
    def __init__(self):
        from rag.retrieval.retriever import TfidfRetriever

        self._retriever = TfidfRetriever.from_directory()

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        return [RetrievedChunk(**c) for c in self._retriever.retrieve(query, top_k)]


class SafetyAdapter:
    def check_input(self, text: str) -> InputSafetyAssessment:
        from safety.guardrails import check_input

        return InputSafetyAssessment(**check_input(text))

    def check_output(self, text: str) -> OutputSafetyAssessment:
        from safety.guardrails import check_output

        return OutputSafetyAssessment(**check_output(text))


@lru_cache
def voice_emotion() -> VoiceEmotionAdapter:
    return VoiceEmotionAdapter(settings.VOICE_EMOTION_MODEL_PATH)


@lru_cache
def speech_to_text() -> SpeechToTextAdapter:
    return SpeechToTextAdapter(settings.STT_ENABLED, settings.WHISPER_MODEL_SIZE)


@lru_cache
def text_analysis() -> TextAnalysisAdapter:
    return TextAnalysisAdapter()


@lru_cache
def fusion() -> FusionAdapter:
    return FusionAdapter()


@lru_cache
def retrieval() -> RetrievalAdapter:
    return RetrievalAdapter()


@lru_cache
def safety() -> SafetyAdapter:
    return SafetyAdapter()


@lru_cache
def llm():
    from app.services.llm import build_llm_service

    service = build_llm_service(settings)
    logger.info("LLM provider: %s", type(service).__name__)
    return service
