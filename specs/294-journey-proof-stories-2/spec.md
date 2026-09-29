# Feature Specification: Journey Proof Stories, Round Two

**Feature Branch**: `294-journey-proof-stories-2`

**Created**: 2026-09-29

**Status**: Draft

**Language**: English

**Input**: After specs 292 and 293, the Business Journey Guide lists 69 partial journeys. For eleven of them every building block exists; only an end-to-end executable story is missing. Prove them the way spec 292 did, so the Guide states them as supported or names what a story finds missing.

## Context and Intent

### Problem

Spec 292 promoted eleven partial journeys by writing one business story each. Spec 293 added the customer exchange and promoted F07. The coverage notes in `docs/scenarios/coverage.md` show eleven more journeys whose pieces are tested separately, or on the other trading side, or not at all in combination. The Guide still calls them "not yet proven", which a prospective customer reads as "does not work". This round covers purchasing, receipt, master data, source integration and the combined order story.

### Scope

Write one executable business story per journey below, using only the shared application services and reviewed tools that CLI, Web and Chat use. Promote each journey whose story passes to `supported`, with that story as its executable evidence. Regenerate the Guide.

| ID | Journey | Story must show |
|---|---|---|
| D16 | Free replacement shipment without a new order | a free replacement promise without an order document is reserved and shipped, the movement explains why the stock left and for which promise, and nothing is billed or reported as unbilled |
| G07 | Tiered purchase prices | a supplier invoice at the price the supplier states for the ordered quantity tier is recorded as stated, and a price outside the ordered price is reported as a price difference |
| H03 | Under-delivery, rest never | a confirmed downward revision closes the undelivered rest of a purchase, and the revision keeps its reason and the confirming decision |
| I06 | Several partial invoices for one purchase | two supplier invoices for parts of one purchase line sum against it; nothing is reported while they stay within what was received, and billing beyond it is reported |
| I07 | Freight invoice from a third party for a purchase | a freight invoice from a carrier other than the goods supplier is attributed to the receipt's cost |
| K05 | Variant items (size, colour) purchased together | several variants on one purchase each receive, hold and reserve their own stock |
| L06 | Pre-order of an item not yet available | a dated customer promise without stock is backed by an incoming supplier promise, and its shortage and protection by that supply are visible |
| O01 | Item number renamed | after a SKU change, earlier movements, stock, reservations and documents still belong to the same item, and document lines keep the number they stated |
| P04 | Source deletes an order afterwards | after a source cancellation is reviewed, the order line is closed with the source record as its reason |
| P07 | Integration down for a day, then catches up | a silent source is reported; replaying a day's backlog, including repeated payloads, creates no duplicates and clears the silence |
| R01 | Combined order story | the sequence in the catalog (partial stock, partial prepayment, release, partial shipment, reorder, split receipt, cancellation of one unit, rest shipped, two damaged returns) reconciles every quantity and every euro at the end |

### Non-Goals

- New business capabilities, schema, tools or UI. A journey that needs any of them stays `partial` with its finding.
- The seven uncertain journeys (F04, F08, H09, P02, P05, P08, B09) and the roughly fifty journeys that need real functions.
- Changing how the Guide answers or matches journeys, except adding keywords and question examples to promoted entries so ordinary questions find them (spec 293 showed that entries without them are not found).
- Removing limitations outside a journey's question, such as the absence of a parent item for variants (K05) or of volume price tiers on purchases (G07).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Purchasing and receipt are proven end to end (Priority: P1)

As a prospective customer's purchasing lead, I see G07, H03, I06, I07 and K05 as supported, because a story shows the whole purchase journey.

**Why this priority**: Supplier deviations and supplier invoices decide whether purchasing trusts the system.

**Independent Test**: Run the purchasing stories against the shared services; each asserts its journey's question from purchase to final state.

**Acceptance Scenarios**:

1. **Given** a purchase whose supplier stated a tier price, **When** the supplier invoice is recorded at that price, **Then** it is kept as stated; **When** another invoice states a different price, **Then** a price difference is reported.
2. **Given** a purchase of 10 with 7 received, **When** the rest is closed through a confirmed revision with a reason, **Then** nothing is open, and the revision names its reason and the decision that confirmed it.
3. **Given** a purchase line of 10 received in full, **When** two invoices bill 6 and 4, **Then** nothing is reported; **When** a third invoice bills 1 more, **Then** billing beyond what was received is reported.
4. **Given** a received purchase, **When** a carrier's freight invoice is attributed to the receipt, **Then** the receipt's cost includes the freight and names the carrier's invoice.
5. **Given** one purchase of three variants, **When** it is received, **Then** each variant holds its own stock and can be reserved on its own.

---

### User Story 2 - Sales and master data are proven end to end (Priority: P1)

As a prospective customer, I see D16, L06 and O01 as supported.

**Why this priority**: Free replacements, pre-orders and renamed item numbers come up in every e-commerce demo.

**Independent Test**: Run the three stories; each asserts traceability after the change.

**Acceptance Scenarios**:

