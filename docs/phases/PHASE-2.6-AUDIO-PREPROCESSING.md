# Phase 2.6 — Audio Preprocessing (Specification)

> **Status: Proposed — not started.** Nothing in this document is implemented.
> Items marked **Decision needed** must be approved by the project owner
> before implementation begins. Proposed values are starting points, not
> measured or validated choices.

---

## 1. Goal

Turn an uploaded audio clip into clean, consistent mono audio that later
phases (feature extraction in 2.7, then emotion inference and
speech-to-text) can rely on:

```
raw audio bytes
  -> decode + validate
  -> downmix to mono
  -> resample
  -> noise handling (basic)
  -> normalization
  -> leading/trailing silence removal
  -> PreprocessedAudio
```

## 2. Scope

### In scope

1. **Decode & validate** — decode audio bytes in memory; reject empty,
   unreadable or unsupported input with a typed error.
2. **Downmix** — convert multi-channel audio to mono (channel mean).
3. **Resample** — convert to a single target sample rate.
4. **Basic noise handling** — DC-offset removal and a high-pass filter to
   remove low-frequency rumble/hum. No spectral noise reduction.
5. **Normalization** — peak normalization to a fixed target level. Silent
   input is rejected, never amplified.
6. **Silence removal** — trim leading and trailing silence using frame RMS
   energy against a threshold relative to the clip's peak.
7. **Duration checks** — reject clips that are too short after trimming or
   too long.
8. Unit tests using synthetic signals generated inside the tests.
9. Documentation (`docs/ml/AUDIO-PREPROCESSING.md`) and phase status updates.

### Explicitly out of scope

- Feature extraction (MFCC, chroma, spectral centroid/bandwidth, ZCR, RMS
  features) — **Phase 2.7**.
- Voice Activity Detection segmentation (speech/silence timeline, internal
  pauses) and audio-quality scoring — separate phase unless decision D4 says otherwise.
- Emotion models, datasets, training, evaluation, metrics.
- Speech-to-text, text analysis, fusion, LLM, RAG, safety.
- Wiring into `POST /api/v1/emotion/analyze` or any API change — the endpoint
  stays `501` in this phase.
- Database tables/migrations; persisting raw or processed audio.
- Streaming/real-time audio, WebSockets.
- Decoding compressed formats that need ffmpeg (MP3, WebM/Opus, AAC).
- Advanced noise reduction (spectral gating, denoising models).
- Frontend, Docker, CI/CD.

## 3. Inputs and outputs

### Input

| Field | Type | Notes |
|---|---|---|
| `audio` | `bytes` | Complete file contents, already size-limited to 25 MB by the API layer. |
| `content_type` | `str` | e.g. `audio/wav`; matches the Phase 2.5 `VoiceEmotionService` input. |
| `config` | `PreprocessingConfig` | Optional; defaults below. |

### Output — `PreprocessedAudio` (frozen dataclass)

| Field | Type | Meaning |
|---|---|---|
| `samples` | `numpy.ndarray` (`float32`, 1-D) | Mono samples in `[-1.0, 1.0]`. |
| `sample_rate` | `int` | Always `config.target_sample_rate`. |
| `duration_seconds` | `float` | Duration after trimming. |
| `original_sample_rate` | `int` | As decoded. |
| `original_channels` | `int` | As decoded. |
| `original_duration_seconds` | `float` | Before trimming. |
| `trimmed_leading_seconds` | `float` | Silence removed at the start. |
| `trimmed_trailing_seconds` | `float` | Silence removed at the end. |

### Configuration — `PreprocessingConfig` (proposed defaults, **Decision needed: D5**)

| Setting | Proposed default | Rationale |
|---|---|---|
| `target_sample_rate` | 16000 Hz | Common rate for speech models; already the `AUDIO_SAMPLE_RATE` value in the root `.env.example`. |
| `highpass_cutoff_hz` | 80 Hz | Below most speech energy; removes rumble/hum. |
| `peak_target` | 0.95 | Leaves headroom below clipping. |
| `silence_threshold_db` | −40 dB relative to peak | Starting point; to be tuned against real recordings. |
| `frame_ms` / `hop_ms` | 25 ms / 10 ms | Conventional speech framing. |
| `min_duration_seconds` | 0.5 s (after trimming) | Rejects clips with too little audio. |
| `max_duration_seconds` | 60 s | Bounds processing cost. |

### Errors (defined in the ML module; no backend imports)

| Error | When |
|---|---|
| `AudioPreprocessingError` | Base class. |
| `UnsupportedAudioFormatError` | Content type / container not supported. |
| `InvalidAudioError` | Empty, undecodable, all-silent, too short or too long. |

The backend maps these to `InvalidInputError` (→ `422`) only when the audio
pipeline is integrated in a later phase.

## 4. Service interface

Location: `ml/audio/preprocessing.py` (ML is isolated from application logic
and must not import `backend`).

```python
class AudioPreprocessor(Protocol):
    def preprocess(self, audio: bytes, content_type: str) -> PreprocessedAudio: ...
```

