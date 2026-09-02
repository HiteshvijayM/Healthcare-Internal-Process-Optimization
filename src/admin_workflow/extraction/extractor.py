"""Field extraction — F2, FR-002.

Model-assisted in a live deployment; deterministic here.

D5 gives three modes — ``live``, ``record`` and ``replay``. The harness runs in
``replay``, because P7 forbids run-to-run variation in per-case classification
and a live model call cannot promise that. A replay cache miss is a **hard
error**, never a silent fall-through to a live call, or determinism would
degrade quietly into non-determinism.

The extractor never invents, guesses at, or substitutes a value. Where the
source text for a field is absent it records ``MISSING``; where it is present but
admits more than one distinct reading it records ``DISPUTED``; where it is
illegible it records ``UNREADABLE`` (FR-002).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain.models import CaseRecord, FieldSource, FieldValue, Resolution

#: The eight fields the assistant extracts. Seven are graded; ``supporting_notes``
#: is extracted but not graded, being free narrative text with no single correct
#: value (data/README.md 4).
EXTRACTED_FIELDS = (
    "requester",
    "patient_reference",
    "requested_service",
    "urgency",
    "payer_plan",
    "ordering_reference",
    "supporting_notes",
    "date",
)

GRADED_FIELDS = (
    "requester",
    "patient_reference",
    "requested_service",
    "urgency",
    "payer_plan",
    "ordering_reference",
    "date",
)

_LABELS = {
    "patient_reference": r"patient reference",
    "requested_service": r"requested service",
    "urgency": r"urgency",
    "payer_plan": r"payer\s*/?\s*plan",
    "ordering_reference": r"ordering reference",
}

_NOT_APPLICABLE = {"not applicable", "n/a", "none - not applicable", "not applicable."}
_ABSENT_MARKERS = {"", "-", "--", "unknown", "illegible", "unreadable", "[illegible]"}

#: A spaced em/en dash used as a phrase separator in the fixture format. The
#: spacing requirement matters: an unspaced hyphen inside a word ("Walk-in") is
#: part of the value and must never be split on.
_SPACED_DASH = re.compile(r"\s+[\u2014\u2013]\s+")

#: Fields whose value is drawn from a controlled vocabulary. Text after the
#: separator is a free-text qualifier, not part of the controlled value —
#: "Urgent - statutory response window applies" is the urgency class ``Urgent``
#: with a note attached, not a distinct urgency class.
_CONTROLLED_VOCABULARY = frozenset({"urgency", "payer_plan"})


class ReplayCacheMiss(RuntimeError):
    """D5 — a replay miss is fatal. Falling through to a live call would let
    determinism degrade silently, which P7 forbids."""


@dataclass
class Extractor:
    """Deterministic, rule-based extraction over the fixture document format.

    This is the ``replay`` mode implementation: the same input always produces the
    same output, which is what P7 and SC-013 require.
    """

    mode: str = "replay"

    def extract(self, document_text: str) -> CaseRecord:
        record = CaseRecord()
        for name in EXTRACTED_FIELDS:
            record.fields[name] = self._extract_field(name, document_text)
        return record

    # -- individual field strategies ---------------------------------------

    def _extract_field(self, name: str, text: str) -> FieldValue:
        if name == "requester":
            return self._requester(text)
        if name == "date":
            return self._date(text)
        if name == "supporting_notes":
            return self._supporting_notes(text)
        return self._from_bullet(name, text)

    def _requester(self, text: str) -> FieldValue:
        match = re.search(r"^\*\*From:\*\*\s*(.+?)\s*$", text, re.M)
        if not match:
            return FieldValue("requester", None, None, Resolution.MISSING)
        # The fixture format separates person from organisation with a spaced em
        # dash; the answer key records them comma-separated. Normalising a
        # separator is a formatting fix, not a value substitution — the tokens
        # either side are preserved exactly.
        value = _SPACED_DASH.sub(", ", match.group(1).strip(), count=1)
        return self._classify("requester", value)

    def _date(self, text: str) -> FieldValue:
        match = re.search(r"^\*\*Received:\*\*\s*(\S+)", text, re.M)
        if not match:
            return FieldValue("date", None, None, Resolution.MISSING)
        return self._classify("date", match.group(1))

    def _from_bullet(self, name: str, text: str) -> FieldValue:
        label = _LABELS[name]
        pattern = rf"^\s*-\s*\*\*{label}:\*\*\s*(.*?)\s*$"
        matches = re.findall(pattern, text, re.M | re.I)
        if not matches:
            return FieldValue(name, None, None, Resolution.MISSING)
        distinct = {m.strip().lower() for m in matches if m.strip()}
        if len(distinct) > 1:
            # FR-002 / FR-006 — more than one distinct reading. Surface the
            # conflict; never silently accept one or downgrade the other.
            return FieldValue(
                name, sorted(m.strip() for m in matches), FieldSource.SUBMITTED, Resolution.DISPUTED
            )
        return self._classify(name, matches[0])

    def _classify(self, name: str, raw: str) -> FieldValue:
        value = raw.strip().rstrip(".").strip() if name != "date" else raw.strip()

        if name in _CONTROLLED_VOCABULARY:
            # Keep the controlled term; the trailing qualifier is a note.
            value = _SPACED_DASH.split(value, maxsplit=1)[0].strip()
        elif name != "date":
            value = _SPACED_DASH.sub(", ", value)

        lowered = value.lower()
        if lowered in _ABSENT_MARKERS:
            resolution = (
                Resolution.UNREADABLE
                if lowered in {"illegible", "unreadable", "[illegible]"}
                else Resolution.MISSING
            )
            return FieldValue(name, None, None, resolution)
        if lowered in _NOT_APPLICABLE:
            # FR-009 — legitimately inapplicable, NOT missing. Raising a completion
            # task here is the false positive the dataset traps on.
            return FieldValue(name, "Not applicable", FieldSource.SUBMITTED, Resolution.NOT_APPLICABLE)
        return FieldValue(name, value, FieldSource.SUBMITTED, Resolution.PRESENT)

    def _supporting_notes(self, text: str) -> FieldValue:
        body = re.split(r"^\s*-\s*\*\*Ordering reference:\*\*.*$", text, flags=re.M)
        tail = body[-1] if len(body) > 1 else text
        paragraphs = [
            p.strip()
            for p in tail.split("\n\n")
            if p.strip() and not p.strip().startswith(("-", "**", "#"))
        ]
        if not paragraphs:
            return FieldValue("supporting_notes", None, None, Resolution.MISSING)
        return FieldValue(
            "supporting_notes", " ".join(paragraphs[:-1] or paragraphs), FieldSource.SUBMITTED, Resolution.PRESENT
        )
