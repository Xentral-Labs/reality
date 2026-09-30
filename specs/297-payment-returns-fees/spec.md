# Feature Specification: Chargebacks, Returned Direct Debits and Payment Fees

**Feature Branch**: `297-payment-returns-fees`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 3. Close the capability gap behind the partial journeys C15, E08 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Reversing a payment reopens the receivable, but a chargeback or returned direct debit is not a recorded event, its fee is not recorded, and payment-provider fees on payouts are not recorded either.

| Journey | Title | Status today |
|---|---|---|
| C15 | Chargeback / returned direct debit after shipment | partial |
| E08 | Shipping cost, small-quantity surcharge, payment fees | partial |

### Scope

- A person records a returned direct debit or a chargeback against the payment it reverses, with its kind, stated reason and provider or bank reference, through one reviewed tool.
- The payment's posting is reversed as today, so the invoice is open again; the return is its own record, not only a reversal.
- A stated fee is recorded with the return; per case the person charges it on to the customer (its own receivable, like the dunning fee) or books it as the company's payment-fee expense.
- The reopened invoice shows the return, and a finding "Payment returned" stays until the invoice is settled again; dunning continues as usual.
- A customer payment can state a fee the provider deducted (an invoice of 100 paid as 97 plus a fee of 3): the invoice is settled in full and the fee is the company's payment-fee expense.
- Freight and surcharges on sales invoices are separate lines that no goods finding misreads (E08).

### Non-Goals

- Dispute handling with the provider.
- Marketplace payout reconciliation (see missing journey L03).
- Anything that requires a document status field (Constitution II).
- Importing returns, chargebacks or payouts from bank or provider files; a later specification.
- Calculating fees; every fee is the amount stated by the bank or provider.

## Clarifications

### Session 2026-09-30

- Q: Who bears the fee of a returned debit or chargeback? → A: The person chooses per case: charge it on to the customer (a receivable) or book it as the company's expense; charging it on is preselected.
- Q: How do returns and chargebacks arrive? → A: A person records them through a reviewed tool on Web, Chat and CLI; source imports come later.
- Q: How is the reopened invoice followed up? → A: A finding "Payment returned" with reason and reference until the invoice is settled again; the open item names the reason.
- Q: Are fees deducted from an ordinary payment in scope? → A: Yes: a payment can state the deducted fee; the invoice is settled in full and the fee is an expense.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Chargebacks, Returned Direct Debits and Payment Fees (Priority: P1)

As a receivables clerk, I record a returned direct debit with its bank fee, and the customer's open item is back with the reason.

**Why this priority**: Rank 3 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a paid invoice, **When** its direct debit comes back with a fee charged on to the customer, **Then** the payment is reversed and recorded as a returned direct debit, the fee is the customer's own receivable, and the invoice is open again with the return named.
2. **Given** a chargeback, **When** it is recorded with its fee as an expense, **Then** the kind, reason and provider reference are kept as stated, the fee is booked to payment-fee expense, and nothing is charged to the customer.
3. **Given** a returned payment, **When** the invoice is paid again, **Then** the finding "Payment returned" clears; before that it is reported (positive control).
4. **Given** an invoice of 100, **When** the provider pays 97 and states a fee of 3, **Then** the invoice is settled in full and 3 is booked as payment-fee expense.
5. **Given** a sales invoice with a freight and a surcharge line, **When** it is posted, **Then** the lines are recorded separately from the goods and no goods finding reports them.

### User Story 2 - Reviewed tools on every surface (Priority: P1)

As a clerk or an agent, I record a return or a payment fee through the same reviewed tool on Web, Chat/MCP and CLI.

**Independent Test**: Adapter tests for the return tool and the payment fee field.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).
- A payment allocated to two invoices comes back: both invoices reopen and each is named in the finding.
- A payment already reversed or returned cannot be returned again.
- A fee of zero records no fee posting.
- A fee charged on is its own open item; paying the invoice again does not settle the fee.
- A payment fee larger than the payment is refused.
- Returning a payment settled together with a payment fee is refused in this specification; the fee adjustment is reversed first.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A returned direct debit or chargeback MUST be recorded as its own record linked to the payment it reverses, with its kind, stated reason and reference, and MUST reverse the payment's posting through the existing reversal so the invoices it paid are open again.
- **FR-002**: A return's fee MUST be recorded separately as stated and MUST NOT change the invoice amount; the person MUST choose per return whether it is charged to the customer (its own receivable) or booked as payment-fee expense.
- **FR-003**: The reopened invoice MUST name the return, and a finding "Payment returned" MUST report it until the invoice is settled again.
- **FR-006**: A customer payment MUST be able to state a fee the provider deducted; the invoice is settled by the payment plus the fee, and the fee is booked as payment-fee expense.
- **FR-007**: A sales invoice MUST carry freight and surcharges as separate lines without an order line, and no goods finding MUST report them.
- **FR-004**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-005**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Created as a short draft from the sales-gap roadmap; clarified with the owner on 2026-09-30.
- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.
- Known gap inherited from spec 295: a fee charged on to the customer is a ledger receivable but not an open item, because `financial_open_items` reads invoices and opening debts only.
- A payment settled together with a reduction (payment fee, discount, agreed deduction, small remainder) is returned only after that reduction is reversed, so the invoice never reopens short.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 1–3 | Return service tests and the C15 story |
| FR-006, FR-007 | US1 4–5 | Payment fee tests and the E08 story |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions |
