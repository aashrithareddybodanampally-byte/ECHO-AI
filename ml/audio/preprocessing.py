"""
Audio preprocessing.

raw bytes -> decode -> mono -> resample -> DC removal + high-pass
          -> peak normalization -> leading/trailing silence trim

All processing happens in memory; nothing is written to disk.
Supported containers: WAV and FLAC (decoded with soundfile, no ffmpeg).
"""

import io
from dataclasses import dataclass
from math import gcd
from typing import Protocol

import numpy as np
import soundfile as sf
from scipy import signal

SUPPORTED_CONTENT_TYPES = {
    "audio/wav": "WAV",
    "audio/wave": "WAV",
    "audio/x-wav": "WAV",
    "audio/vnd.wave": "WAV",
    "audio/flac": "FLAC",
    "audio/x-flac": "FLAC",
}


class AudioPreprocessingError(Exception):
    """Base class for preprocessing errors."""


class UnsupportedAudioFormatError(AudioPreprocessingError):
    """The content type or container is not supported."""


class InvalidAudioError(AudioPreprocessingError):
    """The audio is empty, undecodable, silent, too short or too long."""


@dataclass(frozen=True)
class PreprocessingConfig:
    target_sample_rate: int = 16000
    highpass_cutoff_hz: float = 80.0
    peak_target: float = 0.95
    silence_threshold_db: float = -40.0
    frame_ms: float = 25.0
    hop_ms: float = 10.0
    min_duration_seconds: float = 0.5
    max_duration_seconds: float = 60.0


@dataclass(frozen=True)
class PreprocessedAudio:
    samples: np.ndarray
    sample_rate: int
    duration_seconds: float
    original_sample_rate: int
    original_channels: int
    original_duration_seconds: float
    trimmed_leading_seconds: float
    trimmed_trailing_seconds: float


def _base_content_type(content_type: str) -> str:
    return content_type.split(";")[0].strip().lower()


def decode_audio(
    audio: bytes, content_type: str, max_seconds: float | None = None
) -> tuple[np.ndarray, int]:
    """Decode audio bytes. Returns (samples[frames, channels] float32, sample_rate).

    When max_seconds is given, the duration is read from the header first so a
    small but highly compressed file cannot decode into an enormous array.
    """
    base = _base_content_type(content_type)
    if base not in SUPPORTED_CONTENT_TYPES:
        raise UnsupportedAudioFormatError(
            f"Unsupported audio format '{base}'. Supported: WAV, FLAC."
        )
    if not audio:
        raise InvalidAudioError("Audio is empty")
    try:
        if max_seconds is not None:
            info = sf.info(io.BytesIO(audio))
            if info.samplerate <= 0 or info.frames > max_seconds * info.samplerate:
                raise InvalidAudioError(f"Audio is longer than {max_seconds:g} seconds")
        samples, sample_rate = sf.read(io.BytesIO(audio), dtype="float32", always_2d=True)
    except (RuntimeError, sf.LibsndfileError) as exc:
        raise InvalidAudioError("Audio could not be decoded") from exc
    if samples.shape[0] == 0:
        raise InvalidAudioError("Audio contains no samples")
    return samples, int(sample_rate)


def to_mono(samples: np.ndarray) -> np.ndarray:
    if samples.ndim == 1:
        return samples.astype(np.float32)
    return samples.mean(axis=1).astype(np.float32)


def resample(samples: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return samples
    divisor = gcd(orig_sr, target_sr)
    up, down = target_sr // divisor, orig_sr // divisor
    return signal.resample_poly(samples, up, down).astype(np.float32)


def remove_dc_offset(samples: np.ndarray) -> np.ndarray:
    return (samples - samples.mean()).astype(np.float32)


def high_pass(samples: np.ndarray, sample_rate: int, cutoff_hz: float) -> np.ndarray:
    sos = signal.butter(4, cutoff_hz, btype="highpass", fs=sample_rate, output="sos")
    # sosfiltfilt needs more samples than its padding; very short clips are left as-is
    # and rejected later by the duration check.
    if samples.shape[0] <= 27:
        return samples
    return signal.sosfiltfilt(sos, samples).astype(np.float32)


def normalize_peak(samples: np.ndarray, target: float) -> np.ndarray:
    peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    if peak < 1e-6:
        raise InvalidAudioError("Audio is silent")
    return (samples * (target / peak)).astype(np.float32)


def trim_silence(
    samples: np.ndarray,
    sample_rate: int,
    threshold_db: float,
    frame_ms: float,
    hop_ms: float,
) -> tuple[np.ndarray, float, float]:
    """Trim leading/trailing frames whose RMS is below threshold_db relative to the peak frame."""
    frame = max(1, int(sample_rate * frame_ms / 1000))
    hop = max(1, int(sample_rate * hop_ms / 1000))
    if samples.shape[0] < frame:
        return samples, 0.0, 0.0
    starts = np.arange(0, samples.shape[0] - frame + 1, hop)
    rms = np.array([np.sqrt(np.mean(samples[s:s + frame] ** 2)) for s in starts])
    peak = rms.max()
    if peak <= 0:
        raise InvalidAudioError("Audio is silent")
    db = 20 * np.log10(np.maximum(rms, 1e-12) / peak)
    voiced = np.flatnonzero(db > threshold_db)
    start = int(starts[voiced[0]])
    end = min(samples.shape[0], int(starts[voiced[-1]]) + frame)
    trimmed = samples[start:end]
    return (
        trimmed,
        start / sample_rate,
        (samples.shape[0] - end) / sample_rate,
    )


class AudioPreprocessor(Protocol):
    def preprocess(self, audio: bytes, content_type: str) -> PreprocessedAudio: ...


class DefaultAudioPreprocessor:
    def __init__(self, config: PreprocessingConfig | None = None):
        self.config = config or PreprocessingConfig()

    def preprocess(self, audio: bytes, content_type: str) -> PreprocessedAudio:
        cfg = self.config
        raw, sr = decode_audio(audio, content_type, max_seconds=cfg.max_duration_seconds)
        channels = raw.shape[1]
        original_duration = raw.shape[0] / sr
        if original_duration > cfg.max_duration_seconds:
            raise InvalidAudioError(
                f"Audio is longer than {cfg.max_duration_seconds:g} seconds"
            )

        mono = to_mono(raw)
        mono = resample(mono, sr, cfg.target_sample_rate)
        mono = remove_dc_offset(mono)
        mono = high_pass(mono, cfg.target_sample_rate, cfg.highpass_cutoff_hz)
        mono = normalize_peak(mono, cfg.peak_target)
        trimmed, lead, trail = trim_silence(
            mono, cfg.target_sample_rate, cfg.silence_threshold_db, cfg.frame_ms, cfg.hop_ms
        )
        duration = trimmed.shape[0] / cfg.target_sample_rate
        if duration < cfg.min_duration_seconds:
            raise InvalidAudioError(
                f"Audio contains less than {cfg.min_duration_seconds:g} seconds of sound"
            )
        return PreprocessedAudio(
            samples=trimmed,
            sample_rate=cfg.target_sample_rate,
            duration_seconds=duration,
            original_sample_rate=sr,
            original_channels=channels,
            original_duration_seconds=original_duration,
            trimmed_leading_seconds=lead,
            trimmed_trailing_seconds=trail,
        )
