"""
RAVDESS speech dataset loader.

Filename format: MM-VC-EE-II-SS-RR-AA.wav
  EE = emotion code, AA = actor (odd = male, even = female).

Split is speaker-independent (no actor appears in more than one split):
  train: actors 1-16, validation: 17-20, test: 21-24.
"""

from dataclasses import dataclass
from pathlib import Path

EMOTIONS = {
    "01": "neutral",
    "02": "calm",
    "03": "happy",
    "04": "sad",
    "05": "angry",
    "06": "fearful",
    "07": "disgust",
    "08": "surprised",
}

TRAIN_ACTORS = set(range(1, 17))
VAL_ACTORS = set(range(17, 21))
TEST_ACTORS = set(range(21, 25))


@dataclass(frozen=True)
class Sample:
    path: Path
    emotion: str
    actor: int


def parse_filename(path: Path) -> Sample:
    parts = path.stem.split("-")
    if len(parts) != 7 or parts[2] not in EMOTIONS:
        raise ValueError(f"Not a RAVDESS filename: {path.name}")
    return Sample(path=path, emotion=EMOTIONS[parts[2]], actor=int(parts[6]))


def load_samples(root: Path) -> list[Sample]:
    samples = [parse_filename(p) for p in sorted(root.rglob("*.wav"))]
    if not samples:
        raise FileNotFoundError(f"No RAVDESS .wav files found under {root}")
    return samples


def split(samples: list[Sample]) -> tuple[list[Sample], list[Sample], list[Sample]]:
    train = [s for s in samples if s.actor in TRAIN_ACTORS]
    val = [s for s in samples if s.actor in VAL_ACTORS]
    test = [s for s in samples if s.actor in TEST_ACTORS]
    return train, val, test
