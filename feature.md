# Feature Request — Healthcare Agents

**Program:** AI Champs Hackathon
**Track:** Healthcare
**Stack:** Microsoft Agent Framework (MAF) + Copilot SDK
**Status:** Draft v1 — for review
**Owner:** _(team name)_
**Date:** 2026-07-31

---

## 1. Overview

Our group is assigned the **Healthcare** track, which has two problem statements. We are building **two agents** that share one platform, one safety layer, and one test harness.

| # | Agent | Problem statement | Expected value |
|---|---|---|---|
| A | **Clinical Knowledge Assistant** | Clinical and scientific information is fragmented across systems and difficult to find. | Faster answers; reduced staff workload |
| B | **Admin Workflow Assistant** | Administrative workflows involve repetitive tasks, handoffs, and delays. | Lower cycle time; fewer errors |

Both agents follow the same rule: **the agent does the fetching, reading, typing and routing — a human still decides.**

---

## 2. Scope

### In scope (hackathon)
- Two working agents, demo-able end to end.
- **Synthetic / de-identified data only.** No real PHI at any point.
- 2–3 document sources per agent, not "the whole hospital".
- One happy path + one failure path per agent, done properly.
- A repeatable test harness so we can prove the numbers.

### Out of scope (say this out loud in the review)
- Live EHR integration (Epic / Oracle Health). We use FHIR-shaped sample data instead.
- Any clinical, diagnostic, or medical-necessity decision. The agent never approves or denies care.
- Real payer submissions, real claims, real credentialing.
- Multi-tenant auth, SSO, production hosting.

---

## 3. Agent A — Clinical Knowledge Assistant

> Staff waste time hunting across a policy portal, a PDF share, and an intranet wiki. Give them one place to ask.

| ID | Feature | What it does | Done when | Size |
|---|---|---|---|---|
| **A1** | Ask in plain English | User types a question and gets a written answer instead of a list of links. | Question in → paragraph answer out, no keyword syntax needed. | S |
| **A2** | Search several sources at once | One query fans out to all configured sources (policy PDFs, guideline docs, intranet pages). | Agent returns a correct answer when the fact lives in any one of the 3 sources. | M |
| **A3** | Always show citations | Every answer lists the source file and section/page it came from. | 100% of answers carry at least one clickable/named citation. | S |
| **A4** | Admit when it doesn't know | If nothing relevant is found, reply "I couldn't find this in the available sources" — never invent an answer. | On 5 deliberately unanswerable questions, agent says "not found" 5/5 times. | S |
| **A5** | Follow-up questions | Remembers the last few turns so "what about for paediatrics?" works. | A 3-turn conversation resolves pronouns/context correctly. | S |
| **A6** | Feedback capture | Thumbs up / thumbs down on each answer, written to a log. | Feedback row saved with question, answer, sources, verdict. | S |

**Nice-to-have (only if time permits):** A7 — return the source snippet inline; A8 — "summarise this document" mode.

---

## 4. Agent B — Admin Workflow Assistant

> Pick **one** admin workflow and automate it well. Recommended: **referral / request intake → completeness check → routing → draft next step.** It has repetitive typing, handoffs and delay all in one place.

| ID | Feature | What it does | Done when | Size |
|---|---|---|---|---|
| **B1** | Read the incoming request | Takes an unstructured intake document (PDF / scanned fax / email text) and pulls out the key fields into a structured record. | Fields extracted correctly on the sample set (see §6). | M |
| **B2** | Completeness check | Flags missing or obviously invalid fields **before** the item moves to the next desk. | Agent lists exactly what's missing on an incomplete sample doc. | S |
| **B3** | Route to the right queue | Simple, readable rules decide the owner/queue (e.g. by department, urgency, payer). | 10 sample items route to the expected queue. | S |
| **B4** | Draft the next artifact | Writes the first draft of whatever the human would have typed next — a summary, a request-for-info reply, or a handoff note. | Draft is generated and shown in an editable box. | M |
| **B5** | Human approval gate | Nothing is sent, submitted or finalised without an explicit human **Approve**. Reviewer can edit first. | Approve / Edit / Reject all work; nothing auto-sends. Verified in demo. | M |
| **B6** | Status + cycle time | A simple table showing each item's stage, owner and elapsed time. | Table shows stage + start/end timestamps per item. | S |

