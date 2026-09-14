# Implementation Plan: Close What Is Never Coming

**Branch**: `085-close-stale-promises` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Two operations — preview and close — over promises a person has selected and counted. No
schema, no exception class, no new vocabulary. The first feature in this line of work that adds
a way *out* of the queue rather than another way in.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/`
**Project Type**: backend service consumed by Web, MCP, and Chat adapters
**Constraints**: Decimal quantities; opaque IDs; strict tenant scope; atomic mutation
**Scale/Scope**: Two operations, two transports, no derivation

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Only Reality changes. A cancelled promise is an obligation the company withdraws; no Document or SourceRecord is rewritten, so nothing claims a source said something it did not | PASS |
| Reality owns operational state | Cancellation is the operational state Reality already owns, and this feature performs it many times rather than differently | PASS |
| Proven schema only | No schema change. Cancellation, reservation release and the business event record all exist | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; the closure calls the existing shared cancellation rather than writing status itself | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Nothing closes that has not been previewed and counted, and the act itself is a record naming the criteria, the reason and the number | PASS |
| Received values not recomputed | No value a source stated is touched. The count is an observation over what matches, taken twice and required to agree | PASS |
| Smallest coherent design | Four alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **One call that closes everything matching.** Half the code and the wrong product: a bulk
  mutation nobody has looked at is exactly what this repository refuses everywhere else, and
  the set can change between deciding and acting.
- **Close by an explicit list of identities.** Safest of all and useless at the scale that
  creates the problem — nobody pastes four thousand identities — while adding no safety the
  confirmed count does not already give.
- **Let Reality decide what is dead** from age, absence of movement and a heuristic. It would
  close the backlog of a company that is still working it, and no wording in a confirmation
  dialog makes that acceptable.
- **Close the documents too.** Tempting because the queue is full of them, and wrong: a
  document is what a source said, and rewriting it would be a claim about the past rather than
  a decision about the future.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py           # preview and close
packages/reality-core/src/reality/web/api.py                 # two endpoints
packages/reality-core/src/reality/mcp/catalog.py             # two agent tools
packages/reality-core/src/reality/tools/application.py       # the tool handlers
packages/reality-core/config/command_catalog.yaml            # the commands and parameters
packages/reality-core/config/tenant_isolation_catalog.yaml   # the new public operations
packages/reality-core/tests/test_stale_promises.py           # the proof
docs/features/commitments.md                                 # closing many at once
docs/SPEC_COVERAGE_MATRIX.md                                 # specification and evidence rows
```

## Design

### What matches

One selection, used by both operations, so the preview and the closure can never disagree:
open customer-delivery or supplier-delivery commitments, with a due date before the stated one,
with nothing moved against them.

"Nothing moved" is read through the existing correction-aware movement quantity, so a shipment
recorded in error and voided does not protect a promise that never actually saw goods.

A promise under a hold never matches, and neither does one whose party is under a delivery
hold. A hold is somebody saying they are dealing with this promise; a bulk closure that
overruled it would be doing the one thing this operation exists to avoid.

A promise with no due date never matches. It is not residue with an old date; it is the
condition Spec 080 judges against how long this company normally takes, and closing those in
bulk would need a rule nobody has stated.

### Preview

Returns the count, the quantity that would be released from active reservations, and a bounded
sample of promises. The sample exists so a person recognises what they are about to close; the
count exists so they can confirm it. Writing nothing is a requirement rather than an
implementation detail, and is tested as one.

### Closing

Takes the criteria again, the count the caller saw, and a reason. It re-runs the selection and
refuses unless the count still matches exactly — the same shape as the document correction
path's `expected_revision`, and for the same reason: what you looked at may not be what is
there.

It then cancels each promise **through `cancel_commitment`**, rather than writing status
itself. Cancelling releases reservations and emits an event, and a second implementation of
that would drift within a release.

