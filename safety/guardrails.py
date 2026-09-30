"""
Rule-based safety guardrails.

Input:  classify a user message as normal / distress / high_risk.
Output: flag unsupported diagnoses, medication dosing, self-harm method
        content and overconfident medical claims in generated text.

Rules are deliberately conservative (prefer false positives on high-risk
input). They are not a clinical risk assessment. ECHO-AI does not diagnose,
treat, or replace professional care.
"""

import re

NORMAL, DISTRESS, HIGH_RISK = "normal", "distress", "high_risk"

_HIGH_RISK_PATTERNS = {
    "suicidal_ideation": [
        r"\bkill(ing)? my ?self\b", r"\bend(ing)? (my|it all|my own) li(fe|ves)\b", r"\bend it all\b",
        r"\bsuicid(e|al)\b", r"\bwant(ed)? to die\b", r"\bwish i (was|were) dead\b",
        r"\bdon'?t want to (live|be alive|exist)\b", r"\bbetter off dead\b",
        r"\bno reason to (live|go on)\b", r"\btake my (own )?life\b",
    ],
    "self_harm": [
        r"\b(hurt|harm|cut|burn)(ing)? my ?self\b", r"\bself[- ]?harm", r"\boverdos(e|ing)\b",
    ],
    "harm_to_others": [
        # Requires stated intent toward a person; "I hurt my knee" must not match.
        r"\b(want|going|gonna|plan(ning)?|about|trying) to (kill|hurt|harm|attack|shoot|stab) "
        r"(him|her|them|someone|somebody|people|everyone|my (mom|mother|dad|father|brother|sister|"
        r"wife|husband|partner|girlfriend|boyfriend|friend|family|boss|teacher|roommate|child|kids?))\b",
        r"\bi('ll| will) (kill|hurt|shoot|stab) (him|her|them|someone|somebody|people)\b",
    ],
}

_DISTRESS_PATTERNS = {
    "overwhelmed": [r"\b(can'?t|cannot|can not) (handle|cope|take) (this|it|anymore)",
                    r"\b(handle|cope with|take) (this|it) any ?more\b", r"\boverwhelm(ed|ing)\b",
                    r"\bfalling apart\b", r"\bbreaking down\b", r"\bcan'?t do this anymore\b"],
    "hopelessness": [r"\bhopeless\b", r"\bworthless\b", r"\bnothing matters\b", r"\bgive up\b"],
    "anxiety": [r"\bpanic( attack)?s?\b", r"\banxi(ous|ety)\b", r"\bso (stressed|scared)\b"],
    "low_mood": [r"\bdepress(ed|ing|ion)\b", r"\bso (sad|lonely)\b", r"\bcrying\b"],
}

_OUTPUT_PATTERNS = {
    "unsupported_diagnosis": [
        r"\byou (have|are suffering from|probably have|clearly have|definitely have|must have)\s+"
        r"(clinical |major |severe )?(depression|an? anxiety disorder|anxiety|bipolar|ptsd|adhd|ocd|"
        r"schizophrenia|an? (mental|mood|personality|eating) disorder)",
        r"\byou are (clinically )?(depressed|bipolar|schizophrenic)\b",
        r"\bi (can )?diagnose\b", r"\bmy diagnosis\b",
    ],
    "medication_dosing": [
        # Drug-dose units only: "500 ml of water" is not dosing advice.
        r"\b\d+(\.\d+)?\s?(mg|milligrams?|mcg|micrograms?)\b",
        r"\b(take|double|increase|stop taking) (your |the )?(dose|dosage|medication|pills|meds)\b",
    ],
    "self_harm_method": [
        r"\b(how to|ways to|best way to) (kill|hurt|harm) (yourself|oneself)\b",
        r"\blethal dose\b",
    ],
    "overconfident_medical_claim": [
        r"\b(this|it) will (cure|fix|heal) your\b", r"\bguaranteed to (cure|work)\b",
    ],
}

CRISIS_RESPONSE = (
    "I'm really sorry you're going through this, and I'm glad you told me. "
    "Your safety matters most right now, and you deserve support from a real person.\n\n"
    "- If you are in immediate danger, please call your local emergency number now.\n"
    "- India: Tele-MANAS mental health helpline, 14416 (free, 24/7).\n"
    "- US and Canada: call or text 988 (Suicide & Crisis Lifeline).\n"
    "- Elsewhere: find a local helpline at findahelpline.com.\n\n"
    "If you can, reach out to someone you trust and let them know how you're feeling. "
    "I'm an AI and can't provide crisis care, but I'm here to keep talking with you."
)

SAFE_FALLBACK_RESPONSE = (
    "I want to be careful here: I can't diagnose conditions or give medical or medication "
    "advice. A doctor or licensed mental-health professional is the right person for that. "
    "I'm happy to keep talking about how you're feeling or share general wellbeing ideas."
)


def normalize(text: str) -> str:
    """Lowercase and map typographic apostrophes (default on many phone keyboards) to ASCII."""
    return text.lower().replace("’", "'").replace("‘", "'").replace("ʼ", "'")


def _match(text: str, groups: dict[str, list[str]]) -> list[str]:
    lowered = normalize(text)
    return [name for name, patterns in groups.items()
            if any(re.search(p, lowered) for p in patterns)]


def check_input(text: str) -> dict:
    reasons = _match(text, _HIGH_RISK_PATTERNS)
    if reasons:
        return {"level": HIGH_RISK, "reasons": reasons}
    reasons = _match(text, _DISTRESS_PATTERNS)
    if reasons:
        return {"level": DISTRESS, "reasons": reasons}
    return {"level": NORMAL, "reasons": []}


def check_output(text: str) -> dict:
    flags = _match(text, _OUTPUT_PATTERNS)
    return {"approved": not flags, "flags": flags}
