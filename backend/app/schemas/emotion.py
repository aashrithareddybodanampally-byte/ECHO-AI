"""
Emotion, speech and fusion contracts.

Phase 2.5: Contracts only — no feature extraction, model inference,
transcription or fusion logic is implemented here.

Emotion/sentiment label sets are intentionally plain strings: the actual
labels must come from the dataset/model selected in a later phase and are
not fixed by this contract. All outputs are model predictions, not
clinical or psychological diagnoses.
"""

import math
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

# Scores, confidences and probabilities are always expressed in [0.0, 1.0].
Probability = Annotated[float, Field(ge=0.0, le=1.0)]

# Allowed floating-point drift when checking that a distribution sums to 1.
PROBABILITY_SUM_TOLERANCE = 1e-3


class VoiceEmotionResult(BaseModel):
    """Output of the voice emotion inference interface."""

    emotion: str = Field(min_length=1)
    confidence: Probability
    probabilities: dict[str, Probability] = Field(min_length=1)
    model_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_distribution(self) -> "VoiceEmotionResult":
        if self.emotion not in self.probabilities:
            raise ValueError("emotion must be one of the keys in probabilities")
        total = sum(self.probabilities.values())
        if not math.isclose(total, 1.0, abs_tol=PROBABILITY_SUM_TOLERANCE):
            raise ValueError("probabilities must sum to 1.0")
        if not math.isclose(
            self.confidence, self.probabilities[self.emotion], abs_tol=1e-6
        ):
            raise ValueError("confidence must equal the probability of emotion")
        return self


class TranscriptionResult(BaseModel):
    """Output of the speech-to-text interface."""

    text: str
    language: str | None = None
    # Not every speech-to-text model reports confidence.
    confidence: Probability | None = None


class TextAnalysisResult(BaseModel):
    """Output of the text sentiment/emotion interface."""

    sentiment: str = Field(min_length=1)
    emotion: str = Field(min_length=1)
    confidence: Probability
    model_version: str = Field(min_length=1)


class ContextSignal(BaseModel):
    """A conversation-context signal supplied to fusion (e.g. exam-related stress)."""

    label: str = Field(min_length=1)
    score: Probability


class FusionRequest(BaseModel):
    """Inputs to multimodal fusion. At least one of voice or text is required."""

    voice: VoiceEmotionResult | None = None
    text: TextAnalysisResult | None = None
    context: ContextSignal | None = None

    @model_validator(mode="after")
    def check_has_modality(self) -> "FusionRequest":
        if self.voice is None and self.text is None:
            raise ValueError("at least one of voice or text must be provided")
        return self


class FusionSignals(BaseModel):
    """Per-modality scores that supported the fused state."""

    voice: Probability | None = None
    text: Probability | None = None
    context: Probability | None = None


class FusionResult(BaseModel):
    """Output of multimodal fusion. The fusion method itself is not part of the contract."""

    state: str = Field(min_length=1)
    confidence: Probability
    signals: FusionSignals
