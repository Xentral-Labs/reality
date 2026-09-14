# Implementation Plan: Goods Going Back the Other Way

**Branch**: `090-supplier-returns` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One movement kind, bounded the way a customer return is bounded, able to settle a customer return
the way spec 082 already said something should — and the two classes that compare what went back
to a supplier against what the supplier credited.

No schema. This closes the last gap the 2026-09-05 trading survey found, and it is the half spec
089 named as missing when it shipped.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalogs
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/` and `tests/operational_exceptions/`
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: Decimal quantities; movements are the only truth about stock; tenant scope
**Scale/Scope**: One movement kind, one shared derivation body, two classes, one correction

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The return is a Movement the tenant recorded; every quantity compared comes from a movement or a document line | PASS |
| Reality owns operational state | Nothing gains a status. Stock, fulfilment and both classes are derived from movements as they already are | PASS |
| Proven schema only | No schema change. A movement type is already a free string and `resolves_movement_id` already exists | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; the queue reads the same correction-aware movement quantity the service uses | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Each entry names what went back, what was billed, what was credited and the difference, and traces by identity | PASS |
| Received values not recomputed | Every figure is a recorded quantity or a difference of two of them. Nothing is apportioned or inferred | PASS |
| Smallest coherent design | Four alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Reuse the `return` movement type with a supplier delivery.** The obvious saving and it is
  wrong: `return` requires a location to bring goods *into*, and a supplier return takes them
  *out*. One type would have to infer its own direction from the commitment, which is how a
  movement stops being a plain statement about what physically happened.
- **Record it as a `shipment` against the supplier delivery.** Directionally right and it would
  corrupt fulfilment: `fulfilled_quantity` reads shipments for customer deliveries and receipts
  for supplier ones, and a shipment sitting on a supplier promise would be a figure with two
  meanings.
- **Mirror `return_unresolved` as well.** A customer return sits somewhere waiting for a
  decision, which is the condition that class reports. Goods sent to a supplier are gone. The
  mirror would be a class that can never be true.
- **A third class for goods returned that nobody invoiced.** Deliberately silent instead: the
  company was never charged, so nothing is owed back, exactly as on the selling side.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py               # the movement kind and its guards
packages/reality-core/src/reality/services/exceptions.py         # the shared body, two classes, one correction
packages/reality-core/src/reality/catalogs.py                    # class order
packages/reality-core/config/operational_exception_catalog.yaml  # the classes and their guidance
packages/reality-core/config/command_catalog.yaml                # parameter descriptions
packages/reality-core/src/reality/mcp/catalog.py                 # movement tool schema
docs/features/movements.md, operational_exceptions.md, procure_to_pay.md
apps/docs/content/catalogs/ (+ de/)                               # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                      # specification row
```

## Design

### One movement kind, with the direction it actually has

`supplier_return` joins the movement vocabulary with `(from_location required, to_location not)`
— the opposite of `return`. That vocabulary lives in exactly one place, `_append_movement`, and
nothing outside it enumerates movement types, so adding a kind is a two-line change plus its
guards.

Against a commitment it is allowed only for a `supplier_delivery`, and only for that
commitment's item. What bounds it is what actually arrived less what has already gone back —
never the promise's open quantity, because on a fully received promise that figure is zero and
every return would be refused. That is the identical reasoning the selling side uses, and the
comment there says so; the buying side now says it too.

It does not touch fulfilment. `fulfilled_quantity` reads receipts for a supplier promise, and a
supplier return is not a receipt, so a promise kept when the goods arrived stays kept. The
selling side made the same choice for the same reason.

### The chains meet

Spec 082 let a return name the movement that settles it, and its own description listed "a
shipment to the supplier" as one of the things that settles one. That movement did not exist. It
does now, and the existing settlement rules apply unchanged: the goods must leave the location
the return came back to, and settlements must not exceed what came back.

This is the strongest argument for the feature. The most ordinary resolution of a faulty item —
customer sends it back, company sends it on to the supplier — was the one the model could not
express, and closing it needed no new concept at all.

### Two classes, one body

`_return_exceptions` already produces `returned_not_credited` and `credited_not_returned` from
one body, parameterised by class. It gains two more parameters — which commitment type it walks
and which document type credits it — and produces the buying-side pair from the same code.

`supplier_return_not_credited` reports goods that went back and were not credited, counting only
quantities a supplier invoice actually billed: goods the company was never charged for need no
credit. `supplier_credit_not_returned` reports a credit larger than what went back, and stays
silent where nothing went back at all — which is what keeps a rebate, an allowance or a price
correction out of it, exactly as "keep it" stays out of the selling-side mirror.

One order line still produces at most one of the pair, because the body computes a single
difference and reports whichever direction it falls in.

### One correction to a shipped class

