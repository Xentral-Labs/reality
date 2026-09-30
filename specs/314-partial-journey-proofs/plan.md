# Implementation Plan: Journey Proof Stories, Round Three

**Branch**: `314-partial-journey-proofs` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

## Summary

Seven business stories, one per journey, in the scenario catalog modules. Six journeys are promoted; B09 is recorded and moved to spec 305. Four defects found in research are fixed first, each with a regression test that fails without the fix:

1. A receipt's stated reason is kept and explains it.
2. A delivery-path receipt without a commitment is reported.
3. A payment's uniquely matching reference becomes a candidate reason.
4. A shop line without a price is kept without an invented price and reported; one without a quantity fails in the reported path.

See [research.md](research.md) and [data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: SQLAlchemy 2, Alembic, pytest; existing services, intake paths and reviewed tools

**Storage**: PostgreSQL; one migration makes `document_line.unit_price` nullable

**Testing**: pytest regression tests, business stories, catalog tests, Guide question checks; full backend suite

**Target Platform**: Backend suite, generated Docs payload

**Project Type**: Evidence and catalog content plus four defect fixes

**Performance Goals**: The stories add under 20 s to the suite; `unexplained_movement` gains one read of the stated-reason records per derivation, not one per movement

**Constraints**: No ORM writes in stories; stated values asserted as recorded; every "no finding" assertion has a positive control; every refusal and failure asserts its code

**Scale/Scope**: Three story modules, four service fixes, one migration, one exception class, catalog, coverage, roadmap and generated Guide

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Stories start from stored sources, documents and movements; the P05 line keeps its lossless payload. |
| II. Reality is the operational authority | PASS | Findings and explanations are derived at read time; no status on documents. |
| III. Proven schema only | PASS | The nullable price is required by FR-006 and DR-002: a typed price nobody stated would be an invented value. No other schema. |
| IV. Tenant and service boundaries | PASS | Reviewed tools and tenant-scoped services only; each fix is in the shared service all adapters use. |
| V. Specification and test evidence | PASS | Regression tests precede each fix; stories precede catalog changes. |
| VI. Explainable Web product | PASS | The receipt's reason appears in the existing movement explanation; the new finding names the line and its source. |
| VII. Simplicity and storage discipline | PASS | The receipt reason reuses the adjustment's change-record pattern instead of a new column. |
| VIII. Received values are recorded, never recomputed | PASS | A missing price stays missing; the stated reference is named as stated. |

## Design

### Receipt reason (FR-003, FR-004)

- `_append_movement` adds a `movement_reason_stated` change record for a receipt without a commitment whose reason is not blank. The record holds the reason as input and the movement id as output, like `inventory_adjusted`.
- `movement_explanation` reads both record types as `explicit_reason`.
- `_movement_exceptions` loads the stated-reason movement ids once and excludes them. A shipment package no longer excludes a receipt.
- The reviewed `shipment_receive` path passes a line's `reason` through to the movement, if it is not already allowed.
- A correction's replacement carries no stated reason unless the correction states one. The corrected original stays excluded, as today.

### Candidate reason (FR-005)

In `payment_candidates`, a stated reference that resolves to exactly one invoice adds "stated reference names this invoice" to that invoice. The ambiguous branch stays as it is.

### Missing price and quantity (FR-006)

- Migration: `document_line.unit_price` becomes nullable. The model changes to `Mapped[Decimal | None]`. The default of 0 stays for callers that state no price on purpose (manual lines state one).
- Shopify interpretation:
  - A missing or null `price` gives `unit_price = None`, and line and promise amounts of 0.
  - A missing or null `quantity` raises `InvalidOperation(code="source_line_quantity_missing")`, so the job fails with a code in the reported path; a non-positive one keeps its existing code.
  - The file `sales_order` import keeps a row without a price the same way.
  - `process_pending_import_jobs` is checked to keep other orders going.
- New class `order_line_price_missing` (severity normal, record `document_line`), derived from sales-order lines with a null `unit_price` and a source record. Class gates: CLASS_ORDER, DERIVATION_REGISTRY, catalogs order, `operational_exception_catalog.yaml`, the class lists in the catalog, coverage and clock tests, the reference-integrity count, and the German resource label.
- Reader audit: each of the 28 `.unit_price` reads handles null.
  - Comparisons skip a null price: `sold_below_purchase_price` and `invoice_price_differs`.
  - Serialisers emit null.
  - Billing offers an unpriced position without a price; an invoice recorded from it carries no unit price.
  - `shop_order_changes` reads a missing earlier price as none, so a later stated price is held as `price_changed`.

### Stories

| Journey | Module |
|---|---|
| F04, F08 | `tests/scenarios/test_catalog_stock_and_returns.py` |
| H09, B09 | `tests/scenarios/test_catalog_purchasing.py` |
| P02, P05 | `tests/scenarios/test_catalog_sources.py` (Shopify helpers and scenario clock) |
| P08 | `tests/scenarios/test_catalog_sources.py` |

B09's story pins today's behaviour under a name that says so, as spec 292's outcome rule requires.

### Catalog, Guide and follow-ups

- `config/business_journey_catalog.yaml`: six promotions with story-first evidence and English and German keywords; B09's limitation names the finding.
- `tests/test_business_journey_catalog.py`: `PROVEN_BY_STORY` and `FINDABLE_BY_KEYWORD` gain the six.
- `docs/scenarios/coverage.md` and `docs/scenarios/roadmap.md`; `specs/305-backorder-allocation/spec.md` lists B09 and its finding.
- `docs/SPEC_COVERAGE_MATRIX.md` rows for new test files.
- `make docs-generate`.

## Project Structure

```text
specs/314-partial-journey-proofs/{spec,plan,research,data-model,quickstart,tasks}.md, checklists/requirements.md

packages/reality-core/
├── migrations/versions/01NN_line_price_optional.py      # numbered after rebasing onto main
├── src/reality/db/core.py                               # unit_price nullable
├── src/reality/services/core.py                         # receipt reason record, Shopify price/quantity
├── src/reality/services/movement_explanations.py        # explicit_reason for receipts
├── src/reality/services/exceptions.py                   # unexplained_movement, order_line_price_missing
├── src/reality/services/payment_intake.py               # unique reference as a reason
├── src/reality/services/{invoice_billing,shop_order_changes,...}.py  # null price readers
├── config/{operational_exception_catalog,resource_catalog,business_journey_catalog,service_refusals}.*
└── tests/
    ├── test_movement_reasons.py                         # new: FR-003, FR-004
    ├── test_payment_candidates_reference.py             # new: FR-005
    ├── test_shop_line_gaps.py                           # new: FR-006
    ├── test_business_journey_catalog.py
    └── scenarios/test_catalog_{stock_and_returns,purchasing,sources}.py

docs/scenarios/{coverage,roadmap}.md, docs/SPEC_COVERAGE_MATRIX.md, specs/305-backorder-allocation/spec.md, generated Docs payload
```

## Rollback

Revert the commits. The migration's downgrade refuses while a line has a null price, rather than inventing one.

## Complexity Tracking

No Constitution violations.
