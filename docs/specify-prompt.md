# `/specify` Prompt — Admin Workflow Agent

**Track:** Healthcare — Internal Process Optimization
**How to use:** paste everything inside the fenced block in §1 into your `specify` agent as a single message.

**Rule being followed:** `/specify` describes **WHAT** and **WHY**, never **HOW**. Technology choices are deliberately withheld and belong in `/plan` — see §2.

---

## 1. The prompt

```text
Build an Administrative Workflow Assistant for a healthcare provider organisation.

WHY THIS EXISTS
Administrative work in a clinic or hospital is slow for three specific reasons, and they compound. First, it is repetitive: a request arrives as an unstructured document and a coordinator re-types the same handful of details into a system, every single time, all day. Second, it is full of handoffs: the item passes through an intake desk, a completeness check, a chase-the-sender loop, a routing decision, a drafting step, and a supervisor approval, and each of those is a different person and a different queue. Third, it is full of delay: most of the elapsed time on any item is spent waiting between steps, not being worked on.

The errors follow from the same causes. Items advance with details missing. They get sent to the wrong team. They get re-keyed with mistakes. The same request gets worked twice because nobody noticed it had already arrived.

We want to reduce the elapsed time it takes to process an administrative request, and reduce the number of mistakes made while processing it. We want to do that by having software do the reading, the typing, the checking and the routing, while a human keeps every decision.

WHO USES IT
- An administrative coordinator who receives incoming requests and is responsible for checking, progressing, and routing them.
- A supervisor or reviewer who approves anything before it leaves the organisation, and who can edit or reject it first.
- A team lead who needs to see what is in flight, who owns it, and how long it has been sitting.
- A compliance reviewer who must be able to reconstruct exactly what happened to any single item and why.

THE WORKFLOW BEING AUTOMATED
Incoming referral and service-request intake. A request arrives as an unstructured document. Today a person reads it, re-types its details, notices whether anything is missing, chases the sender if it is, decides which team should own it, writes a handoff summary for that team, and gets it approved. The system should collapse that into: the request arrives, the assistant prepares everything, one human reviews and approves.

---

WHAT THE ASSISTANT MUST DO

Intake and understanding
- Accept an incoming request that arrives as an unstructured document and register it as a tracked work item with an identifier and a time of arrival.
- Read that document and produce a structured record of its key details: who sent it, which patient it concerns, what service is being requested, how urgent it is, which payer or plan applies, any supporting notes, and the date.

Checking
- Check that record for completeness and plausibility, and clearly name anything that is missing or does not make sense, before the item is allowed to advance.
- Hold an incomplete item rather than passing it on.
- Recognise when an incoming request appears to duplicate one already in progress, and flag it instead of allowing the same work to be done twice.

Progressing
- When details are missing, prepare the message that asks the sender for exactly those details.
- Determine which team should own the item, using rules that a non-technical reviewer can read and understand, and be able to state the reason for the decision in one line.
- Prepare the handoff summary that the receiving team needs, in the form the coordinator would otherwise have typed.

Human control
- Present everything it has prepared to a human, who can approve it, edit it first, or reject it.
- Never send, submit, or finalise anything without an explicit human approval.
- When something is rejected, return the item to an earlier stage rather than discarding it.
- Retain the human's edited version, not the original draft, when an edit has been made.

Visibility
- Show, for every item in progress, which stage it is in, who owns it, and how long it has been in progress.
- Make the total elapsed time for a completed item visible, so it can be compared against doing the same work by hand.

---

ACCEPTANCE SCENARIOS

1. A complete incoming request is submitted. The assistant registers it and extracts its key details accurately into a structured record.
2. An incoming request with a required detail missing is submitted. The assistant names precisely what is missing, holds the item, and does not advance it.
3. Following on from the above, the assistant prepares a message back to the sender asking for exactly the missing details and nothing else.
4. A request that clearly belongs to a particular team is submitted. The assistant assigns it to that team and states in one line why.
5. The assistant prepares a handoff summary. A reviewer changes some of the wording and approves it. The changed version is what is retained and used.
6. A reviewer rejects a prepared handoff summary. Nothing is sent, and the item returns to an earlier stage.
7. A request that has already been submitted is submitted again. The assistant flags it as a probable duplicate rather than processing it a second time.
8. A team lead opens the status view and can see every item in progress, its stage, its owner, and how long it has been in progress.
9. A user asks the assistant a clinical or medical-necessity question. It declines plainly and directs them to a qualified human.
10. A compliance reviewer picks any completed item and can reconstruct what arrived, what was extracted, what rules were applied, what was drafted, who approved it, and when.

---

NON-NEGOTIABLE CONSTRAINTS

- Only synthetic or de-identified sample data is ever used. No real patient information at any point.
- The assistant assists; a human decides. Every outbound or final action requires an explicit, recorded human approval.
- The assistant does not answer clinical, diagnostic, treatment, or medical-necessity questions, and never determines whether care should be approved, denied, or delayed.
- Personal identifiers are masked in logs and audit records.
- The routing logic must be inspectable and explainable to a non-technical reviewer. A decision the reviewer cannot understand is not acceptable.
- The assistant's accuracy and speed must be re-measurable on demand against a fixed set of sample documents, producing a repeatable result.

EXPLICITLY OUT OF SCOPE

- Connecting to any live electronic health record or production clinical system.
- Submitting anything to a real insurer, payer, or external body.
- Making prior authorisation or coverage determinations of any kind.
- Any clinical or diagnostic judgement.
- Multi-organisation tenancy, single sign-on, and production hosting concerns.
- Any claim of financial savings or headcount reduction.

SUCCESS CRITERIA

Lower cycle time
- Processing an item through the assistant takes measurably less elapsed time than doing the identical work by hand on the same document.
- The number of separate people who must touch an item falls from roughly six to one.
- A prepared draft is ready for human review within a short time of the request arriving.

Fewer errors
- Key details are extracted correctly from the large majority of sample documents.
- Every deliberately introduced omission in a test document is detected.
- Items are assigned to the expected team in nine out of ten sample cases.
- The large majority of items reach the routing stage with complete details, without needing a rework loop.
- No item is ever sent or finalised without a recorded human approval.

Flag any requirement above that is ambiguous or that needs a decision before implementation, rather than assuming an answer.
```

