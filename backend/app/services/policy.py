"""
Personalized response policy: deterministic rules from emotion, confidence,
user preference, safety and conversation stage to tone / length / question /
resources / stage.

Stage follows counseling practice (motivational interviewing's OARS skills and
the "righting reflex"): listen and explore before offering anything, and give
advice or techniques only when the person asks for help.
"""

import re

from app.schemas.emotion import FusionResult
from app.schemas.llm import ResponsePolicy
from app.schemas.safety import SafetyLevel

NEGATIVE_STATES = {"sad", "angry", "fearful", "disgust"}
POSITIVE_STATES = {"happy", "surprised"}
CONFIDENT = 0.5

# Counseling replies are short, like a person talking; "detailed" still stays conversational.
_STYLE_LENGTH = {"concise": "brief", "balanced": "short", "detailed": "medium"}

# Safety reasons that warrant (once, gently) suggesting a trusted person or counselor.
# Ordinary stress, anxiety or low mood are engaged with directly instead of referred.
REFERRAL_REASONS = {"hopelessness"}

# User turns (including the current one) spent listening before moving to "deepen".
EXPLORE_TURNS = 2

_HELP_REQUEST = re.compile(
    r"\b(what (should|can|do) i do|how (do|can|should|could) i|what can i try|any (tips|advice|ideas|suggestions)"
    r"|give me (some )?(tips|advice|ideas)|help me (with|to|figure)|what would you (suggest|recommend|do)"
    r"|can you (suggest|recommend|help)|i need (advice|help|tips)|advice)\b"
)


def asks_for_help(message: str) -> bool:
    """True when the person explicitly asks for advice, ideas or what to do."""
    text = message.lower().replace("’", "'")
    return bool(_HELP_REQUEST.search(text))


def decide_stage(user_turns: int, wants_help: bool) -> str:
    if wants_help:
        return "support"
    return "explore" if user_turns <= EXPLORE_TURNS else "deepen"


def decide_policy(
    emotion: FusionResult | None,
    response_style: str,
    safety_level: SafetyLevel,
    safety_reasons: list[str] | tuple[str, ...] = (),
    user_turns: int = 1,
    wants_help: bool = False,
) -> ResponsePolicy:
    state = emotion.state if emotion else None
    confidence = emotion.confidence if emotion else 0.0

    if safety_level != SafetyLevel.NORMAL or (state in NEGATIVE_STATES and confidence >= CONFIDENT):
        tone = "supportive"
    elif state in POSITIVE_STATES and confidence >= CONFIDENT:
        tone = "warm"
    else:
        tone = "neutral"

    stage = decide_stage(user_turns, wants_help)
    length = _STYLE_LENGTH.get(response_style, "short")
    if stage == "support" and length == "brief":
        length = "short"  # room for one concrete idea

    include_resources = safety_level == SafetyLevel.DISTRESS and bool(
        REFERRAL_REASONS.intersection(safety_reasons)
    )
    return ResponsePolicy(
        tone=tone,
        length=length,
        # Counseling replies almost always end with one small question to keep the person talking.
        ask_question=True,
        include_resources=include_resources,
        stage=stage,
    )
