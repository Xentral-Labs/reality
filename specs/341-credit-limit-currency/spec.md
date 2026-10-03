# Feature Specification: Credit Limit and Orders in Another Currency

**Feature Branch**: `341-credit-limit-currency`

**Created**: 2026-10-03

**Status**: Accepted (owner decision, 2026-10-03)

**Language**: English

**Input**: The owner noticed that a customer's credit limit shows amounts in other currencies but
does not count them, and asked to close the operational risk without converting (option 1:
hold such an order for a person), and to document where currency limits remain.

## Context and Intent

### Problem

Spec 298 holds a new sales order that takes its customer past the credit limit. The exposure is
counted in the customer's own currency; amounts in another currency are named as not counted,
because converting would guess. An order in another currency was not checked at all: it was
never held, whatever the customer already owed, so a customer could pass the limit unnoticed by
ordering in another currency.

### Decision

An order in another currency than the customer's limit is held for a person, with a reason that
says the limit is stated in its currency and Reality does not convert. Nothing is converted and
no rate is assumed. The hold is an ordinary credit hold: only an owner releases it, with a
reason, and raising the order later asks again.

### Non-Goals

- Converting amounts between currencies, or a stated rate for the limit.
- A credit limit per currency.
- Changing the credit-limit finding, which keeps counting the customer's own currency.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - No order passes the limit unchecked (Priority: P1)

As a credit controller, I want an order in another currency than the customer's limit to wait
for me, because Reality cannot tell whether it is within the limit.

**Independent Test**: A USD order for a customer with a EUR limit is held with the reason.

**Acceptance Scenarios**:

1. **Given** a customer with a limit of 1,000 EUR and an EUR order of 200, **When** a USD order
   of 50 is recorded, **Then** its promises are held with "Credit limit 1000.00 EUR is stated in
   EUR; this order is in USD, which Reality does not convert, so a person decides", and the EUR
   order is not held.
2. **Given** that hold, **When** an owner releases it with a reason, **Then** the order is free,
   and **When** the order is raised later, **Then** it is held again.
3. **Given** a customer without a limit, **When** an order in any currency is recorded, **Then**
   nothing is held.

### Edge Cases

- An order in another currency with nothing left to invoice adds no credit and is not held.
- A line assigned later to an order held for credit is held with the same reason.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every path that records or raises a sales order MUST hold the order's promises for
  a person when the customer has a credit limit and the order is in another currency than the
  limit, with a reason naming both currencies and that Reality does not convert.
- **FR-002**: The hold MUST be an ordinary credit hold of spec 298 (owner-only release with a
  reason), and its event MUST carry the exposure and the order's currency.
- **FR-003**: The Business Journey Guide and the scenario coverage MUST state where Reality
  names another currency instead of converting.

### Domain and Architecture Requirements

- **DR-001**: No schema change; the hold and its facts use the existing records.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No sales order for a customer with a credit limit passes the credit check without
  being counted or held.

## Assumptions and Dependencies

- Builds on [spec 298](../298-automatic-credit-hold/spec.md); its edge case is updated.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, SC-001 | US1.1, US1.3 | `tests/test_credit_hold.py::test_an_order_in_another_currency_waits_for_a_person`, `::test_no_limit_holds_nothing_in_any_currency` |
| FR-002 | US1.2 | `tests/test_credit_hold.py::test_an_owner_releases_a_currency_hold_and_a_raise_asks_again`, `::test_an_assigned_line_of_a_credit_held_order_is_held` |
| FR-003 | All | `docs/scenarios/coverage.md`, journey C07 |
