# Feature Specification: Journey Proof Stories, Round Three

**Feature Branch**: `314-partial-journey-proofs`

**Created**: 2026-09-30

**Status**: Approved

**Language**: English

**Input**: Spec 294 set aside seven uncertain partial journeys for a test round of their own (B09, F04, F08, H09, P02, P05, P08). Prove each with a business story, fix the defects the stories find against existing behaviour, and let the Guide state what is proven.

## Context and Intent

### Problem

After specs 292–297 the Business Journey Guide lists 50 partial journeys. Seven of them look provable with existing capabilities but were never exercised end to end. Research for this specification found four defects behind them:

- A stated reason on a receipt without a purchase order is discarded.
- A receipt recorded through the delivery path without a purchase order is never reported.
- A payment whose stated reference later matches exactly one invoice gets no candidate for that invoice.
- A shop order line without a stated price becomes a price of zero, and a line with a null price or no quantity makes the whole import job fail outside the reported failure path.

### Scope

| ID | Journey | Story must show | Outcome sought |
|---|---|---|---|
| F04 | Unannounced return | a parcel without an announcement is accepted and reported; a reviewed correction later links it to its delivery; what is owed back becomes visible and settles with a credit | supported |
| F08 | Refund before the return arrives | a credit note and its refund are paid before the goods come back; the announced return stays expected and is reported once overdue; the arrival fulfils it | supported |
| H09 | Receipt without purchase order | a receipt with a stated reason (sample, free of charge, misdelivery) keeps the reason and is explained by it; one without a reason is reported, whichever path recorded it | supported |
| P02 | Events out of order | a shop refund that arrives before its order is linked by itself once the order is in; a payment that arrives before its order is offered for that order's invoice, with its stated reference as the reason, and a person allocates it | supported |
| P05 | Incomplete payload accepted | an order with a line lacking its price or quantity is accepted, the rest is interpreted, and the gap is reported; nothing is invented for the missing value | supported |
| P08 | Open orders at go-live | an order partly delivered before go-live is recorded with its original quantity as evidence and only its open rest as a promise, both traced to the legacy source; nothing is reported for the part delivered before go-live | supported |
| B09 | Receipt covers only part of the backorders | the story records the finding only | stays partial; moves to spec 305 |

### Non-Goals

- New tools, UI, or schema beyond what a fix below needs; any addition is justified in the plan.
- Assignment-aware coverage after a receipt (B09): a receipt does not consume supply assignments, so "which promises remain uncovered" is answered only through reservations. This belongs to spec 305, *Serving Backorders on Receipt*.
- Linking a return to its announcement through a correction (F04), and a credit issued through the invoice counting towards *credited not returned* (F08). Both are recorded as limitations.
- Automatic allocation of a payment once its order arrives (P02); a person decides.
- A delivered-before-go-live quantity as a typed value (P08); it stays in the lossless legacy payload.

## Clarifications

### Session 2026-09-30

- Q: How should a receipt without a purchase order and with a stated reason be treated (H09)? → A: The reason is kept, the movement explanation shows it, and it no longer counts as unexplained. A receipt without a commitment recorded through the delivery path is reported like any other unexplained receipt until a reason, a purchase or a correction explains it.
- Q: What should happen to a line without a stated price or quantity (P05)? → A: The job no longer fails outside the reported path; a line without a stated price is accepted without inventing a price, and the gap is reported until the price is stated.
- Q: Which small defects are fixed here (F08, P02)? → A: P02 only: a payment's stated reference that now matches exactly one invoice makes that invoice a candidate with the reference as its reason. The invoice-path credit for F08 stays as it is and is recorded as a limitation.
- Q: How honest is the promotion (B09, P08)? → A: P08 is promoted with the limitation that the pre-go-live delivered quantity lives only in the legacy payload. B09 stays partial and its finding is added to spec 305.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Returns and refunds are proven end to end (Priority: P1)

As a prospective customer's service lead, I see F04 and F08 as supported, because a story shows how an unannounced parcel and a goodwill refund are followed up.

**Why this priority**: Returns without paperwork and refunds before the goods arrive come up in every e-commerce demo.

**Independent Test**: Run the two stories through the shared services and reviewed tools.

**Acceptance Scenarios**:

1. **Given** an invoiced delivery of 2, **When** a parcel of 2 arrives without an announcement, **Then** the stock is back, the return is reported as unexplained, and nothing is owed back yet.
2. **Given** that return, **When** a person links it to the delivery through a reviewed correction, **Then** the unexplained finding clears, *returned not credited* is reported for 2, and a credit of 2 settles it.
3. **Given** an announced return of 2 due in five days, **When** a credit note is posted and refunded before anything arrives, **Then** the credit is settled, the announcement is still open for 2, and nothing is reported before the due date.
4. **Given** that state after the due date, **When** it is read, **Then** the overdue announcement is reported; **When** the goods arrive against it, **Then** it is fulfilled and nothing is reported.

---

### User Story 2 - Receipts without a purchase order explain themselves (Priority: P1)

As a warehouse lead, I see why stock arrived without a purchase order.

**Why this priority**: Samples, free goods and misdeliveries are daily receiving work.

**Independent Test**: Record receipts with and without a reason through the reviewed paths and read their explanations and findings.

**Acceptance Scenarios**:

1. **Given** no purchase order, **When** a receipt of 2 is recorded with the reason "free sample", **Then** its explanation shows that reason, and it is not reported as unexplained.
2. **Given** no purchase order, **When** a receipt is recorded without a reason, through the movement or the delivery path, **Then** it is reported as unexplained.
3. **Given** such a reported receipt, **When** a correction links it to a purchase, **Then** the finding clears.

---

### User Story 3 - Sources out of order and incomplete are proven (Priority: P2)

