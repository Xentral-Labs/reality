# Implementation Plan: Picking and Planned Outbound Deliveries

**Branch**: `334-picking-and-planned-delivery` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

- **Planned delivery:** A reviewed record of one customer's promises, planned before dispatch, with an optional recipient, a stated address, an optional booked slot and an optional staging location.
  - Each statement of it (plan and every revision) is kept as a version of one internal source record stream.
- **Picking:**
  - Picking is a `transfer` movement from where a promise is reserved to the delivery's staging location, and the promise's reservation moves with it.
  - A put-back is the reverse transfer.
  - Picked quantities are read from the pick movements.
- **Dispatch:**
  - `shipment_dispatch` takes `outbound_delivery_id`.
  - The review and the confirmation refuse movements that differ from what the delivery carries.
  - The shipment's notice keeps the recipient, address and slot, and the delivery records its shipment.

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Storage**: migration `0128_outbound_deliveries`, three new tables, no change to existing tables

**Testing**:
- service tests (`tests/test_outbound_deliveries.py`);
- adapter tests (`tests/test_outbound_delivery_adapters.py`);
- business stories A08, A11, A21, A24, D04, D13, M05;
- the shipment, reservation, fulfilment and exception suites as regression;
- web checks and the full suite.

**Constraints**:
- dispatches without a planned delivery behave as before;
- old schemas are untouched (new tables only);
- tenant-scoped;
- reviewed tools.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Every plan and revision statement is an internal source record version; the delivery points to its current statement. |
| II. Reality is the operational authority | PASS | No status on the delivery or any document; planned, picked, put back and shipped are read from lines, movements and the shipment link. |
| III. Proven schema only | PASS | See the typed fields table below; the address and slot stay stated values in the statement. |
| IV. Tenant and service boundaries | PASS | One service behind Web, MCP and CLI; composite tenant keys on every new table. |
| V. Specification and test evidence | PASS | Tests first, a story per journey. |
| VI. Explainable Web product | PASS | The planned delivery shows its lines, picks, statements and shipment, each linked. |
| VII. Simplicity and storage discipline | PASS | Picking reuses the transfer movement and the reservation; there is no pick status. |
| VIII. Received values are recorded, never recomputed | PASS | The address, recipient and slot are kept as stated, and the shipment keeps what it used. |

## Data Model (DR-001)

| Table | Field | Why typed |
|---|---|---|
| `outbound_delivery` | `customer_id` (FK party) | Every line's promise is checked against it, the dispatch's counterparty must equal it, and the list filters by it. |
| | `recipient_party_id` (FK party, nullable) | The recipient is joined for display and the list filters by it. It is an opaque identity, never a name (rule 6). |
| | `staging_location_id` (FK location, nullable) | Picking moves to it, a put-back and the dispatch move from it, and the review checks it. |
| | `shipment_id` (FK shipment, nullable) | Shipped is derived from it, and every mutation refuses once it is set. |
| | `source_record_id` (FK source_record) | The current statement, which holds the address and slot. |
| `outbound_delivery_line` | `outbound_delivery_id`, `commitment_id`, `quantity` | Planned quantities are summed per promise to bound new plans, compared with picks and the dispatch, and joined to the promise. |
| `outbound_delivery_pick` | `outbound_delivery_line_id`, `movement_id` (unique), `kind` (`pick`, `put_back`) | Picked is the sum of pick movements less put-backs, per line. |

- **Address and slot:** The address (`name`, `street`, `postal_code`, `city`, `country`, `note`) and the slot (`from`, `until`) live only in the statement. Nothing filters or joins on them; the slot is compared in Python when read.
- **Indexes:** every foreign key leads an index (spec 181 FR-001).

## Design

