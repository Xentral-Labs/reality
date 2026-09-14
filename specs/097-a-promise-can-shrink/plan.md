# Implementation Plan: Eighty of the Hundred

**Branch**: `097-a-promise-can-shrink` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One nullable column on the record Spec 093 built, a second shared rule beside its first, four
call sites that stop reading the promise directly, and a rename because the operation no longer
does only what its name says.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, PyYAML
**Storage**: PostgreSQL; one column added, one made nullable, one revision
**Testing**: pytest, `tests/test_commitment_revisions.py` and the derivation suite
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: Append-only; nothing on the promise changes; strict tenant scope
**Scale/Scope**: One migration, one rule, four call sites, one rename

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | A revision is Evidence a counterparty stated; the promise it concerns is Reality and is not rewritten | PASS |
| Reality owns operational state | The quantity in force is derived per read. The one stored change is the promise's status, which the product already owns and already sets on movement | PASS |
| Proven schema only | One nullable column on an existing table, because the statement being recorded is the same statement | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; one rule answers the quantity in force for every caller | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | An overdue entry measures remaining against what is in force and already says the promise was revised | PASS |
| Received values not recomputed | Every quantity stored is one somebody stated; the quantity in force is a selection among stated figures, never an adjustment | PASS |
| Smallest coherent design | Three alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **A second table for quantity revisions.** It would let one sentence become two records with
  two timestamps that can disagree about when the supplier said it. The statement is the unit,
  not the field.
- **A `confirmed_quantity` column on the promise.** The argument Spec 093 already settled for
  dates: the second statement would erase the first, and a quantity somebody stated is a received
  value.
- **Cancel and recreate the promise.** What a company has to do today. It loses the link between
  the order line and its promise, and `create_commitment` is reachable from no surface anyway, so
  it is not even a workaround.

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/0042_commitment_revision_quantity.py
packages/reality-core/src/reality/db/core.py                     # the column
packages/reality-core/src/reality/services/core.py               # the rule, the rename, open_quantity
packages/reality-core/src/reality/services/exceptions.py         # three call sites
packages/reality-core/config/command_catalog.yaml                # the renamed command, one parameter
packages/reality-core/config/tenant_isolation_catalog.yaml       # the renamed operation and tool
packages/reality-core/config/business_event_catalog.yaml         # the renamed producer
packages/reality-core/src/reality/tools/application.py, mcp/catalog.py, web/api.py
docs/features/commitments.md, procure_to_pay.md
apps/docs/content/catalogs/ (+ de/), docs/SPEC_COVERAGE_MATRIX.md
```

## Design

### One statement, two figures

`commitment_revision` gains a nullable `quantity`, and its `due_at` becomes nullable. A statement
must restate at least one of the two; restating neither is refused, because a statement that says
nothing is not a statement.

That shape is the point. *"Eighty pieces, two weeks later"* is one sentence, and a company should
record it once with one `stated_at`. Two tables would have produced two records that can disagree
about when it was said.

### Two rules, side by side

`commitment_due_at` answers the date in force; `commitment_quantity` answers the quantity, from
the most recent revision that stated one — which is not necessarily the most recent revision. A
later statement about the date alone leaves an earlier quantity standing, which is what the
sentence meant.

Four places stop reading the promise directly: `open_quantity`, the remaining quantity in
`_commitment_exceptions`, and the two reads in the stalled-order class and its threshold learner.
A test asserts nothing else computes it.

### Falling to nothing, and below

A promise revised to what has already arrived is finished, and it is settled **at that moment**
rather than at the next movement — because there may not be a next movement. That is the one
stored thing this feature writes, and it is the same field `_append_movement` already sets for
the same reason.

A quantity below what has already moved is accepted. The supplier said eighty and ninety came;
both are true, the ninety is recorded, and refusing would lose the statement — the same argument
Spec 093 used for a date already past. What is open becomes nothing, which is what it is.

### What this deliberately leaves alone

Stock reserved for the original hundred stays reserved when the promise shrinks to eighty.
Nothing releases it and no class reports it, because over-reserving has never been a condition
this queue reports. Releasing somebody's stock as a side effect of recording a sentence would be
the product deciding something nobody asked it to. It is a real limit and it is in the
specification rather than in a comment.

### The rename

`revise_commitment_due_date` becomes `revise_commitment`. The old name would be a lie the moment
it revises a quantity, and Spec 092 made the same call about four helpers named after their only
caller. It shipped hours ago and has no consumer outside this repository, so the cost is five
declarations and no migration of anybody's code.

### Data and migration impact

One revision. `quantity` added nullable; `due_at` altered to nullable. No backfill: every
existing revision states a date and no quantity, which is exactly what it meant.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_commitment_revisions.py::test_one_statement_can_restate_both` | quantity is not accepted |
| FR-002 | service | `test_commitment_revisions.py::test_a_statement_must_restate_something` | an empty revision is accepted |
| FR-003 | service | `test_a_statement_must_restate_something` | zero or negative is accepted |
| FR-004 | service | `test_commitment_revisions.py::test_the_quantity_in_force_is_the_latest_stated` | an earlier figure wins |
| FR-005 | story | `test_derivation.py::test_a_shrunk_promise_is_judged_by_what_is_in_force` | the queue measures the original |
| FR-006 | service | `test_commitment_revisions.py::test_a_promise_can_shrink_below_what_arrived` | it is refused |
| FR-007 | service | `test_commitment_revisions.py::test_shrinking_to_what_arrived_finishes_the_promise` | it stays open |
| FR-008 | service | `test_a_statement_must_restate_something` | a closed promise is revised |
| FR-009 | unit | the catalog drift gates | catalog drift |
| FR-010 | story | every existing suite, unchanged | an existing behaviour moves |
| DR-001 | review | exactly one migration, no new table | — |
| DR-002 | service | `test_one_statement_can_restate_both` | the promise is mutated |
| DR-003 | unit | `test_derivation.py::test_one_rule_answers_the_quantity_in_force` | a second rule appears |
| DR-004 | service | `test_commitment_revisions.py::test_revisions_are_tenant_scoped` | another tenant is reachable |
| DR-005 | unit | `test_coverage.py` closed registry test | passes unchanged |
| DR-006 | service | `test_one_statement_can_restate_both` | a quantity was adjusted |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

One migration adding a nullable column and relaxing another. No promise has a stated quantity on
deploy, so every rule falls back to the promise's own and every class behaves exactly as today.
Rollback drops the column; the date revisions Spec 093 recorded are untouched.

The demo month records no revision and its queue is unchanged.

## Review Risks

- **A promise can now shrink out from under reserved stock.** Nothing releases the reservation
  and nothing reports it. That is the largest thing this feature does not do, and the reason is
  that releasing stock as a side effect of recording a sentence is a decision the product was not
  asked to make. A reviewer who disagrees is arguing for a class or a release step, both of which
  are separable work.
- **Accepting a quantity below what arrived means fulfilment can exceed the promise.** True, and
  the alternative loses a statement. The over-delivery is already recorded and the queue reports
  nothing open, which is accurate.
- **Settling the status on a revision is the one stored write.** It is the same field the
  movement path already sets, for the same reason, and without it a company would have a promise
  reading "open" with nothing left to do until something else happened to it.
- **A rename touches five declarations of an operation that shipped hours ago.** Cheap now,
  and the alternative is a name that describes what the operation used to do.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| Schema change: one nullable column, one relaxed | A quantity a counterparty stated is a received value and belongs in the same statement as the date it came with | A second table, and a column on the promise — one splits a sentence, the other overwrites | Recorded here; one revision, no backfill |
