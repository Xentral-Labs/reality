# Feature Specification: An analysis you request and collect

**Language**: English

## Context and Intent
Analysis answers inside one HTTP request. That decision is why nine of its sixty-four
objects refuse above 20,000 input rows, why a statement deadline of 30 seconds bounds
them, and why a company at the target spec 181 records stops being able to ask about its
own money within about a month of ordinary operation.

The owner's position is that analysis does not need to be immediate: a question whose
answer arrives in five or thirty minutes is entirely acceptable. That reframes the limit.
It is not a performance problem to be optimised away — it is the cost of insisting the
answer arrive before the connection closes.

This feature lets a question be requested, run in the worker that already exists, and be
collected when it is ready. The derivations are untouched: the same canonical services
produce the same rows. What changes is who waits, and where.

Spec 235 remains necessary and is not replaced by this. Its subject is the projection
that feeds the registers under a five-second budget, and a fold that holds 5.3 KiB of
heap per document. Neither of those is relieved by letting an analysis take longer.

### Non-Goals
No change to any derivation, measure, edge or answer. No persisted derived balance and no
cache: a collected result is the answer to one question asked at one moment, not a
standing figure other reads may trust. No new scheduling infrastructure — the registry,
scheduler and worker of spec 147 are used as they are. Immediate answers do not go away.

## User Scenarios & Testing
### US1 — Ask now, collect later (P1)
Given a question that would exceed the immediate budget, the asker requests it, is told it
was accepted, and finds the result when it is ready. The result carries the question, the
moment it was answered and the model version, so what it means is not guessed later.
### US2 — Small questions stay immediate (P1)
Given a question the compiler can answer within the immediate budget, it is answered in
the request as it is today. Nobody waits for something that was already fast.
### US3 — A request that cannot be answered says so (P1)
Given a question that refuses — an unknown property, a fan-out, a unit mismatch — the
refusal arrives at request time with its existing reason, not minutes later as a failed
job. Only cost may be deferred, never a judgement about the question.
### US4 — The asker sees where it stands (P2)
Given a requested analysis, its state is visible: accepted, running, ready or failed with
a reason. A result that is never collected is removed on a stated retention.
### US5 — One company cannot starve another (P2)
Given many requested analyses across companies, the worker's work is spread by request
time and company, so one large company's questions do not hold up everyone else's.

## Requirements
- **FR-001**: Register an analysis job through the existing job registry, with a
  configuration type holding the checked traversal, the requesting principal and the
  tenant. Reject extra fields; store no source payloads in the configuration.
- **FR-002**: Check the question at request time with the existing traversal checks, and
  return every existing refusal then. A request is accepted only if the question is
  answerable; the job may then fail for cost, never for meaning.
- **FR-003**: Decide immediate or deferred by a declared budget, not by asking the user to
  choose. Where the reachable input exceeds the immediate budget, the request is deferred
  and the asker is told so, with the reason.
- **FR-004**: Run the job with the same services, the same tenant scope and the same
  principal the request carried. Re-validate that principal's access at execution.
- **FR-005**: Store the result with the question that produced it, the moment it was
  answered, the model version and the row set, under a stated retention. A stored result
  is evidence of one answer, never an authority another read derives from.
- **FR-006**: Raise the input caps for the deferred path to what the worker can hold, and
  keep the immediate path's caps and its statement deadline unchanged.
- **FR-007**: Expose state and collection as read tools on the existing analysis surfaces
  — web, tools and MCP — so a requested analysis is not a second way to ask a question.
  Requesting one is a mutation: it records a question and enqueues a run. It is therefore
  offered on the web API, where an authenticated person has already asked, and its
  agent-facing form is a declared command with a confirmation. That is FR-008.
- **FR-008**: Offer requesting an analysis as a declared command, confirmed like every
  other mutation, so an agent can ask for one without the read surface having to pretend
  that recording a question changes nothing.

## Assumptions and Dependencies
The scheduler and worker of spec 147 are deployed and their contract (docs/features/
scheduled-jobs.md) is followed rather than extended. The traversal is already a checkable
object, so a question can be validated at request time and carried to a worker unchanged.
Results are private to their tenant and their requester, like the saved reports of spec
185. Memory remains bounded by whatever spec 235 leaves the derivations holding; this
feature moves the wait, not the ceiling.

## Success Criteria
- **SC-001**: A question over a company at the recorded target volume returns a result
  through the deferred path, where today it is refused.
- **SC-002**: A question within the immediate budget is answered in the request, with no
  added latency against today.
- **SC-003**: Every refusal that arrives today at request time still arrives at request
  time.
- **SC-004**: A stored result names its question, its moment and its model version, and no
  read derives a business figure from it.
- **SC-005**: Requested analyses across many companies are executed in an order that does
  not depend on company size.

## Requirement Traceability
| Requirement | Story | Tasks | Tests |
|---|---|---|---|
| FR-001 | US1 | T001,T002 | Registry, configuration and permission validation |
| FR-002 | US3 | T002 | Every existing refusal arrives at request time |
| FR-003 | US1,US2 | T003 | Budget decides; small questions stay immediate |
| FR-004 | US1 | T002,T004 | Tenant scope and principal re-validated at execution |
| FR-005 | US1,US4 | T004 | Result carries question, moment, model version; retention |
| FR-006 | US1 | T005 | Deferred caps raised, immediate caps unchanged |
| FR-007 | US1,US4 | T006 | Web request; state and collection as read tools |
| FR-008 | US1 | T007 | Proposed and confirmed; sealed; refused at proposal time |

## Evidence and risks
Measured on the repository's fixture at the full profile, best of three, statistics
analysed: at 20,000 finance documents the canonical derivations cost 2.7 to 4.1 seconds
and the fold holds 104 MiB. Those numbers are why the immediate path has caps. They are
not changed by this feature; they stop being the reason a question cannot be asked.

The risk worth naming is FR-005. A stored result is one answer to one question at one
moment. The moment it is treated as a standing figure — read by another page, compared
against a register, used to decide something — it has become a second authority beside the
canonical services, which is what this codebase refuses. The requirement is written to
make that visible, and the tests exist to keep it visible.

The application catalog refused an earlier shape of this work, correctly. Requesting an
analysis had been written as a read tool, and a read may declare no side effect. Recording
a question and enqueueing a run is a side effect, so the honest split is the one above:
collecting and listing are reads and stay on the tool surface; requesting is a mutation and
is a proposal an agent prepares and a person confirms (FR-008). The question inside that
proposal is sealed, for the same reason a private report change is: a proposal record is
visible to the company, and a question somebody asked is theirs. What the company sees is
that an analysis was requested, not what was asked.

The question is planned, but not executed, when the proposal is prepared. Planning is what
turns an unknown name or an edge that fans out into a refusal, so that refusal reaches
whoever is still looking; executing it is the expensive part and waits for the
confirmation.

The second risk is FR-003. Deciding immediate against deferred by a budget means some
questions change behaviour as a company grows, which is a surprise unless the asker is
told plainly why this one is being queued. A silent switch would be worse than a refusal.
