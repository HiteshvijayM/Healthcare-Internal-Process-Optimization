# Feature Request — Admin Workflow Agent

**Program:** AI Champs Hackathon
**Track:** Healthcare — Internal Process Optimization
**Stack:** Microsoft Agent Framework (MAF) + Copilot SDK
**Status:** Draft v2 — for review
**Owner:** _(team name)_
**Date:** 2026-07-31

---

## 1. The Assignment

| Field | Value |
|---|---|
| **Industry** | Healthcare |
| **Agent** | Internal Process Optimization |
| **Problem statement** | Administrative workflows involve repetitive tasks, handoffs, and delays. |
| **Expected value** | Lower cycle time; fewer errors |

**One-line pitch:** an agent that takes an incoming administrative request, reads it, checks it, routes it, and drafts the next step — so a human only reviews and approves instead of re-typing and chasing.

---

## 2. The Problem, Concretely

The problem statement names three things. Here is what each one actually looks like on the ground:

| Named problem | What it looks like today |
|---|---|
| **Repetitive tasks** | A request arrives as a fax, PDF or email. A coordinator reads it and re-types the same 8–10 fields into a system. Every single time. |
| **Handoffs** | Intake desk → completeness check → chase the sender for missing info → decide which team owns it → write a handoff note → supervisor approves. Six desks, six queues. |
| **Delays** | The item sits between every one of those steps. Most of the elapsed time is waiting, not working. |

And the errors that follow: items advance with fields missing, get routed to the wrong team, get re-keyed with typos, or get worked twice because nobody noticed a duplicate.

---

## 3. What We're Building

**One agent, one workflow, done properly.**

Chosen workflow: **incoming referral / service-request intake.** It contains all three named problems in a single flow, and it generalises cleanly to other request types later — which matters if this becomes a marketplace offer.

### Before → After

```
BEFORE (manual)
  Document arrives → read it → re-type 10 fields → notice something's missing
  → email the sender → wait → decide which team → write handoff note
  → supervisor approves → item moves
  ≈ 6 handoffs, most time spent waiting

AFTER (with agent)
  Document arrives → agent extracts fields, flags gaps, picks the queue,
                     drafts the note
  → ONE human reviews and approves
  → item moves
  ≈ 1 handoff, human time spent deciding not typing
```

The agent does the fetching, reading, typing and routing. **A human still decides.**

---

## 4. Scope

### In scope
- One request type, end to end, demo-able.
- **Synthetic / de-identified sample documents only.** No real PHI at any point.
- A happy path and a broken path (missing info, misroute, rejection) — both handled properly.
- Measurable before/after numbers for cycle time and errors.

### Out of scope — say this in the review
- Live EHR integration (Epic / Oracle Health). We use realistically-shaped sample data instead.
- Any clinical, diagnostic, or medical-necessity decision. The agent never approves or denies care.
- Real submissions to any payer or external body.
- Prior authorisation decisioning — deliberately avoided. It is heavily regulated (CMS-0057-F; California SB 1120 bars AI from making medical-necessity determinations) and is the wrong bet for a hackathon.
- Multi-tenancy, SSO, production hosting.

---

## 5. Features

Every feature traces to one of the two expected values. If it traces to neither, we don't build it.

### 5.1 Core Workflow

| ID | Feature | What it does | Done when | Value | Size |
|---|---|---|---|---|---|
| **F1** | Intake a request | Accepts an incoming document (PDF, scanned fax, or email text) and registers it as a tracked work item. | A dropped-in document appears as an item with an ID and a timestamp. | Cycle time | S |
| **F2** | Extract the fields | Reads the document and fills a structured record — requester, patient reference, requested service, urgency, payer/plan, notes, date. | Fields extracted correctly on the sample set (§7). | Both | M |
| **F3** | Completeness check | Flags missing or implausible fields **before** the item advances. | Given a document with a field removed, the agent names exactly what's missing and holds the item. | Fewer errors | S |
| **F4** | Draft the chase message | When something is missing, writes the request-for-information message back to the sender. | Draft message generated, naming the specific missing fields. | Cycle time | S |
| **F5** | Route to the right team | Picks the owning queue using simple, readable, inspectable rules — and can explain why. | 10 sample items route as expected; each shows a one-line reason. | Both | S |
| **F6** | Draft the handoff note | Writes the summary the coordinator would otherwise type for the receiving team. | Draft appears in an editable box, pre-filled. | Cycle time | M |
| **F7** | Human approval gate | Reviewer can **Approve / Edit / Reject**. Nothing is sent or finalised without an explicit approval. | All three actions work; nothing auto-sends. Verified live in demo. | Fewer errors | M |
| **F8** | Status board + cycle time | A table showing every item's stage, owner, and elapsed time — per item and in total. | Table shows stage, owner, start/end timestamps, total elapsed. | Cycle time | S |

### 5.2 Trust & Safety

| ID | Feature | What it does | Done when | Value | Size |
|---|---|---|---|---|---|
| **F9** | Duplicate detection | Flags an item that looks like one already in flight, instead of working it twice. | A resubmitted sample document is flagged as a possible duplicate. | Fewer errors | S |
| **F10** | Safety boundary | Refuses clinical, diagnostic, treatment and medical-necessity questions, and hands back to a human. | Declines 5/5 out-of-bounds prompts with a clear message. | Fewer errors | M |
| **F11** | Audit log | Records every step: input, extraction, rules fired, draft produced, who approved, when. Identifiers masked. | A full trace for any item can be exported and read by a non-technical reviewer. | Fewer errors | M |

