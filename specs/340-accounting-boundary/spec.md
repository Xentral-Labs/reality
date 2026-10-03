# Feature Specification: Reality Is Not an Accounting System

**Feature Branch**: `340-accounting-boundary`

**Created**: 2026-10-03

**Status**: Accepted (owner decision, 2026-10-03)

**Language**: English

**Input**: Owner decision after round 3 of the sales-gap roadmap: tax rates are never calculated,
and period close stays out because Reality is not meant to be the bookkeeping system. The Business
Journey Guide should state these boundaries instead of listing them as gaps.

## Context and Intent

### Problem

The scenario coverage listed L11 (destination-country VAT), Q02 (a backdated posting into a closed
period) and Q04 (year end with open backorders and purchases) as gaps. Two of them are
bookkeeping questions Reality deliberately does not answer; the third is an operational question
Reality already answers but had never proven.

### Decisions

- **Tax is recorded as stated, never determined.** Shops do not always state a rate. Deriving one
  from gross and net amounts brings rounding problems and claims a precision the source never
  gave. Reality keeps the amounts a source states (spec 284) and keeps a rate only where a source
  states it, in the lossless source payload. No rate is typed or calculated until a consumer acts
  on it; the existing N08 boundary of spec 148 ("no tax engine or tax calculation") applies.
- **No accounting periods.** Reality has no period record, no close and no lock on backdated
  postings. Closing periods belongs to the accounting system that receives the records. The
  period close stub [184](../184-period-close/spec.md) is deferred by this decision.
- **Open promises cross the year end unchanged.** With no period, nothing resets on 1 January:
  open orders and purchases stay open, and deliveries keep their stated dates.

### Non-Goals

- Determining, deriving or validating tax rates, including back-calculating a rate from amounts.
- Accounting periods, period close, year-end close and posting locks.
- This spec does not decide the neutral handoff package of spec 148 FR-012 (journey N07); that
  stays an open gap for a separate owner decision.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Honest boundaries in the Guide (Priority: P1)

As a prospect asking about VAT or period close, I learn that Reality keeps what my sources state
and leaves tax determination and closing to my accounting system.

**Independent Test**: The Guide states L11 and Q02 as out of scope with this specification as the
reason.

**Acceptance Scenarios**:

1. **Given** the Guide, **When** L11 or Q02 is asked, **Then** the answer names the boundary and
   cites this specification.

### User Story 2 - Year end without a period (Priority: P1)

As a warehouse lead, I keep working open orders and purchases across the year end.

**Independent Test**: A business story crosses the year end.

**Acceptance Scenarios**:

1. **Given** an order and a purchase of 10, 4 received and shipped in December, **When** the year
   ends, **Then** 6 stay open on both, and **When** the rest arrives and ships in January,
   **Then** both are fulfilled with December's delivery still counted.

### Edge Cases

- A source that states no tax: nothing is derived; the tax stays unstated.
- A source that states tax amounts per line whose sum differs from its order total by rounding:
  both stay as stated; nothing is redistributed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Business Journey Guide MUST state L11 and Q02 as out of scope and cite this
  specification.
- **FR-002**: Q04 MUST be proven by a business story that crosses the year end.
- **FR-003**: No tax rate MUST be derived from stated amounts anywhere in Reality.

### Domain and Architecture Requirements

- **DR-001**: No schema change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: L11 and Q02 are `out_of_scope`, Q04 is `supported`, and the coverage counts add up.

## Assumptions and Dependencies

- Spec 284 records stated net and tax per invoice position; spec 148 already excludes a tax engine.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, SC-001 | US1 | Journey catalog and Guide tests |
| FR-002 | US2 | `tests/scenarios/test_catalog_time.py::test_open_orders_and_purchases_carry_over_the_year_end` |
| FR-003, DR-001 | All | Diff review: no code change |
