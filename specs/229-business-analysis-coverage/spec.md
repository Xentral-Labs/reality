# Feature Specification: Business analysis coverage

**Language**: English

Created: 2026-09-18
Status: Accepted scope — owner requested implementation after the coverage audit.
Branch: main (explicit owner preference)

## Context and Intent

The data explorer currently lists a sales-focused subset as business objects. Users
cannot find supplier invoices, credits, payments or warehouse details and reasonably
mistake the list for complete application coverage. Expand the existing read-only
analysis model over retained records, with business names and grouped navigation.

### Non-Goals

No new business storage, write tools, inferred document status, financial authority,
or generic access to authentication/configuration tables. Do not manufacture inventory,
availability, aging or net cash calculations by summing evidence. Such derived operational
views continue to use their canonical services and are explicitly distinguished from
record browsing. Technical mapping histories and raw source payload browsing remain in
the Inspector; their existence must not imply complete analysis support.

## User Scenarios & Testing

### US1 — Find sales, purchasing and payments (P1)

A reader chooses sales invoices, customer credits, purchase orders and their lines,
supplier invoices/credits and their lines, customer/supplier payments and refunds.
Acceptance: each typed entry returns only its stated document types, follows its
partner and applicable lines, and exposes recorded amounts with currency separation.
Existing invoice queries still include their original sales invoices and credits.
Tests must exercise PostgreSQL with mixed document types and a neighboring tenant.

### US2 — Explore warehouse and supporting details (P2)

A reader follows reservations to commitments, items and locations; holds to their
owners; lots, serial units and handling units to movements; packages to shipments;
and pricing, payment terms, partner roles/groups and ledger accounts to their records.
Acceptance: every declared relationship follows an existing identity reference, optional
missing relationships preserve rows, counts and quantities do not multiply on fan-out.
Shipment event history explicitly exposes supersession rather than claiming current status.

### US3 — Understand coverage without an overwhelming list (P2)

Objects are grouped by business area and searchable using labels and common synonyms.
Acceptance: searching for Gutschrift, Lieferant, Zahlung or Reservierung finds the
relevant distinct objects; existing object selection and preview/analysis handoff work.
The explorer describes itself as the available analysis catalog, not all application data.

### Edge Cases

Mixed currencies; repeated human document numbers; missing partner/item; empty tenant;
credit amounts retain their recorded sign; active and released reservations; historical
shipment events; same-table subtypes; old saved definitions; long localized names.

## Requirements

- **FR-001**: Typed document entries and positions cover sales, purchase, invoice, credit,
  payment and refund records with explicit labels. Legacy node semantics remain stable.
- **FR-002**: Warehouse/supporting objects cover reservations, holds, traceability,
  shipment packages/events, partner roles/groups, pricing/payment terms and accounts.
- **FR-003**: Fields, identity-based relationships and supported measures are declared once
  for chat, CLI and browser. Amounts are received values; units/currency remain mandatory.
- **FR-004**: Grouped searchable navigation identifies scope and distinguishes historical
  evidence from derived operational state. Existing builder and preview remain usable.
- **FR-005**: All reads and observed filter vocabularies enforce tenant and node subtype
  scope. A supplier-only catalog must not suggest unrelated sales document types.
- **FR-006**: Tests prove subtype/line boundaries, tenancy, fan-out safety, recorded signs,
  old-query compatibility and schema relationship coverage. Deferral audit is updated
  precisely; remaining unsupported concepts are documented with reasons.

## Success Criteria

- SC-001: Every named object in US1/US2 can be found and its declared fields queried.
- SC-002: No mixed-type/neighbor-tenant records leak in the acceptance fixtures.
- SC-003: Existing reporting and builder regression suites pass unchanged in meaning.

## Assumptions and Dependencies

Owner's “ja mach” approves the audited expansion and order of work. Existing business
services and database are the authority. Expansion is additive; the original invoice
node remains the combined customer invoice/credit view with a truthful label. Dedicated
entries provide precise discovery without rewriting saved definitions. No unresolved
product clarification; raw technical histories and new derived reports need their own
semantics and are not silently represented as complete by this catalog expansion.

Financial detail and evidence scope: include received financial components, opening scopes/items, generic evidence documents/lines, source-version metadata and historical additional facts. Raw payload inspection and mapping/assignment histories stay in the Inspector. These are existing records, not newly computed authorities.

## Requirement Traceability

| Requirement | Tasks | Verification |
|---|---|---|
| FR-001 | T004, T005 | Typed documents/positions, legacy compatibility tests |
| FR-002 | T006, T007 | All-node and all-edge PostgreSQL tests, coverage audit |
| FR-003 | T003–T007 | Recorded-sign, fan-out and currency regression tests |
| FR-004 | T008, T009 | Catalog search/group tests and Chrome review |
| FR-005 | T002, T003 | Parent/type/tenant and observed-vocabulary tests |
| FR-006 | T002, T005, T007, T010 | Reporting/web suites and documented remaining gaps |
