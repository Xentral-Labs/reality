# Implementation Plan: Long by This Company's Own Standard

**Branch**: `080-learned-lag` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One shape of rule, applied twice: measure how long this tenant normally takes, and report
what has taken far longer. No schema, no configuration, and no new vocabulary — the second
and third uses of the idea Spec 072 introduced for a source that stopped delivering.

The catalog goes from seventeen classes to nineteen, and the largest blind spot in consumer
trade — an order nobody dated and nobody shipped — becomes visible for the first time.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/operational_exceptions/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: Decimal quantities; UTC instants; opaque IDs; strict tenant scope
**Scale/Scope**: One learned-norm helper, two derivations, eight product constants

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Both read Reality the tenant owns — promises, movements and the lines they hang off — and trace to them by opaque identity | PASS |
| Reality owns operational state | Nothing gains a status and no norm is stored. Both entries and both norms are derived per read | PASS |
| Proven schema only | No schema change. Every instant both rules need already exists: `Commitment.created_at`, `Movement.occurred_at`, and the document date | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`, including the two that learn the norms — a norm learned across tenants would be a leak, and is tested as one | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Each entry returns how long it has stood, the norm and the threshold, so an operator can see why this one and not that one | PASS |
| Received values not recomputed | Nothing here is a value a source stated. Both figures are observations over instants that were recorded, computed at read time and stored nowhere, which principle VIII allows explicitly | PASS |
| Smallest coherent design | Three alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **A configured threshold per tenant.** Obvious, and the thing Spec 072 refused for good
  reason: a number somebody types once is wrong within a quarter and nobody revisits it, and
  it makes the product's first setting a number nobody can justify. A learned norm describes
  what the business does rather than what somebody once thought it should.
- **The longest lag observed, as Spec 072 uses.** Right for a source, whose pauses are
  bounded by nights and weekends, and wrong here: an order's lag has no upper bound, so one
  eight-month order would silence the class forever. The bound is what makes the longest safe
  there and unsafe here.
- **A fixed number of days for everybody.** Simplest of all and defensible for one business.
  A wholesaler shipping in a week and a shop shipping in an hour cannot share it, and the
  first tenant it does not suit would ask for a setting — which is the alternative already
  rejected.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/exceptions.py         # the norm helper, two derivations, registry, order
packages/reality-core/src/reality/catalogs.py                    # class order
packages/reality-core/config/operational_exception_catalog.yaml  # two classes and guidance
packages/reality-core/tests/operational_exceptions/              # norm, derivation and explanation proof
docs/features/operational_exceptions.md                          # taxonomy rows and the learned-norm rule
apps/docs/content/catalogs/exceptions.md (+ de/)                  # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                     # specification row
```

**Files/layers affected**: the exception service and the catalog. No model, no migration, no
transport, no frontend.

## Design

### The learned norm

One helper takes a list of completed lags and returns a threshold, or nothing. It sorts the
most recent cases, takes the median, multiplies by the factor, and applies the floor — and
returns nothing at all where there are fewer cases than the minimum.

Returning nothing rather than a large number matters: a tenant without history is not a
tenant with a lenient threshold, it is a tenant this rule cannot speak about, and the
difference has to be visible to the caller rather than hidden inside an arithmetic.

The constants are product decisions identical for every tenant, recorded beside the code with
their reasoning as Spec 072's four are:

| Constant | Fulfilment | Billing | Why |
|---|---|---|---|
| History | 20 most recent | 20 most recent | Enough to describe a business, short enough to follow it when it changes |
| Minimum | 5 | 5 | Below this a median is a guess, and silence beats a guess |
| Factor | 3 | 3 | Two is inside normal variation; three is a business saying something is wrong |
| Floor | 7 days | 14 days | A week is the shortest span in which an unshipped order means anything; a supplier invoice inside a fortnight is ordinary |

The two floors differ because the businesses do, which is also why the norms are learned
separately rather than shared.

### Order stalled

`order_stalled` walks open customer-delivery promises that carry **no** due date and have
quantity outstanding, and reports those older than the fulfilment threshold. Excluding dated
promises makes it disjoint from `overdue_outgoing_customer_commitment` by construction rather
than by a precedence rule, which is the cheaper kind of disjointness to keep true.

The norm is learned from promises that finished: created to last shipment, over promises with
nothing outstanding. Unfinished promises are excluded deliberately — a backlog must not be
allowed to raise the bar that measures the backlog. A cancelled promise is excluded from both
sides: it will never ship, so reporting it would name something nobody is waiting for, and
learning from it would teach a lag that never happened.

The carrier is the Commitment, beside the other delivery classes.

### Receipt unbilled

`receipt_unbilled` walks purchase order lines with goods received and an unbilled remainder,
and reports those whose last receipt is older than the billing threshold. It is the class
Spec 076 deliberately left out, and time is the only thing that was missing.

The norm is learned from lines that were billed: last receipt to the first billing document's
date. Where a document states no readable date, the case is skipped rather than guessed at.

