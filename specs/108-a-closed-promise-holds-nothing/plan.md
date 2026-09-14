# Implementation Plan: A Closed Promise Holds Nothing

**Branch**: `108-a-closed-promise-holds-nothing` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One argument on the existing release operation so it can join a caller's transaction, two callers
added where a promise stops being open, and one invariant proven from every direction. No schema,
no new operation, no new class.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL
**Storage**: PostgreSQL; **no migration**
**Testing**: pytest, `tests/test_commitment_holds.py` and the revision and closure suites
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: Nothing erased; one release path; what a hold blocks is untouched
**Scale/Scope**: One argument, two call sites, one invariant

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | A hold is Reality the product owns; releasing it when its subject is gone is the product keeping its own records true | PASS |
| Reality owns operational state | The only write is `released_at`, the same field the release operation already sets, through the same operation | PASS |
| Proven schema only | No migration. No field is added | PASS |
| Tenant + shared service boundaries | Every read and write filters `tenant_id`; the release runs inside the caller's transaction | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | The cancellation event names the holds it released, and the release is recorded by the operation that releases holds | PASS |
| Received values not recomputed | Nothing anybody stated is touched. Reason, note, author and creation instant survive a release untouched | PASS |
| Smallest coherent design | Four alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Report the hold instead of releasing it.** Spec 107's shape, and wrong here: the entry would be
  asking a person to tidy up after the product. A hold whose promise is off is not a condition
  somebody should have to clear, it is a record the product should not have left behind.
- **Inline the release in each caller.** Two copies of "set `released_at` and emit the event" is
  how the two copies stop agreeing. The existing operation gains one argument instead, which is
  what `_commit=False` already means everywhere else in this service.
- **Emit `commitment.hold_released` from the cancellation.** It would give the event two producers,
  and the business event catalog declares one per type for exactly that reason. Calling the
  operation keeps the producer honest.
- **Backfill the holds already sitting on closed promises.** A migration that edits a tenant's
  operational records to tidy them is not something this product should do, and there is no way to
  know whether an old hold was left deliberately. They stay, they are reachable from every surface,
  and the specification says so.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py   # one argument, two callers
