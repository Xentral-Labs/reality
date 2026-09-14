# Feature Specification: Unified financial reversal
**Language**: English
**Created**: 2026-09-08
**Status**: Owner-approved next increment after multi-position invoices.

## Context and Intent
### Problem
The new app records invoices and payments but lacks their common, explainable reversal path.
### Scope
Select a recorded financial posting group, state a reason, review inverse postings and effects on open items/payment allocations, then explicitly confirm a complete reversal. Use one shared Finance/Actions/Chat/Decisions card.
### Non-Goals
No refund/bank transfer, credit-note creation, partial reversal, invoice editing/replacement, renewed billing of already billed positions, schema expansion, deployment or legacy retirement.

## User Scenarios & Testing
### US1 — Reverse a mistaken invoice or payment (P1)
Find the posting through Finance or Actions, give a reason and review exact effects before confirmation.
Acceptance: one inverse group is recorded, originals remain intact, payment reversal reopens its allocated invoice amount, and invoice reversal removes its obligation while making its still-active payment allocation unallocated. Previously inactive allocations are distinguished from newly inactive ones. Stock is unchanged.
### US2 — Resume and recover safely (P1)
Review from Chat/Decisions, edit/reject, reload and recover an uncertain result.
Acceptance: current authorization/state is required; competing financial changes invalidate stale review; one attributed receipt is reconstructed without repeating mutation. Later financial activity does not erase historical proof.
### Edge Cases
Foreign, missing, reversed and reversing groups; blank reason; changed allocation or counterpart reversal; unresolved overlapping payment/reversal; malformed event or inverse proof; current read failure; narrow screens and four languages.

## Requirements
- **FR-001**: Search recorded posting groups with human document/party context and permit a reason-based reversal from Finance and global Actions.
- **FR-002**: Shared read-only review shows exact inverse amounts/accounts, execution-time timestamp semantics, newly versus already inactive allocations, and affected invoice/payment before/after values without temporary writes.
- **FR-003**: Explicit confirmation binds intent and all relevant current financial state and authorization. Guard unresolved overlapping actions across payments and reversals.
- **FR-004**: Reuse canonical full-group reversal atomically, preserve original evidence, and attribute the existing reversal event to the executing proposal. Retain existing direct API and canonical receipt contracts.
- **FR-005**: Verify exact relation, inverse entries and attributed event; recover response loss without executing again. Historical proof and current observations remain separate.
- **FR-006**: One localized responsive card supports Finance/Actions/Chat/Decisions, edit/reject/reload/recovery, Inspector links and loading/error/empty states. Explain that invoice reversal neither deletes evidence nor enables repeat billing.

## Key Entities
Existing LedgerEntry, LedgerReversal, SettlementAllocation, Document, SourceRecord, BusinessEvent and ChangeProposal. No new table or document status.

## Success Criteria
Both invoice and payment reversals can be completed and inspected through the unified shell. Exact before/after and unknown-result proof pass in both customer and supplier directions. Invalid or stale work produces no inverse group. Full required core/web/browser gates pass.

## Assumptions and Dependencies
Owner approved financial corrections/stornos; this increment implements existing complete posting-group reversal, with no new credit or replacement semantics. Shared preview data is read-only for testing. Tests are planned and added first. No unresolved clarification or constitutional exception.

## Requirement Traceability
| Requirements | Tests | Implementation |
| --- | --- | --- |
| FR-002/003/004/005 | T001 | T002/T003 |
| FR-001/006 | T004 | T005 |
| FR-001–006 | T006 | T006 |
