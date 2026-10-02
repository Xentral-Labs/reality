# Implementation Plan: Customer Pickup and Late 3PL Confirmations

**Branch**: `312-shipping-modes` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

- `shipment.delivery_mode` (nullable: `carrier`, `pickup`), migration `0123`. A pickup refuses a carrier and a tracking number and is allowed for customer deliveries only.
- The collector's name is a stated value in the shipment's `shipment.notice_recorded` event payload.
- `record_packaged_execution` passes the stated `occurred_at` to every movement and refuses a future one.
- `shipment_explain` and the shipment reads add:
  - `delivery_mode`;
  - `collected_by`;
  - `moved_at`, the stated time of the notice;
  - `recorded_at`;
  - `confirmation_lag_seconds`.

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Storage**: PostgreSQL; migration `0123_shipment_delivery_mode`

**Testing**:
- shipment service, tool, adapter and story tests;
- the shipment, fulfilment and exception suites as regression;
- web checks and the full suite.

**Constraints**:
- unchanged results without a mode or a stated time;
- old schemas keep working, since the column is deferred and left out of INSERTs that do not set it;
- tenant-scoped;
- reviewed tools.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The stated time and collector are kept as stated. |
| II. Reality is the operational authority | PASS | No document status. |
| III. Proven schema only | PASS | The mode is checked on every dispatch (carrier refusal), filtered in reads and shown. The collector is not typed. |
| IV. Tenant and service boundaries | PASS | One shipment service behind every adapter. |
| V. Specification and test evidence | PASS | Tests first. |
| VI. Explainable Web product | PASS | The shipment shows mode, collector, times and lag. |
| VII. Simplicity and storage discipline | PASS | One nullable column. |
| VIII. Received values are recorded, never recomputed | PASS | Stated times and names are kept; the lag is derived at read time. |

## Design

1. **Schema:** migration `0123`.
   - `shipment.delivery_mode` with a check on `carrier` and `pickup`.
   - The model uses FetchedValue, deferred and `eager_defaults` False.
2. **Service:** `record_shipment_notice` and `record_packaged_execution` take `delivery_mode` and `collected_by`.
   - Refusals:
     - `shipment_pickup_customer_only`;
     - `shipment_pickup_carrier_refused`;
     - `shipment_delivery_mode_invalid`;
     - `shipment_occurred_at_future`.
   - The stated `occurred_at` is passed to each `record_movement`.
3. **Reads:** `shipment_explain` and `_details` add mode, collector, moved and recorded times and the lag.
4. **Adapters:**
   - the tool field sets;
   - the MCP schemas of `shipment_dispatch_propose` and `shipment_receive_propose`;
   - the Web shipment actions.
5. **Web:**
   - in the dispatch card, a pickup choice, the collector and an optional "goods left at" time;
   - the shipment detail shows them;
   - translations.
6. **Stories and Guide:** D15 and D12.

## Rollback

The downgrade refuses while pickups are recorded.
