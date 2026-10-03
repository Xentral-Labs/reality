# Implementation Plan: Drop Shipping

**Branch**: `337-drop-shipping` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

## Summary

- The link from a drop-ship purchase to the customer order already exists: the supply assignment for customer demand (spec 305).
- A purchase order whose stated ship-to party is a customer is a drop-ship order. A shared SQL condition, `ships_to_customer()`, recognises its promises.
- A reviewed action, `drop_shipment_record`, records the supplier's dispatch as one statement with a customer shipment and two movements without a location: a receipt on the purchase promise and a shipment on the customer promise.
- Three readers learn what drop-ship supply is: incoming stock leaves it out, the reorder point leaves it out, and at-risk does not count the customer demand it still covers as a shortage.

## Technical Context

**Language/Version**: Python 3.12, SQLAlchemy 2, PostgreSQL

**Storage**: none new. No table, no column, no migration.

**Testing**:
- service tests with positive controls (`tests/test_drop_shipping.py`);
- the agent's strict schema, review and verification;
- stories D10, D11, G15 and R03 (`tests/scenarios/test_catalog_drop_shipping.py`);
- the movement, shipment, exception and finance suites as regression.

**Constraints**: tenant-scoped; one delivery lock per drop shipment; at-risk derivation costs one query when no drop-ship purchase is open.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The supplier's dispatch is a source record; the shipment and both movements carry it. |
| II. Reality is the operational authority | PASS | No document status. Delivered is read from the movements as for any order. |
| III. Proven schema only | PASS | Nothing new is stored. The ship-to party already exists on documents. |
| IV. Tenant and service boundaries | PASS | One reviewed action under the delivery lock; every read is tenant-scoped. |
| V. Specification and test evidence | PASS | Tests first; stories per journey. |
| VI. Explainable Web product | PASS | The drop shipment shows as a shipment with its tracking number; `drop_shipments` names the assignment and what shipped. |
| VII. Simplicity and storage discipline | PASS | The existing assignment is the link; the existing movement types carry the effect. |
| VIII. Received values are recorded, never recomputed | PASS | Quantity, time, carrier and tracking number are recorded as the supplier stated them. |

### DR-001

No new typed field or table. The ship-to party of a purchase order is an existing stated value, now filtered on by three readers.

## Design

### 1. Movements without a location (`services/core.py`)

- `_append_movement` gains a private `_drop_ship` flag. With it, a receipt or a shipment may name no location, and must name a promise. Any other shape is refused (`movement_drop_ship_shape_invalid`).
- Stock is the sum of movements naming a location, so these change nothing physical. The physical-stock check is skipped for them; there is nothing to take from.
- Public `record_movement` is unchanged: it still requires the locations.

### 2. The drop shipment (`services/drop_shipping.py`)

**Preview** (`preview_drop_shipment`):
- The purchase promise is open; it is assigned to customer demand. Without a named customer promise it serves exactly one, or `drop_ship_customer_promise_required`.
- The purchase order's ship-to party is the customer: the order's party or ship-to, or the promise's recipient. Otherwise `drop_ship_purchase_not_to_customer`.
- The quantity fits what is left of the assignment and what both promises still have open.
- The stated time is not in the future; a customer hold refuses as for any shipment.

**Execution** (`record_drop_shipment`), under the delivery lock:
1. A `drop_shipment` source record with the stated values.
2. A customer shipment with carrier and tracking number (`record_shipment_notice`).
3. A receipt on the purchase promise and a shipment on the customer promise, both under the source; the shipment movement is in the shipment's package. Reservations are not consumed: the goods never came from stock.
4. `drop_shipment.recorded`.

**Read** (`drop_shipments`): for a purchase or customer promise, the assignments with assigned and drop-shipped quantity, and every drop shipment with its shipment, carrier and tracking number. A standing pair is a receipt and a shipment without a location under one source, neither voided by a correction.

### 3. What drop-ship supply is not

- `ships_to_customer()`: a correlated condition on `Commitment`: its document states a ship-to party that has the customer role.
- `inventory_position_query`: incoming leaves drop-ship promises out.
- `reorder_point_reached`: incoming at a location leaves them out.
- `_commitment_exceptions`: the unreserved quantity of a customer promise is reduced by `drop_ship_cover`, what drop-ship supply assigned to it still has to come. The overdue class is unchanged: a late drop shipment is late.
- Available to promise already ignores assigned supply; it needs no change.

### 4. Adapters

- Review: `services/drop_ship_actions.py` (`drop_shipment_record`), wired into the delivery-action review, detail, verification and unresolved checks.
- Tools: `drop_shipment_record` and `drop_shipments`; MCP `drop_shipment_record_propose` and `drop_shipments`; CLI `drop-shipments`, `drop-shipment-propose`, `drop-shipment-confirm`; the web form in the shipment actions.
- Catalogs: command, capability guidance, agent coverage, action discovery, tool topic, isolation, resource (German label "Streckengeschäft erfassen"), event, refusals with de, nl and es.

## Risks

- A purchase order with a customer as ship-to that is meant for the company's own stock would be treated as drop-ship. The ship-to party is the statement of where the goods go, so this is the purchase order saying so.
- The contribution read costs a drop-shipped line from stock valuation, which has none. Recorded as a limitation.
- The warehouse fulfillment queue still lists a drop-ship line as not reserved until the dispatch is recorded. Changing it needs the supply assignment to emit an event that refreshes the queue, and narrowed-versus-full parity for it; left for a follow-up and recorded in the spec.
