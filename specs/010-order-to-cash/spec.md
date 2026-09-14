# Feature Specification: Order to Cash Baseline

**Baseline ID**: `010-order-to-cash`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline the existing source-to-delivery-to-cash customer business story."

## Context and Intent

### Problem

Operators need one traceable customer flow from an external order through delivery and
financial settlement while keeping Evidence, physical execution, and finance as
independent authorities. This baseline composes existing capabilities; it does not
introduce a second implementation of their rules.

### Scope

- Lossless Shopify order ingestion and normalized sales-order Evidence.
- Outgoing customer-delivery Commitment per applicable order line.
- Reservation with shortage visibility and partial/full shipment.
- Sales-invoice Evidence and balanced receivable/revenue posting.
- Separate customer-payment Evidence, settlement allocation, partial/full payment.
- Sales credit reducing the open receivable without altering delivery fulfilment.
- End-to-end tenant isolation and Source → Evidence → Reality explanation.

### Non-Goals

- Checkout, quoting, sales automation, tax calculation, or customer communication.
- Treating order/invoice Documents as delivery or payment state authorities.
- Automatically invoicing shipment or shipping invoice/payment.
- Duplicating Source, Evidence, Inventory, Commitment, or Ledger rules owned elsewhere.
- General bank reconciliation, collections, FX, or statutory accounting.

### Existing Contracts

