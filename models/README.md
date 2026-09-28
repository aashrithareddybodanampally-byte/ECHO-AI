# Models Directory — ECHO-AI

---

## Purpose

This directory stores trained ML model artifacts, checkpoints, and exported models for ECHO-AI.

## Rules

1. **Model files are git-ignored** — Trained models are typically large binary files and must not be committed to Git. Use a model registry, cloud storage, or DVC for versioning.

2. **Document every model** — For each model, record:
   - Model name and version
   - Architecture (e.g., "2-layer LSTM", "DistilBERT fine-tuned")
   - Training dataset(s) used
   - Training date
   - Key hyperparameters
   - Evaluation metrics (accuracy, F1, etc.)
   - File format (`.pt`, `.onnx`, `.pkl`, etc.)
   - File size

3. **Version models systematically** — Use semantic versioning or date-based naming:
   ```
   models/
   ├── emotion_classifier_v1.0.0.pt
   ├── sentiment_analyzer_v0.2.1.pkl
   └── whisper_fine_tuned_2026-09-01.pt
   ```

4. **Track experiments** — Use MLflow, Weights & Biases, or equivalent to track training runs, hyperparameters, and metrics.

## Current Models

| Model | File | Details |
|---|---|---|
| `emotion_model_v1` (Random Forest, 8 RAVDESS emotions) | `emotion_model_v1.pkl` (~31 MB, joblib) + `metrics.json` + `confusion_matrix.png` | [`docs/ml/VOICE-EMOTION-MODEL.md`](../docs/ml/VOICE-EMOTION-MODEL.md) |

Regenerate from the repository root:

```bash
python -m ml.training.train_voice_emotion --data data/raw/ravdess --out models
```

## Loading Models

The backend loads the artifact from `VOICE_EMOTION_MODEL_PATH` (default
`models/emotion_model_v1.pkl`). The artifact records its `feature_version`;
the loader refuses an artifact built with different features. The Whisper
speech-to-text model is downloaded by faster-whisper into its own cache and is
not stored here.
