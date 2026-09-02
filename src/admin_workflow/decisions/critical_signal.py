"""Critical-condition signal matching — FR-057, P11, CRC-1..CRC-6.

Literal marker matching **only**. No fuzzy matching, no similarity, no
embeddings, no model call. The register is the exclusive source of matches, and
nothing outside it is a critical condition.

Three prohibitions from the register, enforced here rather than described:

1. **No inference** — a signal not matched by a registered marker is not a
   critical condition.
2. **No negative claim** — a non-match is reported only as
   ``"no registered signal matched"``, never as "no critical condition present".
   :data:`NO_MATCH_STATEMENT` is the only permitted wording, and
   :func:`forbidden_negative_claim` exists so a test can prove the difference.
3. **No silent failure** — an absent, empty or unresolvable register holds the
   case. A missing register is never treated as an empty one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

NO_MATCH_STATEMENT = "no registered signal matched"

#: Phrasings that would constitute a prohibited negative clinical claim (Sev 0).
FORBIDDEN_NEGATIVE_CLAIMS = (
    "no critical condition present",
    "no critical condition found",
    "patient is not critical",
    "nothing critical",
)


class RegisterUnresolvable(RuntimeError):
    """CRC-4 — absent, empty, or version-unresolvable. Holds the case; never
    downgraded to an empty register."""


@dataclass(frozen=True)
class SignalMatch:
    signal_id: str
    signal: str
    marker: str
    clinical_owner: str


@dataclass(frozen=True)
class MatchResult:
    matches: tuple[SignalMatch, ...]
    register_version: str

    @property
    def matched(self) -> bool:
        return bool(self.matches)

    def statement(self) -> str:
        if not self.matches:
            return NO_MATCH_STATEMENT
        ids = ", ".join(m.signal_id for m in self.matches)
        return f"registered signal matched: {ids}"

    def description(self) -> str:
        """FR-027 — states the observed signal and its source, and nothing else."""
        parts = [f"{m.signal_id} ({m.signal}); observed marker: \"{m.marker}\"" for m in self.matches]
        return " | ".join(parts)


def _normalise(text: str) -> str:
    text = text.replace("*", "").replace("_", "")
    return re.sub(r"\s+", " ", text).strip().lower()


def load_register(bundle: Any) -> dict[str, Any]:
    register = getattr(bundle, "critical_signal_register", None)
    if not register:
        raise RegisterUnresolvable("critical-condition register absent from the policy bundle")
    if not register.get("entries"):
        raise RegisterUnresolvable("critical-condition register is empty")
    declared = bundle.register_id
    if declared and register.get("register_id") != declared:
        raise RegisterUnresolvable(
            f"register version unresolvable: policy table names {declared}, "
            f"bundle file carries {register.get('register_id')}"
        )
    if register.get("match_mode") != "literal_marker":
        raise RegisterUnresolvable(
            f"match_mode {register.get('match_mode')!r} is not literal_marker; "
            "inference-capable matching is forbidden by CRC-2"
        )
    return register


def match_signals(document_text: str, bundle: Any) -> MatchResult:
    """Return every registered entry whose marker literally occurs in the document.

    Multiple matches on one case produce one result naming every matched ID
    (CRC-5) — the caller builds one packet, not one per match.
    """
    register = load_register(bundle)
    haystack = _normalise(document_text)
    matches: list[SignalMatch] = []
    for entry in register["entries"]:
        for marker in entry["markers"]:
            if _normalise(marker) in haystack:
                matches.append(
                    SignalMatch(
                        signal_id=entry["id"],
                        signal=entry["signal"],
                        marker=marker,
                        clinical_owner=entry["clinical_owner"],
                    )
                )
                break  # one match per entry — CRC-5
    return MatchResult(matches=tuple(matches), register_version=register["register_id"])


def forbidden_negative_claim(text: str) -> bool:
    """True when the text makes the prohibited negative clinical claim (Sev 0)."""
    lowered = text.lower()
    return any(claim in lowered for claim in FORBIDDEN_NEGATIVE_CLAIMS)
