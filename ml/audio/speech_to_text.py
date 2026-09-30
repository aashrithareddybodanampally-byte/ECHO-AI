"""
Speech-to-text using faster-whisper (local CPU inference).

The Whisper model is downloaded from Hugging Face on first use and cached by
faster-whisper. Input is preprocessed 16 kHz mono float32 audio.
"""

import math
import threading

import numpy as np


class SpeechToTextUnavailableError(Exception):
    """faster-whisper is not installed or the model could not be loaded."""


class WhisperTranscriber:
    def __init__(self, model_size: str = "base", compute_type: str = "int8"):
        self.model_size = model_size
        self.compute_type = compute_type
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                try:
                    from faster_whisper import WhisperModel
                    self._model = WhisperModel(
                        self.model_size, device="cpu", compute_type=self.compute_type
                    )
                except Exception as exc:  # import error, download failure, bad model name
                    raise SpeechToTextUnavailableError(str(exc)) from exc
        return self._model

    def transcribe(self, samples: np.ndarray, sample_rate: int, language: str | None = None) -> dict:
        if sample_rate != 16000:
            raise ValueError("Whisper expects 16 kHz audio")
        model = self._load()
        segments, info = model.transcribe(
            samples.astype(np.float32), language=language, beam_size=1, vad_filter=False
        )
        segments = list(segments)
        text = " ".join(s.text.strip() for s in segments).strip()
        # Heuristic confidence: mean per-segment token probability (exp of avg log-prob).
        confidence = None
        if segments:
            confidence = float(np.mean([math.exp(s.avg_logprob) for s in segments]))
            confidence = min(1.0, max(0.0, confidence))
        return {"text": text, "language": info.language, "confidence": confidence}