packages/reality-core/config/operational_exception_catalog.yaml  # Spec 107's guidance corrected
packages/reality-core/tests/test_commitment_holds.py             # the invariant
docs/features/commitment_holds.md, docs/features/operational_exceptions.md
apps/docs/content/catalogs/ (+ de/), docs/SPEC_COVERAGE_MATRIX.md
```

## Design

### Why this is not the thing Spec 107 refused

Spec 107 refused releasing a hold **because time passed**, and the reason still stands: a hold is a
person's statement that they are dealing with something, and the clock does not answer it.

This releases a hold because its **subject is gone**. The promise it was raised against is
cancelled, or the counterparty has said the delivery is complete. There is no execution left to
prevent, so the hold is not a weaker statement — it is a statement about nothing.

The test for the difference is simple and worth keeping: *is anything still being blocked?* Time
passing does not change the answer. A promise closing does.

### The one sequence that reaches a fulfilled promise

`hold_commitment` refuses a promise that is not open, and `require_not_held` refuses every movement
naming a held one. So a held promise cannot be shipped, and cannot become fulfilled by shipping.

Spec 093 decided deliberately that a held promise may still be **revised** — a hold stops
execution, and what the other side says is not execution — and Spec 097 settles a promise as
fulfilled the instant a stated quantity falls to what has already moved. That is the only path,
and it is why the revision site needs the release as much as the cancellation does.

Both of the other two legs are pinned by tests rather than trusted: holding a closed promise is
refused, and shipping a held promise is refused.

### One release path

`release_commitment_hold` gains `_commit: bool = True`, the meaning it already has on a dozen
operations in this service. The two new callers pass `_commit=False`, so the release joins the
transaction that closed the promise: a cancellation that is rolled back releases nothing.

Writing that test corrected a claim in the first draft of this plan. The stale-promise closure
looked like the caller that made the transaction matter — forty promises, forty sets of holds — and
it cannot be, because `_stale_promises` skips a promise with an active hold on purpose. So the
closure never cancels a held one. The property is still worth having for any other caller, and it
is proven by a rollback rather than through a caller that cannot reach it.

The cancellation event names the holds it released, so a reader of the timeline can see the two
facts together. The release itself is still emitted by `release_commitment_hold`, which keeps the
business event catalog's one-producer-per-type rule true.

### What Spec 107's class does now

Nothing changes about its behaviour. Its skip — *a hold on a promise that is not open holds nothing
back* — becomes **true by construction** for anything closed after this ships, and it goes on
correctly ignoring holds left on promises closed before it. Its guidance is corrected to say that,
because the current wording implies the situation is ordinary when it is now legacy.

### Data and migration impact

None. Holds already sitting on closed promises are left where they are, reachable by
`release_commitment_hold` from CLI, Web, API, MCP and Chat.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_commitment_holds.py::test_cancelling_a_promise_releases_its_hold` | the hold stays active |
| FR-002 | service | `test_commitment_holds.py::test_settling_a_promise_by_revision_releases_its_hold` | the hold stays active |
| FR-003 | service | `test_cancelling_a_promise_releases_its_hold` | something was erased |
| FR-004 | service | `test_commitment_holds.py::test_the_release_is_recorded_by_the_release_operation` | no event, or two producers |
| FR-005 | service | `test_cancelling_a_promise_releases_its_hold` | an unheld cancellation changed |
| FR-006 | service | `test_settling_a_promise_by_revision_releases_its_hold` | an open promise lost its hold |
| FR-007 | service | `test_commitment_holds.py::test_a_closed_promise_cannot_be_held` | a closed promise is holdable |
| FR-008 | service | `test_commitment_holds.py::test_a_held_promise_cannot_be_shipped` | a held promise ships |
| FR-009 | service | `test_commitment_holds.py::test_no_closed_promise_carries_an_active_hold` | one direction leaks |
| FR-010 | review | `require_not_held` untouched in the diff | — |
| FR-011 | story | every existing suite, unchanged | an existing behaviour moved |
| DR-001 | review | no migration, no command added | — |
| DR-002 | service | `test_commitment_holds.py::test_the_release_joins_the_caller_s_transaction` and `::test_a_closure_never_cancels_a_held_promise` | a release survives a rollback |
| DR-003 | review | the limit stated; no backfill in the diff | — |
| DR-004 | unit | the docs contract tests over the corrected guidance | stale wording |
| DR-005 | story | the existing isolation suites | — |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no schema. On deploy, holds end sooner; nothing that was possible becomes
impossible. A tenant that holds nothing is unaffected. Rollback restores the previous cancellation
and revision behaviour and leaves the holds released so far released, which is harmless.

The demo month holds nothing and its pinned queue is unchanged.

## Review Risks

- **Automatic release is a behaviour change to two shipped operations.** Anyone relying on a hold
  outliving its promise loses that. The argument is that nothing should rely on it: the hold blocks
  movements against a promise that is off, which is the bug this fixes, and a durable block on a
  counterparty is a party hold.
- **The invariant is proven per path, not enforced by a constraint.** A future operation that closes
  a promise some third way would slip through. A database constraint cannot express it — the
  condition spans two tables and a status — so the honest guard is a named test per path plus the
  invariant test, and a reviewer adding a third path has to add a leg to it.
- **Legacy holds stay.** A tenant that has been running has holds on closed promises that nothing
  reports and nothing tidies. That is deliberate: no migration should edit operational records, and
  no rule can tell a hold left deliberately from one forgotten. It is the largest thing this
  specification does not do.
- **Spec 107's test pinned the old behaviour and had to be inverted.** It asserted that a hold
  survives a cancellation, which was true and is the bug. Inverting it is right; what would have
  been wrong is deleting it, so the legacy state it covered is now reconstructed by hand in the
  same test and the skip keeps its proof.
- **Spec 107's skip loses its original justification.** It said such holds hold nothing back; after
  this, they mostly do not exist. Keeping the skip is right for legacy rows and its wording has to
  change to say so, or the next reader will believe something that is no longer the reason.

## Complexity Tracking

No Constitution exception is claimed. No schema change, no new entity, no new operation, no new
class, no new cause.
