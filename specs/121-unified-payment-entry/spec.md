# Feature Specification: Unified Payment Entry

**Language**: English
**Created**: 2026-09-08
**Status**: Accepted through the owner's continuation of the proposed payment increment.

## Context and Intent
### Problem
The unified Finance view records invoices but still needs the older presentation to record
and allocate payments against them.
### Scope
Record a customer or supplier payment and allocate its stated amount to one selected invoice,
using shared Finance/Actions/Chat/Decisions review, confirmation and recovery.
### Non-Goals
No bank transfer initiation, bank connection, bulk payment run, multi-invoice split, allocation
of previously unallocated payments, refunds/credits, new schema, deployment or legacy retirement.
No test financial actions in the shared local company database.

## User Scenarios & Testing
### US1 — Record a payment against an invoice (P1)
Choose customer/supplier and a searchable open invoice. Enter actual payment amount and optional
reference/effective time. Review invoice, party, currency, payment and open-before/open-after.
Acceptance: confirmation creates balanced payment postings and one allocation; partial payment
leaves the remainder open and a later distinct payment can settle it. Preparation is inert.
### US2 — Resume and inspect safely (P1)
Review the same proposal from Actions, Chat or Decisions, edit or reject, reload and recover a
lost execution response. Acceptance: no duplicate effects; changed invoice or allocation invalidates
review. Later payment reversal does not erase the historical creation receipt.
### Edge Cases
Foreign/wrong-type/unposted/reversed/settled invoice; nonpositive/nonfinite/excess amount; foreign
source; same human reference for legitimate payments; stale open amount; unresolved same-invoice
execution; incomplete/malformed attributable proof; current read failure; narrow screens and languages.

## Requirements
- **FR-001**: Provide searchable invoice selection for customer/supplier payments, actual amount,
  optional reference/time, and preserve supported richer canonical intent on edit.
- **FR-002**: Pure shared preview validates invoice type, posted active control entry, scoped source,
  positive amount representable without rounding and no greater than open amount, with party/currency and derived before/after values.
- **FR-003**: Explicit confirmation binds exact intent and current invoice/allocation/reference state;
  current tenant membership and practice policy are checked. Competing same-invoice changes cannot
  silently consume stale reviewed capacity.
- **FR-004**: Canonical services atomically record payment evidence, two balanced postings and a
  settlement allocation. Record the stated amount, reuse any supplied source and expose absence of
  supplied source honestly. Do not invent provenance, initiate transfers or move stock.
- **FR-005**: Prove and reconstruct the exact canonical ledger-only receipt from attributable
  document/posting/allocation evidence without rerunning mutation. Reject ambiguous proof and guard
  unresolved same-invoice actions. Historical proof is separate from current open/allocation state.
- **FR-006**: Finance, Actions, Chat and Decisions use one form/review/recovery flow, with
  edit/reject/reload, verified invoice/payment/Inspector links and loading/error/empty states.
- **FR-007**: Preserve existing tables/actions, keyboard usability, four languages and light/dark
  presentation at 390 and 1440 px. Keep business calculations out of the browser.

## Key Entities
Existing Document, LedgerEntry, SettlementAllocation, ChangeProposal, BusinessEvent and optional
SourceRecord. No document payment-status field; open amounts derive from postings/allocations.

## Success Criteria
Both payment directions and partial-to-full settlement work without old forms or JSON. Every
mutation requires a current review; replay and recovery do not duplicate effects. All mapped tests
and complete regression gates pass.

## Assumptions and Dependencies
Owner accepted continuing with payment recording and allocation. Existing canonical selected-invoice
payment tools are authoritative. Optional source remains optional; do not reuse an invoice source
as payment provenance. Missing payment reference/time retain their existing execution-time defaults.
No unresolved clarification or schema exception remains.

## Requirement Traceability
| Requirements | Tests | Implementation |
| --- | --- | --- |
| FR-001/006/007 | T004 | T005 |
| FR-002/004 | T001 | T002 |
| FR-003/005 | T001 | T003 |
| FR-001–007 | T006 | T006 |
