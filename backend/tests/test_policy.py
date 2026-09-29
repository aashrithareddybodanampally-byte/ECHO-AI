"""Response policy: counseling stages, length mapping and referral rules."""

import pytest

from app.schemas.emotion import FusionResult
from app.schemas.safety import SafetyLevel
from app.services.policy import asks_for_help, decide_policy, decide_stage

SAD = FusionResult(state="sad", confidence=0.8, signals={})


@pytest.mark.parametrize("message", [
    "What should I do?", "how can I stop overthinking", "any tips for sleep?",
    "Can you suggest something", "I need advice", "what would you recommend",
])
def test_detects_help_requests(message):
    assert asks_for_help(message)


@pytest.mark.parametrize("message", [
    "no one cares what i need", "they left me out again", "I'm fine",
    "I don't know how I feel", "How are you?",
])
def test_ignores_non_requests(message):
    assert not asks_for_help(message)


def test_stages():
    assert decide_stage(1, False) == "explore"
    assert decide_stage(2, False) == "explore"
    assert decide_stage(3, False) == "deepen"
    assert decide_stage(1, True) == "support"


def test_policy_is_short_and_always_asks_one_question():
    policy = decide_policy(SAD, "balanced", SafetyLevel.NORMAL)
    assert policy.length == "short"
    assert policy.ask_question is True
    assert policy.tone == "supportive"
    assert policy.stage == "explore"


def test_style_mapping():
    assert decide_policy(None, "concise", SafetyLevel.NORMAL).length == "brief"
    assert decide_policy(None, "detailed", SafetyLevel.NORMAL).length == "medium"
    # Asking for help with the concise style still leaves room for one idea.
    assert decide_policy(None, "concise", SafetyLevel.NORMAL, wants_help=True).length == "short"


def test_referral_only_for_hopelessness():
    assert not decide_policy(SAD, "balanced", SafetyLevel.DISTRESS, ["overwhelmed"]).include_resources
    assert decide_policy(SAD, "balanced", SafetyLevel.DISTRESS, ["hopelessness"]).include_resources
