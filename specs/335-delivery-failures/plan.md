# Implementation Plan: Undeliverable, Refused and Lost Parcels

**Branch**: `335-delivery-failures` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

- A new reviewed delivery action, `shipment_delivery_failure`, on an outbound customer shipment. Its kind is `undeliverable`, `refused` or `lost`, with a stated reason and time.
- It reverses every standing movement of the shipment through `core.correct_movement`. The goods come back for undeliverable and refused parcels, and are written off for a lost one.
- One row in a new table, `delivery_failure`, records what was stated.
- A lost parcel may open a `carrier_claim` receivable against a stated business partner. It is posted against a new account role, `carrier_claim_income`, and settled through the existing settlement flow.

## Technical Context

**Language/Version**: Python 3.12, TypeScript (web form)

**Storage**: PostgreSQL. Migration `0125_delivery_failures`:
- the table `delivery_failure`;
- the role `carrier_claim_income` in `ck_subledger_account_role`.

**Testing**:
- service and review tests with positive controls;
- stories D07, D08 and D09;
- the adapter schema test;
- the migration test;
- the full suite.

**Constraints**:
- tenant-scoped;
- one reversal path;
- nothing derived is stored.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Each failure has a manual source record. The claim document carries it. |
| II. Reality is the operational authority | PASS | No status on documents or shipments. Fulfilment is derived from standing movements. |
| III. Proven schema only | PASS | See DR-001 below. |
| IV. Tenant and service boundaries | PASS | One service, called by the delivery review shared by Web, MCP and CLI. |
| V. Specification and test evidence | PASS | Tests are planned before the code. |
| VI. Explainable Web product | PASS | The shipment read shows the kind, reason, time, the corrections and the claim. |
| VII. Simplicity and storage discipline | PASS | Reuses correction, fee-claim settlement and the delivery review. |
| VIII. Received values are recorded, never recomputed | PASS | Kind, reason, time and claim amount are kept as stated. |

### DR-001: why a table

`delivery_failure` (tenant, id, shipment_id unique, kind, reason, occurred_at, claim_document_id, source_record_id, created_at). The core acts on it repeatedly:
- It refuses a second failure of a shipment, which the unique constraint enforces.
- It labels the shipment's state in the shipment read and register.
- It links the claim document.

A payload-only event would need a JSONB search for each of these. The role is needed because the subledger role check constrains every account.

## Design

1. **Service** `services/delivery_failures.py`:
   - `preview_delivery_failure` validates:
     - the shipment is outbound and its purpose is `customer_delivery`;
     - the kind and the reason;
     - the time is not in the future;
     - it has not failed before;
     - standing movements exist;
     - the claim is for a lost parcel only, names a business partner and has a positive amount;
     - the claim account default exists.
   - `record_delivery_failure` locks the delivery state, creates the source record and corrects each standing movement:
     - for a lost parcel, with an adjustment out of the from-location as the replacement;
     - corrections reopen the promise as they already do.
   - It then writes the row, creates and posts the claim, and emits `shipment.delivery_failed`.
   - `delivery_failure_summary` is the read.
2. **Review** `services/delivery_failure_actions.py`:
   - a state-bound review;
   - an execution guard;
   - a detail with verification, wired into `delivery_actions`.
3. **Tools:**
   - application tools `shipment_delivery_failure` and `delivery_failure_summary`;
   - MCP `shipment_delivery_failure_propose` and the read;
   - CLI propose and confirm;
   - web pass-through and a form in `ShipmentActions`.
4. **Finance:**
   - `carrier_claim` in `SETTLEMENT_CONTROL`, `FEE_RECEIVABLE_TYPES` and `TRANSACTION_MATRIX`;
   - the role in `ACCOUNT_ROLES` and the tool's role list.
5. **Shipment read:** `delivery_failure` on the shipment detail and on register rows.
6. **Gates:**
   - isolation catalog;
   - reference catalog;
   - resource catalog (German labels);
   - command catalog and agent coverage;
   - action discovery;
   - service refusals and the ratchet;
   - i18n;
   - `catalogs.py`;
   - pinned counts;
   - data model docs;
   - `make docs-generate`.
7. **Stories and Guide:** D07, D08 and D09, then the promotion, coverage, roadmap and matrix.

## Rollback

The migration's downgrade drops the table and restores the role check. It refuses while carrier-claim accounts exist.
