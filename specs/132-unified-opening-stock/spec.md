# Reviewed opening stock in the unified warehouse
**Language**: English
**Created**: 2026-09-08
**Status**: Accepted within the continued migration of retained warehouse actions

## Context and Intent
### Problem
The unified app can receive against orders but lacks a clear way to record the stock a company already has when starting. Existing opening-stock tools and practice workflows should be reused without confusing an additive entry with a stock count.
### Scope
One positive untracked opening-stock movement for a stocked item and stock-capable destination, optional occurrence time, current-stock review, explicit confirmation, exact receipt/recovery and existing correction access. Warehouse, launcher and matching Chat/Decisions share the same form.
### Non-Goals
Setting a target stock balance, inventory counts, bulk imports, lots/serials/handling units, source attachment, general adjustments/transfers/returns, new ledger entries, new schema or retiring Playground.

## User Scenarios & Testing
### US1 — Start with held stock (P1)
A member selects item/location and quantity. The review shows physical stock before, added quantity and stock after; reserved stock stays unchanged. Confirm records a movement; preview/cancel do not change stock.
### US2 — Prevent misleading or duplicate changes (P1)
Unsupported tracked/non-stocked/foreign inputs, invalid precision and changed stock/references fail before execution. Existing stock is allowed: 10 plus 5 becomes 15, never 5. Reopening the same proposal cannot create another movement.
### US3 — Recover and explain (P1)
Reload or a lost response restores exact review/receipt. Reconcile uses attributable movement/event evidence without replay. A later correction changes the current observation but preserves the original receipt. The movement opens in Inspector and remains correctable via existing Warehouse controls.
### Edge Cases
Zero/negative/nonfinite/overprecision quantities, inactive reference changes, unsupported extra fields, stock changing during confirmation, concurrent proposals, uncommitted versus committed failure, ambiguous event/receipt, no choices and company switch.

## Requirements
- **FR-001**: Offer opening stock in Warehouse and Actions and route matching company Chat/Decisions proposals to the same typed form. Select tenant-scoped item/location references with bounded search, positive quantity and optional local occurrence time.
- **FR-002**: Accept only untracked stocked items, a destination allowing stock, quantity exactly representable at current movement precision (18,4), optional occurrence time. Reject unsupported source/from-location/commitment/tracking/reason/return fields; preserve existing active/inactive core semantics. Default time is execution time. No hidden quantity rounding.
- **FR-003**: Shared review snapshots item/location identity and relevant attributes, current physical/reserved balance, exact canonical intent and additive before/after effect. Revalidate under existing tenant mutation lock; changed displayed state requires fresh review. No browser business arithmetic or direct ORM writes.
- **FR-004**: Existing movement_create/record_movement creates the movement and attributed event. Existing stock is additive; no document, commitment, reservation or financial record is invented. Manual provenance is the explicit proposal and event, not a fabricated external source.
- **FR-005**: Exact proposal/request replay is inert. Same-pool unresolved movement/reservation/correction actions block overlapping new work in both directions. Receipt requires exactly matching movement/event/intent and canonical output; current observation is separate. Committed-but-unsettled receipt recovery never reexecutes. Historical proof survives later corrections.
- **FR-006**: Use existing tenant/active-user/service controls and exclude Playground from this new company flow; existing practice opening stock remains unchanged. Unknown results require checking; persistent request identity protects lost preparation; company switch discards visible state.
- **FR-007**: Four languages, modal keyboard/focus behavior, responsive light/dark form/review/result and explicit empty/error states. Link verified movement and event; use existing movement correction instead of a duplicate correction path.

## Assumptions and Dependencies
Movement quantity uses Numeric(18,4), canonical IDs identify references, and opening stock adds quantity without requiring zero previous stock. Existing source-free manual movement semantics already apply; no new source record is fabricated. Core already serializes movements and reference updates. Reviewed snapshots are guards, not new stock authorities. The owner requested continued migration; this is the retained A2 opening-stock slice.

## Success Criteria
A member can start stock from Warehouse, review exact effect, confirm and inspect it without old UI. No preview/cancel/replay changes stock. Stale and concurrent reviews cannot silently invalidate displayed before/after values. All requirements pass backend/browser and required regression gates.

## Requirement Traceability
| Requirement | Tasks | Proof |
|---|---|---|
| FR-001/007 | T004/T005 | Warehouse/launcher/Chat/Decisions and localized browser |
| FR-002/003/004 | T002/T003 | Validation, additive state, no preview write and stale-state tests |
| FR-005 | T002/T003/T005 | Independent concurrent execution, overlap, exact recovery and historical receipt |
| FR-006 | T002/T004/T005 | Tenant/practice/API boundary and response-loss/company browser |
