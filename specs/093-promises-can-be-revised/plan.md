# Implementation Plan: When the Other Side Says a New Date

**Branch**: `093-promises-can-be-revised` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One append-only table, one operation, one shared rule for the date in force, and one cause so a
revision cannot buy silence.

The fifth schema change in this line of work, and the first that exists to stop a received value
being overwritten rather than to record a new kind of fact.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, PyYAML for the closed catalogs
**Storage**: PostgreSQL; one new table, one revision
**Testing**: pytest business stories under `tests/` and `tests/operational_exceptions/`
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: Append-only; nothing on the promise changes; opaque IDs; strict tenant scope
**Scale/Scope**: One table, one operation, one rule, one cause, three classes reading it

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | A revision is Evidence a counterparty stated, optionally carrying the source record it came from; the promise it concerns is Reality | PASS |
| Reality owns operational state | Nothing gains a status. The date in force is derived per read and stored nowhere | PASS |
| Proven schema only | One table, because the alternative — a column — would overwrite the previous statement every time. Justified in Complexity Tracking | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; one shared rule answers what date is in force for every caller | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | An overdue entry on a revised promise names the original date and how many times it moved | PASS |
| Received values not recomputed | Every date stored is one somebody stated. The date in force is a selection among stated dates, never an adjustment of one | PASS |
| Smallest coherent design | Four alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **A `confirmed_due_at` column on the promise.** One column instead of a table, and it
  overwrites: a supplier's second statement would erase its first. A date somebody stated is a
  received value, and this product does not overwrite those. This is the deciding argument and it
  is why the table is not gold-plating.
- **Update `due_at` in place.** The same objection with nothing left at all.
- **A class for a promise moved too often.** "Too often" is a number nobody has measured, and
  this queue already carries eight unmeasured constants. A cause on the entry the promise
  produces when it is late again says the same thing and needs no threshold.
