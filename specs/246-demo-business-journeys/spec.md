# Feature Specification: Complete Demo Business Journeys

**Feature Branch**: `245-demo-setup-finance-readiness`  
**Created**: 2026-09-21  
**Status**: Approved

**Language**: English

## Context and Intent

### Problem

The canonical demo shows stock, fulfillment, invoices, payments and contribution
analysis, but it does not yet provide a discoverable reference for several ordinary
return, credit and cancellation journeys. A person evaluating the product cannot tell
which cases exist, where to find them, or whether an absent record is intentional.

### Scope

Extend the canonical demo with deterministic, source-backed business journeys for
customer and supplier returns, credits and cancellations, and publish an English
catalog that explains every baseline journey and its expected result.

### Non-Goals

- No new persistence fields, accounting rules or alternative demo-only services.
- No automatic returns, credits, shipments or cancellations in continuous intake.
- No claim that the catalog is accounting, tax or legal advice.
- No quotation, manufacturing, serial-number or payroll scenarios.

## User Scenarios & Testing

### User Story 1 - Explore ordinary sales exceptions (Priority: P1)

As an evaluator, I can inspect complete and partial returns, commercial credits and
cancellations so I understand how Reality represents common order-to-cash changes.

**Acceptance Scenarios**:

1. A fully delivered and invoiced sale has a full return and full credit.
2. A delivered sale has a partial return and matching partial credit.
3. One order is cancelled before shipment and another after partial shipment without
   rewriting the movements that already happened.

### User Story 2 - Explore ordinary purchasing exceptions (Priority: P1)

As an evaluator, I can inspect supplier returns, supplier credits and purchase
cancellations alongside the existing receipt, invoice and payment states.

**Acceptance Scenarios**:

1. Received and invoiced goods are partly returned and the supplier credit is allocated
   to the original supplier invoice.
2. A supplier return awaiting credit remains visible as an unresolved exception.
3. A purchase commitment cancelled before receipt retains its source order and audit
   trail without creating a receipt.

### User Story 3 - Learn from a stable catalog (Priority: P1)

As a user or contributor, I can open one documentation page that lists each demo
journey, its references, expected operational/financial state, contribution coverage
and deliberate limitations.

**Acceptance Scenarios**:

1. The catalog separates static baseline cases from continuous live intake.
2. Every added journey has stable document references and a direct description of what
   to inspect in Sales, Purchasing, Warehouse and Finance.
3. The catalog distinguishes a document date from an optional due date and states that
   every demo business document has a document date.

### Edge Cases

- Returns never exceed the quantity delivered or received on their linked commitment.
- Credits use the same party, currency and source-stated amount as their related trade.
- Cancelling a partly fulfilled promise preserves its prior movement.
- Commercial allowances do not fabricate a physical return.
- Existing demo creation replay remains idempotent and profile-version mismatches fail.

## Requirements

### Functional Requirements

- **FR-001**: The profile MUST contain both a full and a partial customer return with
  corresponding posted customer credits.
- **FR-002**: The profile MUST contain a partial supplier return with an allocated
  supplier credit and one supplier return awaiting credit.
- **FR-003**: The profile MUST contain a purchase cancellation before receipt, retain
  the existing sales cancellation before shipment and add cancellation after partial
  shipment.
- **FR-004**: Every business document MUST state a document date and use the canonical
  numbering families for its document type.
- **FR-005**: Added billed sales lines that claim contribution coverage MUST expose a
  reviewed cost basis and calculated DB values; deliberately unresolved cases MUST be
  labelled as such in the catalog.
- **FR-006**: The durable demo documentation and its discoverable English and German
  public Docs pages MUST inventory baseline master data,
  purchase-to-pay, order-to-cash, inventory, finance, contribution and exception cases,
  including stable references and expected outcomes.
- **FR-007**: Static profile creation and replay MUST remain deterministic, tenant
  scoped and idempotent; continuous intake MUST remain separate.

### Domain and Traceability Requirements

- **DR-001**: Every added journey MUST preserve SourceRecord → Document/DocumentLine →
  Commitment/Movement/LedgerEntry links wherever those stages apply.
- **DR-002**: Operational and financial state MUST be derived from Reality records and
  settlement allocations, never stored as document status.
- **DR-003**: Source-stated dates, quantities and amounts MUST be recorded without
  recomputation.
- **DR-004**: Setup MUST invoke only existing shared application services under the
  profile's bounded initialization authority.

## Success Criteria

- **SC-001**: Automated profile verification identifies every FR-001 through FR-004
  journey by stable reference and confirms its expected quantities and balances.
- **SC-002**: A reader can identify where to inspect any documented journey and its
  expected result from one catalog page in under two minutes.
- **SC-003**: Two companies created from the same profile version have equivalent
  journey expectations and no duplicate effects after retry.
- **SC-004**: Existing demo, finance, costing and company-setup regression suites pass.

## Assumptions and Dependencies

- Existing return, credit, settlement, movement, commitment cancellation and costing
  services are authoritative and sufficient; no schema expansion is required.
- The canonical profile version is incremented because its deterministic fixture shape
  changes.
- The existing customer-return cost fixture remains the authoritative detailed DB
  example; exception-only journeys may intentionally remain unresolved and say so.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, DR-001–DR-003 | US1 | Full and partial return/credit assertions in the international demo scenario |
| FR-002, DR-001–DR-003 | US2 | Supplier return, credit allocation and open-exception assertions |
| FR-003, DR-002 | US1–US2 | Pre-shipment, post-partial-shipment and pre-receipt cancellation assertions |
| FR-004, DR-003 | US1–US3 | Document-date completeness and stable-reference verification |
| FR-005 | US1 | Canonical costing and contribution regression suite |
| FR-006 | US3 | Demo Data Catalog review and documentation policy check |
| FR-007, DR-004 | All | Company-setup replay, profile-version and tenant-scope regression tests |
