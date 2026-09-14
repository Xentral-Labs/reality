# Implementation Plan: A Return May Say What It Reverses

**Branch**: `079-returns-connect` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Two guards in the write path, one correction to a class that ships today, and the two classes
the connection makes derivable. No schema: the Commitment link on a Movement and the
billed-line reference on a DocumentLine both exist and are both unusable for a return.

The catalog goes from fifteen classes to seventeen. One live wrong signal disappears and one
class stops over-reporting.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/operational_exceptions/` and `tests/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: Decimal quantities; opaque IDs; strict tenant scope
**Scale/Scope**: Two write-path guards, one corrected derivation, two new classes

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | A return becomes Reality that names the promise it reverses; a credit note line is Evidence naming the agreed line it credits. Both traces reach documents, lines and the SourceRecord by opaque identity | PASS |
| Reality owns operational state | Nothing gains a status. Whether goods have come back is derived from movements per read, and no document or commitment records a return state | PASS |
| Proven schema only | No schema change at all. Both links exist; the feature is that a return is allowed to use them | PASS |
| Tenant + shared service boundaries | Validation and every derivation filter `tenant_id`; returned and delivered quantities come from the existing shared movement path | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Each entry returns the two quantities it compares and their difference, and a return that used to be unexplainable now names its promise | PASS |
| Received values not recomputed | Every quantity compared was stated by somebody: on the order line, on the movement, on the credit note line. The classes add movements and lines up at read time and store nothing | PASS |
| Smallest coherent design | Three alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **A third Commitment type for returns.** It would let a declared return be late, which is
  a real condition. It is also a new promise vocabulary, a new lifecycle and a new set of
  classes, and none of it is needed to answer "how much came back and was it credited". Named
  as a non-goal so the next feature can take it.
- **Point the credit note line at the invoice line it credits.** One hop closer to the
  money and one grain away from everything else: the movements, the billing and the
  agreement all hang off the order line, and a second grain would mean two different joins
  for one question. Rejected on the same ground Spec 076 chose the order line.
- **Subtract returns from fulfilment and change nothing else.** Smallest possible change and
  wrong: a kept promise would reopen as overdue, and a fully returned order would look
  undelivered. Fulfilment answers whether the company kept its word, which a return does not
  undo.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py               # two write-path guards
