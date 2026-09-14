# Feature Specification: Unified Finance Investigation

**Feature Branch**: `139-unified-app-foundation` (additive isolated increment)
**Language**: English
**Created**: 2026-09-07
**Status**: Owner-authorized continuation of the new App migration.
**Input**: Continue building from the accepted new design, reusing useful existing capabilities.

## Context and Intent

### Problem
Financial investigation still leaves the new App. Operators need to understand outstanding invoices and recorded payments and follow their financial evidence.

### Scope
Add Finance with open items, payments and journal in the unified shell. Preserve canonical controls, currency separation, filtering, pagination and native explanations. Offer existing advanced financial operations through supporting paths.

### Non-Goals
No new financial calculations, postings, payment/allocation/reversal forms, schema, account sheet redesign, reconciliation/aging migration, advice, forecast, Finance AI context extension, practice admission changes, deployment, merge or retirement.

## User Scenarios & Testing

### US1 — Understand what remains open (P1)
An operator opens Finance, selects receivables or payables, filters outstanding/partial/settled items and searches an invoice or party.

Independent proof: a partially settled invoice shows the canonical gross, settled and open amounts. Controls include all filtered records beyond page one and retain separate currencies. Selecting its amount opens its document explanation and supporting records.

Acceptance: default receivables and outstanding; no combined receivable/payable headline; selecting all states reveals settled items; no due date or overdue claim is invented where not held. Missing/foreign records and empty/error states remain explicit.

### US2 — Follow payments and postings (P1)
An operator switches to Payments or Journal, searches and filters, pages through results and opens a record in the Inspector.

Independent proof: incoming/outgoing payments preserve amount, allocated and unallocated values and reversal roles. Journal retains debit/credit direction, account, posting group, dates and currency. Exact account filtering is recoverable from the URL; selecting an account filters the journal to that exact account.

Acceptance: every table and control uses shared observations; open-item and journal sums are separated by currency; payment amounts remain per recorded row; the Inspector survives reload; advanced action links do not execute anything.

### US3 — Stay in the new App (P2)
Finance shares sidebar, company context and accessible controls. Selected company, tab, query, filter, page and Inspector recover on reload; company switching clears record and filter context.

Independent proof: sidebar → Finance → payment explanation → journal → reload → company switch with no mutation requests, at desktop and mobile widths in all four languages and both themes.

### Edge Cases
Multiple currencies; partial and complete settlement; reversed payments; zero results; missing party/reference; long IDs; out-of-range pages; unavailable reads; invalid URL filters; foreign Inspector identity; company switch during a read.

## Requirements

- **FR-001**: Finance is a unified destination with open items, payments and journal, retaining existing supporting routes.
- **FR-002**: Open items default to outstanding receivables and support receivable/payable, search, status and server pagination; show authoritative gross, settled and open values and currency-separated filtered controls.
- **FR-003**: Payments support direction/search/paging, preserve reversal roles and authoritative amount/allocated/unallocated values, without aggregate payment headlines.
- **FR-004**: Journal supports account/search/paging, preserves debit/credit and recorded history, and shows complete filtered debit/credit/balance controls by currency.
- **FR-005**: Row explanations use the existing native Inspector and shortest true evidence links; account links filter the same journal to the exact account. Read navigation creates no business effects.
- **FR-006**: Allowlisted URL state preserves tab, query, filters, page and selected Inspector; company switching clears references and filters. Existing authorization remains enforced.
- **FR-007**: Controls are localized in en/de/nl/es, keyboard accessible, usable in light/dark at 390/1440 px, with explicit empty/loading/error/retry states and no horizontal page overflow.

## Key Entities
Existing Document evidence, LedgerEntry, SettlementAllocation and derived financial projections. No stored balances or new relationship.

## Assumptions and Dependencies
The owner's continuation covers this bounded next workspace within the established migration direction. Existing shared finance APIs and Inspector are authoritative. Ordinary-company admission remains owned by the unified shell; existing endpoints retain their policies. Financial read contracts and previous reversal behavior remain unchanged. The default is outstanding receivables, with a visible switch to payables; currency totals reflect the active filters and never add unlike currencies or both flows into a business headline.

## Success Criteria
All three views reproduce shared financial reads, expose explanation for every row, preserve paging/reload and separate currencies. No investigation creates a posting, allocation or proposal. All seven requirements map to executable checks, with complete locale/theme/viewport navigation review before technical completion.

## Requirement Traceability

| Requirements | Stories | Planned evidence |
| --- | --- | --- |
| FR-001 FR-006 | US1 US3 | Route contracts, company reset and reload browser tests |
| FR-002 | US1 | Existing financial API controls/paging tests and Finance browser |
| FR-003 FR-004 FR-005 | US2 | Existing ledger/journal tests and Finance browser |
| FR-007 | US3 | Localization audit and full visual/keyboard/failure matrix |