A pair recorded in different units is left alone rather than converted, which is the rule
every other class comparing a received quantity with a billed one already applies.

The carrier is the order line, beside `billed_not_received`.

### Negative lags

A shipment recorded as having occurred before its promise existed is possible — a backdated
`occurred_at` is accepted by the write path. Such a lag is clamped to zero rather than
recorded as negative, so one backdated record cannot drag a median below nothing.

### Identity, ordering and guidance

Identities are `exc__order_stalled__{commitment_id}` and
`exc__receipt_unbilled__{order_line_id}`. Both sort beside the classes they neighbour, and
each entry sorts on the instant its condition started, so the longest-standing comes first.

Spec 071's cross-reference rule applies. `order_stalled` and
`overdue_outgoing_customer_commitment` are the two ways a delivery goes wrong and must name
each other — one has a date and missed it, the other never had one. `receipt_unbilled` and
`billed_not_received` are opposite directions of the same pair of records.

### Data and migration impact

None. No column, no revision, no backfill, and nothing stored — including the norms.

### Failure, security, and tenant behavior

Every query filters `tenant_id`, and that includes the two that learn the norms: a norm
learned across tenants would leak one company's speed into another's queue, which is tested
explicitly rather than assumed.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `test_derivation.py::test_the_fulfilment_norm_describes_this_tenant` | no norm is derived |
| FR-002 | unit | `test_derivation.py::test_the_billing_norm_describes_this_tenant` | no norm is derived |
| FR-003 | unit | `test_derivation.py::test_one_slow_case_does_not_move_the_norm` | an outlier moves it |
| FR-004 | story | `test_derivation.py::test_a_young_tenant_is_never_judged` | a norm is claimed from three cases |
| FR-005 | story | `test_derivation.py::test_order_stalled` | class is not derived |
| FR-006 | story | `test_derivation.py::test_a_dated_promise_is_left_to_the_overdue_class` | a dated promise is reported twice |
| FR-007 | story | `test_derivation.py::test_receipt_unbilled` | class is not derived |
| FR-005a | story | `test_derivation.py::test_a_cancelled_promise_is_neither_reported_nor_learned_from` | a cancelled promise is reported |
| FR-007a | story | `test_derivation.py::test_lag_classes_ignore_mismatched_units` | boxes compared with pieces |
| FR-008 | story | `test_derivation.py::test_a_fast_tenant_is_not_reported_at_once` | the floor is ignored |
| FR-009 | service | `test_derivation.py::test_lag_classes_expose_full_entry_shape` | causal values missing |
| FR-010 | service | `test_lag_classes_expose_full_entry_shape` | trace keys missing |
| FR-011 | story | `test_derivation.py::test_lag_classes_clear_through_reality` | entries persist after shipping |
| FR-012 | service | `test_explanation.py::test_lag_classes_explanation_and_not_found_parity` | identities unknown to explanation |
| FR-013 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-014 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| FR-015 | story | `test_derivation.py::test_lag_classes_order_longest_first` | order varies between reads |
| FR-016 | unit | `test_derivation.py::test_a_backdated_shipment_cannot_drag_the_norm` | the median goes negative |
| DR-001 | review | no file under `migrations/versions/` is added | — |
| DR-002 | story | `test_lag_classes_clear_through_reality` | something persists |
| DR-003 | unit | `test_derivation.py::test_lag_classes_use_the_shared_movement_quantity` | a second count appears |
| DR-004 | service | `test_lag_classes_expose_full_entry_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_norms_are_learned_per_tenant` | one tenant's speed judges another |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |
| DR-007 | review | the constants and their reasoning, read as a reviewer | — |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no stored values. Rollback is a plain revert.

The first-read volume matters more here than for any class so far, and in one specific way: a
tenant that has been running a while and never shipped a backlog will see all of it at once,
correctly. The measurement should report the number on the demo month rather than assert it
is small, and should say what a real backlog would look like.

## Review Risks

- **The median describes a bimodal business badly.** A tenant with express orders shipped in
  an hour and special orders shipped in a month has a median that describes neither, and the
  class will either shout about special orders or stay silent about express ones. This is the
  most likely way the rule is wrong in practice, and the thing to revisit is the statistic,
  not the idea.
- **Eight constants, none of them measured.** The factor of three and both floors are
  judgements made without a real tenant to check them against. They are recorded as product
  decisions with reasoning, which is honest, and they are still guesses.
- **A norm that moves under the condition.** Because the norm is recomputed per read, a
  tenant that gets slower makes its own threshold rise, and a stalled order can clear itself
  without anything shipping. That is intended — the class asks "is this unusual here" and the
  answer genuinely changes — but it will surprise somebody, and the guidance has to say so.
- **The second class overlaps a deliberate non-goal.** Spec 076 said receipts without
  invoices are ordinary. This says they stop being ordinary. Both are true and the boundary
  is a constant, so a reviewer should be satisfied the boundary sits somewhere defensible.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
