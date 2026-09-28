# Feature Specification: Journey Proof Stories

**Feature Branch**: `292-journey-proof-stories`

**Created**: 2026-09-28

**Status**: Draft

**Language**: English

**Input**: Twelve Business Journey Guide entries are `partial` although every building block exists; only an end-to-end executable story is missing. Prove them with business-story tests so the Guide can state them as supported, starting with the journeys that come up in sales conversations.

## Context and Intent

### Problem

The Business Journey Guide (spec 290) publishes 81 `partial` journeys. For a subset, the coverage audit in `docs/scenarios/coverage.md` shows that each piece of behavior is already tested on its own, or on the other trading side, but no single story runs the whole journey. The Guide must then say "not yet proven", which a prospective customer reads as "does not work". Examples are a B2C withdrawal with full refund (F01), an exchange without money moving (F07) and one payment releasing two prepaid orders (C04).

Supported status requires executable evidence (spec 290 FR-003). The gap is therefore evidence, not capability, until a story shows otherwise.

### Scope

Write one executable business story per journey below, using only the shared application services and tools that CLI, Web and Chat already use. Promote each journey whose story passes to `supported` with that story as its executable evidence, and regenerate the Guide.

| ID | Journey | Story must show |
|---|---|---|
| A04 | Customer raises the quantity after a partial delivery | the open quantity after the upward revision equals the revised quantity minus what was delivered |
| A06 | One line cancelled, the rest stays | the cancelled line is closed and unreserved while the other lines of the same order stay open and reserved |
| A07 | Whole order cancelled after reservation | cancelling every line of a reserved multi-line order releases every reservation |
| A19 | Zero-price line (sample, gift, replacement) | a zero-price order line is committed, reserved and shipped, and invoicing it yields no revenue |
| C04 | One payment for two prepaid orders | one payment settles both prepayment invoices and both orders become ready to ship |
| F01 | B2C withdrawal within 14 days, full refund | on one order: delivery, return with stock back, full credit note and the refund paid, with nothing left open |
| F05 | Damaged return, partial refund | a damaged return's disposition and a reduced credit on the same order, independent of each other |
| F07 | Exchange: return plus new delivery, no money | a return and a replacement delivery on the same customer, with no credit, refund or payment |
| M08 | Customer deducts a penalty or marketing contribution | a customer short payment with an agreed-deduction reason leaves nothing open and names the reason |
| N01 | Intra-community supply (VAT-exempt, VAT ID) | a sales invoice with zero stated tax, its tax case and the customer's VAT ID are recorded as stated |
| N02 | Reverse charge on purchase | a supplier invoice under reverse charge keeps its stated net and tax components |
| N06 | Open items per party including credits and prepayments | the party balance is correct with a deposit and a prepayment next to open invoices and credits |

### Non-Goals

- New business capabilities, schema, tables, tools or UI. A journey that needs any of them stays `partial`.
- The other `partial` journeys, including the ones whose feasibility is uncertain (F04, F08, H09, P02, P05, P08, B09) and the purchasing and operations candidates (H03, I06, I07, G07, K05, L06, O01, P04, P07, R01). They are candidates for a follow-up.
- Changing how the Guide answers, matches or renders journeys.
- Removing limitations that describe behavior outside the journey's question, such as the absence of an order-level cancellation in A07.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Order changes are proven end to end (Priority: P1)

As a prospective customer asking about order changes, I see A04, A06, A07 and A19 as supported, with evidence that the whole journey works.

**Why this priority**: Quantity changes and cancellations come up in every sales demo of order handling.

**Independent Test**: Run the order-change stories against the shared services; each asserts the journey's question from order to final state.

**Acceptance Scenarios**:

1. **Given** an order line of 10 with 4 delivered, **When** the customer raises the quantity to 12, **Then** 8 are open and the delivered 4 stay delivered.
2. **Given** a reserved three-line order, **When** one line is cancelled, **Then** only that line is closed and unreserved, and the other two stay open and reserved.
3. **Given** a reserved multi-line order, **When** every line is cancelled, **Then** no reservation of that order remains and the stock is available again.
4. **Given** a zero-price line next to a priced line, **When** both are shipped and invoiced, **Then** the zero-price line is fulfilled and contributes no revenue.

---

### User Story 2 - Returns and refunds are proven end to end (Priority: P1)

As a prospective e-commerce customer, I see F01, F05 and F07 as supported because one story on one order shows stock, credit and money together.

**Why this priority**: Withdrawal, damaged returns and exchanges are daily B2C work and appear in every e-commerce evaluation.

**Independent Test**: Run the three return stories; each reconciles quantities and amounts at the end.

**Acceptance Scenarios**:

1. **Given** a paid, delivered B2C order, **When** the customer withdraws and returns everything, **Then** stock is back, the credit note equals the invoice, the refund is paid and neither the receivable nor the credit stays open.
2. **Given** a delivered order returned partly damaged, **When** the damaged part is written off and a reduced credit is granted, **Then** the disposition and the credit amount are each correct and neither depends on the other.
3. **Given** a delivered item exchanged for another, **When** the return and the replacement delivery are recorded, **Then** both are traceable to the customer and no credit note, refund or payment exists for the exchange.

---

### User Story 3 - Payments and balances are proven end to end (Priority: P2)

As a prospective customer's finance lead, I see C04, M08 and N06 as supported.

