# Implementation Plan: Unit Conversion Between Purchase and Stock Units

**Branch**: `301-unit-conversion` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Purchasing in cartons now adds up:
- A purchase order line keeps its stated cartons. Its supplier promise is held in pieces by the item's stated factor.
- A receipt stated in cartons is recorded in pieces, keeping the stated quantity and unit on the movement.
- Everything that compares promises, receipts, stock, valuation and invoices then works in one unit.
- A unit without a stated relation is refused.
- Purchase orders recorded before keep their meaning and are named.

See [research.md](research.md), [data-model.md](data-model.md) and [contracts/receipts-in-purchase-units.md](contracts/receipts-in-purchase-units.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Primary Dependencies**: SQLAlchemy 2, Alembic, FastAPI, Typer, pytest

**Storage**: PostgreSQL; migration `0106_movement_stated_unit`

**Testing**:
- service, adapter and business-story tests
- migration tests
- web `test:i18n`, the audit and the build
- the full backend suite

**Target Platform**: Backend, Web, MCP, CLI

**Project Type**: Domain change with adapters

**Performance Goals**: The conversion is arithmetic on values already read; no reader adds a query per row.

**Constraints**:
- stated values kept;
- the one shared unit rule;
- tenant-scoped;
- reviewed tools;
- sales unchanged.

**Scale/Scope**: two movement columns, one domain module, the purchase order and receipt paths, three readers, one cause, the web receipt form and a story.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The line is evidence as stated; the promise and the movement are its Reality in the stock unit. |
| II. Reality is the operational authority | PASS | No document status; quantities are read from movements and promises. |
| III. Proven schema only | PASS | `stated_quantity` and `stated_unit` are shown on every receipt read and filtered by the downgrade guard. |
| IV. Tenant and service boundaries | PASS | One service path for every adapter; tenant-scoped. |
| V. Specification and test evidence | PASS | Tests planned before each phase. |
| VI. Explainable Web product | PASS | Both units are shown wherever a purchase is read. |
| VII. Simplicity and storage discipline | PASS | One shared rule in `domain/units.py`; no per-supplier table. |
| VIII. Received values are recorded, never recomputed | PASS | Stated quantity and unit are kept; the stock quantity is the item's stated factor applied once, at interpretation. |

## Design

### `domain/units.py`

- `in_unit(item, quantity, recorded, target)`: moved from `services/exceptions._in_unit`, which then imports it. Behaviour is unchanged.
- `to_stock_unit(item, quantity, unit)` raises the coded refusal.
- `promise_unit(commitment, line, item)`: `"stock"` or `"line"`, distinguishing new from recorded promises.

### Purchase orders

`create_manual_order` applies `to_stock_unit` to a purchase line's promise quantity (direction `purchase` only). The review of `order_create` states both.

### Receipts

`record_movement(..., unit=None)` converts and keeps the stated pair through `_append_movement`. The reviewed `movement_create` and `shipment_receive` pass it on, and their reviews show both.

### Readers

- `receipt_unbilled` and `billed_not_received` convert billed lines into the stock unit for promises in the stock unit.
- `item_oversold` uses `promise_unit`.
- Delivery case and open-work rows add the purchase-unit view.
- `units_not_comparable` gains the cause `promise_in_purchase_unit` for open supplier promises recorded before.

### Migration

`0106_movement_stated_unit` adds the two columns with a pairing check. The ORM declares them deferred with `FetchedValue`, so that old-schema tests keep inserting. The downgrade refuses while stated receipts exist.

### Adapters and Web

- MCP: `unit` on `movement_create_propose` and `shipment_receive_propose`.
- Web: pass-through of `unit`.
- CLI: `--unit`.
- Web receipt form: a unit selector (stock unit and, when stated, purchase unit) and the converted quantity in the review.
- Movement inspector: the stated pair.
- Translations.

### Story and Guide

- O05 in `tests/scenarios/test_catalog_purchasing.py`:
  - order 5 cartons;
  - receive 5 cartons through the reviewed receipt;
  - 60 pieces in stock and valued;
  - a supplier invoice for 5 cartons matches;
  - pallets are refused.
- Then the catalog promotion, coverage, roadmap and docs.

## Project Structure

```text
specs/301-unit-conversion/{spec,plan,research,data-model,quickstart,tasks}.md, contracts/receipts-in-purchase-units.md
packages/reality-core/
├── migrations/versions/0106_movement_stated_unit.py
├── src/reality/domain/units.py (new), db/core.py
├── src/reality/services/{core.py, exceptions.py, delivery_reads.py, delivery_actions.py, shipments.py}
├── src/reality/tools/application.py, mcp/catalog.py, cli/app.py, web/api.py
└── tests/{test_purchase_units.py, test_purchase_unit_adapters.py}, scenarios/test_catalog_purchasing.py
apps/web/src/unified/ActionCard.tsx (receipt form), Inspector rows, localization.tsx
```

## Rollback

The downgrade drops the two columns and refuses while stated receipts exist. Promises created in the stock unit stay valid, because the stock unit is what every stock reader already assumed.

## Complexity Tracking

No Constitution violations.
