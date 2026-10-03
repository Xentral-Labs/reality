# Feature Specification: Marketplace and Payment-Provider Payouts

**Feature Branch**: `336-marketplace-payouts`

**Created**: 2026-10-02

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 2. Close the capability gap behind the journeys L03, R04, C09, C10, C13 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Marketplace and payment-provider payouts are not matched to orders; fees, refunds and chargebacks within a payout are not allocated; authorizations, captures and cash on delivery are not recorded.

| Journey | Title | Status today |
|---|---|---|
| L03 | Marketplace payout: one payment for hundreds of orders minus fees and refunds | missing |
| R04 | Marketplace payout with 400 orders, 12 refunds, 3 chargebacks and fees | missing |
| C09 | Card/PayPal/Klarna: authorization ≠ capture | missing |
| C10 | Authorization expires before a late partial shipment | missing |
| C13 | Cash on delivery | missing |

### Scope

- A payout statement that settles one bank payment across many orders, minus fees, refunds and chargebacks.
- Authorization and capture as separate stated records, with an expired authorization reported.
- Cash on delivery: the carrier's remittance is a payout whose lines name the shipment.

### Non-Goals

- Live marketplace or provider APIs and file profiles for their report formats. The statement is stated through the reviewed command, from a file by CLI or as arguments by an agent.
- A web screen for entering or browsing payouts. The statement is too long to type; the web API proposes it and reads what was settled, and the payment and document registers show the bookings. A payout register in the web app is a follow-up.
- Moving the receivable to the provider at capture time. A capture is a stated fact about the authorization, not a posting; the money posts when the payout arrives.
- The accounting export package of spec 148.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

The owner delegated these decisions to the recommended options.

- Q: Is a payout allocated automatically by order reference with a review, or line by line by a person? → A: Automatically, by the references each line states, shown in one review and confirmed as one action.
  - The review names, for every line, what it will do: allocate to an invoice, record for the customer without an invoice, return a payment, or book a fee.
  - A line that leads nowhere stays unbooked and is reported for a person.
  - Settling the same statement again later books only what was still unbooked, for example after the order arrived.
- Q: Where does the provider's money sit between sale and payout? → A: On a cash account the person chooses for the provider, such as "Amazon Payments" or "PayPal".
  - Each order's payment is booked on that account, so the payments, open items, returns and down-payment rules keep treating it as money received.
  - The bank deposit moves the stated net payout from that account to the bank account.
  - Whatever stays on the provider account is what the provider still holds or what was not booked.
- Q: What must a statement satisfy? → A: Its lines must add up to the stated net payout: charges, minus refunds, minus chargebacks, minus fees. A statement that does not add up is refused with both totals. Nothing is recomputed or corrected.
- Q: How are refunds and chargebacks booked? → A: Each through the existing primitives.
  - A refund is a customer refund on the provider account, allocated to an open credit note of the order when one exists. Otherwise it is recorded for the customer, who then shows a debit until a credit note follows.
  - A chargeback returns the order's payment that was booked on this provider account through the spec 297 return, kind chargeback. A chargeback for a payment Reality does not hold on that account stays unbooked.
- Q: Are authorization and capture separate facts? → A: Yes. An authorization is a stated amount for one sales order, with its expiry. A capture is a stated amount against one authorization, and never more than is left. Both are recorded through reviewed commands.
- Q: When is an expired authorization reported? → A: When an authorization has expired with an uncaptured remainder, the order still has goods to ship, and live authorizations do not cover the remainder. The finding names the uncovered amount. It clears through a new authorization, or once the order has nothing left to ship.
- Q: How is cash on delivery tied to the shipment? → A: The carrier remits as a payout. Its line states the shipment's tracking number, which leads to the order and its invoice. The payout read names the shipment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Settle a Marketplace Payout (Priority: P1)

As a bookkeeper, I state a marketplace payout and see which orders it paid and what it kept.

**Why this priority**: Round 2 of the sales-gap roadmap: one bank payment for hundreds of orders is the everyday situation of every merchant selling on a marketplace.

**Independent Test**: A business story per journey through the reviewed command, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a payout of 400 orders minus fees, 12 refunds and 3 chargebacks, **When** stated and confirmed, **Then** each order is paid, every refund settles its credit note, every chargeback reopens its invoice, every fee is booked, and the bank receives the stated net.
2. **Given** a payout line that names an order Reality does not hold, **When** confirmed, **Then** the line stays unbooked and is reported. **When** the order arrives and the statement is settled again, **Then** only that line is booked.
3. **Given** a statement whose lines do not add up to the stated net payout, **When** reviewed, **Then** it is refused with both totals.

### User Story 2 - Authorization and Capture (Priority: P1)

As a bookkeeper, I see what a card provider authorized for an order, what was captured, and what is no longer secured.

**Independent Test**: The authorization read and the expired-authorization finding.

**Acceptance Scenarios**:

1. **Given** an order of 100 authorized for 100, **When** 60 are captured, **Then** the order reads authorized 100, captured 60, remaining 40.
2. **Given** that authorization expires while 40 remain to ship, **When** read, **Then** the uncovered 40 are reported. **When** a new authorization of 40 is recorded, **Then** the finding clears.

### User Story 3 - Cash on Delivery (Priority: P2)

As a bookkeeper, I see the carrier's cash-on-delivery remittance settle the order it was collected for.

**Acceptance Scenarios**:

1. **Given** a shipped and invoiced order, **When** the carrier remits a payout whose line states the tracking number, minus its fee, **Then** the invoice is paid and the payout read names the shipment.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).
- A charge for an order that is not invoiced yet is recorded for its customer and offered as a candidate later.
- A charge larger than the invoice's open amount allocates what is open; the rest is the customer's credit.
- A chargeback in the same payout as its charge is booked after the charge.
- The same statement settled twice books nothing twice; a statement changed under the same payout reference is refused.
- A provider account that is the bank account itself is refused.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A payout MUST be allocated to the orders it pays, with fees, refunds and chargebacks booked.
  - The lines MUST add up to the stated net payout, or the statement is refused.
  - Lines that lead nowhere MUST stay unbooked and be reported until settled.
- **FR-002**: An authorization MUST be recordable apart from its capture. An expired authorization whose remainder is not covered MUST be reported while the order has goods to ship.
- **FR-003**: Cash on delivery MUST tie a payment to a shipment through the stated tracking number.
- **FR-004**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-005**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.
- **SC-003**: The 400-order payout is reviewed and settled in one action, and its query count grows linearly with its lines.

## Assumptions and Dependencies

- Builds on payment intake (spec 168), customer refunds and credit notes, payment returns (spec 297) and the finance account roles.
- The provider is a business partner, and its account is a cash-role account the person creates with the existing finance account commands.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1 | `tests/finance/test_payouts.py`; stories L03 and R04 |
| FR-002 | US2 | `tests/finance/test_payment_authorizations.py`; stories C09 and C10 |
| FR-003 | US3 | Story C13 |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review |
| FR-005, SC-001, SC-002 | All | Catalog tests and Guide questions |
| SC-003 | US1 | Story R04 with a bounded query count |
