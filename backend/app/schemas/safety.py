"""
Safety guardrail contracts (internal; no public endpoint).

Phase 2.5: Contracts only — no classification or guardrail logic.
"""

import enum

from pydantic import BaseModel, Field


class SafetyLevel(str, enum.Enum):
    """Input safety outcome.

    - NORMAL    : Continue.
    - DISTRESS  : Continue with a careful response.
    - HIGH_RISK : Follow the safety protocol.
    """

    NORMAL = "normal"
    DISTRESS = "distress"
    HIGH_RISK = "high_risk"


class InputSafetyAssessment(BaseModel):
    level: SafetyLevel
    reasons: list[str] = Field(default_factory=list)


class OutputSafetyAssessment(BaseModel):
    approved: bool
    # e.g. unsupported diagnosis, dangerous advice, overconfident medical claim.
    flags: list[str] = Field(default_factory=list)
