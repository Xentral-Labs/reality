# Implementation Plan: Invoice Lines Know What They Bill

**Branch**: `076-invoice-order-link` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One nullable column on `document_line`, the validation that keeps it honest, and the three
classes it makes derivable. This is the first schema change in this line of work, and the
three classes are what proves it: none of them can exist without the reference, and the
reference is worth nothing without them.

The quantity comparisons reuse the path that already runs from an order line through its
Commitment to its Movements. Nothing in the financial flow changes.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; one nullable self-referencing column on `document_line`
**Testing**: pytest business stories under `tests/operational_exceptions/` and `tests/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: Decimal quantities and prices; opaque IDs; strict tenant scope
**Scale/Scope**: One column, one validation, three classes, no new cause

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The reference is Evidence about Evidence: which agreed line a billed line settles. Quantities still come from Reality through the Commitment; the trace reaches both lines, their documents and the SourceRecord by opaque identity | PASS |
| Reality owns operational state | The reference records what was billed, not a status. No document or line gains a state field, and all three classes are derived per read | PASS |
| Proven schema only | The column exists solely to make three named conditions derivable, and all three ship with it. Without it none of them can be expressed at all — the header alternative was rejected on consolidated invoicing | PASS |
| Tenant + shared service boundaries | Validation and every derivation filter `tenant_id`; the quantity path is the existing shared one | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Each entry returns the two figures it compares and their difference, so a judgement can be checked rather than believed | PASS |
| Received values not recomputed | Every figure compared here was stated by somebody: the quantity on an order line, the quantity on a movement, the price on an invoice. The classes add up movements and invoice lines at read time and store nothing, which principle VIII allows explicitly — and comparing two received values is what it encourages | PASS |
| Smallest coherent design | Three alternatives rejected below, including the smaller header reference | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **A header reference from an invoice to an order.** Smaller and wrong: it cannot express a
  consolidated invoice over several orders, which is ordinary B2B billing, and it cannot say
  how much of an order is billed, which is the whole question when deliveries are partial.
- **A many-to-many relation at header level.** Expresses consolidation and still cannot
  answer "how much", so two of the three conditions remain underivable.
- **Matching invoices to orders by party, item and date window.** No schema at all, and
  rejected for the reason this line of work has hit repeatedly: an exception that is
  sometimes wrong is worse than none.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/db/core.py               # the column
packages/reality-core/migrations/versions/0037_*.py        # its revision
packages/reality-core/src/reality/services/core.py         # validation on record and correct
packages/reality-core/src/reality/web/api.py               # the field on the line write model
packages/reality-core/src/reality/services/exceptions.py   # three derivations, registry, order
packages/reality-core/src/reality/catalogs.py              # class order
packages/reality-core/config/operational_exception_catalog.yaml  # three classes and guidance
packages/reality-core/tests/                               # migration, validation and derivation proof
docs/DATA_MODEL.md                                          # the new relationship
docs/features/operational_exceptions.md                     # taxonomy rows
apps/docs/content/catalogs/exceptions.md (+ de/)            # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                # spec and evidence rows
```

**Files/layers affected**: model, migration, one service validation, one transport field,
and the exception service. No frontend change: recording the reference is an API field, and
the queue row contract is untouched.

## Design

### The column

`document_line` gains `billed_document_line_id`, a nullable self-referencing foreign key to
`document_line.id`. Nullable is the design, not a concession: an invoice line may bill
something no order promised — freight, a one-off service, a rounding line — and `null` says
exactly that.

The revision is `0037_invoice_order_link`, following `0036_erp_interpretation_rules`. It
adds one column and nothing else, so downgrade drops it and no data moves in either
direction.

### Validation

The reference is checked where a line is recorded and where it is corrected. It must point
at a line of the same tenant, on a document of type `sales_order` or `purchase_order`, and
on the matching side: a `sales_invoice` line may bill only a `sales_order` line, a
`supplier_invoice` line only a `purchase_order` line. Anything else is refused rather than
stored and later ignored, because a wrong reference would produce a confidently wrong
exception.

### The three derivations

All three start from an order line and use one shared helper for the quantity billed against
it — the sum over every invoice line that references it, which is what makes consolidated
and partial invoicing work without special handling.

Both quantity classes consider only order lines that carry a Commitment. A freight,
discount or service line promises no goods and can never be received, so reporting it for
failing to arrive would flag an ordinary supplier invoice. For the same reason a comparison
is made only between lines recorded in the same unit: converting would guess and not
converting would be wrong, so a mismatched pair is left alone.

`shipped_not_billed` walks sales order lines, takes the delivered quantity through the
line's Commitment and its Movements, and reports the excess over the billed quantity. A
line with nothing delivered says nothing, whatever has been billed.

`billed_not_received` walks purchase order lines and reports the opposite excess: billed
beyond received. The two are not two directions of one comparison but the same comparison on
opposite sides of the business, and the other two cells of that square are ordinary —
prepayment on the sales side, an invoice still to come on the purchase side.

