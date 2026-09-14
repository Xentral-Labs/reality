# Feature Specification: Multi-position invoices
**Language**: English
**Created**: 2026-09-08
**Status**: Accepted by the owner: implement multiple invoice positions before financial corrections.

## Context and Intent
### Problem
The invoice form only accepts one order position, forcing separate invoices for a normal multi-position order.
### Scope
Record one customer or supplier invoice containing one or more selected positions of the same order. Capture each stated quantity and line amount plus the independently stated invoice total. Use the existing common review and confirmation flow.
### Non-Goals
No multiple-order consolidation, repeated partial billing of an already invoiced order position, tax/price calculation, credits/stornos, bank execution, schema expansion, deployment or legacy retirement.

## User Scenarios & Testing
### US1 — Record a multi-position invoice (P1)
Select an order, add/remove selected positions, enter quantities and stated line amounts, invoice number and stated total. Review all positions and confirm once.
Acceptance: two positions create one invoice, two linked evidence lines and one balanced posting group at the stated invoice total, for both customer and supplier directions. Neither line amounts nor header total are recalculated; differing stated totals are preserved.
### US2 — Review and recover consistently (P1)
The same invoice is reviewable from Finance, Actions, Chat and Decisions. Editing/reloading preserves all selected positions and amounts. A lost response is recoverable without duplicate records.
Acceptance: changed or billed positions invalidate review; a failed position creates no partial invoice; legacy one-position proposals and receipts still work.
### Edge Cases
Empty/duplicate positions, mixed orders/tenants/types, excess or invalid quantities, amounts that cannot be stored unchanged, an already invoiced position, concurrent overlapping selections, malformed or incomplete proof, narrow layouts and translations.

## Requirements
- **FR-001**: Form supports adding/removing one or more distinct positions from the selected order, each with explicit quantity and line amount; header total stays independently stated.
- **FR-002**: Shared validation rejects invalid, foreign, duplicate, mixed-order, already-billed and unrepresentable inputs before writes. Retain the existing no-repeat-billing boundary.
- **FR-003**: Confirmation records one lossless manual source, one invoice, all linked lines and two balanced postings atomically, without stock/payment effects or recomputing received values.
- **FR-004**: Review binds every selected position and reference; overlapping unresolved execution blocks duplicates. Exact receipts include all invoice lines and remain recoverable after later activity.
- **FR-005**: Existing single-position services/tools/proposals retain their contracts. Common application and MCP tools expose multi-position input without alternate adapter business rules.
- **FR-006**: Shared Finance/Actions/Chat/Decisions card preserves multi-position editing/reload/recovery, Inspector links, four languages, keyboard operation and responsive light/dark layouts.

## Key Entities
Existing SourceRecord, Document, DocumentLine with billed_document_line_id, LedgerEntry, ChangeProposal and BusinessEvent. No new identity or status fields.

## Success Criteria
Two positions can be entered, reviewed, confirmed and inspected as one invoice in both directions. Invalid later positions leave no financial records. Every selected line is represented in review and verified receipt. Existing single-position journeys and full required gates pass.

## Assumptions and Dependencies
The owner approved multi-position invoices; same-order selection is the initial coherent scope. Further partial invoices for one already billed position remain a separately stated limitation. Existing document lines already represent the required relation; no schema exception is required. Tests precede implementation where practical. Shared preview checks are read-only; business mutations use isolated test databases.

## Requirement Traceability
| Requirements | Tests | Implementation |
| --- | --- | --- |
| FR-001/006 | T004 | T005 |
| FR-002/003/005 | T001 | T002 |
| FR-004/005 | T001 | T003 |
| FR-001–006 | T006 | T006 |
