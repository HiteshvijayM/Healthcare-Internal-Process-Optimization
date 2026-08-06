# Specification Quality Checklist: Administrative Workflow Assistant

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-06
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Validation Notes

**Iteration 1** — Initial draft reviewed against all items above.

- *No implementation details*: the spec deliberately omits the stack named in `feature.md` §9 (agent framework, SDK, tracing, config-file location). Routing is described as "inspectable, declarative rules" without stating where they live.
- *No [NEEDS CLARIFICATION] markers*: five clarification items were resolved in the `## Clarifications` section (provisional-routing threshold, "large majority" quantification, approval SLAs, duplicate window and match behavior, escalation packet completeness). Values were adopted from the project's already-approved policy table (`feature.md` §5.4 P1–P9) rather than invented.
- *Requirements testable*: every vague adjective in the source feature request ("large majority", "short time", "policy confidence thresholds") was resolved to a number in either a functional requirement or a success criterion, and recorded as an assumption.
- *Acceptance scenarios defined*: all 14 source acceptance scenarios are mapped in the **Acceptance Scenario Traceability** table (AS-1 … AS-14) to specific FR identifiers.
- *Scope bounded*: an explicit **Out of Scope** section carries the six exclusions from the source feature request.

**Iteration 2** — Independent consistency review performed against `docs/constitution.md`, `feature.md` §5.4 / §7 / §13, and the approver role registry in `docs/multipass-validation-harness.md` §4.1. Findings addressed in the spec; no contradictions outstanding.

**Iterations 3–5** — Four further independent review passes were run over the escalation cluster, which proved to be the only area with residual inconsistency. Each pass surfaced ripples from the previous fix, and each was resolved:

- *Pass 3*: escalation dispatch authority was resolved without inventing a role. The §4.1 registry authorizes no role to approve dispatch, so FR-051 requires a designated **Escalation Dispatch Approver** to exist and holds the packet under a governance blocker where none is designated — mirroring the FR-028 pattern for a missing clinical recipient.
- *Pass 4*: the proposed 15-minute dispatch-approval deadline was **de-normativized**. `feature.md` §5.4 requires every scored threshold to live in the approved policy table, so FR-052 now requires only that an approved deadline exists and is strictly shorter than the 30-minute critical acknowledgement window, and blocks where none is approved. 15 minutes is recorded as a candidate value, not as a requirement.
- *Pass 5*: SC-011 was found to test an outcome partition that was neither mutually exclusive nor exhaustive — a missing clinical recipient qualified as both a completeness failure (FR-025) and a governance failure (FR-028). **FR-054** was added to make the precedence normative (governance evaluated first), and FR-024, FR-026, the Q5 clarification answer and User Story 5 were aligned to it.

Final state after pass 5: FR-001 … FR-054 (54 unique), SC-001 … SC-015 (15 unique), 14 acceptance-scenario traceability rows, every cited FR defined, no residual clarification markers. The reviewer's closing verdict recorded no outstanding contradictions, broken traceability, or untestable requirements.

### Iteration 6 — resolution of the open decisions

The twelve items recorded under **Needs human decision** in `docs/progress-log.md` §8 were each given a recommended answer with stated rationale, and the specification-affecting ones were applied. Three requirements were added and four revised:

