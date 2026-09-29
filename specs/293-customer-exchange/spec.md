# Feature Specification: Customer Exchange

**Feature Branch**: `293-customer-exchange`

**Created**: 2026-09-28

**Status**: Approved

**Language**: English

**Input**: A customer sends goods back and receives another unit, another size or another variant instead of money. Today Reality records the return and a separate zero-price replacement order, but nothing says the one replaces the other, so the return waits for a credit and the replacement for an invoice. Make an exchange a first-class, confirmed business fact (Business Journey Guide F07).

## Context and Intent

### Problem

An exchange is daily e-commerce and B2B service work: wrong size, faulty unit, wrong variant. Reality can record each half. The return comes back against its delivery (spec 079), optionally announced first (spec 099). The replacement goes out on its own zero-price order (spec 246 US7). Nothing states that the replacement settles the return. The result is two false findings for a correct exchange:

- **Returned and not credited**: the returned goods look like they are still owed a credit.
- **Shipped and not billed**: the free replacement looks like it is still owed an invoice.

Spec 292 pinned this as `test_an_exchange_moves_no_money_but_reads_as_uncredited_and_unbilled`, and the Guide lists F07 as partial.

### Scope

- A confirmed **exchange** states that a replacement delivery to the same customer settles a stated quantity of a customer return, instead of a credit.
- The replacement may be the same item or another item or variant. No money moves: the replacement carries no price of its own and is never billed.
- An exchange can be recorded after the return has arrived, or in advance against a return announcement, before the goods are back.
- The exchanged quantity is no longer reported as returned and not credited. The replacement is no longer reported as shipped and not billed.
- An advance exchange whose return never arrives is visible as an open obligation of the customer.
- Every surface that records returns can record and explain an exchange: Web, Chat/agent and CLI, through the same reviewed tool.

### Non-Goals

- **Price differences.** An exchange into a more or less expensive item is not an exchange here. The difference goes through the existing invoice or credit note.
- Supplier-side exchanges (a supplier replacing goods that were returned to it).
- Automatic exchanges from shop or marketplace sources. Interpreting source exchange events is a later interpreter feature; this feature provides the fact they would record.
- Reopening the original delivery promise. A return still never reopens a kept promise (spec 079); the replacement is its own promise.
- Choosing the replacement item, checking stock or reserving automatically beyond what an ordinary order line does.
- Printed exchange documents, return labels or customer notifications.

## Clarifications

### Session 2026-09-28

- Q: What may the replacement be? → A: The same item or another item or variant at the same price. Price differences stay with invoices and credit notes.
- Q: May the replacement leave before the return arrives? → A: Yes, both orders are supported. A replacement against an announcement makes the missing return visible if it never arrives.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Exchange a returned unit for another (Priority: P1)

As a customer service clerk, when a customer has sent back a delivered item and wants another size instead of a refund, I record an exchange so that the replacement goes out and nothing is left open for credit or billing.

**Why this priority**: This is the common exchange, and the one that produces two false findings today.

**Independent Test**: Deliver and invoice one unit, receive it back, record an exchange for another variant, ship the replacement; the return is not owed a credit, the replacement is not owed an invoice, and no money moved.

**Acceptance Scenarios**:

1. **Given** a delivered and invoiced order line and its customer return of 1 unit, **When** the clerk records an exchange of that 1 unit for 1 unit of another variant and confirms it, **Then** a replacement delivery promise of 1 unit exists for the same customer and the returned unit is no longer reported as returned and not credited.
2. **Given** that exchange, **When** the replacement ships, **Then** it is fulfilled and not reported as shipped and not billed, and no invoice, credit note, payment or refund exists for it.
3. **Given** a return of 2 units, **When** 1 unit is exchanged and 1 unit is credited, **Then** neither the exchanged nor the credited unit is reported, and the original invoice keeps its amount.
4. **Given** the review before confirmation, **When** the clerk reads it, **Then** it states the returned delivery, the exchanged quantity, the replacement item and quantity, and that no money will move.