1. **Given** a customer who is owed a replacement, **When** a free promise without an order is shipped, **Then** its movement explains the promise, and neither an invoice nor an unbilled finding exists.
2. **Given** a dated customer promise with no stock and an incoming supplier promise assigned to it, **When** the state is read, **Then** the shortage is visible together with the supply that protects it.
3. **Given** an item with stock, a reservation and invoiced documents, **When** its SKU is changed, **Then** every earlier record still belongs to the same item, and documents keep the number they stated.

---

### User Story 3 - Source integration is proven end to end (Priority: P2)

As a prospective customer's IT lead, I see P04 and P07 as supported.

**Why this priority**: Integration failure modes decide whether an ERP can run unattended.

**Independent Test**: Run the two source stories with stored source payloads.

**Acceptance Scenarios**:

1. **Given** a shop order interpreted into a promise, **When** the shop sends a cancellation and a person closes the line from the review, **Then** the line is closed with the source record as its reason.
2. **Given** a source that delivered regularly and then went silent, **When** its backlog, including repeated payloads, arrives, **Then** no record is duplicated and the silent-source finding clears.

---

### User Story 4 - The combined story reconciles (Priority: P2)

As an evaluator, I see R01 as supported, because one story reconciles every quantity and euro across its steps.

**Why this priority**: The combined story is the evaluator's stress test.

**Independent Test**: Run R01 and assert the final quantities, open items, credits and stock.

**Acceptance Scenarios**:

1. **Given** the catalog sequence, **When** the story ends, **Then** the delivered, returned, credited, invoiced and paid quantities and amounts reconcile, and no finding remains that the story did not intend.

---

### User Story 5 - The Guide follows the evidence (Priority: P1)

As a Guide reader, I see a journey as supported only when its story passes, and an honest limitation when it does not.

**Acceptance Scenarios**:

1. **Given** a passing story, **When** the catalog is updated, **Then** the journey is `supported` with executable evidence, and it is found by an ordinary English and German question.
2. **Given** a story that reveals a defect against an existing requirement, **When** the defect is fixed with a regression test, **Then** the journey may be promoted in the same change.
3. **Given** a story that reveals a missing capability, **When** the change is complete, **Then** the journey stays `partial`, its limitation names the finding, and the finding is recorded in `docs/scenarios/coverage.md`.

### Edge Cases

- A story passes only with a direct database write or a test-only shortcut. It does not count; the journey stays `partial`.
- R01's "released anyway" needs a release that overrides an unmet prepayment. If no reviewed release exists, R01 stays `partial` and names it.
- G07's tier price is stated by the supplier; Reality does not compute tiers. If no purchase-side price basis exists to compare against, the story proves only that the stated price is kept, and the limitation says so.
- P07's backlog repeats payloads on purpose; source idempotency, not luck, must prevent duplicates.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each journey in scope MUST have one executable business story that runs from start to final state through shared application services or reviewed tools only.
- **FR-002**: A story MUST assert the business outcome its journey asks for, quantities and amounts included. Every "no finding" assertion MUST have a positive control, and every refusal MUST assert its code.
- **FR-003**: A journey MUST be promoted to `supported` with `executable` evidence only when its story passes; its internal evidence MUST cite that story first.
- **FR-004**: A promoted journey's public limitation MUST no longer describe it as unproven; limitations outside its question MAY remain.
- **FR-005**: A promoted journey MUST carry English and German keywords or question examples so that an ordinary question finds it.
- **FR-006**: A defect against an existing requirement MAY be fixed here with a regression test naming that requirement; any other failure MUST leave the journey `partial` with an updated limitation, recorded in `docs/scenarios/coverage.md`.
- **FR-007**: The Guide payload MUST be regenerated.
- **FR-008**: This feature MUST NOT add schema, tools, service entry points or UI.

### Domain and Architecture Requirements

- **DR-001**: Stories MUST respect Source → Evidence → Reality and MUST NOT assert fulfilment, billing or payment status stored on documents.
- **DR-002**: Stated prices, amounts and tax MUST be asserted as recorded, never recomputed (Constitution VIII).
- **DR-003**: Every story MUST run tenant-scoped through the same services and confirmation boundaries as CLI, Web and Chat.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All eleven journeys have a business story in the required backend suite.
- **SC-002**: The number of supported journeys rises by exactly the number of passing stories; the partial count falls by the same number.
- **SC-003**: No journey is promoted without a passing story, and no failed story is left without a recorded finding.
- **SC-004**: An English and a German question about each promoted journey return it as supported.

## Assumptions and Dependencies

- Builds on the catalog story modules and outcome rule of spec 292 and on the document-less replacement promise of spec 293 (D16).
- Candidates come from the internal evidence notes in `business_journey_catalog.yaml` and `docs/scenarios/coverage.md`; feasibility is confirmed only by the story.
- Existing evidence stays; each new story is added in front of it.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002, DR-001, DR-003 | US1–US4 | One business story per journey |
| DR-002 | US1.1, US1.3, US4 | Stated price and amount assertions |
| FR-003–FR-007 | US5 | Catalog update, catalog tests, Guide questions, coverage record |
| FR-008 | All | Diff review |
| SC-001–SC-004 | All | Backend suite, catalog tests, Guide question checks |
