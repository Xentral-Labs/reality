# Implementation Plan: Receipt and Shipment Deviations

**Branch**: `338-receipt-deviations` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

## Summary

- **Over-delivery**:
  - A receipt movement may state `beyond_order`, which lifts the open-quantity bound for receipts on a purchase promise.
  - The surplus is a derived finding, `received_beyond_order`.
  - The spec 313 allowance for raising a fulfilled line now also covers purchase lines, bounded by received net of supplier returns.
- **Wrong item**:
  - A movement may state `meant_for_commitment_id` instead of `commitment_id`.
  - `_append_movement` validates it and writes one `misdelivery` row that links the movement to the line.
  - The movement explanation names the line, the unexplained-movement derivation skips it, and `misdelivery_outstanding` reports the line until the wrong goods have gone back.
- **Substitute**:
  - A reviewed command, `commitment_substitute_accept`, writes one `commitment_substitute` row.
  - The commitment–item check in `_append_movement` accepts a substitute item for that promise.
- **Advice**:
  - `record_shipment_notice` takes `advised` lines for inbound supplier notices and writes `shipment_advice_line` rows.
  - `record_packaged_execution` takes `shipment_id` to receive into an announced inbound shipment: the movements go into that shipment's package.
  - The shipment read shows advised against received. The three-way match shows advised in transit per line.

## Technical Context

**Language/Version**: Python 3.12, SQLAlchemy 2, Alembic, PostgreSQL

**Storage**: migration `0130_receipt_deviations` with `misdelivery`, `commitment_substitute` and `shipment_advice_line`. No new column on an existing table.

**Testing**:
- service tests with positive controls (`tests/test_receipt_deviations.py`);
- adapter tests (`tests/test_receipt_deviation_adapters.py`): MCP strict schemas, CLI, catalogs;
- stories H04, H05, H06, H07, H17, G16 and D05;
- the receipt, shipment, correction and purchase suites as regression.

**Constraints**:
- tenant-scoped;
- the shipment register keeps its bounded query count, with one more read for the advice lines;
- the exception derivation stays one query per class, with no read per promise beyond the retained inputs.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Movements stay the reality. A wrong-item row links a movement to the line it was meant for. A substitute is a stated decision kept as a source record. Advice lines belong to their notice. |
| II. Reality is the operational authority | PASS | No document status. Surplus, wrong goods out, advised against received and in transit are read from movements and rows. |
| III. Proven schema only | PASS | Three tables, justified below. |
| IV. Tenant and service boundaries | PASS | Reviewed tools only; every read and row is tenant-scoped. |
| V. Specification and test evidence | PASS | Tests first per phase; positive controls for every negative. |
| VI. Explainable Web product | PASS | Each finding names the line, the order and the quantities. The movement explanation names the line a wrong item was meant for, and the shipment read names advised and received per line. |
| VII. Simplicity and storage discipline | PASS | Existing receipt, correction, revision and three-way-match paths carry the new cases. |
| VIII. Received values are recorded, never recomputed | PASS | Advised quantities and substitutes are stored as stated. The surplus is derived, never stored. |

### DR-001: the three tables

- `misdelivery` (movement → line it was meant for):
  - It is joined on every derivation of `misdelivery_outstanding`, which sums wrong goods out against back per line and item.
  - The unexplained-movement derivation filters its movements out.
  - The movement explanation and the bound on wrong goods going back read it.
  - A column on `movement` would break the historical schema tests and widen the hottest table for a rare case.
- `commitment_substitute` (line → accepted item):
  - Every movement validation against a purchase promise filters on it, to accept the substitute's item.
  - The three-way match reads it.
- `shipment_advice_line` (notice → promise, advised quantity):
  - Its quantities are summed per shipment against received for the shipment read.
  - They are summed per purchase line, joined with whether its shipment has received goods, for in transit.
  - A payload in the notice event cannot be joined per purchase.

## Design

### 1. Movements (`services/core.py`, kept local)

- `_append_movement(..., beyond_order=False, meant_for_commitment_id=None)`:
  - `beyond_order` is valid only for a receipt naming a supplier promise. It skips `validate_commitment_movement_quantity` and the corrected-open check.
  - `meant_for_commitment_id` is validated by `services/receipt_deviations.py::validate_meant_for`:
    - no `commitment_id`;
    - a type the promise's side allows;
    - another item than the line asks for, and not an accepted substitute;
    - goods going back bounded by what of that item is out on the line.
  - After the movement row, `record_misdelivery` writes the link.
  - The spec 314 stated reason is not also written; the reason goes on the link.
- The commitment–item check accepts `accepted_substitute(session, tenant, commitment, item_id)`.
- `record_movement`, `correct_movement`'s replacement and the correction preview pass both fields through.
- `_keeps_what_was_shipped` covers supplier promises: kept = receipts − supplier returns, refused beyond with `revision_beyond_received`. The review's `kept` state follows.

### 2. Service module (`services/receipt_deviations.py`)

- `validate_meant_for`, `record_misdelivery`, `outstanding_misdeliveries` (one grouped query).
- `accepted_substitute`, `accept_substitute` (reviewed; stores the decision as an internal source record and emits `commitment.substitute_accepted`) and `review_substitute`.
- `validate_advice` and `record_advice` (notice lines), `advice_by_shipment` (advised and received per shipment, one query each) and `in_transit_by_commitment` (one grouped query).

### 3. Shipments (`services/shipments.py`, `services/shipment_actions.py`, `services/delivery_actions.py`)

- `record_shipment_notice(..., advised=None)`: inbound supplier notices only.
- `record_packaged_execution(..., shipment_id=None)`: inbound only. The shipment must match purpose and counterparty, and its first package takes the movements. No new notice is written.
- Review and execution field sets gain `beyond_order`, `meant_for_commitment_id`, `advised` and `shipment_id`. The review refuses what execution refuses.
- `_details`: `quantities.announced` is the advised total, and an `advice` list holds advised, received and difference per promise. Movement rows name a wrong item's line.

### 4. Findings (`services/exceptions.py`)

- `received_beyond_order` (record: the promise): received − supplier returns − in force > 0, for non-cancelled supplier promises. Dated by the last receipt.
- `misdelivery_outstanding` (record: the promise): Σ out − Σ back of wrong items > 0 per line. Dated by the first wrong movement.
- `_movement_exceptions` skips movements with a `misdelivery` row.

### 5. Three-way match (`services/purchase_match.py`)

- Per line: `substitutes`, the accepted items, and `in_transit`, advised on shipments with nothing received yet.

### 6. Gates

- Command `commitment_substitute_accept`:
  - application tool and review;
  - MCP propose tool with its topic, CLI command and web proposals pass-through;
  - `command_catalog.yaml`, `action_discovery.json`, the action-reference fixture;
  - isolation catalog, `catalogs.py`, event catalog, resource catalog with German labels.
- Schemas: MCP shipment and correction schemas gain the new fields.
- Exception classes:
  - class order, registry, catalog;
  - reference catalog consumers and pinned counts;
  - pinned lists, `WITHOUT_A_SCENARIO`, translations.
- Tables: `data_model.yaml`, reporting-graph deferred list, FK indexes.
- `service_refusals.json` and translations; `make docs-generate`.

## Rollback

Downgrade 0130 drops the three tables and is refused while any of them holds rows. Movements recorded with a wrong-item link stay valid unlinked movements.