packages/reality-core/src/reality/services/exceptions.py         # netting, two derivations, registry, order
packages/reality-core/src/reality/catalogs.py                    # class order
packages/reality-core/config/operational_exception_catalog.yaml  # two classes and guidance
packages/reality-core/tests/                                     # write path, derivation and explanation proof
docs/features/movements.md                                       # a return may name its delivery
docs/features/operational_exceptions.md                          # taxonomy rows
apps/docs/content/catalogs/exceptions.md (+ de/)                  # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                     # specification row
```

**Files/layers affected**: one service validation, the exception service and the catalog. No
model, no migration, no transport, no frontend.

## Design

### The two guards

`record_movement` today computes one expected movement type per commitment type and refuses
anything else, then refuses a quantity above the commitment's open quantity. Both need to
know about returns, and each for its own reason.

A `return` is accepted against a `customer_delivery` commitment and refused against a
`supplier_delivery` one. Goods going back to a supplier are the mirror flow with a different
document and a different owner, and letting them share this path would mean one condition
reporting two different business situations.

The open-quantity check does not apply to a return, because a return is not fulfilment: on a
fully shipped commitment the open quantity is zero and every return would be refused. What
replaces it is the true constraint — a return may not exceed what actually went out against
that commitment. That is the same shape as the existing rule, measured against the right
figure.

### Fulfilment stays untouched

`fulfilled_quantity` keeps counting shipments alone. This is the decision the feature turns
on, and it is deliberately not the obvious one: subtracting returns there would reopen a kept
promise as overdue and make a returned order look undelivered. The promise was kept when the
goods went out.

What changes is `shipped_not_billed`, which asks a different question — how much did the
customer keep — and must therefore subtract returns. That is a correction to a class that
ships today, and it is why this feature carries a test for a class it does not introduce.

### The credit reference

A credit note line uses the `billed_document_line_id` Spec 076 added, pointing at the order
line it credits. `_pricing_direction` learns that `credit_note` is a sales-side document, so
the existing validation accepts a credit note line against a sales order line and refuses one
against a purchase order line without any new rule being written.

Everything then hangs off the order line: its Commitment carries shipments and returns,
invoice lines bill it, credit note lines credit it. The two new classes are the invoicing
comparison with different inputs.

### The two derivations

`returned_not_credited` walks customer-delivery promises, takes the returned quantity through
the Commitment's movements, and compares it with what credit note lines credit against the
order line. What it reports is not the whole return: goods that no invoice line ever billed
need no credit, because the company never charged for them. The reportable quantity is
therefore the part of the return that was billed, less what has been credited. A line with
nothing returned says nothing.

The two return classes are opposite directions of one difference, so one order line produces
at most one of them — the same discipline the overdue and at-risk commitment classes keep.

`credited_not_returned` reports the opposite excess and only where some quantity has come
back. A credit with no return at all is a policy decision — "keep it" is ordinary in consumer
trade — and reporting it would make the class noise in exactly the businesses that return
most.

Both skip a pair recorded in different units, as the invoicing classes do.

### One correction-aware quantity

The service layer's `fulfilled_quantity` subtracts movements a correction has voided. The
exception module's own helper does not, so the queue and the service disagree about how much
was delivered the moment anything is corrected — and `shipped_not_billed`, which ships today,
reports a voided shipment as delivered and unbilled.

That is a second live defect alongside the returns one, with the same root: two helpers
counting one thing. Both move onto one correction-aware helper in the service layer,
parameterised by movement type so it serves shipments, receipts and returns alike. The
exception module then has no quantity path of its own.

### Identity, ordering and guidance

Identities are `exc__returned_not_credited__{order_line_id}` and
`exc__credited_not_returned__{order_line_id}`. Both sort beside the invoicing classes,
because they are the same comparison about the same line.

Spec 071's cross-reference rule applies. `returned_not_credited` and `shipped_not_billed` are
the two sides of one line's life and must name each other; `credited_not_returned` and
`billed_not_received` are mirror images across the two directions of goods and money.

### Data and migration impact

None. No column, no revision, no backfill. Returns already recorded without a commitment stay
as they are and keep being reported as unexplained, which is what they are.

### Failure, security, and tenant behavior

Both refusals happen at the point of recording with a message naming what is wrong. Every
derivation filters `tenant_id`. Explanation re-derives, so cleared identities produce the
existing `NotFound`.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `tests/test_movements.py::test_a_return_may_name_the_delivery_it_reverses` | the movement is refused |
| FR-002 | unit | `test_a_return_may_name_the_delivery_it_reverses` | a supplier promise accepts a return |
| FR-003 | unit | `tests/test_movements.py::test_a_return_may_not_exceed_what_went_out` | over-return accepted |
| FR-004 | unit | `tests/test_movements.py::test_a_return_leaves_the_promise_kept` | fulfilment drops |
| FR-005 | unit | `tests/test_documents.py::test_a_credit_note_line_credits_an_order_line` | the reference is refused |
| FR-006 | story | `test_derivation.py::test_returned_goods_are_not_reported_as_unbilled` | returned goods stay reported |
| FR-007 | story | `test_derivation.py::test_returned_not_credited` | class is not derived |
| FR-008 | story | `test_derivation.py::test_credited_not_returned` | class is not derived |
| FR-009 | story | `test_derivation.py::test_crediting_sums_across_credit_notes` | a second line is ignored |
| FR-010 | story | `test_derivation.py::test_return_classes_ignore_mismatched_units` | boxes compared with pieces |
| FR-011 | unit | `test_derivation.py::test_one_returned_quantity_path` | the movement sum is computed twice |
| FR-011a | story | `test_derivation.py::test_a_voided_movement_stops_counting` | a voided shipment is still reported |
| FR-007a | story | `test_derivation.py::test_goods_that_were_never_billed_need_no_credit` | an unbilled return is reported |
| FR-008a | story | `test_derivation.py::test_one_line_produces_at_most_one_return_entry` | both classes fire together |
| FR-012 | service | `test_derivation.py::test_return_classes_expose_full_entry_shape` | causal values missing |
| FR-013 | service | `test_return_classes_expose_full_entry_shape` | trace keys missing |
| FR-014 | story | `test_derivation.py::test_return_classes_clear_through_reality` | entries persist after crediting |
| FR-015 | service | `test_explanation.py::test_return_classes_explanation_and_not_found_parity` | identities unknown to explanation |
| FR-016 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-017 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| FR-018 | story | `test_derivation.py::test_return_classes_order_longest_first` | order varies between reads |
| DR-001 | review | no file under `migrations/versions/` is added | — |
| DR-002 | story | `test_return_classes_clear_through_reality` | derivation is not read-time |
| DR-003 | unit | `test_one_returned_quantity_path` | a second quantity path appears |
| DR-004 | unit | `test_a_return_leaves_the_promise_kept` | state is written |
| DR-005 | service | `test_return_classes_expose_full_entry_shape` | trace restates business fields |
| DR-006 | story | `test_derivation.py::test_return_classes_are_tenant_scoped` | cross-tenant rows leak |
| DR-007 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |
| DR-008 | story | `tests/test_movements.py::test_a_returned_movement_is_still_correctable` | correction rejects a return |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no stored value changes. Rollback is a plain revert, after which returns
carrying a commitment would be refused again — but none exist today, so nothing is stranded.

The demo month changes, and deliberately. Its return on day 18 is recorded without a
commitment and will keep being reported as unexplained until the demo is updated to name the
delivery. Whether to update it is a decision about the demo story, and
`test_the_month_ends_with_exactly_these_exceptions` forces it to be made rather than drift.

## Review Risks

- **The fulfilment decision is invisible in the code.** Nothing in `fulfilled_quantity`
  says "returns are deliberately not subtracted here", and the next reader looking at a
  returned order that still counts as delivered will read it as a bug. The reason has to live
  next to the code, not only in this plan.
- **Two guards in one condition.** `record_movement`'s commitment check is already dense, and
  this adds a second exception to it. A reviewer should judge whether the guard is still
  readable or whether it now needs a named helper.
- **Absence as a statement, a second time.** `returned_not_credited` concludes from a missing
  credit reference exactly as `shipped_not_billed` concludes from a missing billing reference,
  and rests on the same contract: every crediting line sets it. The assumption is now load
  bearing in two places.
- **A correction fix rides along.** FR-011a repairs a divergence that predates this
  feature and touches `shipped_not_billed`, a class outside its scope. Bundling it is
  defensible because returns cannot be counted correctly without it and because leaving one
  helper correction-blind while adding a second would double the defect — but a reviewer is
  entitled to ask for it as its own change.
- **`credited_not_returned` may be the wrong rule.** Requiring some return before reporting is
  a judgement about consumer trade. A B2B wholesaler who never credits without a return would
  want the stricter rule and will not get it. That is a rule to revisit with a real business,
  not a model change.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
