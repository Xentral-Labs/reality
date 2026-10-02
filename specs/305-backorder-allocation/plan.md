# Implementation Plan: Serving Backorders on Receipt

**Branch**: `305-backorder-allocation` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

A reviewed tool, `backorders_serve`, proposes reservations for the waiting customer promises of an item at a location. The serving order is: the promises the received purchase is assigned to, in assignment order; then the other waiting promises by due date, then by when they were promised. The person can change or drop lines, and nothing is reserved before confirmation. The receipt confirmation offers the step right away (B08, H16, B09).

`supply_coverage` splits each assignment into what has arrived and what is still to come, at read time in assignment order (B09). A read, `available_to_promise`, answers per item what is free now and, per open purchase, from which date how much more is free, naming the purchase (B07).

A cancelled customer promise already ends its assignments since #205. The R02 and G13 stories prove it.

No new table, column or event. See [research.md](research.md), [data-model.md](data-model.md) and [contracts/backorders.md](contracts/backorders.md).

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React)

**Storage**: PostgreSQL; no migration

**Testing**:
- service tests for the serving order, the split and available-to-promise;
- adapter tests (MCP, Web, CLI, tenant isolation);
- business stories for B07, B08, B09, G13, H16 and R02 (B09's pinned test rewritten);
- the supply-assignment, reservation and delivery suites as regression;
- web checks, browser fixtures and the full suite.

**Performance Goals**: Each read runs a fixed number of grouped queries per item, not per promise.

**Constraints**:
- results without assignments are unchanged;
- nothing stored for the split or the answer;
- tenant-scoped;
- reviewed tools.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Reservations are made by the existing reservation service under the confirmed proposal; nothing bypasses it. |
| II. Reality is the operational authority | PASS | No document status; waiting, arrived and promisable are read from commitments, movements, reservations, blocks and assignments. |
| III. Proven schema only | PASS | No new schema. |
| IV. Tenant and service boundaries | PASS | One service path behind MCP, Web and CLI; tenant-scoped reads. |
| V. Specification and test evidence | PASS | Tests planned per phase, written first where practical. |
| VI. Explainable Web product | PASS | Each proposed line names its promise, customer, due date and why it stands where it stands (assigned or due). |
| VII. Simplicity and storage discipline | PASS | Reuses `core.reserve`, `supply_assignments._effective_rows` and the change-proposal review. |
| VIII. Received values are recorded, never recomputed | PASS | The split and the answer are read-time observations and never stored. |

## Design

1. **Split (FR-006)**: in `supply_assignments.py`, `assignment_split` orders each purchase's effective assignments by creation. The purchase's received quantity covers them in that order. `supply_coverage` gains `arrived` and `still_to_come` per item and per customer; `protecting_supply` stays the total.
2. **Serving order (FR-001)**, in `services/backorders.py`:
   - `waiting_promises` lists open customer deliveries of the item held at the location, plus those the named purchase is assigned to. Each needs its open quantity less its active reservations. Promises under a hold are listed apart with the reason and are not served.
   - `review_backorder_serving` computes what is available at the location (physical less reserved less blocked) and allocates in the serving order. Stated lines are validated instead: each at most the promise's need, all together at most what is available.
   - `serve_backorders` re-validates and reserves each line through `core.reserve` with the location and the action. A line that can no longer be reserved in full refuses the whole confirmation (`backorder_serving_changed_since_review`).
   - Lot- and serial-tracked items are refused (`backorder_serving_tracked_item`): their reservations name an identity, which stays an ordinary reservation.
3. **Available-to-promise (FR-003)**: `available_to_promise(item)` reads company-wide over stock locations.
   - Free now is physical less reserved less blocked, less the waiting need that neither a reservation nor supply still to come covers.
   - Then each open purchase, by due date, adds its open quantity less what its customer assignments still expect.
   - Each row names the purchase, its supplier, its date, whether it is overdue, and the running total.
4. **Adapters**:
   - tools `backorders_serve` (reviewed) and `available_to_promise` (read);
   - MCP `backorders_serve_propose` and `available_to_promise`;
   - Web `POST /backorders/proposals` and `GET /items/{item_id}/available-to-promise`;
   - CLI `backorders serve` and `backorders promise`.
5. **Web**:
   - The receipt result offers "Serve backorders" for the received item and location.
   - The warehouse row preview shows available-to-promise and offers "Serve backorders".
   - The serving card lists the proposed lines with editable quantities, confirms or withdraws.
   - Translations.
6. **Stories and Guide**: B07, B08, B09, G13, H16 and R02 as business stories, then the promotion, coverage, roadmap, matrix and docs (`docs/features/b2b-operational-chain.md`).

## Rollback

No schema; reverting the code removes the step and the reads. Reservations made through it stay ordinary reservations.

## Complexity Tracking

No Constitution violations.
