"""
Voice emotion inference: preprocess -> features -> trained classifier.

Returns plain dicts so this module never depends on backend schemas.
"""

from pathlib import Path

import joblib
import numpy as np

from ml.audio.features import FEATURE_VERSION, extract_features
from ml.audio.preprocessing import DefaultAudioPreprocessor, PreprocessedAudio


class ModelNotAvailableError(Exception):
    """The trained model artifact is missing or incompatible."""


class VoiceEmotionModel:
    def __init__(self, model_path: Path, preprocessor: DefaultAudioPreprocessor | None = None):
        if not model_path.exists():
            raise ModelNotAvailableError(f"Model artifact not found: {model_path}")
        artifact = joblib.load(model_path)
        if artifact.get("feature_version") != FEATURE_VERSION:
            raise ModelNotAvailableError(
                f"Model was trained with features '{artifact.get('feature_version')}', "
                f"runtime provides '{FEATURE_VERSION}'"
            )
        self._model = artifact["model"]
        # Training uses all cores; for one clip at a time a worker pool only adds overhead.
        classifier = getattr(self._model, "named_steps", {}).get("clf")
        if classifier is not None and hasattr(classifier, "n_jobs"):
            classifier.n_jobs = 1
        self.labels: list[str] = [str(label) for label in artifact["labels"]]
        self.model_version: str = artifact["model_version"]
        self.preprocessor = preprocessor or DefaultAudioPreprocessor()

    def predict_preprocessed(self, audio: PreprocessedAudio) -> dict:
        vector = extract_features(audio.samples, audio.sample_rate).reshape(1, -1)
        probabilities = self._model.predict_proba(vector)[0].astype(float)
        probabilities = probabilities / probabilities.sum()
        distribution = {
            label: round(float(p), 6) for label, p in zip(self.labels, probabilities)
        }
        # Rounding to 6 places keeps the sum within the contract's 1e-3 tolerance.
        emotion = self.labels[int(np.argmax(probabilities))]
        return {
            "emotion": emotion,
            "confidence": distribution[emotion],
            "probabilities": distribution,
            "model_version": self.model_version,
        }

    def predict(self, audio: bytes, content_type: str) -> dict:
        return self.predict_preprocessed(self.preprocessor.preprocess(audio, content_type))
