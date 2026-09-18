# Feature Specification: Derivations that scale with the database, not with the process

**Language**: English

## Context and Intent
Nine of the sixty-four analysis objects — customer and supplier balances, open items,
stock positions and their historical variants — are refused outright above 20,000 input
rows. The other fifty-five have no such limit: they compile to one SQL aggregate and
scale with PostgreSQL. The difference is not the question. It is that the nine rest on a
canonical service that loads the company's finance or inventory history into Python
objects and folds it there.

Spec 181 records the owner's target: 10,000 companies at 100 to 1,000 orders a day each.
At 1,000 orders a day a company reaches 20,000 finance documents in about twenty days, so
the limit is not a ceiling somebody might one day touch — it is reached within a month of
ordinary operation, and the analysis simply stops answering.

This specification does not raise the limit. It removes the reason for it: the canonical
derivations become SQL that PostgreSQL folds, and the registers read the same SQL, so
there is still exactly one definition of what an open item is.

### Non-Goals
No persisted or materialized balance, no second definition beside the canonical one, no
cache that outlives a request, and no change to any answer. No new analysis object,
measure or edge. Partitioning and multi-cluster placement are spec 181's User Story 4 and
stay there; this feature is what makes a derivation cheap enough for that to matter.

## User Scenarios & Testing
### US1 — A company a year into the target volume still answers (P1)
Given a company with hundreds of thousands of finance documents, asking for customer
balances, open items or stock positions returns the same rows the canonical service
returns today, within the page's time budget, without an input-size refusal.
### US2 — One definition, two readers (P1)
Given the registers and the analysis both asking what is open on an invoice, both reach
the same expression, and a change to the rule changes both. Two answers that agree most
of the time are the failure this prevents.
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
- **SC-001**: On a company with 100,000 finance documents, customer balances, supplier
  balances and open items each return within 300 ms server time, the budget spec 181
  SC-004 already sets for the registers.
- **SC-002**: Every derived row equals what the canonical service returns today, checked
  document by document on a company built from the scale fixture, not by sampling.
- **SC-003**: No analysis refusal remains whose reason is the size of the company.
- **SC-004**: The cost of a derivation grows sub-linearly in company size across the
  fixture's three sizes, where it is measured linear today.
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

**The cost is linear in the company.** 130 µs per finance document, stable across
companies of 177, 688, 711 and 3,430 finance documents. Extrapolated: 2.6 s at the
current 20,000 cap, 13 s at 100,000, 2.2 minutes at a million, 22 minutes at ten million —
per question, uncached.

**The formulation is proven, not proposed.** The same arithmetic written as one SQL
statement — control entry by document type and side, signed balance per document and
account, allocations excluding reversed posting groups, reversal role, open amount —
returns **exactly the same open amount for all 3,430 documents**, with no document missing
and none added, in 45 ms against 536 ms. The draft is in this spec's research notes.

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
