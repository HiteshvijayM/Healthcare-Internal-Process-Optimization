# `/specify` Prompt — Healthcare Agents

**How to use:** paste everything inside the fenced block below into your `specify` agent as a single message.

**Rule being followed:** `/specify` describes **WHAT** and **WHY**, never **HOW**. All technology choices are deliberately withheld and belong in `/plan` (see §2 at the bottom).

---

## 1. The prompt

```text
Build a Healthcare Assistant Platform containing two assistants that share one safety layer, one audit trail, and one chat surface.

WHY THIS EXISTS
Hospital and clinic staff lose hours every day to two things. First, the information they need is scattered across a policy portal, a shared drive of PDFs, and an intranet wiki, so a simple question turns into a fifteen-minute hunt. Second, routine administrative requests arrive as unstructured documents and then crawl through a chain of manual re-typing, missing-information ping-pong, and handoffs between desks. We want to cut time-to-answer and cut administrative cycle time, without ever letting software make a care decision.

WHO USES IT
- Clinical staff (nurses, pharmacists, physicians) who need a fast, trustworthy answer to a policy or guideline question while working.
- Administrative coordinators who receive incoming requests and are responsible for checking, routing, and progressing them.
- A supervisor or reviewer who approves anything before it leaves the organisation.
- A compliance reviewer who must be able to reconstruct exactly what happened and why.

---

ASSISTANT A — CLINICAL KNOWLEDGE ASSISTANT

Purpose: let staff ask a question in plain English and get one written, sourced answer instead of a list of links.

It must:
- Accept a natural-language question with no special syntax or keywords.
- Search every configured knowledge source in one go and return a single consolidated written answer.
- Show, with every answer, which source documents it used and which section or page each fact came from.
- State clearly that it could not find an answer when the information is not present in the available sources, rather than producing a plausible-sounding guess.
- Support follow-up questions that depend on earlier turns in the same conversation.
- Let the user mark each answer as helpful or not helpful, and retain that judgement.

Acceptance scenarios:
1. A user asks a question whose answer exists in exactly one of the available documents. The assistant returns the correct answer and names that document and its section.
2. A user asks a question whose answer requires combining facts from two different documents. The assistant returns one answer and cites both.
3. A user asks a question about a topic that is not covered anywhere in the sources. The assistant says it could not find the information and does not invent an answer.
4. A user asks a question, then asks a follow-up that refers back to the first question without repeating the subject. The assistant answers correctly using the earlier context.
5. A user marks an answer as unhelpful. The question, the answer, the sources used, and the rating are retained for later review.

---

ASSISTANT B — ADMIN WORKFLOW ASSISTANT

Purpose: take a single high-friction administrative workflow — incoming referral and service-request intake — and remove the repetitive typing, the missing-information delays, and the manual routing.

The workflow, end to end: a request arrives as an unstructured document; someone reads it and re-types the details into a system; someone checks whether anything is missing and chases it; someone decides which team owns it; someone writes the next message or handoff note; someone approves it; and the item waits between each of those steps.

It must:
- Read an incoming request that arrives as an unstructured document and produce a structured record of the key details.
- Check that record for completeness and validity, and clearly list anything missing or implausible before the item advances.
- Determine which team or queue should own the item, based on transparent, inspectable rules, and be able to explain the decision.
- Draft the next piece of written work a human would otherwise produce, such as a request for the missing information or a handoff summary.
- Present that draft to a human, who can edit it, approve it, or reject it. Nothing is sent, submitted, or finalised without an explicit human approval.
- Track each item's current stage, owner, and elapsed time, and make that visible.

Acceptance scenarios:
1. A complete incoming request is submitted. The assistant extracts the key details accurately into a structured record.
2. An incomplete incoming request is submitted. The assistant identifies precisely which required details are missing and does not advance the item.
3. A request that clearly belongs to a particular team is submitted. The assistant routes it to that team and can state why.
4. The assistant produces a draft handoff note. A reviewer edits the wording and approves it, and the edited version is what is retained.
5. A reviewer rejects a draft. Nothing is sent, and the item returns to an earlier stage.
6. A reviewer opens the status view and can see, for every item, which stage it is in, who owns it, and how long it has been in progress.

---

SHARED BEHAVIOUR ACROSS BOTH ASSISTANTS

- Safety boundary: neither assistant answers clinical, diagnostic, treatment, or medical-necessity questions, and neither decides whether care should be approved, denied, or delayed. When asked to do any of these, it declines plainly and directs the user to a qualified human.
- Audit trail: every interaction records what was asked, which sources or documents were used, what the assistant produced, who approved or rejected it, and when. A compliance reviewer can reconstruct any single interaction end to end.
- Identifier handling: personal identifiers are masked in logs and audit records.
- Single entry point: a user reaches both assistants from one conversational interface and can move between them.
- Measurable behaviour: the system's accuracy and speed can be re-measured on demand against a fixed set of test questions and test documents, producing a repeatable scorecard.

---

NON-NEGOTIABLE CONSTRAINTS

- Only synthetic or de-identified sample data is ever used. No real patient information at any point.
- The assistants assist; a human decides. Every outbound or final action requires explicit human approval.
- Answers without a source are not acceptable. If it cannot cite, it must say it does not know.
- The routing logic must be inspectable and explainable to a non-technical reviewer.

EXPLICITLY OUT OF SCOPE

- Connecting to any live electronic health record or production clinical system.
- Submitting anything to a real insurer, payer, or external body.
- Any clinical, diagnostic, or medical-necessity determination.
- Multi-organisation tenancy, single sign-on, and production hosting concerns.
- Any claim of financial savings or staff reduction.

SUCCESS CRITERIA

- A staff member gets a correct, sourced answer to a policy question in a single interaction, in under ten seconds, on at least four out of five typical questions.
- Every answer produced carries at least one source reference.
- The assistant correctly declines every question that falls outside its safety boundary.
- Key details are extracted correctly from a clear majority of sample intake documents.
- Sample items are routed to the expected team in nine out of ten cases.
- The end-to-end time for an intake item is demonstrably shorter than doing the same work by hand.
- No item is ever sent or finalised without a recorded human approval.

Flag any requirement above that is ambiguous or that needs a decision before implementation, rather than assuming an answer.
```

