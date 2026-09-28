import subprocess
import sys

import numpy as np
import pytest

from ml.audio.preprocessing import (
    DefaultAudioPreprocessor,
    InvalidAudioError,
    PreprocessingConfig,
    UnsupportedAudioFormatError,
    decode_audio,
    high_pass,
    normalize_peak,
    remove_dc_offset,
    resample,
    to_mono,
    trim_silence,
)
from tests.ml.audio_helpers import encode, peak_frequency, tone


@pytest.mark.parametrize("fmt,ctype", [("WAV", "audio/wav"), ("FLAC", "audio/flac")])
def test_decode_round_trip(fmt, ctype):
    samples = tone(sr=22050)
    decoded, sr = decode_audio(encode(samples, 22050, fmt), ctype)
    assert sr == 22050
    assert decoded.shape == (samples.size, 1)
    assert np.allclose(decoded[:, 0], samples, atol=1e-3)


@pytest.mark.parametrize("payload", [b"", b"definitely not audio" * 10])
def test_decode_rejects_invalid(payload):
    with pytest.raises(InvalidAudioError):
        decode_audio(payload, "audio/wav")


@pytest.mark.parametrize("ctype", ["audio/mpeg", "audio/webm"])
def test_decode_rejects_unsupported(ctype):
    with pytest.raises(UnsupportedAudioFormatError):
        decode_audio(b"xxxx", ctype)


def test_content_type_parameters_are_ignored():
    _, sr = decode_audio(encode(tone(), 16000), "audio/wav; codecs=1")
    assert sr == 16000


def test_to_mono_averages_channels():
    stereo = np.stack([np.ones(10), np.zeros(10)], axis=1).astype(np.float32)
    assert np.allclose(to_mono(stereo), 0.5)
    mono = np.arange(5, dtype=np.float32)
    assert np.array_equal(to_mono(mono), mono)


def test_resample_preserves_frequency():
    out = resample(tone(440, 1.0, 44100), 44100, 16000)
    assert abs(out.size - 16000) <= 1
    assert abs(peak_frequency(out, 16000) - 440) <= 1.0


def test_resample_noop_at_target_rate():
    samples = tone()
    assert resample(samples, 16000, 16000) is samples


def test_remove_dc_offset():
    assert abs(remove_dc_offset(tone() + 0.5).mean()) < 1e-3


def test_high_pass_attenuates_low_frequency():
    low, high = tone(30, 2.0), tone(440, 2.0)
    # Measure the steady-state interior; zero-phase filtering has small edge transients.
    interior = slice(4000, -4000)
    filtered_low = high_pass(low, 16000, 80)[interior]
    filtered_high = high_pass(high, 16000, 80)[interior]
    attenuation_db = 20 * np.log10(np.abs(filtered_low).max() / np.abs(low).max())
    passband_db = 20 * np.log10(np.abs(filtered_high).max() / np.abs(high).max())
    assert attenuation_db <= -20
    assert abs(passband_db) <= 1


def test_normalize_peak():
    out = normalize_peak(tone(amplitude=0.1), 0.95)
    assert abs(np.abs(out).max() - 0.95) < 1e-6


def test_normalize_rejects_silence():
    with pytest.raises(InvalidAudioError):
        normalize_peak(np.zeros(1000, dtype=np.float32), 0.95)


def test_trim_silence():
    sr = 16000
    silence = np.zeros(sr // 2, dtype=np.float32)
    samples = np.concatenate([silence, tone(440, 1.0, sr), silence])
    trimmed, lead, trail = trim_silence(samples, sr, -40, 25, 10)
    # Frame-based trimming keeps at most one frame (25 ms) + one hop of boundary silence per side.
    tolerance = 0.025 + 0.010
    assert abs(trimmed.size / sr - 1.0) <= 2 * tolerance
    assert abs(lead - 0.5) <= tolerance
    assert abs(trail - 0.5) <= tolerance


def test_pipeline_end_to_end_stereo_44k():
    stereo = np.stack([tone(440, 1.5, 44100), tone(440, 1.5, 44100)], axis=1)
    result = DefaultAudioPreprocessor().preprocess(encode(stereo, 44100), "audio/wav")
    assert result.samples.dtype == np.float32
    assert result.samples.ndim == 1
    assert result.sample_rate == 16000
    assert np.abs(result.samples).max() <= 1.0
    assert result.original_channels == 2
    assert result.original_sample_rate == 44100


def test_pipeline_is_deterministic():
    payload = encode(tone(300, 1.0, 22050), 22050)
    a = DefaultAudioPreprocessor().preprocess(payload, "audio/wav")
    b = DefaultAudioPreprocessor().preprocess(payload, "audio/wav")
    assert np.array_equal(a.samples, b.samples)


def test_pipeline_rejects_silence_and_short_and_long_audio():
    pre = DefaultAudioPreprocessor(PreprocessingConfig(max_duration_seconds=2.0))
    with pytest.raises(InvalidAudioError):
        pre.preprocess(encode(np.zeros(16000, dtype=np.float32), 16000), "audio/wav")
    with pytest.raises(InvalidAudioError):
        pre.preprocess(encode(tone(seconds=0.2), 16000), "audio/wav")
    with pytest.raises(InvalidAudioError):
        pre.preprocess(encode(tone(seconds=3.0), 16000), "audio/wav")


def test_ml_package_does_not_import_backend():
    code = (
        "import sys, ml.audio.preprocessing, ml.audio.features, ml.models.fusion, "
        "ml.nlp.text_emotion, safety.guardrails, rag.retrieval.retriever; "
        "print(any(m == 'app' or m.startswith('app.') for m in sys.modules))"
    )
    from tests.conftest import REPO_ROOT

    out = subprocess.run([sys.executable, "-c", code], cwd=REPO_ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False"
