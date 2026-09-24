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

None. Model training will begin in Phase 4+ when ML pipeline development starts.

## Loading Models

When model loading is implemented, models will be loaded via configuration:

```python
# Example (not yet implemented)
MODEL_PATH = os.getenv("MODEL_STORAGE_PATH", "./models")
```

The model path is configurable via the `MODEL_STORAGE_PATH` environment variable (see `.env.example`).
