# Feature Specification: Derivations that scale with the database, not with the process

**Language**: English

## Context and Intent
`financial_open_items` folds a company's finance history in one Python process. It is
reached from two places, and only one of them can afford to wait.

The visible one is analysis: nine of the sixty-four analysis objects rest on it and are
refused above 20,000 input rows. That refusal is not what makes this urgent. If an
analysis may be requested and collected later — spec 236 — then four seconds, or forty,
stops mattering, and the cap can be lifted by moving the work to a worker without
touching a line of derivation logic.

The one that cannot wait is the register. `projections.py` builds the
`open_financial_items` projection from the same fold, and spec 181 SC-002 requires the
affected projections to be ready within **5 seconds** of worker time after one business
event on a company with 100,000 orders. Measured, the fold costs 4 to 5.7 seconds at
20,000 finance documents, so at 100,000 it is roughly 20 to 25 seconds — four to five
times over a budget that belongs to the operational screens, where "it will arrive later"
is not an answer.

Behind that sits a wall that no amount of waiting moves. The fold holds **5.3 KiB of
Python heap per finance document**: 104 MiB at 20,000, and something near 5 GB at a
million. That is not a slow job. That is a process that does not finish.

This specification is therefore about neither analysis latency nor the 20,000 cap. It is
about the projection budget and the memory ceiling, and it removes the cap as a
consequence rather than as a goal.

### Non-Goals
No persisted or materialized balance, no second definition beside the canonical one, no
cache that outlives a request, and no change to any answer. No new analysis object,
measure or edge. Partitioning and multi-cluster placement are spec 181's User Story 4 and
stay there; this feature is what makes a derivation cheap enough for that to matter.

## User Scenarios & Testing
### US1 — The registers stay fresh at the recorded volume (P1)
Given a company with 100,000 orders and one business event, the projections that feed the
registers are ready within the 5 seconds spec 181 SC-002 allows, and the process that
builds them holds a bounded amount of memory regardless of how much history the company
has.
### US2 — One definition, two readers (P1)
Given the registers and the analysis both asking what is open on an invoice, both reach
the same expression, and a change to the rule changes both. Two answers that agree most
of the time are the failure this prevents.
### US3a — A million documents is a size, not a wall (P1)
Given a company with a million finance documents, deriving its open items completes
without holding the company in one process's heap.
### US3 — The narrow question stays narrow (P2)
Given a question filtered to one party, article or period, the narrowing reaches the
expression as a predicate, so PostgreSQL reads only what the question can reach.
### US4 — The limit describes the machine, not the company (P2)
Given a question whose result would exceed what one response can carry, the refusal names
the result size. No refusal is stated in terms of how much history a company has.

## Requirements
- **FR-001**: Express the canonical open-item derivation — control entry, signed document
  balance, active allocations, reversal role, open amount and settlement status — as one
  SQL expression, with the effective-time cutoff as a predicate rather than a second code
  path.
- **FR-002**: Make the registers, the exception classes, the payment run and the analysis
  derivations read that one expression. A second implementation of the same rule, in
  either direction, is the defect this requirement exists to prevent.
- **FR-003**: Do the same for the inventory position derivation: physical, reserved and
  available per article and tracking dimension, from movements and active reservations.
- **FR-004**: Accept the existing identity narrowing (spec 234) as predicates on the
  expression, so a filtered question reads a filtered set rather than a filtered result.
- **FR-005**: Replace the input-size caps with a result-size bound and the existing
  statement deadline. Preserve every refusal that states something true about the
  question; remove those that state only that the company is large.
- **FR-006**: Preserve exact Decimal arithmetic, tenant scope, opaque identity, currency
  and unit grouping, and the fan-out and additivity guards, unchanged.
- **FR-007**: Carry the scale fixture to a company at the recorded target and record the
  cost of each derivation there, as spec 181 FR-006 requires of the ingest path.

## Assumptions and Dependencies
Every input to an open item is already a stored fact — postings, allocations, reversals —
and none of it is recomputed by this feature; only where the fold happens changes.
PostgreSQL remains the only supported database, so an expression may use its aggregates.
Spec 181's User Story 4 (partitioning, tiered payloads, placement) is unbuilt; without it
the plain paths, which already have no cap, will meet their own limit at hundreds of
millions of rows. That is a separate piece of work and this one does not wait for it.