**Nice-to-have (only if time permits):** B7 — batch-process a folder of documents; B8 — "why was this routed here?" explanation.

---

## 5. Shared Platform Features

| ID | Feature | What it does | Done when | Size |
|---|---|---|---|---|
| **S1** | Safety guardrails | Refuse clinical/diagnostic/medical-necessity questions and hand back to a human. Redact obvious identifiers in logs. | Agent declines 5/5 out-of-bounds prompts with a clear message. | M |
| **S2** | Audit log | Every step records: input, sources used, tool calls, output, who approved, timestamp. | Full trace for any run can be exported. | M |
| **S3** | Test harness | A fixed test set + a run script + a scorecard, so results are repeatable. | `run_eval` produces a scorecard we can paste into the review. | M |
| **S4** | One chat surface | Both agents reachable from a single Copilot SDK chat UI. | User can switch between Agent A and Agent B in one app. | S |

---

## 6. Success Metrics (keep them small and provable)

| Metric | Target | How we measure |
|---|---|---|
| Answer accuracy (Agent A) | ≥ 80% correct | 30-question test set, manually graded |
| Citation coverage (Agent A) | 100% | Every answer has ≥1 source |
| "Don't know" behaviour | 5/5 | 5 unanswerable questions |
| Time to answer | < 10 seconds | Timed in harness |
| Field extraction accuracy (Agent B) | ≥ 85% | 20 sample intake documents |
| Routing accuracy (Agent B) | ≥ 9/10 | 10 sample items |
| Cycle time reduction (Agent B) | Show a before/after | Stopwatch the manual path vs. the agent path in the demo |
| Unapproved auto-submits | **0** | Verified in demo |

> We are deliberately **not** claiming dollar savings or FTE reduction. We claim time-to-answer and cycle-time, because we can actually measure those in a hackathon.

---

## 7. Demo Script (what we show at review)

1. **Agent A:** Ask a question whose answer is buried in a policy PDF → get an answer with the citation → ask a follow-up → ask something unanswerable and watch it decline.
2. **Agent B:** Drop in a sample intake fax → fields extracted → one field is missing, agent flags it → item routed to the right queue → draft handoff note generated → reviewer edits and approves → status table shows cycle time.
3. **Safety:** Ask a clinical question → agent refuses and escalates.
4. **Harness:** Run the eval script live, show the scorecard.

---

## 8. Technical Notes

- **MAF** — Agent A is a single agent with retrieval tools. Agent B is a **workflow** (intake → validate → route → draft → human approval → complete), which gives us checkpointing, resumability and a natural human-in-the-loop step.
- **Copilot SDK** — chat surface, streaming responses, feedback controls.
- **Retrieval** — start with a local vector index over ~20–30 sample documents. Swap to Azure AI Search only if it's free and fast to do.
- **Observability** — enable MAF's built-in tracing from day one so S2 is nearly free.
- **Data** — all synthetic. Generate sample referrals/policies ourselves or use public de-identified sets. Document the source in `data/README.md`.

---

## 9. Assumptions & Constraints

- No production system access; no real patient data.
- The agent is an **assistant**, not a decision-maker. Every write action is human-approved.
- Two agents, one shared codebase — don't build two of everything.
- If we run short on time, cut the nice-to-haves, then cut Agent A's A7/A8, then narrow Agent B to a single document type. **Do not cut S1, S2 or B5.**

---

## 10. Milestones

| Date | Deliverable |
|---|---|
| **7/30** | This spec + repo skeleton + sample data |
| Week 1 | Agent A working (A1–A4) + harness skeleton (S3) |
| Week 2 | Agent B working (B1–B5) + safety layer (S1) |
| Week 3 | Metrics run, audit log (S2), single chat surface (S4), demo rehearsal |
| Review | Scorecard + live demo + "what we'd do for production" slide |

---

## 11. Open Questions (for the reviewers)

1. Should Agent B target **referral intake** or a different admin workflow? We picked referral intake because it shows repetition, handoff and delay in one flow — confirm this is a good fit for a marketplace offer.
2. Is there a preferred sample/synthetic dataset the program wants us to standardise on?
3. For the marketplace offer, do you want both agents packaged as **one** listing or two?
4. Any required guardrail or compliance wording the program wants us to reuse?
