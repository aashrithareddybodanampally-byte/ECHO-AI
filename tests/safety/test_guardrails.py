import pytest

from safety.guardrails import DISTRESS, HIGH_RISK, NORMAL, check_input, check_output


@pytest.mark.parametrize("text", [
    "What's a good way to plan my study week?",
    "I had a nice day at college.",
    "This exam question is killing me, haha",
    "I hurt my knee playing football.",
    "I'm going to kill my presentation tomorrow!",
])
def test_normal_conversation(text):
    assert check_input(text)["level"] == NORMAL


@pytest.mark.parametrize("text", [
    "I don't think I can handle this anymore.",
    "I feel hopeless and worthless.",
    "I keep having panic attacks before exams.",
])
def test_distress_language(text):
    assert check_input(text)["level"] == DISTRESS


@pytest.mark.parametrize("text", [
    "I want to kill myself.",
    "I've been thinking about suicide.",
    "Sometimes I want to hurt myself.",
    "I don't want to live anymore.",
    "Everyone would be better off dead without me",
    "I don’t want to live anymore.",  # typographic apostrophe (phone keyboards)
    "I want to hurt someone.",
])
def test_high_risk_content(text):
    result = check_input(text)
    assert result["level"] == HIGH_RISK
    assert result["reasons"]


@pytest.mark.parametrize("text,flag", [
    ("Based on what you said, you have clinical depression.", "unsupported_diagnosis"),
    ("You should take 50 mg of sertraline.", "medication_dosing"),
    ("Just double your dose tonight.", "medication_dosing"),
    ("This will cure your anxiety for good.", "overconfident_medical_claim"),
    ("Here is the lethal dose of that drug.", "self_harm_method"),
])
def test_output_guardrail_flags(text, flag):
    result = check_output(text)
    assert result["approved"] is False
    assert flag in result["flags"]


def test_distress_with_typographic_apostrophe():
    assert check_input("I can’t handle this anymore")["level"] == DISTRESS


def test_output_guardrail_allows_non_drug_quantities():
    assert check_output("Try drinking 500 ml of water before studying.")["approved"] is True


def test_output_guardrail_approves_supportive_reply():
    reply = ("That sounds really stressful. Taking short breaks and talking to a counsellor "
             "can help. What part of the exam worries you most?")
    assert check_output(reply) == {"approved": True, "flags": []}
