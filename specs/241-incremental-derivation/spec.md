# Feature Specification: Derive by change, not by company

**Language**: English

## Context and Intent
Spec 181 FR-002 asks that a business event re-evaluate only the rows that depend on
the record it touched. Today the granularity is one whole projection: a checkpoint
per projection decides *whether* it is stale, and a stale one is rebuilt for the
entire company. Twelve projections work that way, and the two that matter most —
exceptions and the commitment register — are also time-sensitive, so they rebuild
every minute whether or not anything happened.

The pieces this needs already exist and are the reason it is worth doing now.
`business_event` records the subject type and id of every change, with a sequence
the checkpoints already track. Every builder returns rows keyed by a record key, so
a subset merges rather than replaces. And `_replace_rows` already diffs against what
is stored. What is missing is the middle: a builder that can be asked for the rows of
named subjects rather than of a company.

### Non-Goals
No change to what any projection contains or to how a row is derived — the same
builder must produce the same row whether it was asked for one subject or all of
them, and the tests are written to fail if it does not. No new projection, no schema
change to `projection_row`, and no change to the refresh schedule, which is FR-004
and a separate feature. Full company evaluation stays, because a maintenance rebuild
and a version change both need it.

## User Scenarios & Testing
### US1 — One changed record, one re-evaluated row (P1)
Given a company with a large history and a ready generation, when one commitment
changes, the refresh reads and rewrites the rows of that commitment and of the
classes that read it, and not the rest of the company.
### US2 — Incremental and full agree, always (P1)
Given any sequence of business events, when the projections are refreshed
incrementally and then rebuilt in full, the stored rows are identical. A builder that
cannot express its own dependencies must fail this, not pass it quietly.
### US3 — A date passing is found by its date (P1)
Given promises that become overdue without any event, when the time-sensitive refresh
runs, it selects them through an indexed date and evaluates only those, rather than
re-deriving every promise because the clock moved.
### US4 — A rebuild is still available (P2)
Given a projection version change or an operator asking for one, a full rebuild runs
as it does today and is the only thing that runs.
### US5 — An unknown change is safe, not wrong (P1)
Given an event whose subject a builder does not know how to narrow, that builder
falls back to a full evaluation for that refresh rather than deriving a subset it
cannot justify. Narrowing is an optimisation each builder earns; correctness is not
optional.

## Requirements
- **FR-001**: Collect the change set for a refresh — subject types and ids from the
  business events between the stored checkpoint and the target sequence — and pass it
  to each builder that is being refreshed.
- **FR-002**: Give each builder an optional change set. A builder that accepts one
  returns exactly the rows of those subjects; a builder that does not, or that is
  handed a subject it cannot narrow by, evaluates the whole company for that refresh
  and says so through its result rather than silently.
- **FR-003**: Merge a partial result rather than replacing: rows for subjects in the
  change set are inserted, updated or removed, and rows for every other subject are
  left untouched. A row that disappears for a narrowed subject must be removed.
- **FR-004**: Select time-based transitions by indexed date. A refresh that runs
  because the clock moved evaluates the records whose date has passed since the last
  refresh, not every record of the class.
- **FR-005**: Keep full evaluation for a version change, an operator rebuild and any
  builder that declines to narrow, and keep the existing tenant and advisory locking,
  isolation and publication boundaries exactly as they are.
- **FR-006**: Prove equivalence as a property, not as an example: after any sequence of
  events, incremental refresh and full rebuild leave identical stored rows for every
  projection.

## Assumptions and Dependencies
Every change that a projection depends on is recorded as a business event with the
subject it touched; a derivation that reads something no event announces cannot be
narrowed and will say so under FR-002. The existing per-projection dependency catalog
(`projection_catalog.yaml`) stays the coarse filter and this feature refines it.
Measurement uses the ingest benchmark of spec 181 FR-006, which separates the
product's own work from the sweep around it.

## Success Criteria
- **SC-001**: On a company at the fixture's largest size, one business event refreshes
  the affected projections within the budget spec 181 SC-002 sets, where a full
  company rebuild does not.
- **SC-002**: Incremental and full agree on every projection after randomised event
  sequences, with the comparison run as a test rather than by inspection.
- **SC-003**: The work a refresh does is proportional to the change set, not to the
  company: doubling the company's history without changing the event leaves the
  refresh's statement count within ten per cent.
- **SC-004**: A builder that cannot narrow is visible — its fallback is reported and
  counted, so "everything falls back" cannot pass as success.
- **SC-005**: No projection's content changes: the stored rows before and after this
  feature are identical for the same events.

## Requirement Traceability
| Requirement | Story | Tasks | Tests |
|---|---|---|---|
| FR-001 | US1 | T001,T002 | Change set collected from events between checkpoints |
| FR-002 | US1,US5 | T002,T003 | Narrowed builders; a decliner falls back and reports it |
| FR-003 | US1 | T003 | Partial merge inserts, updates and removes only its subjects |
| FR-004 | US3 | T004 | A date passing selects by index, not by scan |
| FR-005 | US4 | T005 | Version change and operator rebuild still evaluate fully |
| FR-006 | US2 | T001 | Incremental equals full after randomised event sequences |

## Evidence and risks

**The risk is a builder that narrows wrongly**, and it is the whole reason FR-006 is
written as a property rather than a set of examples. A builder asked for the rows of
one commitment might miss a row that the change affects indirectly — a blocker that
clears, a total that shifts — and the result would be a stored projection that is
quietly wrong, which is worse than a slow one. The equivalence test is what makes that
a failure instead of a silence, and no builder should be narrowed before it passes.

**Narrowing is earned per builder, not granted globally.** FR-002 lets a builder
decline, and SC-004 makes the declining visible, because the honest first state of this
feature is that most builders still evaluate fully and one or two do not. A version of
this that narrowed everything at once would be faster to write and impossible to trust.

**The order matters.** Spec 181 FR-007 puts incremental derivation after ingest cost,
which is delivered, and before refresh units and storage. This feature does not touch
the schedule: a projection still refreshes when it refreshes, only cheaper.
