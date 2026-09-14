# Feature Specification: Unified Order Entry

**Language**: English

**Created**: 2026-09-08
**Status**: Accepted for implementation through the owner's continuation instruction.
**Input**: Complete order entry in the unified app with a shared form, exact preview and confirmation.

## Context and Intent
### Problem
Operators can fulfill existing orders but still need old screens to record agreements.
### Scope
Multi-line customer orders and supplier purchase orders in Orders, Actions and matching
company Chat/Decisions reviews. Preserve entered references and stated amounts. Continue
from recorded orders to their line-specific deliveries.
### Non-Goals
No pricing/tax calculation, invoice/payment creation, stock mutation at entry, order editing,
new schema, deployment, old UI retirement or test business mutations in the shared database.
Advanced commercial references are preserved in canonical proposals; no price-list authoring.

## User Scenarios & Testing
### US1 — Record an agreement (P1)
Select sales or purchase, company party, customer/supplier and warehouse, enter a reference,
currency, stated total and one or more item lines with quantity, unit price and stated amount.
Add/remove lines without JSON. Review all values and confirm once.
**Acceptance**: Two lines produce one order and two correctly directed deliveries; preparation
creates neither evidence nor operational records. Stated totals can differ from line sums.
### US2 — Continue from a recorded order (P1)
Open the order and each resulting delivery. Reserve/ship customer lines or receive supplier lines.
**Acceptance**: Partial work affects only its delivery; entry itself changes no stock or ledger.
### US3 — Review reliably across entry points (P1)
Use the same reviewed action from Orders, Actions, Chat and Decisions. Reload, edit and reject.
**Acceptance**: Changed references invalidate review; unauthorized confirmation has no effect.
A lost execution response is recovered from exact attributable evidence without creating another order.

### Edge Cases
Missing/foreign references; empty lines; nonpositive/nonfinite quantities and amounts; duplicate
human references; missing totals; item defaults changing; unsupported/extra canonical fields;
concurrent confirmation; ambiguous evidence; downstream fulfillment after creation; response loss;
practice admission; multiple languages and narrow screens; searchable reference lists.

## Requirements
- **FR-001**: Provide sales and purchase order entry with searchable tenant references and editable
  line groups, entered amounts and optional dates/descriptions. Require complete information and
  preserve richer supported canonical intent when editing.
- **FR-002**: Preview through shared service validation with no business writes; show party, warehouse,
  direction, currency, all lines and stated total. Never calculate source-stated amounts.
- **FR-003**: Require explicit confirmation bound to exact intent and current relevant references,
  rechecking tenant access and practice policy. Edits require a new review; reload retains proposal.
- **FR-004**: Atomically record lossless manual Source, Document/Lines and correctly directed
  Commitments with shortest true links. Order entry creates no reservation, movement or posting.
- **FR-005**: Prove exact action-attributed receipt and reconstruct an unknown outcome read-only.
  Same proposal cannot execute twice. Unknown identical-intent requests cannot create a duplicate;
  unrelated legitimate orders may share human numbers. An already recorded identical source payload
  is rejected before another business write. Current observation remains separate from
  historical proof, including after fulfillment or legitimate evidence correction.
- **FR-006**: Share action UI across Orders, launcher, Chat and Decisions; provide recorded-order and
  line-delivery links, Inspector access, explicit loading/error/retry and useful empty states.
- **FR-007**: Preserve table defaults and existing actions; usable localized light/dark forms at
  390 and 1440 px in English, German, Dutch and Spanish. No raw JSON required for entry.

## Key Entities
Existing ChangeProposal, SourceRecord, Document, DocumentLine, Commitment and BusinessEvent.
Party, Item and Location are tenant-scoped references; opaque IDs establish identity.

## Success Criteria
- SC-001: A two-line sales and purchase order can each be entered without the old app or JSON.
- SC-002: All four entry points show the same review; stale/foreign/replayed/unknown outcomes never
  silently create another order. Original supplied totals are recoverable from source evidence.
- SC-003: Every requirement has executable evidence and all required regression gates pass.

## Assumptions and Dependencies
Owner approved the proposed next order-entry increment. Existing canonical manual-order service
is authoritative, including explicit company party and stated line/document totals. Existing
proposal/review infrastructure and reference registers are reused. No inferred company identity,
price calculation or automatic fulfillment. Existing practice semantics remain outside this shell.

## Requirement Traceability

Repository language: English. Conversation may use German.

| Requirements | Tasks | Executable evidence |
| --- | --- | --- |
| FR-001/006/007 | T007–T009 | unified-order-entry-browser.mjs |
| FR-002/004 | T003/T004 | test_unified_order_entry.py |
| FR-003/005 | T003/T005/T006/T009 | test_unified_order_entry.py and browser recovery |