---

### User Story 2 - Send the replacement before the return arrives (Priority: P1)

As a customer service clerk, when a customer announces a return of a faulty unit, I send the replacement right away and trust that the faulty unit follows. If it does not, I see that the customer still owes it.

**Why this priority**: Advance exchange is standard service, and without a visible obligation it becomes a silent free delivery.

**Independent Test**: Announce a return, record an advance exchange against the announcement, ship the replacement; before the return arrives the announcement is outstanding and the exchange shows the goods as still owed; after arrival nothing remains open.

**Acceptance Scenarios**:

1. **Given** a return announcement of 1 unit, **When** the clerk records an exchange against it and ships the replacement, **Then** the replacement is not reported as shipped and not billed.
2. **Given** that advance exchange, **When** the announced goods do not arrive by the stated date, **Then** the announcement is reported as not arrived and the exchange names the replacement that already left.
3. **Given** that advance exchange, **When** the announced goods arrive, **Then** the announcement is fulfilled and the returned unit is not reported as returned and not credited.
4. **Given** an announcement that is withdrawn after an advance exchange shipped, **When** the state is read, **Then** the replacement is reported as delivered without a returned counterpart, not as a completed exchange.

---

### User Story 3 - Explain an exchange (Priority: P2)

As a clerk or controller, I can see from either side of an exchange what it replaced, so the absence of a credit and of an invoice is explained, not just silent.

**Why this priority**: The Web UI invariant requires every important number to be traceable; a silenced finding needs a stated reason.

**Independent Test**: Open the returned delivery and the replacement delivery; each links to the exchange, and the exchange links to the return movement or announcement, the original delivery and the replacement, and to its confirmed decision.

**Acceptance Scenarios**:

1. **Given** a recorded exchange, **When** the returned movement is explained, **Then** the explanation names the exchange and the replacement delivery.
2. **Given** a recorded exchange, **When** the replacement delivery is opened, **Then** it names the exchange and the original delivery it replaces.
3. **Given** a recorded exchange, **When** its history is read, **Then** it shows who confirmed it, when and with which stated reason.

---

### User Story 4 - The Guide states exchanges as supported (Priority: P2)

As a prospective customer asking "Can Reality handle an exchange?", I see F07 as supported with its limits.

**Why this priority**: The capability is a sales question; the Guide must follow the evidence (spec 290, spec 292).

**Independent Test**: The spec 292 exchange story passes with no findings, F07 is promoted and the Guide answers `supported`.

**Acceptance Scenarios**:

1. **Given** the implemented exchange, **When** the F07 story runs, **Then** it asserts no finding for the exchange and replaces the pinned limitation test.
2. **Given** the regenerated Guide, **When** someone asks about an exchange, **Then** F07 is supported and its limitation names that price differences go through invoices and credit notes.

### Edge Cases

