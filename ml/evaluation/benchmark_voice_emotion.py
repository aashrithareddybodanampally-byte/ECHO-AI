"""
Measure voice emotion inference latency on real test-actor clips.

Usage (repo root):
    python -m ml.evaluation.benchmark_voice_emotion --data data/raw/ravdess --model models/emotion_model_v1.pkl

Reports median and p95 wall-clock time per clip for preprocessing,
feature extraction and classification (model already loaded).
"""

import argparse
import json
import statistics
import time
from pathlib import Path

from ml.audio.features import extract_features
from ml.audio.preprocessing import DefaultAudioPreprocessor
from ml.inference.voice_emotion import VoiceEmotionModel
from ml.training.ravdess import load_samples, split


def _pct(values, q):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))]


def benchmark(data: Path, model: Path, limit: int) -> dict:
    voice_model = VoiceEmotionModel(model)
    pre = DefaultAudioPreprocessor()
    _, _, test = split(load_samples(data))
    timings = {"preprocess_ms": [], "features_ms": [], "classify_ms": [], "total_ms": []}
    for sample in test[:limit]:
        raw = sample.path.read_bytes()
        t0 = time.perf_counter()
        audio = pre.preprocess(raw, "audio/wav")
        t1 = time.perf_counter()
        vector = extract_features(audio.samples, audio.sample_rate).reshape(1, -1)
        t2 = time.perf_counter()
        voice_model._model.predict_proba(vector)
        t3 = time.perf_counter()
        for key, value in zip(timings, (t1 - t0, t2 - t1, t3 - t2, t3 - t0)):
            timings[key].append(value * 1000)
    return {
        "clips": len(timings["total_ms"]),
        **{k: {"median": round(statistics.median(v), 2), "p95": round(_pct(v, 0.95), 2)}
           for k, v in timings.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/ravdess"))
    parser.add_argument("--model", type=Path, default=Path("models/emotion_model_v1.pkl"))
    parser.add_argument("--limit", type=int, default=100)
    print(json.dumps(benchmark(**vars(parser.parse_args())), indent=2))


if __name__ == "__main__":
    main()
