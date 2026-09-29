# Feature Specification: Foreign-Currency Purchasing

**Feature Branch**: `309-foreign-currency-purchasing`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 15. Close the capability gap behind the partial journeys G08, R06, I11 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

A purchase keeps its currency and cross-currency settlement is refused; nothing converts at posting, and a realised exchange difference is not recorded.

| Journey | Title | Status today |
|---|---|---|
| G08 | Purchase order in foreign currency (USD, CNY) | partial |
| R06 | Import container: 5 purchases, 2 suppliers, freight, duty, USD rate; 2 customer orders waiting | partial |
| I11 | Exchange difference between USD invoice and payment | missing |

### Scope

- A stated exchange rate at posting.
- Settlement of a USD invoice with a EUR payment and the realised difference.
- Landed cost in the company currency.

### Non-Goals

- Revaluation of open items.
- Rate feeds.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Foreign-Currency Purchasing (Priority: P1)

As a buyer importing from Asia, I pay a USD invoice in EUR and see the exchange difference.

**Why this priority**: Rank 15 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a USD invoice and a EUR payment with a stated rate, **When** it is settled, **Then** the invoice closes and the realised difference is recorded.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A posting in a foreign currency MUST state the rate used.
- **FR-002**: A cross-currency settlement MUST record the realised difference.
- **FR-003**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-004**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Created as a short draft from the sales-gap roadmap; it must be clarified and accepted by the owner before planning.
- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.

## Open Questions

- [NEEDS CLARIFICATION: Who states the rate: the bank line, a person, or a rate table?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-002 | US1 | Business stories and service tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
