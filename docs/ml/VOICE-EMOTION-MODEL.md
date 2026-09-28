# Voice Emotion Model — `emotion_model_v1`

All numbers below come from a real run of
`python -m ml.training.train_voice_emotion --data data/raw/ravdess --out models`
on 2026-09-29, and from `python -m ml.evaluation.benchmark_voice_emotion`.
They are copied from `models/metrics.json` (git-ignored; regenerate with the
same command). Predictions are **not** clinical assessments.

## Summary

| Item | Value |
|---|---|
| Dataset | RAVDESS speech, `Audio_Speech_Actors_01-24` (1,440 clips, 24 actors, 8 emotions), CC BY-NC-SA 4.0 |
| Labels | angry, calm, disgust, fearful, happy, neutral, sad, surprised |
| Split | Speaker-independent: train actors 1–16 (960), validation 17–20 (240), test 21–24 (240); 0 clips skipped |
| Preprocessing | `ml/audio/preprocessing.py` (mono, 16 kHz, DC removal, 80 Hz high-pass, peak normalize, trim silence) |
| Features | `mfcc40-chroma-spectral-zcr-rms-v1`: 100 dims (MFCC mean/std ×40, chroma ×12, centroid, bandwidth, ZCR, RMS mean/std) |
| Candidates | SVM (RBF, C=10, balanced) vs Random Forest (400 trees, balanced), both with standard scaling |
| Selection | Best macro-F1 on validation actors, then refit on train+validation, evaluated once on test actors |
| Selected | **Random Forest** |
| Artifact | `models/emotion_model_v1.pkl` (joblib: pipeline, labels, model/feature versions, timestamp) |

## Model comparison (validation actors 17–20)

| Model | Accuracy | Macro precision | Macro recall | Macro F1 | Train time |
|---|---|---|---|---|---|
| SVM | 0.4542 | 0.4387 | 0.4336 | 0.4263 | 2.5 s |
| Random Forest | 0.4458 | 0.4469 | 0.4336 | **0.4268** | 5.3 s |

The two are effectively tied on validation (macro-F1 differs by 0.0005). Random
Forest was selected by the pre-declared rule.

## Test results (actors 21–24, 240 clips, never seen in training or selection)

| Accuracy | Macro precision | Macro recall | Macro F1 |
|---|---|---|---|
| **0.4583** | 0.4691 | 0.4531 | **0.4530** |

Chance level for 8 balanced classes is 0.125 (neutral has half the clips of the others).

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| angry | 0.476 | 0.625 | 0.541 | 32 |
| calm | 0.412 | 0.438 | 0.424 | 32 |
| disgust | 0.487 | 0.594 | 0.535 | 32 |
| fearful | 0.550 | 0.344 | 0.423 | 32 |
| happy | 0.333 | 0.312 | 0.323 | 32 |
| neutral | 0.300 | 0.375 | 0.333 | 16 |
| sad | 0.281 | 0.281 | 0.281 | 32 |
| surprised | 0.913 | 0.656 | 0.764 | 32 |

### Confusion matrix (rows = actual, columns = predicted)

| | angry | calm | disgust | fearful | happy | neutral | sad | surprised |
|---|---|---|---|---|---|---|---|---|
| **angry** | 20 | 0 | 1 | 3 | 7 | 0 | 0 | 1 |
| **calm** | 0 | 14 | 7 | 0 | 0 | 2 | 9 | 0 |
| **disgust** | 6 | 0 | 19 | 0 | 3 | 1 | 3 | 0 |
| **fearful** | 3 | 5 | 1 | 11 | 3 | 1 | 8 | 0 |
| **happy** | 6 | 1 | 2 | 4 | 10 | 8 | 0 | 1 |
| **neutral** | 0 | 2 | 2 | 0 | 3 | 6 | 3 | 0 |
| **sad** | 1 | 12 | 4 | 2 | 2 | 2 | 9 | 0 |
| **surprised** | 6 | 0 | 3 | 0 | 2 | 0 | 0 | 21 |

The plotted version is written to `models/confusion_matrix.png`.

## Error analysis

- **Sad ↔ calm** is the dominant confusion (12 sad → calm, 9 calm → sad). Both
  are low-arousal and differ mostly in subtle pitch contour and voice quality,
  which utterance-level means and standard deviations of MFCC/spectral features
  capture poorly.
- **Happy → angry/neutral** (6 and 8): high-arousal happy speech shares energy
  and spectral brightness with angry; mild happy speech resembles neutral.
- **Fearful → sad/calm** (8 and 5): fearful clips spoken quietly collapse into the
  low-arousal cluster.
- **Surprised** is the most separable class (precision 0.913).
- Speaker variation matters: every test speaker is unseen. RAVDESS is also
  acted, studio-quality speech with only two sentences, so real microphone
  audio (noise, accents, spontaneous speech) is expected to perform **worse**.
  That has **not been measured**.

Likely improvements (not done): per-speaker normalization, frame-level
sequence models, pitch/prosody features, data augmentation (noise, pitch
shift), more datasets (CREMA-D, TESS) and grouped cross-validation for tuning.

## Latency (measured on the development machine, CPU)

`python -m ml.evaluation.benchmark_voice_emotion` on 100 test-actor clips, model already loaded, single-threaded classifier:

| Stage | Median | p95 |
|---|---|---|
| Preprocessing | 40.5 ms | 56.7 ms |
| Feature extraction | 46.2 ms | 68.5 ms |
| Classification | 99.6 ms | 155.5 ms |
| **Total** | **185.1 ms** | 282.5 ms |

The `inference_latency_ms_per_sample_features_to_proba` value in `metrics.json`
(285.2 ms) was measured during training with the classifier using all cores
(`n_jobs=-1`), which adds pool overhead per single prediction; inference now
forces `n_jobs=1`.

### End-to-end voice turns (manual check, `POST /chat/voice`, 3–4 s RAVDESS clips)

| Call | `audio_ms` (preprocess + Whisper `base` + emotion) |
|---|---|
| First call ever (includes Whisper model download) | 65,974 ms |
| First call after backend restart (model load) | 18,966 ms |
| Warm calls | 5,410 ms and 5,602 ms |

Only three warm calls were measured; treat these as indicative, not a benchmark.
Speech-to-text dominates voice latency on CPU.

## Reproduce

```bash
# dataset: https://zenodo.org/records/1188976 -> Audio_Speech_Actors_01-24.zip, extracted to data/raw/ravdess/
python -m ml.training.train_voice_emotion --data data/raw/ravdess --out models
python -m ml.evaluation.benchmark_voice_emotion --data data/raw/ravdess --model models/emotion_model_v1.pkl
```

Training uses fixed random seeds (`random_state=42`); results may still differ
slightly across library versions and hardware.
