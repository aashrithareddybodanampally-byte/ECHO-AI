import json
from pathlib import Path

import numpy as np
import pytest

from ml.audio.features import FEATURE_DIM, FEATURE_NAMES, extract_features
from ml.inference.voice_emotion import ModelNotAvailableError, VoiceEmotionModel
from ml.training.ravdess import EMOTIONS, parse_filename, split, Sample
from ml.training.train_voice_emotion import train
from tests.ml.audio_helpers import encode, tone


def test_feature_vector_shape_and_names():
    vector = extract_features(tone(), 16000)
    assert vector.shape == (FEATURE_DIM,) == (len(FEATURE_NAMES),)
    assert vector.dtype == np.float32
    assert np.all(np.isfinite(vector))


def test_features_differ_for_different_signals():
    a = extract_features(tone(200), 16000)
    b = extract_features(tone(2000), 16000)
    assert not np.allclose(a, b)


def test_features_reject_too_short_input():
    with pytest.raises(ValueError):
        extract_features(np.zeros(100, dtype=np.float32), 16000)


def test_parse_ravdess_filename():
    sample = parse_filename(Path("03-01-06-01-02-01-12.wav"))
    assert sample.emotion == "fearful"
    assert sample.actor == 12
    with pytest.raises(ValueError):
        parse_filename(Path("random.wav"))


def test_split_is_speaker_independent():
    samples = [Sample(Path(f"{a}.wav"), "sad", a) for a in range(1, 25)]
    train_s, val_s, test_s = split(samples)
    actors = [{s.actor for s in part} for part in (train_s, val_s, test_s)]
    assert actors[0] == set(range(1, 17))
    assert actors[1] == set(range(17, 21))
    assert actors[2] == set(range(21, 25))
    assert not (actors[0] & actors[1] or actors[0] & actors[2] or actors[1] & actors[2])


@pytest.fixture(scope="module")
def synthetic_dataset(tmp_path_factory):
    """Tiny RAVDESS-shaped dataset: each emotion is a different tone frequency."""
    root = tmp_path_factory.mktemp("ravdess")
    rng = np.random.default_rng(0)
    for code in EMOTIONS:
        freq = 150 + 90 * int(code)
        for actor in (1, 2, 17, 21):
            for rep in (1, 2):
                samples = tone(freq, 1.0, 16000) + 0.01 * rng.standard_normal(16000).astype(np.float32)
                name = f"03-01-{code}-01-01-{rep:02d}-{actor:02d}.wav"
                (root / name).write_bytes(encode(samples, 16000))
    return root


def test_training_pipeline_produces_artifacts(synthetic_dataset, tmp_path):
    metrics = train(synthetic_dataset, tmp_path)
    assert (tmp_path / "emotion_model_v1.pkl").exists()
    assert (tmp_path / "confusion_matrix.png").exists()
    saved = json.loads((tmp_path / "metrics.json").read_text())
    assert saved["selected_algorithm"] in {"svm", "random_forest"}
    assert set(saved["comparison_on_validation"]) == {"svm", "random_forest"}
    for key in ("accuracy", "precision_macro", "recall_macro", "f1_macro", "confusion_matrix"):
        assert key in saved["test"]
    assert saved["samples"]["test"] == 16
    assert metrics["labels"] == sorted(EMOTIONS.values())

    model = VoiceEmotionModel(tmp_path / "emotion_model_v1.pkl")
    result = model.predict(encode(tone(150 + 90 * 4, 1.0), 16000), "audio/wav")
    assert set(result) == {"emotion", "confidence", "probabilities", "model_version"}
    assert abs(sum(result["probabilities"].values()) - 1.0) < 1e-3
    assert result["confidence"] == result["probabilities"][result["emotion"]]


def test_inference_requires_artifact(tmp_path):
    with pytest.raises(ModelNotAvailableError):
        VoiceEmotionModel(tmp_path / "missing.pkl")