---

## 2. Hold these back for `/plan`, not `/specify`

Do **not** put these in the prompt above. They are HOW, and naming them during `/specify` turns the spec into a design document:

- Microsoft Agent Framework (MAF), agents vs. workflows, executors, checkpointing
- Copilot SDK, chat surface implementation
- PDF / OCR / document parsing libraries
- FHIR, HL7, X12 data shapes
- Rules engine or config format choices
- OpenTelemetry / tracing implementation
- Language, runtime, and storage choices

---

## 3. Pre-agreed answers to likely clarification questions

The specify agent will probably ask these. Answer from here rather than improvising:

| Likely question | Our answer |
|---|---|
| Which administrative workflow? | Incoming referral / service-request intake. One request type only. |
| What are the "key details" to extract? | Requester, patient reference (synthetic), requested service, urgency, payer/plan, supporting notes, date. |
| What document formats arrive? | Text-layer PDF and email text first. Scanned/OCR documents are a later addition, not a day-one requirement. |
| Which teams can an item be routed to? | A small fixed set — decide and document it. Not dynamic, not customer-configurable during the hackathon. |
| What makes a routing decision "correct"? | Graded against a fixed answer key in the sample set. |
| How is a duplicate defined? | Same sender and same patient reference and same requested service within a short window. Keep it simple and explainable. |
| What does "measurably faster" mean? | A stopwatched manual walkthrough of the same document, compared against the assistant path. |
| Who approves? | A single reviewer role. No multi-level approval chains during the hackathon. |
| What happens after approval? | The item is marked complete and the handoff summary is retained. Nothing is transmitted externally. |

---

## 4. After `/specify`

1. Check the generated spec against [`../feature.md`](../feature.md) — every feature ID **F1–F13** should map to at least one requirement.
2. Resolve every `[NEEDS CLARIFICATION]` using §3 above.
3. Confirm the spec still contains no technology choices. If it does, strip them.
4. Then run `/plan` and introduce MAF + Copilot SDK.

---

## 5. Feature coverage checklist

Use this to verify the generated spec is complete:

| Feature | Covered by prompt section |
|---|---|
| F1 Intake a request | "Intake and understanding" · Scenario 1 |
| F2 Extract the fields | "Intake and understanding" · Scenario 1 |
| F3 Completeness check | "Checking" · Scenario 2 |
| F4 Draft the chase message | "Progressing" · Scenario 3 |
| F5 Route to the right team | "Progressing" · Scenario 4 |
| F6 Draft the handoff note | "Progressing" · Scenario 5 |
| F7 Human approval gate | "Human control" · Scenarios 5, 6 |
| F8 Status board + cycle time | "Visibility" · Scenario 8 |
| F9 Duplicate detection | "Checking" · Scenario 7 |
| F10 Safety boundary | Constraints · Scenario 9 |
| F11 Audit log | Constraints · Scenario 10 |
| F12 Eval harness | Constraints — "re-measurable on demand" |
| F13 Chat surface | Personas — coordinator interaction |
