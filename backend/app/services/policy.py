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
VERY_CONFIDENT = 0.7

_STYLE_LENGTH = {"concise": "short", "balanced": "medium", "detailed": "long"}


def decide_policy(
    emotion: FusionResult | None, response_style: str, safety_level: SafetyLevel
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

    include_resources = safety_level == SafetyLevel.DISTRESS or (
        state in NEGATIVE_STATES and confidence >= VERY_CONFIDENT
    )
    return ResponsePolicy(
        tone=tone,
        length=length,
        ask_question=tone == "supportive",
        include_resources=include_resources,
    )
