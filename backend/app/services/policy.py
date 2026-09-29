"""
Personalized response policy: deterministic rules from emotion, confidence,
user preference and safety level to tone / length / question / resources.
"""

from app.schemas.emotion import FusionResult
from app.schemas.llm import ResponsePolicy
from app.schemas.safety import SafetyLevel

NEGATIVE_STATES = {"sad", "angry", "fearful", "disgust"}
POSITIVE_STATES = {"happy", "surprised"}
CONFIDENT = 0.5

_STYLE_LENGTH = {"concise": "short", "balanced": "medium", "detailed": "long"}


# Safety reasons that warrant (once, gently) suggesting a trusted person or counselor.
# Ordinary stress, anxiety or low mood are engaged with directly instead of referred.
REFERRAL_REASONS = {"hopelessness"}


def decide_policy(
    emotion: FusionResult | None,
    response_style: str,
    safety_level: SafetyLevel,
    safety_reasons: list[str] | tuple[str, ...] = (),
) -> ResponsePolicy:
    state = emotion.state if emotion else None
    confidence = emotion.confidence if emotion else 0.0

    if safety_level != SafetyLevel.NORMAL or (state in NEGATIVE_STATES and confidence >= CONFIDENT):
        tone = "supportive"
    elif state in POSITIVE_STATES and confidence >= CONFIDENT:
        tone = "warm"
    else:
        tone = "neutral"

    length = _STYLE_LENGTH.get(response_style, "medium")
    if safety_level == SafetyLevel.DISTRESS and length == "long":
        length = "medium"

    include_resources = safety_level == SafetyLevel.DISTRESS and bool(
        REFERRAL_REASONS.intersection(safety_reasons)
    )
    return ResponsePolicy(
        tone=tone,
        length=length,
        # Counseling-style replies usually end with one exploratory question.
        ask_question=tone != "neutral",
        include_resources=include_resources,
    )
