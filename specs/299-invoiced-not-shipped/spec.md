# Feature Specification: Invoiced Not Shipped, Down-Payment and Pro-Forma Invoices

**Feature Branch**: `299-invoiced-not-shipped`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 5. Close the capability gap behind the partial journeys E03, Q01, E11, C14 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Invoicing before delivery works, but sales have no "invoiced but not shipped" signal or month-end list. There is no down-payment invoice, so a down payment taken before any invoice is not tied to its order: prepayment readiness reports a missing invoice, and the final invoice does not state the offset. There is no pro-forma document.

| Journey | Title | Status today |
|---|---|---|
| E03 | Invoice before delivery (prepayment, pro forma) | partial |
| Q01 | Month-end: shipped not invoiced, invoiced not shipped | partial |
| E11 | Down-payment invoice and final invoice | partial |
| C14 | 30 % down payment, rest before shipment | partial |

### Scope

- A sales-side "invoiced but not shipped" finding per order line, and the month-end list beside "shipped but not invoiced".
- A down-payment invoice for an order, posted as a receivable against received down payments; paid, it counts towards prepayment readiness.
- A final invoice that states the down payments it offsets, proposed from the order's paid down-payment invoices and confirmed by a person, so only the rest is open.
- A pro-forma invoice for an order that is evidence only: no posting, no receivable, not counted as billed or as prepayment.

### Non-Goals

- Revenue recognition rules and tax treatment beyond the stated amounts.
- Down payments on purchases.
- Converting a pro-forma into an invoice; an invoice is recorded on its own.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-01

- Q: How is a down payment modelled? → A: As its own document, a down-payment invoice for an order, posted as a receivable against received down payments. Paid, it counts towards prepayment readiness; the final invoice deducts it as a stated line, and only the rest is open.
- Q: Is a pro-forma invoice part of this step? → A: Yes, as evidence only: linked to the order, never posted, no receivable, not counted as billed or as prepayment, visible on the order.
- Q: How does "invoiced but not shipped" appear? → A: As a finding per order line where the invoiced quantity exceeds the shipped quantity, severity normal, and from the same derivation as the month-end list beside "shipped but not invoiced". Down-payment invoices do not count as invoiced quantity.
- Q: How does the offset get into the final invoice? → A: Recording the final invoice proposes the order's paid down-payment invoices; the person confirms the stated offset. More than the order's down payments is refused.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Down payment and final invoice (Priority: P1)

As a sales clerk, I invoice a 30 % down payment for an order, and the final invoice deducts it so only the rest is open.

**Why this priority**: Rank 5 of the sales-gap roadmap: it comes up in almost every evaluation of project and custom-order businesses.

**Independent Test**: Business stories E11 and C14 through the reviewed tools, with positive controls.

**Acceptance Scenarios**:

1. **Given** an order of 1,000, **When** a down-payment invoice of 300 is posted, **Then** it is a receivable of 300 tied to the order and bills no quantity.
2. **Given** a prepayment order with that down-payment invoice paid, **When** readiness is read, **Then** 300 counts as received and 700 remains required; nothing ships until the rest is paid (C14).
3. **Given** the down payment paid, **When** the final invoice of 1,000 is recorded, **Then** the paid down payment of 300 is proposed as its offset; confirmed, the final invoice states it, and only 700 is open (E11).
4. **Given** a final invoice, **When** its offset exceeds the order's paid down payments, **Then** it is refused with a code.

---

### User Story 2 - Invoiced but not shipped (Priority: P1)

As a controller at month-end, I see which order lines were invoiced and not yet shipped, beside those shipped and not invoiced.

**Acceptance Scenarios**:

1. **Given** an invoice for 5 of an order line with nothing shipped, **When** findings are read, **Then** the line is reported with 5 invoiced, 0 shipped; **When** 5 ship, **Then** it clears.
2. **Given** a down-payment invoice for an order, **When** findings are read, **Then** no line is reported as invoiced but not shipped because of it (positive control: a goods invoice is).
3. **Given** month-end, **When** the list is read, **Then** it shows both shipped-not-invoiced and invoiced-not-shipped lines from the same derivations as the findings (Q01).

---

### User Story 3 - Pro-forma invoice (Priority: P2)

As a sales clerk, I send a pro-forma for an order without creating a receivable.

**Acceptance Scenarios**:

1. **Given** an order, **When** a pro-forma is recorded, **Then** it is evidence on the order, posts nothing, is no open item, and counts neither as invoiced quantity nor as prepayment (E03).

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A down-payment invoice reversed or credited no longer counts as received or as an offset.
- Two down-payment invoices for one order are both proposed.
- A down-payment invoice in another currency than its order is refused.
- Stated amounts and tax are recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sales MUST report invoiced quantities that were not shipped, per order line, as a finding and in the month-end list beside shipped-not-invoiced.
- **FR-002**: A down-payment invoice MUST be linked to its order, MUST be a receivable, MUST NOT count as invoiced quantity, and paid it MUST count towards prepayment readiness.
- **FR-003**: A final invoice MUST state the down payments it offsets, proposed from the order's paid down-payment invoices and confirmed by a person; an offset beyond them MUST be refused.
- **FR-004**: A pro-forma invoice MUST be evidence linked to its order without posting or receivable, and MUST count neither as invoiced nor as prepayment.
- **FR-005**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-006**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: E03, Q01, E11 and C14 each have a passing business story.
- **SC-002**: E03, Q01, E11 and C14 are `supported` in the Business Journey Guide.
- **SC-003**: The month-end lists and the findings agree for the same instant.

## Assumptions and Dependencies

- Builds on the sales invoice path, prepayment readiness (spec 275), customer deposits and settlement allocation, the shipped-not-billed derivation and the finance account roles.
- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.

## Open Questions

None. The owner decided the scope on 2026-10-01.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US2 | Finding and month-end list tests (planned) |
| FR-002 | US1 1–2 | Down-payment invoice and readiness tests (planned) |
| FR-003 | US1 3–4 | Final invoice offset tests (planned) |
| FR-004 | US3 | Pro-forma tests (planned) |
| FR-005, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-006, SC-001–SC-003 | All | Business stories, catalog tests and Guide questions (planned) |
