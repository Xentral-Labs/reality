# Feature Specification: Unified Invoice Entry

**Language**: English
**Created**: 2026-09-08
**Status**: Accepted through the owner's continuation of the proposed invoice-entry increment.

## Context and Intent
### Problem
Finance can explain invoices but entry still requires the older presentation.
### Scope
Customer and supplier invoice entry using the existing single-order-line tools,
shared review, confirmation and recovery from Finance, Actions, Chat and Decisions.
### Non-Goals
No consolidated invoices, repeated partial invoices, tax/price calculation, payment allocation,
credits, schema migration, deployment, legacy retirement or shared-database test writes.

## User Scenarios & Testing
### US1 — Record stated invoice evidence (P1)
Search an order, choose its position, enter invoice number, quantity and stated gross amount.
Review the linked order, currency, counterparty and financial effect before confirming.
Acceptance: sales creates receivable/revenue; purchase creates inventory/payable postings;
preparation changes no evidence, stock or money. Fulfillment is not a prerequisite.
### US2 — Resume safely (P1)
Open the same proposal from Chat or Decisions, edit or reject before confirmation, and recover
an unknown response through attributed evidence. Acceptance: no duplicate effects; a changed
order line invalidates review, historical receipt remains valid after later financial activity.
### Edge Cases
Foreign/wrong-direction lines, zero/nonfinite quantities, missing amounts, existing billing,
partial quantity followed by another invoice, stale references, lost responses, malformed evidence,
no matching orders, long labels, narrow screens and all four supported languages.

## Requirements
- **FR-001**: Search tenant-scoped sales/purchase orders and select one line; enter number, quantity,
  stated amount and optional effective time. Explain the single-line/no-repeat billing boundary.
- **FR-002**: Shared pure validation previews the canonical evidence and balanced financial effect.
  Retain stated amount even when it differs from the order; never calculate it or require fulfillment.
- **FR-003**: Require explicit current review confirmation, current tenant access and practice policy;
  changed line/order/reference state rejects execution before business writes.
- **FR-004**: Reuse atomic canonical Source → Document/Line → LedgerEntry tools with no physical
  stock, reservation or payment effects. Existing credit and practice semantics remain intact.
- **FR-005**: Prove an exact attributed receipt, separate historical proof from current observations,
  recover unknown outcomes without repeating execution, and guard unresolved same-line actions.
- **FR-006**: Finance, Actions, Chat and Decisions share entry/review/recovery, readable labels,
  Inspector links, reload/edit/reject and explicit loading/error/empty states.
- **FR-007**: Preserve existing tables/actions, keyboard operation, light/dark and four-language
  usability at 390 and 1440 px.

## Key Entities
Existing ChangeProposal, SourceRecord, Document, DocumentLine, LedgerEntry and BusinessEvent.

## Success Criteria
Both directions work without old forms or JSON. Stale/foreign/replayed requests cannot create
unreviewed effects. Every requirement has executable evidence and required regression gates pass.

## Assumptions and Dependencies
The owner's continuation approves the proposed invoice-entry increment. Existing tools invoice
one order line and reject any subsequent billing evidence on that line, including after a partial
quantity. Existing canonical postings are operational financial records, not statutory accounts.
No clarification or schema exception remains.

## Requirement Traceability
| Requirements | Tasks | Evidence |
| --- | --- | --- |
| FR-001/006/007 | T004/T005 | unified-invoice-entry-browser.mjs |
| FR-002/004 | T001/T002 | test_unified_invoice_entry.py |
| FR-003/005 | T001/T003 | test_unified_invoice_entry.py |
| FR-001–007 | T006 | Full regression gates and final review |

## Delivered-quantity approval guard

The authorized Atlas integration correction adds an optional `delivery_guard` to single-position
sales invoices. Ordinary invoice entry retains its existing ability to invoice before delivery.

- **FR-008**: A caller billing a delivered condition MUST be able to bind the unit and unbilled
  quantity it read for the invoiced order line to the reviewed invoice intent. The guard names no
  condition or line of its own; the order line is the condition's subject. The service MUST derive
  the unbilled quantity with the same rule as shipped-not-billed, not with a second copy of it. The shared service MUST compare
  that guard with current retained delivery less billed quantity while holding the same tenant
  delivery lock as shipment, return, correction and invoice writes through invoice commit.
  Missing, ambiguous, foreign, changed or insufficient delivery evidence MUST refuse the
  guarded invoice before any source, invoice or posting is created. Unguarded billing is unchanged.

Acceptance: prepare a guarded invoice for delivered goods, read the unchanged condition, then
return goods before confirmation. Confirmation must fail without invoice effects. A return
started during invoice confirmation must wait on the shared lock. A stable guard permits one
invoice and replay returns the same receipt. A server without guard support must not be used
by a client relying on this invariant.
