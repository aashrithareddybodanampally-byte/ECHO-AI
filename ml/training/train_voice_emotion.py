"""
Train and evaluate voice emotion classifiers (SVM vs Random Forest) on RAVDESS.

Usage (from the repository root):
    python -m ml.training.train_voice_emotion --data data/raw/ravdess --out models

Selection: the candidate with the best macro-F1 on the validation actors is
refit on train+validation and evaluated once on the held-out test actors.

Outputs (in --out):
    emotion_model_<version>.pkl   serialized model + metadata
    metrics.json                  all measured metrics
    confusion_matrix.png          test-set confusion matrix
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from ml.audio.features import FEATURE_VERSION, extract_features
from ml.audio.preprocessing import DefaultAudioPreprocessor
from ml.training.ravdess import load_samples, split

MODEL_VERSION = "emotion_model_v1"
RANDOM_STATE = 42


def candidates() -> dict[str, Pipeline]:
    return {
        "svm": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", SVC(kernel="rbf", C=10.0, gamma="scale", probability=True,
                        class_weight="balanced", random_state=RANDOM_STATE)),
        ]),
        "random_forest": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=400, class_weight="balanced",
                                           random_state=RANDOM_STATE, n_jobs=-1)),
        ]),
    }


def featurize(samples, preprocessor) -> tuple[np.ndarray, np.ndarray, int]:
    features, labels, skipped = [], [], 0
    for sample in samples:
        try:
            audio = preprocessor.preprocess(sample.path.read_bytes(), "audio/wav")
            features.append(extract_features(audio.samples, audio.sample_rate))
            labels.append(sample.emotion)
        except Exception:
            skipped += 1
    return np.stack(features), np.array(labels), skipped


def evaluate(model, X, y, labels) -> dict:
    predicted = model.predict(X)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y, predicted, labels=labels, average="macro", zero_division=0
    )
    per_class = precision_recall_fscore_support(
        y, predicted, labels=labels, average=None, zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(y, predicted)),
        "precision_macro": float(precision),
        "recall_macro": float(recall),
        "f1_macro": float(f1),
        "per_class": {
            label: {
                "precision": float(per_class[0][i]),
                "recall": float(per_class[1][i]),
                "f1": float(per_class[2][i]),
                "support": int(per_class[3][i]),
            }
            for i, label in enumerate(labels)
        },
        "confusion_matrix": confusion_matrix(y, predicted, labels=labels).tolist(),
    }


def plot_confusion(matrix, labels, path: Path, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            ax.text(j, i, str(value), ha="center", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def train(data_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    preprocessor = DefaultAudioPreprocessor()
    train_s, val_s, test_s = split(load_samples(data_dir))

    X_train, y_train, skip_train = featurize(train_s, preprocessor)
    X_val, y_val, skip_val = featurize(val_s, preprocessor)
    X_test, y_test, skip_test = featurize(test_s, preprocessor)
    labels = sorted(set(y_train))

    comparison = {}
    for name, pipeline in candidates().items():
        started = time.perf_counter()
        model = clone(pipeline).fit(X_train, y_train)
        comparison[name] = {
            "validation": evaluate(model, X_val, y_val, labels),
            "train_seconds": round(time.perf_counter() - started, 2),
        }
    best = max(comparison, key=lambda n: comparison[n]["validation"]["f1_macro"])

    final = clone(candidates()[best]).fit(
        np.concatenate([X_train, X_val]), np.concatenate([y_train, y_val])
    )
    test_metrics = evaluate(final, X_test, y_test, labels)

    started = time.perf_counter()
    for row in X_test:
        final.predict_proba(row.reshape(1, -1))
    latency_ms = (time.perf_counter() - started) / len(X_test) * 1000

    artifact = {
        "model": final,
        "labels": list(final.classes_),
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "algorithm": best,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    joblib.dump(artifact, out_dir / f"{MODEL_VERSION}.pkl")

    metrics = {
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "dataset": "RAVDESS speech (Audio_Speech_Actors_01-24)",
        "split": {"train_actors": "1-16", "validation_actors": "17-20", "test_actors": "21-24"},
        "samples": {
            "train": int(len(y_train)), "validation": int(len(y_val)), "test": int(len(y_test)),
            "skipped": skip_train + skip_val + skip_test,
        },
        "labels": labels,
        "comparison_on_validation": comparison,
        "selected_algorithm": best,
        "test": test_metrics,
        "inference_latency_ms_per_sample_features_to_proba": round(latency_ms, 3),
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    plot_confusion(
        np.array(test_metrics["confusion_matrix"]), labels,
        out_dir / "confusion_matrix.png", f"{MODEL_VERSION} ({best}) — test actors 21-24",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/raw/ravdess"))
    parser.add_argument("--out", type=Path, default=Path("models"))
    args = parser.parse_args()
    metrics = train(args.data, args.out)
    t = metrics["test"]
    print(f"selected={metrics['selected_algorithm']} "
          f"test_accuracy={t['accuracy']:.4f} test_f1_macro={t['f1_macro']:.4f}")


if __name__ == "__main__":
    main()