`invoice_price_differs` walks invoice lines that carry a reference and compares the unit
price with the agreed price on the line they bill. It is the only one of the three whose
carrier is the billed line rather than the agreed one, because the wrong figure is on the
invoice.

Delivered and received quantities come from the existing path, not a second count. That path
is the one the commitment classes already use, so a quantity is never derived two ways.

### Identity, ordering and guidance

Identities are `exc__shipped_not_billed__{order_line_id}`,
`exc__billed_not_received__{order_line_id}` and
`exc__invoice_price_differs__{invoice_line_id}`. `document_line` becomes the eighth record
type. The three sort next to the commitment classes, because that is where an order line
belongs, and each entry sorts on the most recent movement or on the invoice date.

Spec 071's cross-reference rule applies: `shipped_not_billed` and `billed_not_received` are
mirror images across the two sides and must name each other, and both should point at the
price class as the third thing that can be wrong about the same pair of lines.

### Data and migration impact

One nullable column, one Alembic revision, no backfill. There is no production data, which
is what allows the first class to read absence as a statement rather than as ignorance —
recorded in the specification as the assumption it is.

### Failure, security, and tenant behavior

Validation refuses a cross-tenant, non-order or wrong-side reference at the point of
recording. Every derivation filters `tenant_id`. Explanation re-derives, so cleared
identities produce the existing `NotFound`.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `tests/test_documents.py::test_invoice_line_records_the_order_line_it_bills` | column does not exist |
| FR-002 | unit | `tests/test_documents.py::test_invoice_line_reference_is_validated` | cross-tenant, non-order and wrong-side references are accepted |
| FR-003 | story | `test_derivation.py::test_shipped_not_billed` | absent reference is treated as unknown |
| FR-004 | story | `test_derivation.py::test_shipped_not_billed` | class is not derived |
| FR-005 | story | `test_derivation.py::test_billed_not_received` | class is not derived |
| FR-005a | story | `test_derivation.py::test_non_deliverable_lines_are_never_reported` | a freight line is reported as never received |
| FR-007a | story | `test_derivation.py::test_mismatched_units_are_not_compared` | boxes are compared with pieces |
| FR-015 | service | `test_derivation.py::test_line_classes_order_longest_first` | order constants lack the ids |
| FR-006 | story | `test_derivation.py::test_invoice_price_differs` | class is not derived |
| FR-007 | story | `test_derivation.py::test_billing_sums_across_invoices` | a second invoice line is ignored |
| FR-008 | unit | `test_derivation.py::test_one_delivered_quantity_path` | the movement sum is computed twice |
| FR-009 | service | `test_derivation.py::test_line_classes_expose_full_entry_shape` | causal values missing |
| FR-010 | service | `test_derivation.py::test_line_classes_expose_full_entry_shape` | trace keys missing |
| FR-011 | story | `test_derivation.py::test_line_classes_clear_through_reality` | entries persist after billing, receipt or correction |
| FR-012 | service | `test_explanation.py::test_line_classes_explanation_and_not_found_parity` | identities unknown to explanation |
| FR-013 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-014 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| DR-001 | story | `test_line_classes_clear_through_reality` | nothing persists |
| DR-002 | story | `test_line_classes_clear_through_reality` | derivation is not read-time |
| DR-003 | unit | `test_one_delivered_quantity_path` | a second quantity path appears |
| DR-004 | service | `test_line_classes_expose_full_entry_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_line_classes_are_tenant_scoped` | cross-tenant rows leak |
| DR-006 | review | shortest-link review against the Constitution | — |
| DR-007 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |

The migration itself is proven by the existing migration-chain test, which applies every
revision to an empty database, plus a focused check that the column exists and is nullable.

## Rollout and Rollback

The revision adds one nullable column, so it applies to a populated database without
locking anything meaningful and downgrades by dropping it. No data is written by the
migration and none is required for the product to keep working: lines without a reference
behave exactly as they do today.

The first-deployment volume is worth measuring for `shipped_not_billed` in particular. On a
tenant where invoicing has not yet begun to set the reference, every delivered order line
would be reported — which is correct by the rule and useless in practice. There is no such
tenant today, and that is precisely the assumption the class rests on, so the measurement
should confirm the demo scenarios stay quiet rather than prove a volume.

## Review Risks

- **Absence as a statement.** The first class concludes from a missing reference. It is
  sound only while every order-billing line sets one. If a later path creates invoices
  without it, the class reports orders that were in fact billed, and it will not be obvious
  that the cause is upstream.
- **The first schema change here.** Everything in this line of work so far has been
  derivation over existing records. A column is a different kind of commitment and the
  justification is three classes that ship with it — a reviewer should judge whether that is
  enough.
- **Units.** A pair recorded in different units is skipped rather than converted, so such a
  line is silently absent from all three classes. That is the safer failure, and it is still
  a failure: an operator has no way to tell a line nobody needs to look at from one the rule
  declined to judge.
- **Eight record types.** `document_line` joins the carriers. Every consumer reading
  `record_type` should be checked, as it was for `item`, `document` and `source_capability`.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
