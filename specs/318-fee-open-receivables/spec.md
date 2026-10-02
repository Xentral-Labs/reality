# Feature Specification: Fee Open Receivables

**Feature Branch**: `codex/journey-consistency`
**Created**: 2026-10-02
**Status**: Implemented; focused verification passed, overall backend verification in progress
**Language**: English
**Input**: Close the fee receivable gap identified in the journey architecture review.

## Context and Intent

### Problem

Posted dunning fees and payment-return fees charged to a customer are ledger receivables but absent from the open-item register, aging and exposure. Operators cannot follow the complete claim through ordinary settlement workflows.

### Scope

- Expose existing customer fee charges as separate open receivables.
- Support ordinary confirmed payment allocation, partial settlement and reversal.
- Count each charge once in party balances and credit exposure.
- Preserve the original fee, source and posting without rebooking historical fees.

### Non-Goals

- Recalculating fees, changing invoices or adding a new fee posting engine.
- Splitting `services/exceptions.py`, automatic fee collection or external notices.
- New database fields unless the reviewed maturity policy proves a use case.

## User Scenarios & Testing

### User Story 1 - See and settle the complete claim (Priority: P1)

A clerk sees a EUR 100 invoice and its EUR 5 fee as separate claims totaling EUR 105. Paying the invoice leaves the fee open; paying the fee closes it.

**Independent Test**: Both fee types through shared finance services, tools and adapter reads; partial allocation, reversal and another tenant as controls.

**Acceptance Scenarios**:

1. **Given** a posted invoice of 100 and fee of 5, **When** open receivables are read, **Then** both appear and total 105.
2. **Given** the invoice is paid, **When** the register is read, **Then** the fee remains open at 5 and can be separately paid through confirmation.
3. **Given** a fee payment or fee posting is reversed, **When** the register is read, **Then** the remaining amount follows effective ledger postings and allocations exactly once.
4. **Given** already-posted historical fees, **When** the new read is used, **Then** those fees appear without a new source, document or posting.

### Edge Cases

- Fees borne by the company are expenses, not customer open items.
- Zero fees produce no fee receivable.
- Cross-tenant and cross-currency allocation remain refused; original allocation history is immutable.
- Discounts and invoice payment terms must not silently become fee entitlements or maturity rules.

## Requirements

- **FR-001**: Existing posted customer dunning and payment-return fee charges MUST appear as separate open receivables with their source and posting links.
- **FR-002**: Existing confirmed settlement tools MUST support full and partial payments of those charges, with the same tenant/currency/over-allocation guards.
- **FR-003**: Party balances, credit exposure and their projections MUST count effective open charges once; expenses and reversed fee charges MUST not contribute.
- **FR-004**: Fee charges MUST have only their explicitly stated maturity, no inherited payment terms or discounts, and MUST remain excluded from manual and automatic dunning. An unstated maturity MUST remain absent. Existing noncash reduction eligibility MUST NOT be expanded by enabling fee payments.
- **FR-005**: Historical charges MUST become visible at read time without rebooking or modifying immutable source/ledger history.
- **FR-006**: Web, CLI, MCP and Chat MUST use the same finance services and preserve confirmation for mutations.

## Success Criteria

- **SC-001**: The 100-plus-5 story conserves the remaining claim through invoice payment, fee payment and reversal on every applicable surface.
- **SC-002**: Historical charges reconcile to the ledger without duplicate postings.

## Assumptions and Dependencies

- Builds on specs 247, 295 and 297 and `docs/features/ledger.md`.
- Both fee types already have settlement control entries. The gap includes document selection and settlement-flow allowlists, not only the OP query.
- Scope and policy approved on 2026-10-02.

## Clarifications

- 2026-10-02: Owner approved separate payable fee open items without renewed dunning. Only already-stated maturity is used; absent maturity remains absent. No inherited discount and no new noncash-reduction entitlement.

## Requirement Traceability

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-001 | US1 1 | Both charge types in canonical OP and adapter reads |
| FR-002 | US1 2-3 | Reviewed payment, partial allocation, over-allocation and reversal |
| FR-003 | US1 1-3 | Party balance and exposure comparisons, expense control |
| FR-004 | Edge cases | No inherited maturity/discount; manual and automatic dunning exclusion; noncash-reduction refusal |
| FR-005 | US1 4 | Existing posting IDs and counts unchanged |
| FR-006 | US1 | Web/MCP/CLI read and confirmation tests |