- **FR-055** (new) — an exact re-send of a document already on file is flagged as a duplicate regardless of elapsed time. This closes the gap where a clinical re-fax arriving on day five passed as new work. The 72-hour window in **FR-014** now bounds fuzzy key matching only, and is named as a policy parameter rather than a constant.
- **FR-056** (new) — the 30-minute critical acknowledgement clock cannot start unless on-call clinical coverage is configured; otherwise a governance blocker is raised. An SLA that nobody is rostered to answer breaches by design and produces false assurance.
- **FR-057** (new) — critical-condition detection must match a versioned, change-controlled register carrying a matching rule and a named clinical owner per entry. Conditions are never inferred beyond it, the absence of a match is never reported as evidence that no critical condition exists, and a missing register blocks rather than silently passing. This resolves the *structure* of the largest open dependency; the register's *contents* remain a clinical deliverable.
- **FR-022** (revised) — approval SLAs now resolve per urgency class *and service line* from the policy table, defaulting to the approved 2 days / 4 hours / 30 minutes, and the applied value is recorded.
- **FR-033** (revised) — the two clearance gates were relaxed to **order-independent**. The property that protects the patient is their conjunction, not their sequence; financial clearance cannot cause clinical harm, so mandating order added latency without adding safety. AS-11 still passes because order-independence is a superset of the source scenario. User Story 6 gained a fourth acceptance scenario covering the reversed order.
- **SC-003** (revised) — the 30-second bound is now measured at the 95th percentile with the sample size reported and exceeding cases itemised, so a single outlier cannot fail acceptance and the figure is falsifiable.

Two recommendations were deliberately **not** written in as approved values, because they amend approved artifacts and only their named owners can ratify them: designating the Intake Coordinator as Escalation Dispatch Approver with the Team Lead as alternate (§4.1 registry), and setting the dispatch-approval deadline to 10 minutes (§5.4 policy table). FR-051, FR-052 and FR-054 continue to hold escalation packets under governance blockers until those ratifications land, so the spec remains truthful either way.

State after pass 6: **FR-001 … FR-057 (57 unique, contiguous)**, SC-001 … SC-015 (15 unique), 14 acceptance-scenario traceability rows, every cited FR defined, no residual clarification markers or encoding corruption.

An independent review of pass 6 returned six blocking findings, all repaired:

- **The acknowledgement clock had no defined start event.** FR-052 described the dispatch deadline as consuming part of an already-running 30-minute window, while FR-056 assumed the clock had not started yet. The clock is now defined to start **at detection**, so it measures elapsed clinical risk rather than administrative handling. On-call coverage therefore became a **fourth governance designation** inside FR-054's precedence rule rather than a separate post-dispatch check — reversing the original scoping decision, which had been made to limit ripple and was simply wrong. FR-024, SC-011 and the Q5 clarification were aligned to four designations.
- **FR-057 raised a blocker without stopping the case.** With no signal detected, FR-011 did not engage, so FR-010 could still have provisionally routed a case whose critical-condition register was unresolvable. FR-057 now explicitly holds progression.
- **Per-service-line SLAs broke fixed downstream references.** FR-052, FR-056 and SC-010 all hard-coded 30 minutes; each now resolves against the SLA value recorded as applied under FR-022.
- **"Document identity" was undefined**, making FR-055 untestable. It now means an identical immutable source-document identifier, or identical normalized content where normalization strips transport-added material only — so channel and format changes cannot defeat a match and a content change cannot survive one.
- **SC-003 named no percentile estimator or population.** It now specifies nearest-rank over every graded case admitted to the run, so slow cases cannot be excluded by their outcome.
- **FR-055, FR-056 and FR-057 had no acceptance coverage.** Seven scenarios were added, each exercising a boundary in both directions: an identity match outside the window and a same-key non-match outside the window; absent coverage and multiple simultaneously absent designations; a concerning value that is *not* a register entry and must not escalate; an absent register that must block rather than report a clean result; and a successful match that must record the register version, entry identifier and clinical owner.

Final state: **FR-001 … FR-057**, SC-001 … SC-015, 14 traceability rows, uniform table structure, zero residual markers.

## Notes

- Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`
- Assumptions carrying residual risk are listed under **Open decisions — recommended resolutions** in `docs/progress-log.md` §8. All twelve now carry a recommended answer. Five require formal ratification before `/speckit.plan` is run — the §4.1 approver-registry amendment naming an Escalation Dispatch Approver, and policy amendments for the dispatch-approval deadline, the per-service-line SLA overrides, the unbounded document-identity duplicate match, and the p95 framing of the 30-second bound. The specification behaves safely and unchanged until each lands. The critical-condition register contents remain a clinical deliverable.