As a prospective customer's IT lead, I see P02 and P05 as supported.

**Why this priority**: Integration failure modes decide whether an ERP can run unattended.

**Independent Test**: Run the stories with stored source payloads through the intake paths.

**Acceptance Scenarios**:

1. **Given** a shop refund whose order has not arrived, **When** it is taken in, **Then** it fails visibly; **When** the order arrives and the retry is due, **Then** the refund is linked to the order without a person and the failure clears.
2. **Given** a payment stating a shop order that is not known yet, **When** it is taken in, **Then** the money is recorded as unallocated with a named reason; **When** the order is taken in and invoiced, **Then** that invoice is offered as a candidate with the stated reference as its reason, also when the amount differs; **When** a person allocates it, **Then** the invoice is settled and nothing unallocated remains.
3. **Given** a shop order whose second line has no price, **When** it is taken in, **Then** the order and its first line are interpreted, the second line keeps what the source stated and no invented price, and the missing price is reported while the line has none.
4. **Given** a shop order whose line has a null price or no quantity, **When** it is taken in, **Then** the import job does not crash; the gap is reported as a failure or finding with a code, and other orders in the batch are unaffected.

---

### User Story 4 - Open orders at go-live are traceable (Priority: P2)

As an implementation consultant, I see P08 as supported.

**Acceptance Scenarios**:

1. **Given** a legacy order of 10 of which 4 were delivered before go-live, **When** it is recorded at go-live, **Then** the order evidence states 10, the promise is for the open 6, and both trace to the legacy source record, whose payload keeps the delivered 4.
2. **Given** that state, **When** 6 are reserved, shipped and invoiced, **Then** no finding reports the 4 delivered before go-live as unbilled or overdue, with a positive control for the open rest before invoicing.

---

### User Story 5 - The Guide follows the evidence (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a passing story, **When** the catalog is updated, **Then** the journey is `supported` with executable evidence and is found by an ordinary English and German question.
2. **Given** B09, **When** the change is complete, **Then** it stays `partial`, its limitation names the finding, and spec 305 lists it.

### Edge Cases

- A receipt reason that is only whitespace counts as no reason.
- A correction of an explained receipt keeps its explanation on the replacement.
- A shipment or return without an order is not explained by a typed reason; it stays reported.
- A payment reference matching several invoices keeps today's ambiguous-candidate behaviour.
- A later shop version that states the missing price is held for review as a price change (spec 296); it does not fail on the missing earlier price.
- A story passes only with a direct database write or a test-only shortcut: it does not count.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each journey in scope MUST have one executable business story through shared application services, source intake or reviewed tools only.
- **FR-002**: A story MUST assert its journey's business outcome, quantities and amounts included; every "no finding" assertion MUST have a positive control, and every refusal or failure MUST assert its code.
- **FR-003**: A stated reason on a receipt without a commitment MUST be kept, shown in the movement explanation, and MUST explain the receipt so it is not reported as unexplained.
- **FR-004**: A receipt without a commitment recorded through the delivery path MUST be reported as unexplained unless a reason, a source record or a correction explains it.
- **FR-005**: A payment whose stated reference matches exactly one open invoice MUST offer that invoice as a candidate with the reference as its reason, independent of the amount; allocation stays a person's decision.
- **FR-006**: A source order line without a stated price or quantity MUST NOT make the import job fail outside the reported failure path; a line without a stated price MUST NOT be recorded as a stated price of zero, and the missing price MUST be reported while the line has none.
- **FR-007**: A journey MUST be promoted to `supported` with `executable` evidence only when its story passes, citing that story first, with English and German keywords or question examples and no "not yet proven" limitation.
- **FR-008**: B09 MUST stay `partial` with a limitation naming the missing assignment-aware coverage, and spec 305 MUST list the finding.
- **FR-009**: The Guide payload, coverage document and roadmap MUST be regenerated or updated.

### Domain and Architecture Requirements

- **DR-001**: Stories MUST respect Source → Evidence → Reality and MUST NOT assert fulfilment, billing or payment status stored on documents.
- **DR-002**: Stated prices, amounts and quantities MUST be recorded as stated; a missing value MUST NOT be replaced by a computed or default one (Constitution VIII).
- **DR-003**: Fixes MUST use the shortest true relationship; a receipt's reason belongs to the decision that recorded it, not to a new document field.
- **DR-004**: Every story and fix MUST stay tenant-scoped and go through the same services and confirmation boundaries as CLI, Web and Chat.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All seven journeys have a business story in the required backend suite.
- **SC-002**: Six journeys (F04, F08, H09, P02, P05, P08) are `supported`; supported rises by six and partial falls by six.
- **SC-003**: Each fixed defect has a regression test that fails without the fix.
- **SC-004**: An English and a German question about each promoted journey return it as supported.

## Assumptions and Dependencies

- Builds on the story modules of specs 292/294, return announcements, movement corrections (reviewed `movement_correct`), payment intake candidates, the Shopify intake retry and the opening stock and opening open-item imports.
- F08's "still expected" signal is the open return announcement and its overdue finding; *credited not returned* waits for a return by design.
- Research notes are in `research.md`.

## Open Questions

None. The owner decided the scope on 2026-09-30.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002, DR-001, DR-004 | US1–US4 | One business story per journey |
| FR-003, FR-004, DR-003 | US2 | Receipt reason and delivery-path receipt regression tests, H09 story |
| FR-005 | US3.2 | Candidate regression test, P02 story |
| FR-006, DR-002 | US3.3–3.4 | Missing price and quantity regression tests, P05 story |
| FR-007–FR-009 | US5 | Catalog tests, Guide questions, coverage and roadmap |
| SC-001–SC-004 | All | Backend suite, catalog tests, Guide question checks |
