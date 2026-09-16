# Feature Specification: Operational quick previews

**Created**: 2026-09-16
**Status**: Approved scope
**Input**: Improve quick previews across Sales, Purchasing, Warehouse and Finance using existing data. User approved the preceding assessment with “ja mach”.

## Context and Intent

### Problem
Quick previews show the first three technical Inspector sections, hiding business information and replacing line descriptions with SKUs. Clerks need to identify the party, goods, quantities, amounts and relevant dates without leaving the register.

### Scope
Read-only previews for orders/invoices, delivery commitments, stock, reservations, movements, shipments/packages, payments and journal entries. Preserve full explanations and existing actions.

### Non-Goals
No schema changes, new business rules, source mapping, inferred contact/address data, new mutations, timers or new register workflows. Finance settings and balance drilldowns remain unchanged.

## User Scenarios & Testing

### User Story 1 - Understand an order or invoice (Priority: P1)
A clerk opens a sales or purchase document and recognizes its counterparty and positions.
**Independent Test**: Open a document with SKU, original description and a renamed item.
**Acceptance Scenarios**:
1. Given a source-stated description and SKU, opening the preview shows both, exact received amounts, quantity/unit and a labeled customer or supplier.
2. Given no description, the current linked item name is identified as current master data; missing names remain explicitly unavailable.
3. Given recorded requested dates or effective commitment dates, the preview distinguishes these dates and displays existing operational quantities. Invoice settlement comes from the existing financial read.

### User Story 2 - Understand goods and fulfillment (Priority: P1)
A clerk opens a commitment, stock record, reservation, movement or shipment and understands the goods and business context.
**Independent Test**: Read each supported kind with linked named items, locations and parties.
**Acceptance Scenarios**:
1. Commitments show promised, reserved, fulfilled, open, due and applicable holds using existing effective reads.
2. Stock shows physical, reserved and available quantities with explicit location scope; reservations and movements show quantity/unit, time, named locations and linked order/party where present.
3. Shipments show party, carrier/tracking, named physical contents and available tracking observations, without claiming dispatched goods were received.

### User Story 3 - Understand money (Priority: P1)
A finance clerk opens an invoice, payment or journal record and recognizes its financial position.
**Independent Test**: Read a partially settled invoice and allocated payment, plus a journal entry.
**Acceptance Scenarios**:
1. Invoice previews show stated gross, settled/open, available due date and settlement state from shared reads.
2. Payment previews show amount/currency, date, incoming/outgoing, allocated/unallocated and linked invoices; journal previews show account, debit/credit, date and linked party/document.

### Edge Cases
Missing optional facts are omitted or shown as unavailable, never zero-filled. Numeric zero remains visible. Revisions, cancellations and reversals retain existing service semantics. Multiple units are never added together. Foreign-tenant links cannot disclose names. Long labels wrap on mobile; large lists are bounded with a visible explanation. Read failure preserves retry. Preview reads never mutate.

### User Story 4 - Recognize master data (Priority: P1)
The user extended the approved scope on 2026-09-16 to include master-data recognition and moving Master data into Workspaces.
**Independent Test**: Open customer, supplier, item and location registers and previews, then navigate with the relocated menu entry.
**Acceptance Scenarios**:
1. Party lists show name, accounting code, payment term, currency and active state; previews group identity/roles, commercial defaults, identifiers and provenance. No invented customer/supplier number replaces a missing accounting code.
2. Item lists show name/SKU, unit, item type, default location and active state; previews also show tracking, purchase unit, conversion factor and lead time. Locations show type, named parent and stock eligibility.
3. Named references remain tenant scoped; numeric zero and false remain visible; money and quantities use user formatting. Original values remain intact for editing and revision checks.
4. Master data appears once, after Finance in Workspaces, including collapsed/mobile navigation. Existing edit, source, customer-hold and Inspector actions remain reachable.

## Requirements

### Functional Requirements
- **FR-001**: Select explicit business preview content per supported record kind; keep correction/provenance details available through the full explanation, and preserve actions.
- **FR-002**: Document previews show party role/name, number/date, currency and exact stated totals; positions show SKU plus original description, quantity/unit and received amount. Current-name fallback is labeled.
- **FR-003**: Order/commitment previews expose existing effective fulfillment quantities, due dates and holds. Requested document dates remain distinct from effective promises.
- **FR-004**: Warehouse previews expose named items/locations, scoped stock quantities, movement/reservation quantities and times, and linked business context through existing relationships.
- **FR-005**: Shipment previews show named party/contents, packages and available current tracking observations.
- **FR-006**: Financial previews expose authoritative settlement/allocation results, available due dates, direction/account and traceable document context, including reversals.
- **FR-007**: All reads remain tenant-scoped, read-only and service-owned; no new persistence or recomputation of source amounts. Missing data and list truncation are explicit.
- **FR-008**: Preserve responsive two-column hierarchy, keyboard disclosure/retry/full explanation, shared locale/date/quantity/money formatting and four-language control labels; original business labels remain verbatim.

- **FR-009**: Master-data lists prioritize the existing business identifiers/settings described in US4 over opaque IDs; previews group all existing editable business fields, show named parent/default locations and retain provenance/record ID in secondary details. Preserve read-only behavior, localized numbers and existing confirmation/revision boundaries.
- **FR-010**: Move the single Master data navigation entry from Company to Workspaces after Finance, preserving route, tenant, active state, tooltip and mobile behavior.

### Key Entities
Existing Document/DocumentLine, Party, Item, Commitment, Reservation, Movement, Shipment, LedgerEntry and settlement relationships. No new business entity.

## Success Criteria
- **SC-001**: All supported record kinds show their defined business context without opening the full explanation in acceptance fixtures.
- **SC-002**: An order position with both SKU and description displays both; exact recorded amounts remain unchanged in all tests.
- **SC-003**: Cross-tenant reads disclose no data and opening previews produces no writes.
- **SC-004**: Preview content remains readable at 390px and desktop widths with working existing actions.

## Assumptions and Dependencies
The user approval covers the assessed first improvement across all four workspaces. Existing data may be incomplete. Existing shared operational/financial services remain authoritative. There are no unresolved product clarifications. Tests are required before implementation where practical, followed by backend, frontend, specification and catalog gates.

## Requirement Traceability

**Language**: English

| Requirements | Story | Proof |
|---|---|---|
| FR-001, FR-002, FR-003 | US1 | Document and commitment tests in test_operational_previews.py |
| FR-004, FR-005 | US2 | Warehouse and shipment tests in test_operational_previews.py |
| FR-006 | US3 | Invoice/payment/journal tests in test_operational_previews.py |
| FR-007 | All | Tenant/read-only assertions in test_operational_previews.py |
| FR-008 | All | operational-previews-browser.mjs, localization audit and web build |
| FR-009, FR-010 | US4 | test_reference_workspace.py, master-data browser fixtures and navigation assertions |