## Success Criteria
- **SC-001**: On a company with 100,000 finance documents, rebuilding the
  `open_financial_items` projection after one business event completes within the 5 s of
  worker time spec 181 SC-002 allows, where it takes 20 to 25 s today.
- **SC-002**: Every derived row equals what the canonical service returns today, checked
  document by document on a company built from the scale fixture, not by sampling.
- **SC-003**: No analysis refusal remains whose reason is the size of the company.
- **SC-004**: The memory the derivation holds does not grow with the company's history,
  where it is measured at 5.3 KiB per finance document today.
- **SC-005**: One expression, one test: deleting the SQL breaks the registers and the
  analysis together.

## Requirement Traceability
| Requirement | Story | Tasks | Tests |
|---|---|---|---|
| FR-001 | US1 | T001,T002 | Open-item parity against the canonical service, per document |
| FR-002 | US2 | T003 | Registers, exceptions and payment run read the one expression |
| FR-003 | US1 | T004 | Inventory position parity, tracking grains and null buckets |
| FR-004 | US3 | T005 | A filtered question reads a filtered set |
| FR-005 | US4 | T006 | No refusal cites company size; result bound and deadline hold |
| FR-006 | US1–4 | T001–T006 | Decimal, tenant, identity, units, fan-out, additivity |
| FR-007 | US1 | T007 | Recorded cost at the fixture's three sizes |

## Evidence and risks

**Where the time goes.** Measured on the largest company available (10,233 documents,
3,430 of them finance documents, 13,590 ledger entries), `financial_open_items` costs
473 ms: 279 ms transferring and hydrating roughly 20,000 rows into ORM objects, 195 ms
folding them in Python. The JSON round trip that hands the result back to PostgreSQL —
which an earlier reading of this code blamed — costs **1 ms**, and a plain SQL aggregate
over the same company also costs 1 ms. The round trip is not the problem and this feature
does not touch it.

**What this is not about.** An earlier draft of this specification argued from analysis
latency and the 20,000 cap. That argument does not hold: an analysis that may be
requested and collected later does not care whether it takes four seconds or forty, and
spec 236 lifts the cap for analysis by moving the work to a worker. The measurements
below matter because the same fold builds the register projections under a 5-second
budget, and because it holds the company in memory.

**The cost is measured, not extrapolated.** The repository's own fixture, at the full
profile with the finance dimension it was missing, best of three samples with statistics
analysed: at 10,000 finance documents the derivations cost 1,151 to 1,647 ms, and at
20,000 — the cap where analysis refuses today — 2,726 to 4,141 ms. Doubling the company
doubles the cost and a little more. The statement counts do not move between the two, so
this is volume carried into a process, not a query per row. The 30-second deadline
arrives between 150,000 and 200,000 finance documents.

**The formulation is proven, not proposed.** The same arithmetic written as one SQL
statement — control entry by document type and side, signed balance per document and
account, allocations excluding reversed posting groups, reversal role, open amount —
returns **exactly the same open amount for all 3,430 documents**, with no document missing
and none added, in 45 ms against 536 ms. The draft is in this spec's research notes.

**The memory is the part waiting cannot fix.** Measured with `tracemalloc` on the fixture
at 20,000 finance documents: 104 MiB of Python heap, 5.3 KiB per document. A worker with
half an hour still cannot hold a million documents this way. Time is negotiable; a
process that runs out of memory is not.

**The remaining risk is the second half, not the first.** 45 ms on this company is not
45 ms at ten million rows; the SQL cost tracks total ledger volume and needs the indexes
and partitioning of spec 181 US4 to stay bounded. What changes here is the shape of the
cost: a fixed set of hash aggregates, which indexes and partitions can bound, instead of
objects in one process, which they cannot.

**The risk worth naming.** Moving the rule to SQL puts the single definition in a place
that is harder to read than Python and cannot be unit-tested in isolation the same way.
FR-002 and SC-005 exist because the tempting shortcut — leaving the Python fold in place
for the registers and giving analysis its own SQL — produces two definitions that agree
until the day they do not, which is the more dangerous kind of wrong.
