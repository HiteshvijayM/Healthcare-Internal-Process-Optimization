"""Stage-independent clinical safety boundary — F19, never-cut.

FR-036, FR-037, constitution 5. D13: the guard sits on BOTH edges.

* The **inbound** edge refuses a request for an autonomous clinical act at any
  workflow stage.
* The **outbound** edge refuses to emit text that asserts, implies or ranks a
  clinical judgement — which is what stops a drafting step from letting clinical
  assertion into an escalation packet (FR-027). That failure is graded Sev 0 on
  CASE-008, and it is why US8 is sequenced ahead of US5.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: The five acts the constitution forbids the assistant from performing.
FORBIDDEN_ACTS = (
    "diagnosis",
    "treatment_recommendation",
    "medical_necessity_determination",
    "clinical_clearance_authorization",
    "discharge_release_authorization",
)

_INBOUND_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("diagnosis", re.compile(r"\b(diagnos\w*|what\s+condition\s+does|what.s\s+wrong\s+with)\b", re.I)),
    ("treatment_recommendation", re.compile(r"\b(recommend|prescrib\w*|what\s+treatment|should\s+(we|they)\s+treat)\b", re.I)),
    ("medical_necessity_determination", re.compile(r"\bmedical(ly)?\s+necess\w*\b", re.I)),
    ("clinical_clearance_authorization", re.compile(r"\b(clinically\s+clear|grant\s+clinical\s+clearance|approve\s+clinical\s+clearance|clear\s+(the\s+)?patient\s+clinically)\b", re.I)),
    ("discharge_release_authorization", re.compile(r"\b(authoris\w*|authoriz\w*|approve)\s+(the\s+)?(discharge|release)\b", re.I)),
)

_OUTBOUND_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(likely|probable|consistent with|suggests?|indicates?)\s+(a\s+)?(diagnos\w*|malignan\w*|infection|fracture)", re.I),
    re.compile(r"\b(urgency|severity|risk)\s+(is|appears|rated)\s+(high|low|moderate|severe|mild)\b", re.I),
    re.compile(r"\b(more|most|less|least)\s+(urgent|severe|critical)\s+than\b", re.I),
    re.compile(r"\bI\s+(recommend|advise|suggest)\b", re.I),
    re.compile(r"\bpatient\s+(should|must)\s+(be\s+)?(treated|admitted|discharged|referred)\b", re.I),
)

REFUSAL_TEMPLATE = (
    "I can't do that. {act_label} is a clinical decision, and this assistant is not "
    "permitted to make one at any stage. I've recorded the request against the case "
    "and directed it to {authority}, who holds that authority."
)

_ACT_LABELS = {
    "diagnosis": "Diagnosing a patient",
    "treatment_recommendation": "Recommending treatment",
    "medical_necessity_determination": "Determining medical necessity",
    "clinical_clearance_authorization": "Authorising clinical clearance",
    "discharge_release_authorization": "Authorising discharge or release",
}

_ACT_AUTHORITY = {
    "diagnosis": "the Clinical Authority",
    "treatment_recommendation": "the Clinical Authority",
    "medical_necessity_determination": "the Clinical Authority",
    "clinical_clearance_authorization": "the Clinical Authority",
    "discharge_release_authorization": "the Clinical Authority",
}


class ClinicalBoundaryViolation(RuntimeError):
    """Outbound guard trip. Sev 0 — the text never leaves."""


@dataclass(frozen=True)
class Refusal:
    act: str
    message: str
    directed_to: str


def check_inbound(request_text: str) -> Refusal | None:
    """Return a :class:`Refusal` when the request asks for a forbidden clinical act.

    Stage-independent by construction: the function takes no stage argument, so
    it cannot behave differently at different points in the journey.
    """
    for act, pattern in _INBOUND_PATTERNS:
        if pattern.search(request_text):
            authority = _ACT_AUTHORITY[act]
            return Refusal(
                act=act,
                message=REFUSAL_TEMPLATE.format(act_label=_ACT_LABELS[act], authority=authority),
                directed_to=authority,
            )
    return None


def assert_outbound_clean(text: str) -> None:
    """Refuse to emit text that asserts, implies or ranks a clinical judgement.

    FR-027 requires an escalation packet to state only the observed signal and its
    source. This is the enforcement, not the intention.
    """
    for pattern in _OUTBOUND_PATTERNS:
        match = pattern.search(text)
        if match:
            raise ClinicalBoundaryViolation(
                f"outbound text asserts or ranks a clinical judgement: {match.group(0)!r}. "
                "FR-027 permits only the observed signal and its source."
            )
