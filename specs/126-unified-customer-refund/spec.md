# Feature Specification: Customer refunds from open credits

**Created**: 2026-09-08
**Status**: Complete; verified locally
**Language**: English
**Input**: Owner approved the proposed next increment: record actual customer refunds from open credit notes, including partial amounts, reference, review and shared Finance/Actions/Chat entry.

## Context and Intent
### Problem
Operators can record customer credits but cannot finish their repayment through the unified action experience.
### Scope
Record a refund already made against one open customer credit. Review its amount and remaining credit, explicitly confirm, recover uncertain outcomes and inspect the evidence through the same experience from Finance, Actions, Chat and Decisions.
### Non-Goals
Initiating bank transfers, supplier refunds, automatic refunding, batch allocation, new credit policy, schema expansion, legacy UI retirement or creation of business records in the shared development company.
### Existing Contracts
- docs/WEB_SPEC.md
- specs/121-unified-payment-entry/spec.md
- specs/123-unified-financial-reversal/spec.md
- specs/125-unified-invoice-credit/spec.md

## User Scenarios & Testing
### User Story 1 - Record an actual refund (Priority: P1)
An operator selects an open customer credit and supplies the amount actually repaid, an optional reference and effective time.
**Independent Test**: A credit with 70 open accepts a 20 refund and has 50 remaining after confirmation.
**Acceptance Scenarios**:
1. Given 70 open, when the operator reviews 20, then the review shows 70 before and 50 after and business records remain unchanged until confirmation.
2. Given the confirmed review, when recorded, then the stated amount/reference/time, outgoing cash evidence and allocation refer to that credit and party; stock and invoice quantities do not change.
3. Given no eligible credits, when opening the form, then an explicit empty state appears; foreign, reversed, unposted and exhausted credits cannot be refunded.
### User Story 2 - Keep execution trustworthy (Priority: P1)
The operator can edit or reject a proposal, refresh stale reviews and recover a lost confirmation response without repeating the refund.
**Independent Test**: Lost-response reconciliation verifies the original refund once; later reversal reopens the credit without invalidating historical proof.
**Acceptance Scenarios**:
1. Given an intervening allocation or reversal, when confirming an older review, then it is rejected without new financial effects.
2. Given simultaneous refunds, when their amounts exceed the shared remainder, then only allowable amounts record; unresolved related execution blocks conflicting actions.
3. Given missing or inconsistent attributed evidence, when checking an outcome, then it stays unresolved; complete exact evidence recovers without a new refund.
4. Given a recorded refund subsequently reversed, when inspecting it, then the original receipt remains verifiable while the current credit balance reflects the reversal.
### User Story 3 - One action across the app (Priority: P2)
Finance offers a selected-credit action; the action launcher, chat proposals and decisions use the same form and review.
**Independent Test**: All entry points open the refund review and link to the credit, refund and original evidence.
**Acceptance Scenarios**:
1. Given a customer credit row, when refund is selected, then the form retains the exact selected credit.
2. Given a chat or saved proposal, when opened, then the same confirmation and recovery controls appear.
3. Given each supported language and desktop/mobile light/dark layout, when used, then labels, controls and evidence links remain usable.
### Edge Cases
Nonpositive/nonfinite/overprecision or excessive amounts; wrong document type or tenant; already netted credit; omitted reference/time; duplicate request; concurrent netting/refund/reversal; posting rollback; missing source; historical reversals; empty and paginated selectors.

## Requirements
### Functional Requirements
- **FR-001**: Select one open customer credit and record a stated positive refund amount, optional reference and effective time, including partial refunds up to its current open amount.
- **FR-002**: Show party, credit, currency, amount and remaining credit before/after; preparation does not record financial effects; confirmation is explicit; edit/reject is supported.
- **FR-003**: Reject invalid, foreign, unsupported, unposted, reversed, exhausted and excessive requests atomically, preserving exact received amounts without rounding.
- **FR-004**: Bind confirmation to reviewed evidence and allocations; serialize competing writers and block related unresolved actions to prevent over-refunding.
- **FR-005**: Recover lost outcomes using exact attributable evidence and receipts without re-execution; keep historical proof separate from current reversal/allocation observations.
- **FR-006**: Provide Finance (including selected credit), Actions, Chat and Decisions through the shared experience, with usable loading/empty/error states and four-language desktop/mobile support.
- **FR-007**: Clearly describe recording an actual refund, expose credit/refund/ledger/source evidence links and retain existing payment, credit, reversal and Playground behavior.
### Domain and Traceability Requirements
- **DR-001**: Preserve stated input and any original source; refund evidence links to outgoing cash and receivable postings; settlement allocation uses the shortest existing ledger links to the credit.
- **DR-002**: Derive open amounts from active postings/allocations; do not store new authoritative balances or change inventory/invoice quantities.
- **DR-003**: All reads and writes are tenant-scoped and use shared services/application tools across adapters; no schema expansion.
### Key Entities
Existing credit note, refund evidence, original source where supplied, posting group, settlement allocation and confirmed action.

## Success Criteria
- **SC-001**: A partial refund leaves the exact expected credit remainder and is inspectable from all four entry points.
- **SC-002**: Invalid, stale and concurrent excessive requests record no extra refund; response loss recovers exactly once.
- **SC-003**: Every FR/DR has executable evidence and all required regression gates pass before completion.

## Assumptions and Dependencies
Owner authorization covers this bounded increment. Reference and effective time remain optional like existing payment entry; absent reference/time are assigned at recording. Existing customer refund service semantics and legacy Playground authorization remain authoritative. No bank integration is added. Financial tests use isolated databases and browser fixtures.

## Requirement Traceability
| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-001, FR-002 | US1.1–2 | Partial refund and shared review tests; browser form/edit/reject |
| FR-003, DR-003 | US1.3; edge cases | Tenant/precision/capacity/atomic rollback tests |
| FR-004 | US2.1–2 | Stale, unresolved and independent-connection concurrency tests |
| FR-005 | US2.3–4 | Exact receipt, tampering, response loss and reversal tests |
| FR-006 | US3.1–3 | HTTP boundary and four-entry/language/responsive browser tests |
| FR-007, DR-001, DR-002 | US1.2; US3.1–2 | Provenance/ledger/allocation and adjacent regression tests |