One further event records the act: the criteria, the reason, the count, and the actor. In a
year that sentence is the only thing that will explain why four thousand promises closed on one
afternoon.

The whole closure is one transaction. Half a wall is worse than a wall.

### Reachability

Two endpoints and two agent tools, the closing one confirmation-required like every other
mutating tool. An operation that exists only in code is the defect Spec 084 was written to fix,
and this feature does not repeat it.

### Data and migration impact

None. No column, no revision, no backfill.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `tests/test_stale_promises.py::test_the_preview_states_what_would_close` | the operation does not exist |
| FR-002 | unit | `test_the_preview_states_what_would_close` | the date and side are ignored |
| FR-003 | unit | `tests/test_stale_promises.py::test_a_promise_with_movement_is_never_closed` | a partly shipped promise closes |
| FR-004 | unit | `tests/test_stale_promises.py::test_only_open_dated_promises_match` | a cancelled promise matches |
| FR-004a | unit | `tests/test_stale_promises.py::test_a_held_promise_is_never_closed` | a held promise closes |
| FR-005 | unit | `test_only_open_dated_promises_match` | a dateless promise matches |
| FR-006 | unit | `tests/test_stale_promises.py::test_a_stale_count_refuses_the_closure` | a changed set closes anyway |
| FR-007 | unit | `tests/test_stale_promises.py::test_a_closure_requires_a_reason` | it closes without one |
| FR-008 | story | `tests/test_stale_promises.py::test_closing_clears_the_wall` | promises stay open |
| FR-009 | unit | `tests/test_stale_promises.py::test_the_act_is_recorded_once` | nothing records the act |
| FR-010 | adapter | endpoint test in `tests/test_master_data_api.py`; tool assertion in `tests/test_application_catalog.py` | neither surface offers them |
| FR-011 | story | `test_closing_clears_the_wall` | documents change |
| FR-012 | unit | `test_a_stale_count_refuses_the_closure` | a partial closure is left behind |
| FR-013 | unit | `tests/test_stale_promises.py::test_closing_nothing_is_not_a_failure` | an empty closure raises |
| DR-001 | review | no file under `migrations/versions/` is added | — |
| DR-002 | story | `tests/test_stale_promises.py::test_a_closure_is_tenant_scoped` | another tenant's promises close |
| DR-003 | unit | `tests/test_stale_promises.py::test_the_preview_writes_nothing` | the preview mutates |
| DR-004 | unit | `test_closing_clears_the_wall` | status is written directly |
| DR-005 | unit | `test_the_act_is_recorded_once` | the record restates business fields |
| DR-006 | unit | the catalog class count, unchanged | a class is added |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no stored value changes. Rollback is a plain revert; promises already closed
stay closed, which is what cancelling means.

The demo month has no stale promises and will not change.
`test_the_month_ends_with_exactly_these_exceptions` will say so.

## Review Risks

- **This is the only destructive operation in the product.** Everything else appends or
  derives. The safety is a preview, a confirmed count, a required reason and a transaction, and
  a reviewer should judge whether that is enough for an act that cannot be undone.
- **"Nothing moved" is the whole safety rule for work in progress.** A company that records
  movements outside Reality — the exact company most likely to arrive with an import — has
  promises that look untouched and are not. The preview is what stands between them and a
  mistake, which is why the sample exists and why the count must be confirmed.
- **The criteria are deliberately poor.** Side and a date, nothing else. A richer selection
  would be more useful and would also make it easy to close something nobody intended, and the
  narrow version can be widened later on evidence.
- **A due date in the future is allowed.** "Due before tomorrow" would sweep today's orders,
  and nothing refuses it: the operator sees the count and confirms it. Refusing future dates
  would be Reality deciding what a person may mean, which this feature declines to do
  everywhere else. It is still a foot-gun, and the preview is the only thing between it and a
  mistake.
- **A closure is not reversible.** Reopening was considered and rejected as a non-goal, so an
  operator who closes the wrong four thousand has no way back inside the product.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