- [`docs/features/order_to_cash.md`](../../docs/features/order_to_cash.md)
- [`docs/features/shopify_ingestion.md`](../../docs/features/shopify_ingestion.md)
- [`docs/features/commitments.md`](../../docs/features/commitments.md)
- [`docs/features/reservations.md`](../../docs/features/reservations.md)
- [`docs/features/movements.md`](../../docs/features/movements.md)
- [`docs/features/ledger.md`](../../docs/features/ledger.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

The current story ingests one Shopify order losslessly, interprets minimal Document and
DocumentLine Evidence, and creates outgoing delivery Commitments. Available stock can
be reserved and shipped in parts; fulfilment derives from linked Movements. Invoice,
payment, and credit are separate Evidence and balanced posting groups. Settlement links
only their control-account entries. Delivery and financial status remain independent
derived views.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accept and Promise a Customer Order (Priority: P1)

As an operator, I can ingest a customer order and see its complete source, normalized
Evidence, and outgoing delivery promise.

**Why this priority**: This establishes the traceable customer obligation.

**Independent Test**: Ingest the Shopify fixture and inspect payload equality, order
Evidence, lines, Commitments, tenant scope, and idempotent repetition.

**Acceptance Scenarios**:

1. **Given** a valid Shopify order, **When** accepted, **Then** its complete payload is
   retained before normalized Evidence and Commitments are interpreted.
2. **Given** an applicable order line, **When** interpreted, **Then** one outgoing
   Commitment links through the shortest true Evidence chain.
3. **Given** identical delivery, **When** repeated, **Then** no duplicate current
   Evidence or Commitment is created.

### User Story 2 - Allocate and Deliver (Priority: P1)

As an operator, I can reserve available stock, see shortage, and record partial or full
shipments while fulfilment remains derived.

**Why this priority**: Delivery must reflect physical execution rather than document state.

**Independent Test**: Reserve a promise, ship it in two parts, and reconcile stock,
Reservation consumption, fulfilled/open quantity, and Document immutability.

**Acceptance Scenarios**:

1. **Given** insufficient available stock, **When** reserved, **Then** safe quantity and
   explicit shortage are returned.
2. **Given** a partial shipment, **When** fulfilment is read, **Then** the Commitment
   stays open with the correct remainder.
3. **Given** final shipment, **When** fulfilment is read, **Then** the Commitment is
   fulfilled and no delivery status is written to the order Document.

### User Story 3 - Invoice and Collect Independently (Priority: P1)

As a finance operator, I can post invoice Evidence and allocate separate customer
payment Evidence while the open receivable derives from Ledger truth.

**Why this priority**: Cash settlement must remain independently auditable from delivery.

**Independent Test**: Post a sales invoice, partial payment, and credit; verify every
group balances and the resulting open amount without changing fulfilment.

**Acceptance Scenarios**:

1. **Given** a EUR 1,470 invoice, **When** posted, **Then** receivable and revenue entries
   balance in one currency.
2. **Given** a EUR 500 customer payment, **When** allocated, **Then** separate payment
   Evidence is retained and EUR 970 remains open.
3. **Given** a EUR 100 sales credit, **When** posted, **Then** EUR 870 remains open and
   shipped quantity is unchanged.
4. **Given** full allocation, **When** status is read, **Then** paid state derives from
   LedgerEntries and allocations rather than an invoice field.

### User Story 4 - Explain the Complete Flow (Priority: P2)

As an operator, I can navigate from customer source through Evidence to delivery and
financial Reality without confusing their independent state.

**Why this priority**: End-to-end explainability is the proof that composed primitives fit.

**Independent Test**: Inspect one completed flow and reproduce source payload,
fulfilment, stock change, posting balance, allocations, and open amount.

**Acceptance Scenarios**:

1. **Given** a completed flow, **When** inspected, **Then** the delivery chain follows
   SourceRecord → Document → DocumentLine → Commitment → Reservation/Movement.
2. **Given** financial Evidence, **When** inspected, **Then** invoice/payment Documents
   link to their own LedgerEntries and SettlementAllocation connects control entries.
3. **Given** delivery complete but receivable open, **When** viewed, **Then** the two
   states are shown independently and accurately.

### Edge Cases

- Changed or stale order source arrives after delivery work has begun.
- Reservation shortage remains when invoicing is recorded.
- Shipment is blocked by Commitment or customer delivery hold.
- Payment exceeds invoice open amount or uses another currency/tenant.
- One payment settles several invoices or one invoice receives several payments.
- Credit exceeds remaining eligible amount or arrives after full settlement.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Customer order ingestion MUST preserve complete immutable Source before
  interpreting minimal sales Document/Line Evidence.
- **FR-002**: Each applicable order line MUST create at most one outgoing delivery
  Commitment through the shared interpreter and Commitment service.
- **FR-003**: Reservation MUST allocate only available stock and report shortage;
  shipment MUST change stock and fulfilment only through Movements.
- **FR-004**: Partial/full delivery MUST derive from linked Movements and MUST NOT be
  stored on sales-order or invoice Documents.
- **FR-005**: Sales invoice posting MUST create one balanced receivable/revenue group in
  the Document currency and MUST reject duplicate posting.
- **FR-006**: Customer payment MUST have separate Evidence and balanced cash/receivable
  entries; allocation MUST link the payment and invoice control entries.
- **FR-007**: Partial payment and credit MUST remain separate append-only postings and
  MUST reduce derived open receivable without changing delivery fulfilment.
- **FR-008**: Open, partial, and paid financial state MUST derive from LedgerEntries and
  SettlementAllocations, never Document status.
- **FR-009**: The composed flow MUST enforce tenant scope, opaque identity, Decimal
  arithmetic, and shared services across every stage.
- **FR-010**: Operators MUST be able to inspect both the delivery chain and the separate
  financial Evidence/Reality chain back to applicable Source.

### Domain and Traceability Requirements

- **DR-001**: Delivery trace MUST use SourceRecord → Document → DocumentLine → Commitment
  → Reservation/Movement with no duplicated Reservation provenance.
- **DR-002**: Invoice/payment Document → LedgerEntries and SettlementAllocation between
  control entries MUST be the financial shortest links.
- **DR-003**: Delivery and financial status MUST remain independently derived.
- **DR-004**: Each stage MUST delegate to its owning Source, Evidence, Commitment,
  Inventory, or Ledger service rather than implement alternate flow rules.

### Key Entities

- **SourceRecord**: Immutable customer order source.
- **Document/DocumentLine**: Sales order, invoice, payment, and credit Evidence.
- **Commitment/Reservation/Movement**: Delivery promise, allocation, and execution.
- **LedgerEntry/SettlementAllocation**: Balanced finance truth and settlement link.

## Reality Applicability

- **Source**: Shopify order and optional payment source remain immutable/lossless.
- **Evidence**: Order, invoice, payment, and credit Documents record distinct claims.
- **Reality**: Commitment, Reservation, Movement, LedgerEntry, and allocation own state.
- **Shortest links**: Delivery and financial chains follow DR-001/DR-002.
- **Stored/derived**: Evidence and append-only Reality are stored; fulfilment, stock,
  availability, open receivable, and status are derived.
- **Shared boundary**: CLI, API, Web, Chat, MCP, and scenarios call owning services.
- **Web explanation**: Order operations and finance views cross-link without merging
  delivery and settlement state.

## Success Criteria *(mandatory)*

- **SC-001**: The complete Shopify fixture remains byte-for-field equivalent after
  decoding and every interpreted line is traceable to it.
- **SC-002**: Partial/full shipment sequences reconcile promised, fulfilled, open,
  reserved, and physical quantities exactly.
- **SC-003**: Every invoice, payment, and credit posting group balances to zero in one currency.
- **SC-004**: A 1,470 invoice less 500 payment and 100 credit yields exactly 870 open.
- **SC-005**: Credits/payments change no delivered quantity and delivery changes no open
  receivable unless a separate finance action occurs.
- **SC-006**: Cross-tenant links and over-allocation are rejected with no partial writes.
- **SC-007**: One inspection path explains the complete delivery and financial chains.

## Assumptions and Dependencies

- `005`, `006`, `008`, `009`, and `012` remain the authorities for component behavior.
- Invoice timing is an explicit operator action; shipment does not auto-create finance.
- Taxes, discounts, FX, dunning, and statutory output remain outside this baseline.

## Open Questions

The product owner approved this baseline on 2026-08-31. It composes existing
capabilities and does not add automatic invoicing, payment matching, or delivery
orchestration.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-002 | Verified as-is | Order-to-Cash and Shopify contracts | ingestion/interpreter services | `tests/scenarios/test_order_to_cash.py`; Shopify tests | — |
| FR-003–FR-004 | Verified as-is | Reservation, Movement, Commitment contracts | reserve/movement/fulfilment services | order-to-cash and inventory tests | — |
| FR-005–FR-008 | Verified as-is | Ledger contract | sales posting/payment/credit/allocation services | order-to-cash and ledger tests | — |
| FR-009–FR-010 | Verified as-is | Constitution; Architecture; Web contract | shared services and Inspector | scenario, tenancy, explain, and API tests | — |
| DR-001–DR-004 | Verified as-is | Constitution; Order-to-Cash contract | cross-domain relationships | scenario and component tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-002 | US1 | Shopify/source story tests |
| FR-003–FR-004 | US2 | Reservation, shipment, and fulfilment tests |
| FR-005–FR-008 | US3 | Balanced posting, payment, credit, and allocation tests |
| FR-009–FR-010 | US4 | End-to-end scenario, tenancy, and explain tests |
| DR-001–DR-004 | All stories | Cross-domain trace review |