---

## 2. Hold these back for `/plan`, not `/specify`

Do **not** put these in the prompt above. They are HOW, and naming them early will contaminate the spec:

- Microsoft Agent Framework (MAF), agents vs. workflows, checkpointing
- Copilot SDK, chat surface implementation
- Vector index, embeddings, Azure AI Search
- Document/OCR parsing libraries
- FHIR, HL7, X12 data shapes
- OpenTelemetry / tracing implementation
- Language and runtime choices

---

## 3. Expected clarification questions

The specify agent will probably push back on these. Pre-agreed answers:

| Likely question | Our answer |
|---|---|
| Which knowledge sources exactly? | Three synthetic sets: policy documents, clinical guideline summaries, an internal wiki export. |
| Which admin workflow? | Referral / service-request intake. One workflow only. |
| What are the "key details" to extract? | Requester, patient reference (synthetic), requested service, urgency, payer/plan, supporting notes, date. |
| Who are the routing targets? | A small fixed set of teams — decide and document, don't make it dynamic. |
| How many conversation turns of memory? | Enough for a natural three-turn follow-up. |
| What counts as "correct"? | Human-graded against a fixed answer key in the test set. |

---

## 4. After `/specify`

1. Review the generated spec against [`../feature.md`](../feature.md) — every feature ID (A1–A6, B1–B6, S1–S4) should map to at least one requirement.
2. Resolve every `[NEEDS CLARIFICATION]` using §3 above.
3. Then run `/plan` and introduce the technology stack.