- **Refuse a revision on a held promise.** Consistent-looking and wrong: a hold stops execution,
  and this records something the other side said. Refusing would lose a statement because of an
  unrelated block.

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/0040_commitment_revisions.py  # one table
packages/reality-core/src/reality/db/core.py                     # the model
packages/reality-core/src/reality/services/core.py               # the operation and the shared rule
packages/reality-core/src/reality/services/exceptions.py         # three classes read the rule, one cause
packages/reality-core/src/reality/catalogs.py                    # cause vocabulary
packages/reality-core/config/operational_exception_catalog.yaml  # the cause and the guidance
packages/reality-core/config/command_catalog.yaml                # the command
packages/reality-core/config/tenant_isolation_catalog.yaml       # operation and tool
packages/reality-core/src/reality/tools/application.py, mcp/catalog.py, web/api.py
docs/features/commitments.md, operational_exceptions.md, procure_to_pay.md
apps/docs/content/catalogs/ (+ de/)                               # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                      # specification row
```

## Design

### One statement, appended

`commitment_revision` holds the promise it concerns, the date now stated, when it was stated, an
optional note and an optional source record. It is written and never updated, like every movement
and every ledger entry in the product.

The promise's own `due_at` is not touched. It stays the date the promise was made with, which is
what makes "originally due" answerable at all.

### The date in force

One rule: the most recently stated revision, or the promise's own date where none has been
stated. Ordered by when it was stated and then by identity, so two statements in the same instant
still resolve the same way on every read.

Three classes ask it — the two overdue classes and the at-risk one, all of which live in the same
body — and `order_stalled` asks it too, in the negative: a promise nobody dated stops being an
undated order the moment somebody states a date for it. That is the one existing class whose
behaviour this feature changes, and it changes correctly.

### Why a revision cannot buy silence

Judging against the date in force is what makes the queue useful, and on its own it would let a
supplier move a date forever and never be late. So the entry says what happened:

`promise_was_revised` rides on the overdue class as a cause, and the causal values gain the date
the promise was originally due and how many times it has been moved — **only when it has been
moved**, so an entry for an unrevised promise is byte-identical to today's.

The entry is not suppressed and no threshold is invented. A promise that is late against a date
its own counterparty chose, having already moved it, is exactly as overdue as any other, and now
it says so.

The limit is stated rather than hidden: a supplier that moves dates repeatedly and always beats
the revised one is never reported, because it is meeting its stated promises.

### Data and migration impact

One revision, `0040_commitment_revisions`, creating one table with a foreign key to the promise
and an index on it. No backfill: no promise has been revised, and none is treated as revised.
Downgrade drops the table.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_commitment_revisions.py::test_a_new_date_never_erases_the_old_one` | the operation does not exist |
| FR-002 | service | `test_a_new_date_never_erases_the_old_one` | fields missing |
| FR-003 | service | `test_commitment_revisions.py::test_the_date_in_force_is_the_latest_stated` | an earlier statement wins |
| FR-004 | story | `test_derivation.py::test_a_revised_promise_is_judged_by_its_new_date` | the class judges the original |
| FR-005 | story | `test_derivation.py::test_a_dated_promise_is_no_longer_a_stalled_order` | it stays an undated order |
| FR-006 | story | `test_derivation.py::test_a_revision_cannot_buy_silence` | no reason on the entry |
| FR-007 | story | `test_a_revision_cannot_buy_silence` | the entry is suppressed or altered |
| FR-008 | service | `test_commitment_revisions.py::test_a_revision_is_refused_where_it_makes_no_sense` | a nonsense revision is accepted |
| FR-009 | service | `test_commitment_revisions.py::test_a_hold_does_not_block_recording_what_was_said` | a hold refuses a statement |
| FR-010 | story | `test_derivation.py::test_both_directions_can_be_revised` | only one direction works |
| FR-011 | unit | `test_application_catalog.py`, `tests/tenant_isolation/`, `test_capability_guidance.py` | catalog drift |
| FR-012 | story | `test_derivation.py::test_revised_promises_order_deterministically` | order varies between reads |
| FR-013 | story | every existing suite, unchanged | an existing behaviour moves |
| DR-001 | review | exactly one file under `migrations/versions/` | — |
| DR-002 | service | `test_a_new_date_never_erases_the_old_one` | the promise is mutated |
| DR-003 | unit | `test_derivation.py::test_one_rule_answers_the_date_in_force` | a second rule appears |
| DR-004 | service | `test_commitment_revisions.py::test_revisions_are_tenant_scoped` | another tenant is reachable |
| DR-005 | story | `test_a_revision_cannot_buy_silence` | trace restates business fields |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | the cause is undeclared |
| DR-007 | service | `test_a_new_date_never_erases_the_old_one` | a date was adjusted |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

One migration creating one table. No promise is revised on deploy, so the date in force is every
promise's own date and every class behaves exactly as it does today. Rollback drops the table.

The demo month records no revision and its queue is unchanged.

## Review Risks

- **The date in force becomes a derived figure several classes depend on.** That is one more
  thing that can drift, which is why it is one rule with a test asserting no class computes it
  for itself. It is also the shape that has bitten this line of work before — three inline unit
  checks in spec 087, two learned thresholds in spec 089 — so the mitigation is structural rather
  than a promise to be careful.
- **Judging against a revised date is a real loosening.** It is the right answer and it is still
  a loosening: an order that was three weeks late becomes not late because somebody typed a new
  date. The protection is that the entry says the promise was moved once it is late again, and
  that the original date is kept and reported. A reviewer who wants more than that is arguing for
  the class this specification deliberately did not build.
- **A supplier that always beats its revised date is never reported.** Stated in the
  specification's assumptions. It is meeting its stated promises, so this is arguably correct —
  but a company that agreed to the first date may not see it that way, and Reality is silent on
  the difference.
- **`order_stalled` changes behaviour.** A promise nobody dated stops being an undated order once
  a date is stated for it. That is correct and it is the only existing class this feature moves.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| Schema change: one new table, `commitment_revision` | Every date a counterparty states is a received value. A column would let the second statement overwrite the first, which is the one thing this product does not do to received values | A `confirmed_due_at` column, and updating `due_at` in place — both overwrite | Recorded here; one revision, one table, no backfill |
