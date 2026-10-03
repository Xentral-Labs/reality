# Feature Specification: Releasing a Partly Prepaid Order

**Feature Branch**: `347-prepayment-release`

**Created**: 2026-10-03

**Status**: Accepted

**Language**: English

**Input**: Scenario coverage, journey R01 (partial): "Customer orders 10, 4 in stock, prepayment
80 % paid, released anyway, 4 shipped; …". Spec 275 FR-005 keeps a prepayment order unshippable
until it is paid, and no reviewed release overrides that. The owner asked to close R01.

## Context and Intent

### Problem

A prepayment order that is 80 % paid is refused by every shipping route until the rest arrives.
Businesses ship such orders anyway when they trust the customer, but Reality had no reviewed way
to record that decision, so the order could only wait or be worked around outside Reality.

### Scope

- A reviewed, owner-only release of one sales order's prepayment gate, with a stated reason,
  modelled on the credit hold release of spec 298.
- The release is recorded and named wherever the gate is read: shipment readiness, the delivery
  case and the decision trail.
- The unpaid rest stays an ordinary open receivable.

### Non-Goals

- Changing what the prepayment gate requires (spec 275), or releasing a whole customer.
- Releasing an order whose invoice also bills other orders: what was paid for it is unclear, and
  that is settled first.
- Undoing a release.

## Clarifications

### Session 2026-10-03

The owner delegated these decisions to the recommended options.

- Q: Who may release? → A: A company owner only, as for credit holds (spec 298); a member may
  prepare it, and the confirmation is refused with `company_owner_access_required`.
- Q: What does a release lift? → A: The payment shortfall only: `prepayment_required` and
  `prepayment_invoice_missing`. An invoice attributed ambiguously or shared with other orders
  still blocks, and releasing then is refused.
- Q: How is it recorded? → A: An append-only `prepayment_release` row on the order (the shortest
  true relationship), holding the reason, the confirming action and the order amount it covers,
  plus the `order.prepayment_released` event. No status on the document.
- Q: Does a raised order ask again? → A: The release covers the order's stated gross amount, which
  is what the gate measures. Should the required amount ever exceed it, the gate blocks again. A
  raised line quantity does not change the order's stated gross amount once the order has
  promises, so it neither raises the gate nor asks again.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An owner ships a partly prepaid order (Priority: P1)

As a company owner, I let a trusted customer's 80 % prepaid order ship before the rest is paid,
and record why.

**Independent Test**: The R01 story.

**Acceptance Scenarios**:

1. **Given** an order of 100 with 80 paid, **When** it is dispatched, **Then** both shipping
   routes refuse it.
2. **Given** that order, **When** a member confirms a release, **Then** it is refused; **When** an
   owner confirms it with a reason, **Then** the order ships and the event carries the reason.
3. **Given** the shipped order, **Then** the 20 still open stay an open receivable.

### User Story 2 - The combined story reconciles (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the released order, **When** 6 are reordered, 5 arrive on two dates, 1 is cancelled,
   the rest ships and 2 come back damaged and are scrapped, and 3 are credited, **Then** every
   quantity, the stock and every open amount end at their reconciled values.

### Edge Cases

- An order without prepayment terms, a paid order, an order already released for its amount, an
  empty reason, a non-sales document or extra fields are refused with their own codes.
- Another company sees nothing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A company owner MUST be able to release one sales order's prepayment gate with a
  stated reason, through the reviewed tool shared by Web, Chat/MCP and CLI.
- **FR-002**: The release MUST lift only `prepayment_required` and `prepayment_invoice_missing`,
  for the order's stated gross amount as it stood when released.
- **FR-003**: Readiness, the delivery case and the decision trail MUST name the release; the unpaid
  rest MUST stay an open receivable.
- **FR-004**: The Business Journey Guide MUST state R01 as supported with the combined story.

### Domain and Architecture Requirements

- **DR-001**: One append-only table, `prepayment_release`, justified because shipment readiness
  reads it on every prepayment order (Constitution III).
- **DR-002**: No document status; readiness derives from the release at read time.

## Success Criteria *(mandatory)*

- **SC-001**: R01 has a passing end-to-end story and is `supported`.

## Assumptions and Dependencies

- Builds on spec 275 (prepayment gate), spec 298 (owner-only release pattern) and spec 263
  (decision trail).

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002 | US1 | `tests/test_prepayment_release.py` |
| FR-003 | US1.2–3 | `tests/test_prepayment_release.py::test_an_owner_releases_a_partly_paid_order_and_it_ships` |
| FR-004, SC-001 | US2 | `tests/scenarios/test_catalog_finance.py::test_a_partly_paid_prepayment_order_is_released_by_an_owner` |