- The exchanged quantity exceeds what came back or was announced and is not yet credited or exchanged: refused.
- The return is already fully credited: refused, because an exchange would settle it twice.
- A later credit note for an exchanged quantity: the unit is then settled twice, so the credited quantity beyond what came back and was not exchanged is reported as credited and not returned.
- The replacement is cancelled before it ships: the exchange no longer settles the return, and the returned unit is again owed a credit or another exchange.
- The replacement ships only partly: only the shipped quantity counts as delivered; the rest stays open like any promise.
- A replacement for a different customer: not expressible; the replacement always goes to the customer of the returned delivery.
- The returned item and the replacement item differ: allowed; the replacement item is stated, not derived.
- A return that was recorded without naming its delivery: it must first be linked to its delivery before it can be exchanged.
- Tenant isolation: an exchange cannot name a return, announcement or item of another tenant.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A person MUST be able to record an exchange that names a customer return (a received return movement or a return announcement), the exchanged quantity, the replacement item and quantity, and a stated reason.
- **FR-002**: Recording an exchange MUST create the replacement as a delivery promise to the same customer with no price and link it to the exchange.
- **FR-003**: The replacement item MAY differ from the returned item; the replacement quantity MUST be positive.
- **FR-004**: The exchanged quantity MUST NOT exceed the quantity returned or announced on that delivery minus what is already credited or exchanged.
- **FR-005**: The exchanged quantity MUST NOT be reported as returned and not credited.
- **FR-006**: A delivered replacement MUST NOT be reported as shipped and not billed.
- **FR-007**: An exchange recorded against an announcement MUST keep the announcement's arrival expectation; a missing return MUST remain reported as announced and not arrived, and MUST name the replacement already delivered.
- **FR-008**: Cancelling a replacement before it ships MUST end the exchange's settlement of the return.
- **FR-009**: Recording an exchange MUST move no money and create no invoice, credit note, payment or refund.
- **FR-010**: Recording an exchange is a mutation and MUST require a review and explicit confirmation; its review MUST state the returned delivery, the quantities, the replacement item and that no money moves.
- **FR-011**: The same reviewed exchange tool MUST be available to Web, Chat/agent and CLI, with a read of an exchange for explanation.
- **FR-012**: The return explanation, the replacement delivery and the exchange MUST link to each other and to the confirmed decision.
- **FR-013**: The Business Journey Guide MUST promote F07 once its story proves FR-005, FR-006 and FR-009.

### Domain and Architecture Requirements

- **DR-001**: An exchange is Reality, not Evidence: it states what the company holds as settled. It MUST NOT add fulfilment, return or billing status fields to documents.
- **DR-002**: The exchange MUST link to the shortest true records: the customer return (movement or announcement) and the replacement promise. Party, item and original order line follow from those links and MUST NOT be duplicated.
- **DR-003**: Findings MUST be derived at read time from the exchange and the movements; no stored "exchanged" flag on returns or promises.
- **DR-004**: Every read and write MUST be tenant-scoped through services; adapters MUST NOT write persistence directly.
- **DR-005**: A return still MUST NOT reopen the original delivery promise (spec 079).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A correct exchange, recorded in either order, leaves zero open findings for returned-not-credited and shipped-not-billed on its records.
- **SC-002**: An advance exchange whose return never arrives is reported within the same read that reports the announcement as not arrived.
- **SC-003**: A clerk can record an exchange from Web, Chat and CLI with one reviewed confirmation each.
- **SC-004**: F07 is supported in the published Guide.

## Assumptions and Dependencies

- Builds on customer returns against their delivery (spec 079), return announcements (spec 099) and the zero-price replacement already used in the demo (spec 246 US7).
- Spec 292 provides the F07 story to be turned from a pinned limitation into proof.
- A new record for the exchange is expected, because no existing record can state "this promise settles that return" without a document status or a duplicated link. The plan must prove this against the Constitution's schema rule.
- The existing reservation, readiness and dispatch rules apply to the replacement unchanged.

## Open Questions

None. The owner answered both scope questions and accepted the scope on 2026-09-28.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-004, FR-009, FR-010 | US1.1, US1.3, US1.4, edge cases | Service and tool tests, review contract |
| FR-005, FR-006 | US1.1–US1.3, US2.1, US2.3 | Exception derivation tests with positive controls |
| FR-007 | US2.2, US2.4 | Announcement and exchange derivation tests |
| FR-008 | Edge cases | Cancellation story |
| FR-011 | US1, US2 | Web API, MCP/Chat and CLI adapter tests |
| FR-012, DR-001–DR-003 | US3 | Explanation and Inspector link tests |
| FR-013 | US4 | Spec 292 F07 story, catalog test, Guide question |
| DR-004 | All | Tenant isolation catalog and tests |
| DR-005 | US1 | Existing spec 079 regression tests |
