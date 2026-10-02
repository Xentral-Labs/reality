# Feature Specification: Foreign-Currency Purchasing

**Feature Branch**: `309-foreign-currency-purchasing`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 15. Close the capability gap behind the partial journeys G08, R06, I11 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

A purchase keeps its currency, but nothing converts it into the company's currency. A USD supplier invoice cannot be paid from a EUR bank account, because cross-currency settlement is refused, and no realised exchange difference is recorded. The company has no currency of its own: amounts default to EUR.

| Journey | Title | Status today |
|---|---|---|
| G08 | Purchase order in foreign currency (USD, CNY) | partial |
| R06 | Import container: 5 purchases, 2 suppliers, freight, duty, USD rate; 2 customer orders waiting | partial |
| I11 | Exchange difference between USD invoice and payment | missing |

### Scope

- **Company currency:** a company currency in the finance settings, EUR by default. It can be changed only while the company has posted nothing.
- **Invoice rate:** a supplier invoice in a foreign currency is posted with the exchange rate a person states. Every ledger entry keeps its amount in the document currency and also carries its amount in the company currency and the rate used.
- **Paying in company currency:** a payment of a foreign invoice states both the amount it settles in the invoice currency and what was paid in the company currency, as a bank statement shows them. The payment's rate follows from these two stated amounts and is never recomputed.
- **Paying in the invoice currency:** a payment without a company-currency amount is paid from an account in the invoice currency, as payment runs do today. It is valued at the invoice rate and realises nothing.
- **Realised difference:** the difference between the invoice's company-currency value of the settled part and what was paid is posted to an exchange-difference account, as a gain or a loss.
  - Partial payments at different rates each realise their own difference.
  - The last payment settles what is left of the invoice's company-currency value, so nothing remains through rounding.
- **Landed cost:** the invoice rate is offered as the currency conversion basis for its receipt costs (spec 242). The receipt's landed cost then reads in the company currency.

### Non-Goals

- Revaluation of open items at a reporting date.
- Rate feeds or a company rate table.
- Foreign-currency sales invoices and customer payments; they keep today's behaviour.
- Foreign-currency payment runs and bank statement columns for a foreign amount.
- Adding a rate to a foreign posting made before this feature; such a posting stays unconverted and cannot be settled across currencies.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

- Q: Who states the rate? → A: The posting and the payment. A person states the rate when posting a foreign supplier invoice. The payment states both amounts it settles (in the invoice currency) and pays (in the company currency), as on the bank statement. The payment rate follows from the two and is never recomputed.
- Q: Where is the company currency kept? → A: In the finance settings, EUR by default. It cannot be changed once the company has posted anything.
- Q: How does the company-currency value reach the ledger? → A: As a second amount on every entry. Each entry keeps its document-currency amount and also its company-currency amount and the rate. Every posting group balances in both. The realised difference is an entry in the payment's group that carries only a company-currency amount, on a new exchange-difference account.
- Q: What else is in scope? → A: Partial payments at different rates, and landed cost from the invoice rate. Payment runs in foreign currency and bank statement columns for a foreign amount stay out.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pay a USD Invoice in EUR (Priority: P1)

As a buyer importing from Asia, I post a USD invoice at the rate of the day, pay it from the EUR account, and see the exchange difference.

**Why this priority**: Rank 15 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a USD purchase order, **When** its invoice of 1,000 USD is posted at a stated rate of 0.92, **Then** the payable is 1,000 USD and 920.00 EUR.
2. **Given** that invoice, **When** it is paid with 912.40 EUR settling 1,000 USD, **Then** the invoice is closed, and an exchange gain of 7.60 EUR is posted.
3. **Given** that invoice, **When** it is paid in two parts at different rates, **Then** each part realises its own difference, and nothing remains open in either currency.
4. **Given** a foreign invoice, **When** a person posts it without a rate, **Then** it is refused.

### User Story 2 - Landed Cost of an Import Container (Priority: P2)

As a buyer, I see the landed cost of a USD container in EUR, with freight and duty.

**Acceptance Scenarios**:

1. **Given** USD supplier invoices posted at their rates, freight and duty in EUR, and two customer orders waiting, **When** the invoice rate is confirmed as the conversion basis, **Then** the receipt's landed cost reads in EUR, and the waiting orders are served from the receipt.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII). The stated rate and both stated payment amounts are kept as stated.
- A posting in the company currency carries the same amount twice and a rate of 1.
- A payment of a foreign invoice without a company-currency amount is paid in the invoice currency and realises nothing. A company-currency amount against an unconverted foreign posting is refused.
- A payment that settles more than is open in the invoice currency is refused, as today.
- Reversing a payment reverses its exchange difference with it.
- Changing the company currency after a posting carries a company-currency value is refused.
- A posted part whose company-currency value would round to nothing is refused.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A posting in a foreign currency MUST state the rate used, and every ledger entry MUST carry its company-currency amount.
- **FR-002**: A cross-currency settlement MUST record the realised difference, per payment, and leave nothing open in either currency once fully paid.
- **FR-003**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-004**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.
- **FR-005**: The company MUST have one company currency, stated in the finance settings, which cannot change once a posting carries a company-currency value. A company whose earlier postings are all in another currency may state that currency, and those postings take their amount as their value.
- **FR-006**: The rate of a foreign supplier invoice MUST be offered as the conversion basis for its receipt costs, confirmed through the existing review.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.
- **SC-003**: Every posting group balances in its document currency and in the company currency.

## Assumptions and Dependencies

- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.
- Builds on spec 242's currency conversion basis for landed cost.

## Open Questions

None; see Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002, FR-005 | US1 | Business stories and service tests (planned) |
| FR-006 | US2 | Business story R06 and costing tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002, SC-003 | US1, US2 | Catalog tests and Guide questions (planned) |
