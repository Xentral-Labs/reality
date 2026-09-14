# Unified customer-wide delivery holds
**Language**: English
**Created**: 2026-09-08
**Status**: Accepted within the owner's continued migration of retained operational controls.

## Context and Intent
### Problem
A delivery case explains a customer-wide hold but cannot release it in the unified app. Operators need to distinguish a customer-wide control from a hold on a single delivery.
### Scope
Reviewed placement and release of customer-wide delivery holds, available from a customer delivery, customer master data, Actions and matching Chat/Decisions. Preserve existing reservation/shipment gating, reasons, notes and historical traceability.
### Non-Goals
Document-wide holds, automatic credit decisions, supplier controls, partial hold release, new release-reason fields, inventory/financial changes, new schema, legacy retirement or changing general tool semantics.

## User Scenarios & Testing
### US1 — Pause a customer's deliveries (P1)
An operator selects a customer, a supported reason and optional note. Review identifies the customer and makes clear that shipments for its current and future customer deliveries are blocked; new reservations remain allowed. Confirm records one customer hold; preview or cancel does not.
### US2 — Release the customer-wide block (P1)
A blocked delivery offers a clearly named customer-wide release. Review shows the exact active customer hold set and notes. Confirm releases only that set; delivery-specific holds remain and no stock, reservation, open quantity or money is changed. Release does not promise that a delivery is otherwise ready.
### US3 — Recover and explain (P1)
The same proposal opens from all supported entries and after reload. Lost preparation uses the same request identity. Unknown execution requires status checking, and attributable recorded evidence can settle the result without repeating a mutation. Historical placement remains verifiable after release and release remains verifiable after a new hold.
### Edge Cases
Already held, no active hold, multiple historical active holds, identical reasons after release/reapply, foreign IDs, non-customer party, inactive customer, invalid reason/note, empty search, concurrent confirmation/reference change, revoked membership, lost replies, event/receipt mismatch and company switch.

## Requirements
- **FR-001**: Provide one customer-wide hold/release experience from the customer delivery case, selected customer master data, Actions and matching company Chat/Decisions. Label broader scope explicitly and keep individual delivery controls distinct.
- **FR-002**: Placement accepts one existing customer, supported reason and optional original note. Release reviews all active delivery holds of that customer. Reject no-op, foreign, unsupported field and invalid inputs. Preserve existing inactive-customer and general non-customer tool behavior outside this bounded form.
- **FR-003**: Review binds exact customer identity/relevant attributes, normalized intent and the full active hold set; confirmation rechecks authorization and state. Changed state requires a fresh review. Same-customer unresolved hold actions block overlapping new hold work. Concurrent confirmations cannot silently change the reviewed hold set.
- **FR-004**: Reuse the existing business actions and reservation/shipment gating. Customer holds apply to existing and future customer deliveries; release leaves delivery-specific holds and all quantities/financial records unchanged. Do not create document fulfillment fields or external evidence for a manual decision.
- **FR-005**: Attribute each mutation to its proposal and verify exact event, hold records and receipt. Replay has one effect, recovery never reexecutes, and historical proof is separate from current hold state. Link customer and event through Inspector.
- **FR-006**: Preserve tenant, active-user and practice boundaries. Persist preparation identity before transport; unknown execution blocks writes until checking status. Company changes discard visible state; cancellation does not execute the proposal.
- **FR-007**: Four-language, responsive light/dark, accessible modal form/review/result with bounded search, clear empty/error states, escaped original notes and keyboard/focus behavior.

## Key Entities
Existing Customer, PartyHold, CommitmentHold, Commitment, ChangeProposal and BusinessEvent. Customer-wide holds belong to the party, not a document or duplicated per-delivery state.

## Assumptions and Dependencies
This is the retained A4 customer-wide increment, authorized by the owner's continued migration. Existing services define hold reasons and release the complete active customer hold set. Current/future scope is shown without inventing an affected-delivery count or shipment-readiness promise. Reservation permission is unchanged: the hold blocks linked customer shipments only. Existing general party tools retain their broader compatibility; reviewed customer entry is narrower. Specs 107/117/132 provide common review, delivery controls and recovery patterns.

## Success Criteria
All five entries reach the same exact review. Preview/reject/replay leave business quantities unchanged. Stale, concurrent, foreign, lost-response and historical-recovery scenarios pass. The user can release a customer-wide blocker without entering the old UI, while seeing any remaining individual delivery blocker.

## Requirement Traceability
| Requirement | Tasks | Proof |
| --- | --- | --- |
| FR-001/007 | T004/T005 | All entries, localized responsive browser and keyboard |
| FR-002/003/004 | T002/T003 | Exact validation, stale/concurrent hold state and existing/future gating |
| FR-005/006 | T002/T003/T005 | Attribution, tenant/practice/API, replay and recovery/history |
