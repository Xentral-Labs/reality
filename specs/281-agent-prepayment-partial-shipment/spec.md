# Feature Specification: Agent-Guided Prepayment and Partial Shipment

**Created**: 2026-09-26
**Status**: Approved
**Language**: English
**Input**: Let Chat guide a future-dated B2B order through a requested prepayment invoice and a full or partial shipment while a human retains every decision.

## Context and Intent

Operators can already record invoices, payments and shipments, but Chat lacks a precise workflow contract joining those capabilities to canonical readiness. This feature makes the safe sequence explicit without creating another source of business truth.

### Scope

- Guide order-backed prepayment invoice proposals.
- Guide exact full or partial shipment proposals from canonical readiness.
- Preserve authenticated human review and stale-context refusal.

### Non-Goals

- Automatic invoicing, payment allocation, dispatch or proposal approval.
- Tax, price, allocation or requested-date inference.
- New document statuses, schema, background jobs or business-rule services.

## User Scenarios & Testing

### User Story 1 - Request Prepayment Safely (Priority: P1)

An operator asks Chat to request prepayment for an existing customer order. Chat resolves the exact order and lines, reads current readiness, prepares an order-backed sales-invoice proposal, and explains that no change occurs before human review.

**Independent Test**: Ask Chat for prepayment on a future-dated order and verify the proposal contains exact order-line identities and stated amounts, with no invoice before confirmation.

### User Story 2 - Propose a Safe Partial Shipment (Priority: P1)

An operator asks what can ship now. Chat reads canonical readiness and may prepare a shipment only for an exact open commitment quantity that current stock, reservation and payment evidence permit.

**Independent Test**: Give an order less available quantity than open quantity and verify Chat explains the remainder and prepares only the explicitly requested eligible quantity.

### User Story 3 - Retain Human Control and Current State (Priority: P1)

The human review shows the proposal and current blockers. Confirmation revalidates the review; stale payment, stock, reservation or open-quantity context refuses execution and requires a fresh proposal.

**Independent Test**: Change payment or inventory after preparation and prove confirmation has no business effect until refreshed and reconfirmed.

### Edge Cases

- Missing or ambiguous order/invoice attribution must not be guessed.
- Mixed currencies or units must not be combined.
- A zero, negative or excessive shipment quantity is refused.
- A future requested date is evidence, not permission to ship early.
- Full payment without stock, or stock without required payment, remains blocked.

## Requirements

- **FR-001**: Chat MUST read canonical order and fulfillment evidence before proposing either action.
- **FR-002**: A prepayment request MUST use exact order-line links and source-stated amounts; Chat MUST NOT invent tax, prices or allocation.
- **FR-003**: A shipment proposal MUST name an exact commitment, quantity and unit and MUST preserve the unfulfilled remainder.
- **FR-004**: Chat MUST distinguish ready, payment-blocked, stock-blocked, reservation-blocked and combined blockers.
- **FR-005**: Chat MAY prepare proposals but MUST NOT approve, reject or execute them.
- **FR-006**: After preparation Chat MUST state that no change occurred and direct the operator to authenticated human review.
- **FR-007**: Confirmation MUST revalidate payment, stock, reservation, holds and open quantity and refuse stale reviews without business effect.
- **FR-008**: Browser, Chat, CLI and MCP MUST use the same application services and proposal identities.
- **FR-009**: Every result MUST expose direct Document, DocumentLine, Commitment, invoice/payment and movement evidence links where applicable.
- **FR-010**: No operational status may be added to Document; readiness remains derived from Reality.

## Success Criteria

- **SC-001**: All acceptance cases produce identical readiness and blockers in Chat and the canonical readiness read.
- **SC-002**: Zero invoices or movements exist before a human confirms the exact reviewed proposal.
- **SC-003**: 100% of stale-review cases refuse with no business effect and a clear refresh instruction.
- **SC-004**: Partial shipment tests preserve the exact remaining quantity and trace it to the same commitment.

## Assumptions and Dependencies

- Existing invoice, shipment, readiness and proposal services remain authoritative.
- This slice adds orchestration guidance and executable proof, not new schema or business authority.

## Requirement Traceability

| Requirement | Scenario | Evidence |
|---|---|---|
| FR-001–FR-004 | Stories 1–2 | Chat prompt and provider-tool contract tests |
| FR-005–FR-008 | Story 3 | Proposal permission and human-review regression tests |
| FR-009–FR-010 | Stories 1–3 | Existing invoice, shipment, readiness and Inspector contracts |