### 5.3 Measurement & Surface

| ID | Feature | What it does | Done when | Value | Size |
|---|---|---|---|---|---|
| **F12** | Eval harness | A fixed test set of sample documents + a run script + a scorecard, so results are repeatable. | `run_eval` prints a scorecard we can paste into the review. | Both | M |
| **F13** | Chat surface | Coordinator interacts with the agent conversationally — submit, ask status, approve. | User can complete a full item without leaving the chat. | Cycle time | S |

**Nice-to-have, only if time permits:** F14 — process a folder of documents in one batch. F15 — "why was this routed here?" expanded explanation with the rule trace.

---

## 6. Priority — what we cut first

| Tier | Features | Rule |
|---|---|---|
| **Must have** | F1, F2, F3, F5, F7, F8, F10, F11 | Without these there is no demo and no story |
| **Should have** | F4, F6, F12, F13 | Cut only if genuinely out of time |
| **Nice to have** | F9, F14, F15 | Cut freely |

**Never cut:** F7 (approval gate), F10 (safety boundary), F11 (audit log). These are what make it a healthcare product rather than a script.

---

## 7. Success Metrics

Small, provable, and directly tied to the two expected values.

### Lower cycle time

| Metric | Target | How we measure |
|---|---|---|
| End-to-end time per item | Agent path measurably faster than manual | Stopwatch both paths in the demo, same document |
| Human touches per item | Down from ~6 to 1 | Count the handoffs, before vs after |
| Time to first action | < 30 seconds from intake to draft ready | Timestamped in the status board |

### Fewer errors

| Metric | Target | How we measure |
|---|---|---|
| Field extraction accuracy | ≥ 85% of fields correct | 20 sample intake documents, human-graded |
| Missing-field detection | Catches every seeded omission | 10 documents with fields deliberately removed |
| Routing accuracy | ≥ 9 / 10 correct | 10 sample items with known correct queues |
| First-pass completeness | ≥ 90% of items reach routing with complete data | Count items that needed a rework loop |
| Unapproved sends | **0** | Verified live in demo |

> We are deliberately **not** claiming dollar savings or FTE reduction. We claim cycle time and error rate, because those are the stated expected values and we can actually measure them in three weeks.

---

## 8. Demo Script

1. **The manual baseline.** Show a sample intake fax. Walk through what a coordinator does by hand. Put a stopwatch on it.
2. **The agent path.** Drop the same document in. Fields extracted, item registered, queue chosen with a reason, handoff note drafted. Stop the watch. Compare.
3. **The broken path.** Drop in a document with a missing field. Agent holds the item, names what's missing, drafts the chase message.
4. **Human control.** Reviewer edits the draft, approves. Then reject one and show it goes back a stage. Show that nothing ever sent itself.
5. **Safety.** Ask the agent a clinical question. It declines and escalates.
6. **Proof.** Open the status board — stages, owners, elapsed time. Run the eval script live and show the scorecard.

---

## 9. Technical Notes

- **MAF** — model this as a **workflow**, not a single agent. The stages (intake → extract → validate → route → draft → approve → complete) map onto workflow executors, which gives us checkpointing, resumability, and a natural pause point for the human approval step in F7.
- **Copilot SDK** — the conversational surface for F13: submit an item, ask for status, approve or reject.
- **Document reading** — start with text-layer PDFs and email text. Add scanned/OCR documents only once the clean path works.
- **Routing rules (F5)** — keep them declarative and in a config file, not buried in code. A reviewer must be able to read them.
- **Observability** — turn on MAF's built-in tracing from day one; F11 then costs us very little.
- **Data** — all synthetic. Generate the sample referrals ourselves. Record provenance in `data/README.md`.

---

## 10. Assumptions & Constraints

- No production system access; no real patient data.
- The agent is an **assistant**, not a decision-maker. Every outbound action is human-approved.
- One request type only. Resist the urge to generalise during the hackathon — design for it, don't build it.
- Routing rules must be explainable to a non-technical reviewer.

---

## 11. Milestones

| Date | Deliverable |
|---|---|
| **7/30** | This spec + repo skeleton + sample documents |
| Week 1 | F1–F3, F5 working. Harness skeleton (F12). Manual baseline timed and recorded. |
| Week 2 | F6–F8 working. Safety boundary (F10). Audit log (F11). |
| Week 3 | F4, F9, F13. Metrics run. Demo rehearsal. |
| Review | Scorecard + live demo + "what production would need" slide |

---

## 12. Open Questions for the Reviewers

1. **Request type.** We picked referral / service-request intake because it contains repetition, handoffs and delay in one flow. Confirm this is the right shape for a marketplace offer, or name a better one.
2. **Sample data.** Is there a synthetic dataset the program wants us to standardise on, or do we generate our own?
3. **Baseline.** For the cycle-time claim, is a stopwatched manual walkthrough acceptable evidence, or do you want something stronger?
4. **Guardrail wording.** Is there required compliance or safety language the program wants reused across all teams?
5. **Packaging.** For the marketplace offer, should the routing rules be customer-configurable at install time, or fixed?
