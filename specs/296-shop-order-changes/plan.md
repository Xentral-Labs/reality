# Implementation Plan: Shop Order Changes and Refunds

**Branch**: `296-shop-order-changes` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

## Summary

Narrow the spec 081 guard: a later Shopify order version is compared with the order's current
Reality and applied automatically when it only reduces open, unshipped quantity; everything else is
held with coded reasons, all or nothing. Refunds are split into their own source records and
recorded as `sales_refund` evidence on the order, with a return announcement where the shop states a
return of shipped goods. An order with an unknown SKU is interpreted for its known lines, and a
person assigns an item to the unknown line through a reviewed tool. A09, A16, A17, F12, L04 and L05
are then proven by business stories and promoted.

## Technical Context

**Language/Version**: Python 3.12; TypeScript 5.8 / React 19 for the Web review and inspector

**Primary Dependencies**: SQLAlchemy 2, Pydantic v2, Typer, FastAPI; existing source intake,
commitment revision/cancellation, return announcements and delivery-review framework

**Storage**: PostgreSQL; no migration (data-model.md)

**Testing**: pytest on disposable PostgreSQL (interpretation, refund, assignment, adapter,
exception, isolation, catalog gates, business stories); Node contract tests and i18n audit for Web

**Target Platform**: Reality core service, Web, MCP/Chat, CLI

**Project Type**: Domain capability across the intake, the delivery tools and the Web

**Performance Goals**: A version is classified with one read of the order's lines, commitments,
fulfilled quantities and reservations; no per-line query beyond the existing services' own

**Constraints**: No document status field; no ledger posting for refunds; nothing applied that
raises or adds demand; tenant-scoped everywhere; the assignment is confirmed by a person

**Scale/Scope**: 1 classification module, 1 refund interpreter, 1 reviewed tool, 1 exception class,
0 tables, 3 adapters, about 12 catalog files

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Every version and refund is a source record; refunds become `sales_refund` Evidence; revisions, cancellations and announcements are Reality citing their source. |
| II. Reality is the operational authority | PASS | What is open, cancelled or expected back is read from commitments, revisions and announcements; documents gain no status (Non-Goal). |
| III. Proven schema only | PASS | No table or column is added; a new document type and existing nullable columns carry everything (data-model.md). |
| IV. Tenant and service boundaries | PASS | Interpretation calls the existing services; the only new mutation tool is shared by Web, MCP/Chat and CLI. |
| V. Specification and test evidence | PASS | Approved spec with clarifications; tests planned before each implementation task. |
| VI. Explainable Web product | PASS | Held reasons name codes and lines; the order inspector lists its refunds; revisions and announcements link their source. |
| VII. Simplicity and storage discipline | PASS | Reuses revise, cancel, announce and the delivery review; the refund split reuses source intake and deduplication. |
| VIII. Received values are recorded, never recomputed | PASS | Quantities, prices, refund amounts and restock types are recorded as the shop states them; nothing is derived into storage. |

Post-design check: PASS. [contracts/shop-order-changes.md](contracts/shop-order-changes.md) narrows spec
081 FR-002 instead of removing the guard.

## Design

### Flow

```text
shopify/order vN ──► classify against current Reality ──► reductions only ──► revise / cancel (source = vN)
        │                                             └──► anything else ──► needs_review (codes)
        └──► refunds[] ──► shopify/refund source ──► sales_refund Document + lines
                                                   └──► restock "return" on shipped ──► return announcement
shopify/order v1 with unknown SKU ──► known lines interpreted; unknown line kept ──► order_line_item_unknown
                                                                                   └──► order_line_item_assign (reviewed)
```

### Modules

- `services/shop_order_changes.py`: `order_for_source`, `stated_lines(payload)` (R3),
  `classify_order_version(session, tenant_id, order, payload)` returning applied operations or held
  codes (R4), and `apply_order_version(...)`, called by `_shopify_interpretation` for version > 1.
- `services/shop_refunds.py`: `split_refunds(session, tenant_id, order_source)` called after an
  order version is stored; `interpret_shop_refund(...)` registered in `SOURCE_INTERPRETERS`.
- `services/order_line_items.py`: `preview_item_assignment`, `assign_line_item`, and the review
  wiring in `delivery_actions.py`.
- `services/core.py`: `_shopify_interpretation` keeps unknown lines (R6) and delegates later
  versions; `ShopifyUpdateNeedsReview` carries codes; `process_import_job` writes them.
- `services/exceptions.py`: class `order_line_item_unknown`.

### Adapters

Web: held reason codes on the import-job review, the order inspector's refunds section, an
"Assign item" action on the exception row and the order line, the next-step guidance for
`cancelled_after_shipment`. MCP: `order_line_item_assign_propose` with a strict schema. CLI:
`order-line-item-assign-propose` and `-confirm`.

### Existing tests that change on purpose

- `tests/test_shopify_update_guard.py`: quantity and cancellation changes on unshipped lines are now
  applied; note-only changes are recorded without effect; shipped cases stay held with their codes.
- `tests/test_shopify_and_explain.py::test_source_survives_interpretation_failure` and the v2
  quantity case: rewritten for R6 and R4.
- `tests/scenarios/test_catalog_sources.py` P04: the unshipped cancellation now applies itself; the
  story keeps a held case (after shipment) for the reviewed cancellation path.

## Risks

- Behaviour change of spec 081: every caller relying on "later versions never change Reality" —
  analytics (spec 185 research) and demo intake — is checked; demo intake uses its own interpreters.
- Reservation choice on reduction: several reservations make the reduction wait
  (`reservation_choice_required`) instead of guessing.
