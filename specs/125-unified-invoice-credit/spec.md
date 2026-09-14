# Feature: Invoice-linked customer credit entry
**Language**: English
## Context and Intent
### Problem
The unified product can invoice and reverse postings but cannot record a partial customer credit directly from an invoice.
### Scope
One customer invoice, multiple selected positions and partial quantities, stated line/header amounts, reason and explicit optional netting amount. Shared Finance/Actions/Chat/Decisions review and recovery.
### Non-Goals
No refund or bank transfer, stock movement, supplier credit entry, automatic prices/taxes, amount-only repeated price adjustments, new schema, deployment or legacy retirement.
## User Scenarios & Testing
US1: Open a customer invoice, select positions/partial quantities, enter stated credit values/reason, inspect impact and confirm. The credit can be financial without a physical return. Both unpaid and paid invoices are supported; only an explicitly supplied allocation amount reduces an open invoice.
US2: Reload/edit/reject or recover a lost response without creating a second credit. Inspect credit→invoice→order and original source. Old return-based credit proposals still work.
Edge cases: two invoices for one order position, legacy order-linked credit ambiguity, over-credit quantity/amount, unposted credit evidence, full credit reversal, reversed/unposted invoices, foreign/mixed/duplicate positions, fractional precision, stale payment/reversal/credit state, concurrency and failure rollback.
## Requirements
- **FR-001**: Reuse billed_document_line_id for credit_note→sales_invoice line→order line; preserve legacy credit→order. Derive remaining invoice-position quantity and header credit amount from linked credit evidence; unposted credit counts and fully reversed posted credit releases capacity. Do not infer attribution of legacy order-linked credit: block the affected invoice with guidance. Preserve received source values.
- **FR-002**: Extend sales_credit_record with mutually exclusive invoice_id/lines/reason/allocation_amount shape. Validate positive exact four-place quantities and stated amounts, distinct positions from one posted unreversed sales invoice, and available capacity. Existing order-line return credit stays compatible. No return is required for the new financial-credit shape; it must not create a missing-return exception.
- **FR-003**: Atomically record immutable source, one credit document and all lines, balanced canonical credit postings and optional explicitly stated settlement against the selected invoice. Allocation cannot exceed credit amount or invoice open amount. No refund/stock effects; netting zero works for paid invoices.
- **FR-004**: Shared state-bound confirmation, tenant locking, overlap guards and exact event/receipt recovery prevent stale or duplicate effects. Old historical proofs remain valid after later reversal/settlement. Update legacy return entitlement to recognize invoice-linked credits without fabricating return movements.
- **FR-005**: Finance invoice rows and action menu launch the same searchable multi-position form as Chat/Decisions. Show remaining quantities, stated amounts, reason, invoice balance before/after and credit left to settle. Four languages, responsive layout, edit/reject/reload/recovery and Inspector links.
## Assumptions and Dependencies
Owner authorized the proposed first step, credit entry directly from the invoice. An optional question offered return-only vs financial credit; default assumption is financial credit without mandatory return. The existing posting service already supports this separation. Existing typed self-FK supports the shortest relationship without schema expansion. A legacy credit without invoice attribution blocks affected new entry instead of guessing. Refund entry remains the next independent increment.
## Success Criteria
Partial multi-position customer credits can be reviewed and posted from the unified app; explicit netting changes the selected invoice correctly. Excess, stale and concurrent attempts are inert; isolated and browser gates pass without shared business test mutations.

## Requirement Traceability
| Requirement | Tests | Implementation |
|---|---|---|
| FR-001–004 | T001 | T002/T003/T004 |
| FR-005 | T005 | T004/T005 |
| FR-001–005 | T006 | T006 |
