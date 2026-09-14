# Feature Specification: Ledger and Finance Baseline

**Baseline ID**: `012-ledger-finance`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline balanced postings, payments, settlement allocations, credits, and derived open items."

## Context and Intent

### Problem

Finance operators need balanced, append-only financial Reality connected to Evidence,
with receivables/payables derived rather than stored on Documents. This baseline defines
the minimal operational subledger, not statutory accounting or a tax engine.

### Scope

- Balanced sales- and supplier-invoice posting groups.
- Separate customer/supplier payment Evidence and balanced payment postings.
- SettlementAllocation between payment and invoice control-account entries.
- Many-to-many partial/full settlement and sales credits.
- Derived open items, allocation state, statements, journal, and control views.
- Tenant/currency isolation, invalid-allocation prevention, and provenance.

### Non-Goals

- Statutory accounting, tax returns, chart administration, closing, consolidation, or FX.
- Automated bank reconciliation, payment matching, collections, or treasury.
- Stored invoice payment status or mutable account balances.
- Financial inventory valuation beyond current bounded postings.

### Existing Contracts

- [`docs/features/ledger.md`](../../docs/features/ledger.md)
- [`docs/features/order_to_cash.md`](../../docs/features/order_to_cash.md)
- [`docs/features/procure_to_pay.md`](../../docs/features/procure_to_pay.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

LedgerEntry is append-only financial Reality grouped into balanced postings in one
currency. Invoice Documents evidence receivable/revenue or expense/inventory/payable
postings. Payment has separate Document Evidence and control entry.
SettlementAllocation links only payment and invoice control entries, enabling
many-to-many settlement without duplicated provenance. Open amount, allocation,
account balance, and financial status are derived.

Sales credit is a bounded customer-invoice reversal that does not affect fulfilment.
The documented rule that arbitrary mistakes use reversal has no general reversal
command and focused proof, so it remains a visible gap.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Post Balanced Invoice Evidence (Priority: P1)

As a finance operator, I can post customer and supplier invoice Evidence into balanced Reality.

**Why this priority**: Balanced postings establish receivable/payable truth.

**Independent Test**: Post both invoice types and verify accounts, currency, provenance,
debit/credit equality, and duplicate prevention.

**Acceptance Scenarios**:

1. **Given** a sales invoice, **When** posted, **Then** receivable/revenue balance.
2. **Given** a supplier invoice, **When** posted, **Then** expense/inventory/payable balance.
3. **Given** an unbalanced group, **When** posted, **Then** it is rejected without partial entries.
4. **Given** an already posted invoice, **When** repeated, **Then** duplication is rejected.

### User Story 2 - Record and Allocate Payments (Priority: P1)

As a finance operator, I can record payment Evidence and allocate it across invoices
without losing the payment's provenance.

**Why this priority**: Settlement must explain cash and affected liability.

**Independent Test**: Record one payment, allocate two invoices, and attempt invalid
tenant, currency, and amount combinations.

**Acceptance Scenarios**:

1. **Given** customer/supplier payment, **When** recorded, **Then** separate Evidence and
   balanced cash/control postings are retained.
2. **Given** one payment and several invoices, **When** allocated, **Then** each positive
   allocation links matching control entries and updates derived open amounts.
3. **Given** insufficient payment or invoice open amount, **When** allocated, **Then** it
   is rejected without partial settlement.
4. **Given** foreign-tenant or different-currency entries, **When** linked, **Then** it fails.

### User Story 3 - Credit and Correct Financial Reality (Priority: P1)

As a finance operator, I can credit a customer invoice while retaining every posting
and leaving delivery fulfilment independent.

**Why this priority**: Financial corrections must be append-only and auditable.

**Independent Test**: Post invoice, payment, and credit; reconcile open amount and
verify physical quantities remain unchanged.

**Acceptance Scenarios**:

1. **Given** a posted invoice, **When** credited, **Then** separate balanced entries
   reduce open receivable.
2. **Given** partial payment and credit, **When** viewed, **Then** both remain distinct.
3. **Given** financial credit, **When** delivery is inspected, **Then** fulfilment is unchanged.
4. **Given** an arbitrary erroneous posting, **When** correction is needed, **Then** the
   unsupported general reversal gap is visible; update/deletion is not permitted.

### User Story 4 - Read One Financial Truth (Priority: P2)

As a finance operator, I can use all finance registers knowing they reconcile to the
same entries and allocations.

**Why this priority**: Registers must not implement competing balance logic.

**Independent Test**: Settle an invoice partially and compare open-item, payment,
journal, statement, T-account, and control-account results.

**Acceptance Scenarios**:

1. **Given** 100 receivable with 40 allocated, **When** read, **Then** every view reports
   60 open and 40 allocated.
2. **Given** chronological entries, **When** statement is read, **Then** running balance
   derives from them without a stored balance.
3. **Given** full settlement, **When** viewed, **Then** paid derives from zero open amount.

### Edge Cases

- Zero/negative entry or allocation amount.
- Numerically balanced group mixing currencies.
- Wrong party/control account or repeated allocation.
- Payment/credit exceeding the remaining amount.
- Cross-tenant entries or two invoice/two payment entries linked.
- Historical arbitrary posting requires reversal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every posting group MUST balance debit and credit exactly in one currency
  using positive Decimal amounts.
- **FR-002**: Sales invoice MUST post receivable/revenue and supplier invoice MUST post
  expense or inventory/payable with Evidence provenance.
- **FR-003**: Duplicate invoice posting and unbalanced groups MUST be rejected atomically.
- **FR-004**: Every payment MUST retain separate Evidence and balanced cash/control
  entries; it MUST NOT reuse invoice Evidence.
- **FR-005**: SettlementAllocation MUST link only payment/invoice control entries, be
  positive, tenant/currency compatible, and not exceed available amounts.
- **FR-006**: One payment MAY settle several invoices and vice versa.
- **FR-007**: Sales credit MUST be separate balanced posting reducing open receivable
  without changing delivery fulfilment.
- **FR-008**: LedgerEntry MUST be append-only; arbitrary mistakes MUST have an auditable
  general reversal path rather than update/deletion.
- **FR-009**: Open amount/status, payment allocation, account balance, and running balance
  MUST derive from entries and allocations.
- **FR-010**: All finance registers MUST share LedgerEntry/SettlementAllocation truth.
- **FR-011**: Every finance operation MUST enforce tenant scope and Evidence/Source trace.
- **FR-012**: All interfaces MUST call shared services; agent mutations require confirmation.

### Domain and Traceability Requirements

- **DR-001**: LedgerEntry is append-only financial Reality, not Document status or Projection.
- **DR-002**: Entry → Document/Source is provenance; Allocation → two control entries is
  the shortest settlement link.
- **DR-003**: Payment Evidence remains separate and allocation MUST NOT duplicate provenance.
- **DR-004**: Financial state and physical fulfilment remain independently derived.
- **DR-005**: Human invoice/payment/account labels MUST NOT serve as identity.

### Key Entities

- **LedgerEntry**: Append-only debit/credit in one posting group.
- **SettlementAllocation**: Positive settlement between payment/invoice control entries.
- **Document**: Invoice, payment, or credit Evidence.
- **SourceRecord**: Optional immutable upstream evidence.

## Reality Applicability

- **Source**: Optional immutable invoice, bank, or PSP source.
- **Evidence**: Invoice, payment, and credit Documents are distinct claims.
- **Reality**: LedgerEntries and SettlementAllocations own finance truth.
- **Shortest links**: Entry → Evidence; allocation → payment/invoice control entries.
- **Stored/derived**: Entries/allocations stored; balances, open amounts, statuses derived.
- **Shared boundary**: Every interface calls tenant-scoped finance services.
- **Web explanation**: Registers cross-link postings, Evidence, allocations, and Source.

## Success Criteria *(mandatory)*

- **SC-001**: Every accepted posting group has equal debit/credit totals in one currency.
- **SC-002**: 1,470 less 500 payment and 100 credit yields exactly 870 receivable.
- **SC-003**: 600 less 250 payment yields exactly 350 payable.
- **SC-004**: One 100 payment settles 60 and 40 with zero unallocated/open; extra fails.
- **SC-005**: All finance registers reconcile to identical balances/allocation totals.
- **SC-006**: Invalid tenant, currency, duplicate, balance, or allocation attempts leave
  records unchanged.
- **SC-007**: Every displayed value reproduces from Evidence-linked entries/allocations.

## Assumptions and Dependencies

- The bounded account vocabulary is not a full managed chart.
- Tax, FX, statutory reports, reconciliation, and closing remain non-goals.
- General posting-group reversal linkage, permissions, time, and explanation are owned
  and verified by Spec 024.

## Open Questions

The product owner approved this baseline on 2026-08-31. Spec 024 closed the former
FR-008 gap on 2026-09-01 with an append-only complete posting-group reversal,
durable correction relation, shared preview/confirmation, tenant isolation, and
automated plus owner-reviewed interface proof.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-003 | Verified as-is | Ledger contract | posting services | `tests/test_ledger.py` balance/duplicate tests | — |
| FR-004–FR-007 | Verified as-is | Ledger contract | payment/allocation/credit services | ledger and scenario tests | — |
| FR-008 | Verified as-is | Ledger contract; Constitution; Spec 024 | `LedgerReversal`, exact inverse service, shared adapters | `test_ledger_reversals.py`, migration/API/catalog/tenant suites, Web build and localization contracts | Whole-group reversal approved 2026-09-01; originals and allocation history remain immutable |
| FR-009–FR-010 | Verified as-is | Ledger/Web contracts | finance read services | `test_finance_registers_share_ledger_and_allocation_truth` | — |
| FR-011–FR-012 | Verified as-is | Constitution; Architecture | tenant-scoped services/tools | ledger, tenancy, API, tool tests | — |
| DR-001–DR-005 | Verified as-is | Constitution; Data Model; Ledger contract | relationships/services | ledger, scenario, Inspector tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Balanced/invalid posting tests |
| FR-004–FR-006 | US2 | Payment and allocation tests |
| FR-007–FR-008 | US3 | Credit tests and Spec 024 reversal proof |
| FR-009–FR-010 | US4 | Cross-register reconciliation tests |
| FR-011–FR-012 | All stories | Tenancy/shared-service tests |
| DR-001–DR-005 | All stories | Constitution/provenance review |