Plus independently testable pure functions:

```python
decode_audio(audio: bytes, content_type: str) -> tuple[np.ndarray, int]   # (samples[frames, channels], sample_rate)
to_mono(samples: np.ndarray) -> np.ndarray
resample(samples: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray
remove_dc_offset(samples: np.ndarray) -> np.ndarray
high_pass(samples: np.ndarray, sample_rate: int, cutoff_hz: float) -> np.ndarray
normalize_peak(samples: np.ndarray, target: float) -> np.ndarray
trim_silence(samples: np.ndarray, sample_rate: int, threshold_db: float,
             frame_ms: float, hop_ms: float) -> tuple[np.ndarray, float, float]
```

## 5. Dependencies (**Decision needed: D2**)

Proposed, in a new `ml/requirements.txt` (kept separate from
`backend/requirements.txt`):

| Package | Purpose | Justification |
|---|---|---|
| `numpy` | Array math | Required by everything below; listed in the tech stack. |
| `soundfile` | Decode WAV/FLAC from bytes | Small, reads from in-memory buffers, no ffmpeg. |
| `scipy` | Polyphase resampling, Butterworth high-pass | Standard, deterministic; already a dependency of librosa. |

`librosa` is **not** added in 2.6; it is expected in 2.7 for MFCC/chroma.

## 6. Decisions needed before implementation

| ID | Decision | Proposal |
|---|---|---|
| D1 | Supported input formats | WAV (PCM 16/24/32-bit, float) and FLAC only. Note: browser `MediaRecorder` usually produces WebM/Opus, which needs ffmpeg — either the frontend sends WAV, or a later phase adds ffmpeg. |
| D2 | Dependencies | `numpy`, `soundfile`, `scipy` (section 5). |
| D3 | Noise handling depth | DC-offset removal + 80 Hz high-pass only. |
| D4 | VAD & audio-quality checks | Out of 2.6; only the rejections listed in section 3 (empty, silent, too short/long). |
| D5 | Config defaults | Table in section 3. |
| D6 | Test/runtime layout | Code in `ml/audio/`, tests in `tests/ml/audio/` run from the repo root with a `conftest.py` that puts the repo root on `sys.path`; use a dedicated environment built from `ml/requirements.txt` (plus `pytest`). |

## 7. Files expected to change

| File | Change |
|---|---|
| `ml/__init__.py`, `ml/audio/__init__.py` | New (package markers). |
| `ml/audio/preprocessing.py` | New — config, dataclass, errors, functions, `DefaultAudioPreprocessor`. |
| `ml/requirements.txt` | New. |
| `tests/ml/audio/test_preprocessing.py`, `tests/conftest.py` | New. |
| `docs/ml/AUDIO-PREPROCESSING.md` | New. |
| `docs/phases/README.md`, `README.md`, `PROJECT-CONTEXT.md`, `AGENTS.md` | Status updates only. |

No changes to `backend/` are expected.

## 8. Tests and validation criteria

All test audio is synthesized in the tests (sine waves, silence, noise); no
dataset files are committed.

| Area | Test | Pass criterion |
|---|---|---|
| Decode | WAV and FLAC written to an in-memory buffer | Samples and sample rate round-trip. |
| Decode | Empty bytes; random bytes | `InvalidAudioError`. |
| Decode | `audio/mpeg`, `audio/webm` | `UnsupportedAudioFormatError`. |
| Mono | Stereo with different L/R | Output equals channel mean; mono input unchanged. |
| Resample | 1 s 440 Hz tone at 44.1 kHz → 16 kHz | Length 16000 ± 1; spectral peak within one FFT bin of 440 Hz. |
| Resample | Input already at target rate | Returned unchanged. |
| Noise | Tone + DC offset | Output mean ≈ 0 (abs < 1e-3). |
| Noise | 30 Hz + 440 Hz mix | 30 Hz attenuated by ≥ 20 dB; 440 Hz within 1 dB. |
| Normalize | Arbitrary-level tone | Peak equals `peak_target` (abs tol 1e-6). |
| Normalize | All-zero input | `InvalidAudioError` (not amplified). |
| Silence | 0.5 s silence + 1 s tone + 0.5 s silence | Output duration 1.0 s ± one hop; reported trims ≈ 0.5 s each. |
| Silence | All silence | `InvalidAudioError`. |
| Duration | Tone shorter than min / longer than max | `InvalidAudioError`. |
| Pipeline | Stereo 44.1 kHz WAV end to end | `float32`, 1-D, 16 kHz, `max(abs) <= 1.0`. |
| Pipeline | Same input twice | Bit-identical output (deterministic). |
| Isolation | Import `ml.audio.preprocessing` | Does not import any `backend`/`app` module. |
| Privacy | Pipeline run | Writes no files (processing is in memory). |
| Regression | `cd backend && pytest` | All existing backend tests still pass. |

**Done when:** all of the above pass, the Git diff contains only the files in
section 7, dependencies are justified in the commit/PR, and a PR into
`develop` is opened for review. Processing latency is **not measured yet**
and no latency target is claimed.
