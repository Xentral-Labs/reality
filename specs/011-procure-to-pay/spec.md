# Feature Specification: Procure to Pay Baseline

**Baseline ID**: `011-procure-to-pay`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline the existing supplier promise-to-receipt-to-payment business story."

## Context and Intent

### Problem

Operators need a traceable supplier flow from purchase promise through receipt,
supplier invoice, and payment while physical and financial truth remain independent.
This baseline composes canonical capabilities without making purchase Documents their
lifecycle authority.

### Scope

- Incoming supplier-delivery Commitment, optionally backed by purchase Evidence.
- Partial/full receipt Movements and derived fulfilment.
- Received stock becoming available for customer Reservation.
- Supplier-invoice Evidence and balanced expense/inventory/payable posting.
- Separate supplier-payment Evidence, allocation, partial/full settlement, and open payable.
- Tenant isolation and Evidence/Reality traceability.

### Non-Goals

- Requisition, approval, sourcing, vendor portal, or automated purchase-order generation.
- Three-way matching, landed cost, tax engine, FX, or statutory accounts payable.
- Purchase-Document receipt/payment status.
- Automatic supplier invoice or payment creation from a receipt.
- Duplicating Commitment, Inventory, Document, or Ledger rules.

### Existing Contracts

- [`docs/features/procure_to_pay.md`](../../docs/features/procure_to_pay.md)
- [`docs/features/commitments.md`](../../docs/features/commitments.md)
- [`docs/features/movements.md`](../../docs/features/movements.md)
- [`docs/features/inventory.md`](../../docs/features/inventory.md)
- [`docs/features/ledger.md`](../../docs/features/ledger.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

An incoming supplier Commitment may stand alone or link to purchase Document/Line
Evidence. Partial and full receipts are append-only Movements that derive fulfilment
and physical stock. Supplier invoice and payment are separate Evidence with balanced
posting groups. Settlement allocations connect payment and invoice control entries;
open payable is derived. No purchase Document represents receipt or payment state.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record a Supplier Promise (Priority: P1)

As an operator, I can record an incoming supplier delivery promise with or without a
purchase Document.

**Why this priority**: Incoming Commitment is the authority for expected supply.

**Independent Test**: Create a supplier Commitment, with and without Evidence, and
verify tenant-owned references, incoming quantity, due time, and opaque identity.

**Acceptance Scenarios**:

1. **Given** tenant-owned supplier, company, item, and location, **When** the promise is
   created, **Then** it records an incoming obligation.
2. **Given** purchase Evidence, **When** linked, **Then** it supports provenance without
   owning fulfilment.
3. **Given** no Document, **When** created, **Then** the Commitment remains valid.

### User Story 2 - Receive Supply and Expose Stock (Priority: P1)

As a warehouse operator, I can record partial/full receipts and make received quantity
available without editing a stock balance.

**Why this priority**: Physical receipt is what fulfils supply and creates stock.

**Independent Test**: Receive a quantity of 20 in two Movements and reconcile fulfilment,
physical stock, incoming remainder, and downstream availability.

**Acceptance Scenarios**:

1. **Given** a promise of 20, **When** 8 is received, **Then** fulfilled is 8, open
   incoming is 12, and physical stock rises by 8.
2. **Given** the remaining 12 is received, **When** read, **Then** fulfilment is 20 and
   open incoming is zero.
3. **Given** received unreserved stock, **When** a customer Reservation is requested,
   **Then** it is available through the normal Reservation service.
4. **Given** receipt, **When** purchase Document is inspected, **Then** no stored receipt
   status is required.

### User Story 3 - Record Liability and Supplier Payment (Priority: P1)

As a finance operator, I can post supplier invoice Evidence and allocate separate
payment Evidence while open payable derives from Ledger truth.

**Why this priority**: Liability and settlement require their own auditable evidence.

**Independent Test**: Post a 600 supplier invoice and 250 payment and verify balanced
groups, distinct Evidence, allocation, and 350 open payable.

**Acceptance Scenarios**:

1. **Given** a supplier invoice, **When** posted, **Then** expense/inventory and payable
   entries balance in one currency.
2. **Given** a supplier payment, **When** recorded, **Then** it has separate Evidence and
   balanced cash/payable entries.
3. **Given** 250 allocated to a 600 invoice, **When** open payable is read, **Then** it is
   350 and status is derived as partial.
4. **Given** receipt remains incomplete, **When** finance is posted, **Then** financial
   state does not fabricate physical fulfilment.

### User Story 4 - Explain the Complete Supplier Flow (Priority: P2)

As an operator, I can explain purchase Evidence, incoming promise, receipts, invoice,
payment, and outstanding liability as distinct linked records.

**Why this priority**: Procurement and finance must reconcile without collapsing domains.

**Independent Test**: Inspect a completed story and reproduce fulfilment, stock,
balanced postings, allocation, and open payable.

**Acceptance Scenarios**:

1. **Given** purchase Evidence, **When** inspected, **Then** physical trace follows
   Document/Line → supplier Commitment → receipt Movement.
2. **Given** invoice/payment Evidence, **When** inspected, **Then** each reaches its own
   LedgerEntries and allocation joins only control entries.
3. **Given** receipt and payment progress differ, **When** viewed, **Then** both states
   remain independently accurate.

### Edge Cases

- Receipt exceeds open supplier quantity or targets a foreign/disallowed location.
- Supplier invoice is posted twice or is unbalanced.
- Payment exceeds open payable, available payment, or crosses tenant/currency.
- Purchase Commitment is cancelled after partial receipt.
- Supplier invoice exists without purchase-order Evidence.
- One payment settles several invoices or one invoice receives several payments.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Supplier delivery MUST be an incoming Commitment and MAY exist without
  purchase Document/Line Evidence.
- **FR-002**: Partial/full receipt MUST be recorded as append-only Movement and MUST
  derive Commitment fulfilment and physical stock.
- **FR-003**: Received available stock MUST participate in the same Reservation and
  inventory calculations as all other physical stock.
- **FR-004**: Purchase Documents MUST NOT store receipt, fulfilment, inventory, or
  payment state.
- **FR-005**: Supplier invoice posting MUST create a balanced expense/inventory and
  payable group and MUST reject duplicate or unbalanced posting.
- **FR-006**: Supplier payment MUST retain separate Evidence and balanced cash/payable
  entries; allocation MUST connect payment and invoice control entries.
- **FR-007**: Partial/full payment and open payable status MUST derive from append-only
  LedgerEntries and SettlementAllocations.
- **FR-008**: Physical receipt and financial settlement MUST remain independent and
  MUST change only through their owning services.
- **FR-009**: The complete flow MUST enforce tenant scope, opaque IDs, Decimal
  arithmetic, append-only history, and shared services.
- **FR-010**: Operators MUST be able to trace physical and financial supplier chains
  without duplicated provenance.

### Domain and Traceability Requirements

- **DR-001**: Physical trace is optional Purchase Document/Line → supplier Commitment →
  receipt Movement.
- **DR-002**: Financial trace is supplier Invoice/Payment Document → LedgerEntries with
  SettlementAllocation only between their control entries.
- **DR-003**: Receipt/fulfilment and payable/payment status MUST be independently derived.
- **DR-004**: The flow MUST delegate to owning Evidence, Commitment, Inventory, and
  Ledger services.

### Key Entities

- **Document/DocumentLine**: Optional purchase, supplier invoice, and payment Evidence.
- **Commitment/Movement**: Incoming promise and physical receipt.
- **LedgerEntry/SettlementAllocation**: Liability, cash effect, and settlement link.

## Reality Applicability

- **Source**: Optional upstream purchase/invoice/payment source remains immutable.
- **Evidence**: Purchase, supplier invoice, and supplier payment Documents are distinct.
- **Reality**: Commitment, Movement, LedgerEntry, and allocation own operational state.
- **Shortest links**: Physical and financial traces follow DR-001 and DR-002.
- **Stored/derived**: Evidence and append-only Reality are stored; fulfilment, stock,
  incoming, open payable, and status are derived.
- **Shared boundary**: All interfaces and scenarios call owning tenant-scoped services.
- **Web explanation**: Warehouse and finance views cross-link without merging receipt
  and settlement state.

## Success Criteria *(mandatory)*

- **SC-001**: Receipts of 8 and 12 against a promise of 20 yield fulfilment and stock of
  exactly 20 with zero open incoming quantity.
- **SC-002**: Received available stock can satisfy a customer Reservation through the
  same inventory rules.
- **SC-003**: Every supplier invoice/payment posting group balances to zero in one currency.
- **SC-004**: A 600 invoice less 250 payment yields exactly 350 open payable.
- **SC-005**: Receipt changes no payable and payment changes no received quantity.
- **SC-006**: Cross-tenant, cross-currency, duplicate, and over-allocation attempts create
  no partial writes.
- **SC-007**: One inspection path explains both physical and financial supplier chains.

## Assumptions and Dependencies

- `006`, `008`, `009`, and `012` remain authorities for component behavior.
- Receipt and finance actions are explicit; neither automatically creates the other.
- Three-way matching, tax, FX, approvals, and statutory reporting are out of scope.

## Open Questions

The product owner approved this baseline on 2026-08-31. It does not add purchase
automation or three-way matching.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-004 | Verified as-is | Procure-to-Pay, Commitment, Movement, Inventory contracts | commitment, receipt, inventory services | `tests/scenarios/test_procure_to_pay.py`; inventory tests | — |
| FR-005–FR-008 | Verified as-is | Ledger contract | supplier posting/payment/allocation services | procure-to-pay and ledger tests | — |
| FR-009–FR-010 | Verified as-is | Constitution; Architecture; Web contract | shared services and Inspector | scenario, tenancy, API, and explain tests | — |
| DR-001–DR-004 | Verified as-is | Constitution; Procure-to-Pay contract | cross-domain relationships | scenario and component tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 | Supplier Commitment and tenancy tests |
| FR-002–FR-004 | US2 | Receipt, inventory, Reservation, and fulfilment tests |
| FR-005–FR-008 | US3 | Supplier posting/payment/allocation tests |
| FR-009–FR-010 | US4 | End-to-end scenario, tenancy, and explanation tests |
| DR-001–DR-004 | All stories | Cross-domain trace review |
