# Feature Specification: Partial invoicing and rebilling
**Language**: English
**Created**: 2026-09-08
**Status**: Owner-approved continuation: complete partial invoicing and rebilling after reversal.

## Context and Intent
### Problem
An order position currently permits only one invoice even when its quantity was only partially billed. Reversed invoice evidence also permanently blocks renewed billing.
### Scope
Permit successive invoices against remaining order quantities in both customer and supplier flows. Show ordered, effectively invoiced and remaining quantities during selection/review. A complete invoice reversal releases its invoiced quantity for renewed billing while preserving history.
### Non-Goals
No price/tax/remainder-amount calculation, invoice editing, partial ledger reversal, credit/refund creation, multiple-order consolidation, new schema, deployment or retirement. Do not rewrite or reject received external evidence merely because it reports overbilling.

## User Scenarios & Testing
### US1 — Invoice part, then remainder (P1)
Select one or more positions, enter a partial quantity and stated amounts, then later invoice the remainder.
Acceptance: each position's active invoiced quantities stay within its order quantity through the canonical selected-order invoice tools; excess intent fails atomically. Header and line amounts remain independent received values. Existing excess evidence remains visible and leaves zero available quantity.
### US2 — Reverse and invoice again (P1)
Reverse an invoice, inspect released availability and record a new invoice against it.
Acceptance: quantities are released only if all original posting groups attached to that invoice have been reversed. Invoice evidence without postings still consumes quantity. Payment reversal and credit notes do not release billing quantity. Old receipts remain verifiable.
### Edge Cases
Multiple groups on one invoice, unposted evidence, reductions of order quantity, overbilling already stated by another source, fractional quantities, simultaneous invoices, stale review after another invoice/reversal, foreign lines, mixed directions, exhausted selection and legacy proposals.

## Requirements
- **FR-001**: Derive ordered/effectively invoiced/remaining quantities and evidence links from matching invoice lines and original posting-group reversal state. Unposted invoices count; credit notes and payments do not affect quantity; remaining never falls below zero while actual billed totals remain visible.
- **FR-002**: Both single/multi-position canonical invoice paths permit positive exact partial quantities up to remaining quantity and reject excess without partial writes. Continue preserving stated money independently.
- **FR-003**: Bind invoice reviews to current billing evidence/reversal state and serialize invoice, manual evidence/correction, posting and reversal writers consistently. Stale/concurrent execution cannot silently consume a different reviewed quantity.
- **FR-004**: Full invoice reversal makes its quantities available again only after every attached original group is reversed; review shows projected availability using the same derivation. Historical invoice and reversal receipts remain unchanged and verifiable.
- **FR-005**: Unified selection and review display quantity availability, disable exhausted choices, support fractional partial quantities and show source links. Shared Finance/Actions/Chat/Decisions flows and all four languages remain usable.
- **FR-006**: Preserve existing canonical inputs/receipts, read and mutation policy, tenant isolation, atomicity, response-loss recovery and legacy historical proof. No new stored billing state.

## Key Entities
Existing order/invoice DocumentLines, Document, LedgerEntry, LedgerReversal, SourceRecord, BusinessEvent and ChangeProposal. Quantity availability is a read-time observation.

## Success Criteria
Sales and purchase orders can be partially invoiced, completed, reversed and rebilled in one UI. Excess/stale/concurrent requests fail without duplicate quantities; all historical receipts remain explainable. Complete required regression gates pass.

## Assumptions and Dependencies
Owner approved partial invoices and renewed billing after full reversal. Every original group attached to an invoice must be reversed before release; absence or partial reversal is insufficient. Received unposted/overbilled evidence is retained and consumes availability. The selected-order operational invoice tools enforce available quantity, while generic evidence recording retains source authority. Shared local preview checks are read-only. No unresolved clarification or schema exception.

## Requirement Traceability
| Requirements | Tests | Implementation |
| --- | --- | --- |
| FR-001/002/003/004/006 | T001 | T002/T003 |
| FR-005 | T004 | T005 |
| FR-001–006 | T006 | T006 |
