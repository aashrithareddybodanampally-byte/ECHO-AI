"""
Multimodal emotion fusion (weighted late fusion).

Each available signal is turned into a distribution over a shared label set,
then combined with fixed weights (voice 0.5, text 0.3, context 0.2),
re-normalized over the signals that are present. The fused state is the
label with the highest combined score.

This is the initial hand-weighted method; it is deterministic and not learned.
"""

DEFAULT_WEIGHTS = {"voice": 0.5, "text": 0.3, "context": 0.2}
BASE_LABELS = ("neutral", "calm", "happy", "sad", "angry", "fearful", "disgust", "surprised")
FUSION_VERSION = "weighted-late-fusion-v1"


def _point_distribution(label: str, score: float, labels: list[str]) -> dict[str, float]:
    rest = (1.0 - score) / (len(labels) - 1) if len(labels) > 1 else 0.0
    return {name: (score if name == label else rest) for name in labels}


def fuse(
    voice: dict | None = None,
    text: dict | None = None,
    context: dict | None = None,
    weights: dict[str, float] | None = None,
) -> dict:
    """
    voice:   {"probabilities": {label: p}, ...}
    text:    {"emotion": label, "confidence": c, ...}
    context: {"label": label, "score": s}
    """
    if voice is None and text is None:
        raise ValueError("at least one of voice or text is required")
    weights = weights or DEFAULT_WEIGHTS

    labels = set(BASE_LABELS)
    if voice:
        labels.update(voice["probabilities"])
    if text:
        labels.add(text["emotion"])
    if context:
        labels.add(context["label"])
    labels = sorted(labels)

    distributions: dict[str, dict[str, float]] = {}
    if voice:
        distributions["voice"] = {l: float(voice["probabilities"].get(l, 0.0)) for l in labels}
    if text:
        distributions["text"] = _point_distribution(text["emotion"], text["confidence"], labels)
    if context:
        distributions["context"] = _point_distribution(context["label"], context["score"], labels)

    total_weight = sum(weights[name] for name in distributions)
    fused = {
        label: sum(weights[n] * d[label] for n, d in distributions.items()) / total_weight
        for label in labels
    }
    state = max(fused, key=lambda l: (fused[l], l == "neutral"))
    return {
        "state": state,
        "confidence": round(min(1.0, max(0.0, fused[state])), 6),
        "signals": {
            name: (round(distributions[name][state], 6) if name in distributions else None)
            for name in ("voice", "text", "context")
        },
    }
