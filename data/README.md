# Data Directory — ECHO-AI

---

## Purpose

This directory stores datasets used for training, evaluation, and testing ECHO-AI's ML models.

## Structure

```
data/
├── raw/           # Original, unmodified data
├── processed/     # Cleaned, transformed, feature-engineered data
└── README.md      # This file
```

## Rules

1. **Raw data is immutable** — Never modify files in `raw/`. Always create processed versions in `processed/`.

2. **Large datasets must not be committed to Git** — Use Git LFS, cloud storage, or DVC (Data Version Control) for large files. The `data/` directories are git-ignored by default (except READMEs).

3. **Document all datasets** — For every dataset, record:
   - Source / origin
   - License
   - Date acquired
   - Description of contents
   - Number of samples
   - Data format
   - Any preprocessing applied

4. **No personal or private data** — Do not commit personally identifiable information (PII), private conversations, or any data the team does not have explicit permission to use.

5. **Respect dataset licenses** — Verify that usage is permitted for the intended purpose (research, commercial, etc.).

## Adding a New Dataset

1. Place raw files in `data/raw/<dataset-name>/`
2. Create a `data/raw/<dataset-name>/README.md` documenting the dataset
3. Processing scripts should read from `raw/` and write to `processed/`
4. Add the dataset to the project's data registry (when established)

## Current Datasets

None. Datasets will be added in Phase 4+ when ML pipeline development begins.