`receipt_unbilled` reports an invoice nobody has sent for goods that arrived. It must count what
the company still holds, or it will keep accruing for goods it sent back. That is exactly the
correction spec 079 made to `shipped_not_billed`, and it gets the mirror of `_kept_quantity`.

`billed_not_received` is deliberately **not** corrected. The goods did arrive; a return does not
unmake a receipt, and subtracting there would report "billed and not received" for goods that
were received and sent back — a false accusation about the supplier's delivery rather than a
true statement about the money.

### Units

The comparison goes through the one comparability rule spec 087 established, so a supplier credit
line in a unit the item cannot reconcile stops the comparison and is reported as
`units_not_comparable` rather than judged here. That class's walk of crediting documents learns
the supplier credit note on the buying side.

### Data and migration impact

None. No column, no revision, no backfill.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_returns.py::test_goods_go_back_to_the_supplier` | the movement kind is unsupported |
| FR-002 | service | `test_goods_go_back_to_the_supplier` | a customer return is accepted instead |
| FR-003 | service | `test_returns.py::test_a_supplier_return_is_refused_without_its_delivery` | a wrong commitment or missing location is accepted |
| FR-004 | service | `test_returns.py::test_a_supplier_return_cannot_exceed_what_arrived` | more than arrived is accepted |
| FR-005 | service | `test_goods_go_back_to_the_supplier` | the promise reopens |
| FR-006 | service | `test_goods_go_back_to_the_supplier` | stock does not fall |
| FR-007 | service | `test_returns.py::test_a_supplier_return_settles_a_customer_return` | the return stays unresolved |
| FR-008 | service | `test_returns.py::test_a_corrected_supplier_return_stops_counting` | a voided movement still counts |
| FR-009 | story | `test_derivation.py::test_supplier_return_not_credited` | class is not derived |
| FR-010 | story | `test_derivation.py::test_supplier_credit_not_returned` | a rebate is reported |
| FR-011 | story | `test_supplier_return_not_credited` | one line produces both |
| FR-012 | story | `test_derivation.py::test_receipt_unbilled_counts_what_is_still_here` | returned goods still accrue |
| FR-013 | story | `test_derivation.py::test_a_return_does_not_unmake_a_receipt` | a return reports as unreceived |
| FR-014 | service | `test_derivation.py::test_the_supplier_return_entries_expose_full_shape` | causal values missing |
| FR-015 | story | `test_derivation.py::test_the_supplier_return_entries_clear_through_reality` | an entry survives its fix |
| FR-016 | service | `test_explanation.py::test_supplier_return_explanation_and_not_found_parity` | identity unknown to explanation |
| FR-017 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-018 | unit | `test_application_catalog.py`, `test_capability_guidance.py` | catalog drift |
| FR-019 | story | `test_derivation.py::test_an_unreconcilable_supplier_credit_is_reported_not_judged` | an incomparable pair is judged |
| FR-020 | story | `test_derivation.py::test_the_supplier_return_entries_order_deterministically` | order varies between reads |
| FR-021 | story | every existing suite, unchanged | an existing behaviour moves |
| DR-001 | review | no file under `migrations/versions/` is added | — |
| DR-002 | story | `test_the_supplier_return_entries_clear_through_reality` | something persists |
| DR-003 | unit | `test_derivation.py::test_both_return_directions_share_one_body` | a second body appears |
| DR-004 | service | `test_the_supplier_return_entries_expose_full_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_the_supplier_return_classes_are_tenant_scoped` | another tenant is read |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |
| DR-007 | service | `test_goods_go_back_to_the_supplier` | a figure was inferred |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and nothing stored changes. Rollback is a plain revert.

One shipped class changes behaviour: `receipt_unbilled` stops counting goods that went back.
That can only differ for a tenant that has recorded a supplier return, and no tenant can have,
because the movement kind did not exist. The change is therefore invisible on deploy and correct
from the first return anybody records.

The demo month records no supplier return and will not change.

## Review Risks

- **`billed_not_received` is deliberately left alone and somebody will read that as an
  oversight.** The argument is in the design above and in the class's own guidance: the goods
  arrived, and subtracting returns there would accuse a supplier of not delivering something it
  delivered. If a reviewer disagrees, the thing to argue is FR-013.
- **A new movement kind is a new physical fact and those are hard to take back.** It is the
  smallest one that could work: no schema, no new reference, and it reuses the settlement rules
  spec 082 already wrote. But a movement vocabulary is a contract with every integration that
  will ever write one.
- **The uncredited class waits for the supplier's invoice.** Goods returned before the invoice
  arrives are reported as nothing until it does. That is the same order of events the selling
  side assumes, and it is still a window in which the queue says less than an operator might
  want.
- **Four class pairs now mirror each other across the two sides.** Every one of them shares a
  body, and each pair's separation is asserted by a test. The risk is the next change made to one
  side only, and the mitigation is structural rather than a promise to be careful.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