1. **Service** `services/outbound_deliveries.py`:
   - `review_outbound_delivery(session, tenant, tool, arguments)` returns normalized arguments and a preview for the four tools. Each tool's review records what the person saw:
     - plan and revise: the planned quantities per promise;
     - pick and put-back: what is picked per line and the reservations moved.
   - `plan_outbound_delivery`, `revise_outbound_delivery`, `pick_outbound_delivery`, `put_back_outbound_delivery`.
   - Each one locks delivery state, stores the statement or the movements, and emits `outbound_delivery.planned`, `.revised`, `.picked` or `.put_back`.
   - **Picking:** For each line it takes the promise's active reservations at `from_location_id` (default: the one location where the promise is reserved), oldest first.
     - For each reserved identity (lot, handling unit, serial) it records a `transfer` movement to staging.
     - The moved part of each reservation is released with cause `picked`, and an active reservation for it is created at staging. A partial rest stays where it was.
   - **Put-back:** It transfers from staging back to a stock location, per identity, from what the line's picks brought there.
     - While the promise is open, its staging reservation moves back with it.
     - When the promise is cancelled or fulfilled, only the stock moves.
   - **Reads:** `outbound_deliveries(customer_id=None, open_only=False)` and `outbound_delivery_detail(id)`. They return:
     - the lines with planned, picked, to-put-back and shipped quantities;
     - the address, slot and recipient;
     - the statements, oldest first;
     - the shipment link;
     - `dispatch`, the ready movements for `shipment_dispatch`;
     - the derived `state` (`planned`, `picking`, `picked`, `shipped`).
2. **Dispatch:** `shipment_dispatch` gains `outbound_delivery_id`. The review (`shipment_actions`) and the confirmation (`record_packaged_execution`) call `require_matches_delivery`:
   - the delivery is not shipped;
   - the counterparty is its customer;
   - the movements are exactly its open lines (cancelled or fulfilled promises carry nothing), from staging when it has picks, with the planned quantity, fully picked when staging is used;
   - nothing of a cancelled promise waits in staging.
   
   The notice payload records `outbound_delivery_id`, `recipient_party_id`, `address` and `slot`. The delivery's `shipment_id` is set, and `shipment_explain` shows them.
3. **Refusal codes:**
   - `outbound_delivery_not_found`;
   - `outbound_delivery_lines_required`;
   - `outbound_delivery_promise_not_customer`;
   - `outbound_delivery_promise_other_customer`;
   - `outbound_delivery_promise_not_open`;
   - `outbound_delivery_quantity_beyond_open`;
   - `outbound_delivery_promise_twice`;
   - `outbound_delivery_slot_invalid`;
   - `outbound_delivery_address_invalid`;
   - `outbound_delivery_staging_invalid`;
   - `outbound_delivery_shipped`;
   - `outbound_delivery_line_picked`;
   - `outbound_delivery_staging_missing`;
   - `outbound_delivery_pick_not_on_delivery`;
   - `outbound_delivery_pick_beyond_planned`;
   - `outbound_delivery_pick_not_reserved`;
   - `outbound_delivery_pick_location_ambiguous`;
   - `outbound_delivery_put_back_beyond_picked`;
   - `outbound_delivery_changed_since_review`;
   - `outbound_delivery_dispatch_mismatch`;
   - `outbound_delivery_dispatch_not_picked`;
   - `outbound_delivery_waiting_put_back`;
   - `outbound_delivery_staging_occupied`, when the staging location is changed while goods are waiting there.
4. **Adapters:**
   - application tools `outbound_delivery_plan`, `outbound_delivery_revise`, `outbound_delivery_pick`, `outbound_delivery_put_back` (mutating), and `outbound_deliveries` and `outbound_delivery_detail` (reads);
   - MCP schemas;
   - CLI group `outbound-delivery`;
   - Web API pass-through;
   - catalogs and gates:
     - command catalog;
     - tool catalog topics;
     - action discovery;
     - isolation catalog;
     - resource catalog with German labels;
     - event catalog;
     - data model;
     - reporting-graph deferral;
     - schema indexes;
     - the web fixture mirror.
5. **Web:** a "Planned deliveries" card on the shipments page:
   - each delivery with its recipient, address, slot, lines (planned, picked, to put back, shipped) and statements;
   - actions through the shared proposal flow: pick, put back and dispatch;
   - translations de, nl, es.
6. **Stories and Guide:** A08, A11, A21, A24, D04, D13, M05 in `tests/scenarios/test_catalog_orders_and_shipments.py`, then catalog, coverage, roadmap and matrix.

## Rollback

Drop the three tables. Shipments and movements recorded through a planned delivery stay ordinary shipments and transfers.