**Why this priority**: Collective payments, customer deductions and correct partner balances decide whether finance trusts the system.

**Independent Test**: Run the three settlement stories; each asserts open items and readiness after settlement.

**Acceptance Scenarios**:

1. **Given** two orders awaiting prepayment, **When** one payment covers both prepayment invoices, **Then** both invoices are settled and both orders are ready to ship.
2. **Given** a customer invoice paid short with an agreed penalty deduction, **When** the payment is settled with that reason, **Then** nothing stays open and the deduction names its reason.
3. **Given** a customer with open invoices, a credit note, a deposit and a prepayment, **When** the party balance is read, **Then** each item appears once with the correct sign and the balance equals their sum.

---

### User Story 4 - Stated tax cases are proven end to end (Priority: P2)

As a prospective customer selling across the EU, I see N01 and N02 as supported because Reality keeps the tax the source states.

**Why this priority**: Intra-community supplies and reverse charge are routine for B2B traders and are checked in every tax review.

**Independent Test**: Run the two tax stories; each asserts that stated values are kept, not recomputed (Constitution VIII).

**Acceptance Scenarios**:

1. **Given** a sales invoice to an EU business customer with a VAT ID and zero stated tax, **When** it is recorded, **Then** the zero tax, its tax case and the customer's VAT ID are kept as stated and no tax is computed.
2. **Given** a supplier invoice under reverse charge, **When** it is recorded, **Then** its stated net and tax components are kept as stated.

---

### User Story 5 - The Guide follows the evidence (Priority: P1)

As a Guide reader, I see a journey as supported only when its story passes, and I still see an honest limitation when it does not.

**Why this priority**: A false supported claim is worse than a cautious one (spec 290 US5).

**Independent Test**: Promote the proven journeys, regenerate the Guide and run the catalog checks; a journey whose story fails keeps `partial`.

**Acceptance Scenarios**:

1. **Given** a passing story, **When** the catalog is updated, **Then** the journey is `supported`, its evidence level is `executable`, the story is its internal evidence and its public limitation no longer says the journey is unproven.
2. **Given** a story that reveals a defect against an already-specified requirement, **When** the defect is fixed with a regression test, **Then** the journey may be promoted in the same change.
3. **Given** a story that reveals a missing capability, **When** the change is completed, **Then** the journey stays `partial`, its public limitation names what the story found, and the finding is recorded in `docs/scenarios/coverage.md`.

### Edge Cases

- A story passes only with a direct database write or a test-only shortcut. It does not count as evidence; the journey stays `partial`.
- A story needs data the demo profile does not seed. The story builds its own fixture; demo references are not added.
- A journey is proven on the sales side but its question also covers the purchase side. Only the proven side is claimed, and the limitation names the other.
- A promoted journey keeps a limitation outside its question. The entry is `supported` with that limitation still visible.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each journey in scope MUST have one executable business-story test that runs the journey's question from start to final state through shared application services or tools only.
- **FR-002**: A story MUST assert the business outcome the journey's question asks for, quantities and amounts included, not only the absence of errors.
- **FR-003**: A journey MUST be promoted to `supported` with `executable` evidence only when its story passes; its internal evidence MUST reference that story.
- **FR-004**: A promoted journey's public limitation MUST no longer describe the journey as unproven; limitations outside its question MAY remain.
- **FR-005**: A story that fails because of a defect against an existing requirement MAY be fixed in this feature with a regression test that references that requirement; any other failure MUST leave the journey `partial` with an updated public limitation.
- **FR-006**: Every finding from a failed story MUST be recorded in `docs/scenarios/coverage.md`.
- **FR-007**: The Guide payload MUST be regenerated so that browsing and question answers reflect the new statuses.
- **FR-008**: This feature MUST NOT add schema, tools, service entry points or UI.

### Domain and Architecture Requirements

- **DR-001**: Stories MUST respect Source → Evidence → Reality and MUST NOT assert fulfilment or payment status stored on documents.
- **DR-002**: Tax stories MUST assert that stated values are recorded and never recomputed (Constitution VIII).
- **DR-003**: Every story MUST run tenant-scoped through the same services and confirmation boundaries as CLI, Web and Chat.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All twelve journeys have a business-story test that runs in the required backend suite.
- **SC-002**: Every journey whose story passes is `supported` in the published Guide; the number of supported journeys rises by exactly the number of passing stories.
- **SC-003**: No journey is promoted without a passing story, and no failed story is left without a recorded finding.
- **SC-004**: Asking the Guide about each promoted journey returns `supported` with that journey cited.

## Assumptions and Dependencies

- Depends on PR #243 (spec 290 FR-002a), which gives every non-supported journey its own limitation text; this feature edits those texts.
- The candidates were selected from the internal evidence notes in `business_journey_catalog.yaml` and `docs/scenarios/coverage.md`; feasibility is confirmed only by the story itself.
- Existing tests named in each journey's internal evidence stay; the new story is added beside them.
- A story may reuse existing test fixtures but not demo seeding.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002, DR-001, DR-003 | US1–US4 | One business-story test per journey |
| DR-002 | US4 | Tax stories assert stated values |
| FR-003–FR-007 | US5 | Catalog update, catalog tests, regenerated Guide, coverage record |
| FR-008 | All | Diff review: no migration, tool, service or UI change |
| SC-001–SC-004 | All | Backend suite, catalog tests, Guide question tests |
