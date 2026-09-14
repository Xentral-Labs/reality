# Feature Specification: The Parcel That Has Not Left Yet

**Feature Branch**: `099-a-return-can-be-announced`
**Created**: 2026-09-07
**Status**: Draft
**Language**: English
**Input**: "Die Retouren-Ankündigung. Eine Retoure ist erst erfassbar, wenn die Ware da ist; 'Kunde hat eine Rücksendung angekündigt' ist unsichtbar."

## Context and Intent

### Problem

A return in Reality is a **Movement** — goods physically arriving back. So the only moment a
company can record a return is the moment it is already standing on the receiving dock, and
everything before that is invisible:

**The customer's own words are lost.** *"I want to send back two of the five lights from order
4711, they are the wrong colour"* is a statement by a counterparty about a transaction, which is
the kind of thing this product exists to keep. Today it is kept in somebody's inbox.

**The desk cannot know what is coming.** A parcel arriving unannounced has to be matched to an
order by a person reading a note inside it. An announcement is what makes the arrival a
confirmation rather than a puzzle, and it is what an RMA reference is *for* — a number the
customer quotes so both sides mean the same return.

**An announcement nobody acted on is invisible too.** A customer said three weeks ago they would
send something back. Either the goods are lost, or they changed their mind and did not say, or
somebody needs to chase. Nothing in the queue can see it, because as far as Reality is concerned
nothing has happened.

The goods half *after* arrival is complete — Spec 079 let a return name the delivery it reverses,
Spec 082 let a movement say which return it settles, and `return_unresolved` reports goods still
sitting. This is the half before.

### Scope

- Record that a customer said they would send goods back, with what they said and when.
- Let the goods, when they arrive, say which announcement they fulfil.
- Report an announcement nothing has arrived against, once that stops being ordinary here.

### Non-Goals

- **Authorising the return.** Reality records that the customer asked and, separately, that the
  company recorded an announcement. Whether the return is accepted, who pays the postage and
  what the customer is owed are commercial judgements with a person behind them.
- **Generating an RMA number.** The reference is a received value like every other: whoever
  states it states it. Reality does not mint one, because a number this product invented would
  become the number the customer has to be told, and that is a notification path this product
  does not have.
- **Deciding what happens to the goods.** That is `return_unresolved` and it is unchanged. An
  announcement's life ends when the goods arrive; what becomes of them starts there.
- **Announcing a return to a supplier.** The mirror case — the company telling a supplier it is
  sending something back — is a different conversation with a different counterparty, and the
  goods half of it (`supplier_return`) already exists. Left out deliberately rather than
  half-built.
- **A credit note before the goods arrive.** Crediting on announcement is a real commercial
  practice and a real decision about money. Spec 079 and 084 own the money half, and an
  announcement does not touch it.
- **Reserving stock or expecting inbound quantity.** An announced return is not supply. Nothing
  about availability, replenishment or the fulfilment queue changes, because goods a customer
  has promised to send are not goods the company can sell.

### Existing Contracts

- [`specs/079-returns-connect/spec.md`](../079-returns-connect/spec.md)
- [`specs/082-return-resolved/spec.md`](../082-return-resolved/spec.md)
- [`specs/080-learned-lag/spec.md`](../080-learned-lag/spec.md) — the learned
  threshold rule this reuses
- [`docs/features/movements.md`](../../docs/features/movements.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [Constitution](../../.specify/memory/constitution.md), principles I, II, III and VIII

## Clarifications

### Session 2026-09-07

- Q: Is an announcement a Commitment? It is a directional promise, which is what a Commitment
  is. → A: Semantically yes, and it is still the wrong home. `Commitment.type` has exactly two
  values today, and `customer_delivery` is referenced 32 times across 8 modules, 17 of them a
  two-way branch whose `else` silently means *supplier delivery*. A third type would make every
  one of those `else` branches wrong, and most of them would go on passing their tests. A
  separate record touches nothing that already works — the same trade Spec 093 made when it put a
  counterparty's restatement in its own table.
- Q: Then how do the goods say which announcement they fulfil? → A: One nullable reference on
  the Movement, exactly as Spec 082 let a movement name the return it settles. Matching on item
  and quantity was considered and refused: two announcements against one delivery would be
  guesses, and a guess about which of a customer's two returns arrived is worse than no link.
- Q: Does the announcement replace the return's link to the delivery it reverses? → A: No. The
  return still names the customer delivery, because that is what bounds it and what four classes
  read. The announcement is an additional, optional statement about the same event.
- Q: How much may be announced? → A: What was shipped, less what has already come back, less
  what other open announcements are already claiming. Otherwise a customer could announce the
  same five items twice. It is the same rule the return movement already applies, so it becomes
  one rule with two callers.
- Q: Does Reality generate the RMA reference? → A: No. It is a received value. A number this
  product invented would be a number somebody has to tell the customer, and there is no
  notification path here.
- Q: When is an announcement finished? → A: When what has arrived against it reaches what was
  announced, settled at that moment rather than at some later read — the same decision Spec 097
  made about a promise shrinking to what had already arrived.
- Q: What if the customer sends more than they announced? → A: Accepted up to what the delivery
  still allows back. The customer said two and sent three; both are true, and the third item
  physically exists. The announcement is finished and the extra is an ordinary return.
- Q: When is an announcement overdue? → A: Past the day the customer stated, where they stated
  one. Where they did not, past this company's own learned rhythm for announced returns
  arriving — the rule Spec 080 built, reused rather than reinvented. The entry says which of the
  two judged it.
- Q: Why not two classes, dated and undated, as Spec 080 did? → A: Because it is one condition
  with one owner and one clearing path — the goods arriving. Spec 080 split because an undated
  *order* is a different operational situation from a late one. Here the difference is only in
  how the date was arrived at, so it belongs in the entry rather than in the catalog.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The Customer Says They Are Sending It Back (Priority: P1)

An operator records what the customer said — how much, why, the reference the parcel will carry,
and the day the customer said it would go — against the delivery the goods went out on.

**Why this priority**: It is the whole gap. Nothing in the product can hold this sentence.

**Independent Test**: Ship five against a customer delivery, announce two, and read the
announcement and what the delivery still allows.

**Acceptance Scenarios**:

1. **Given** five shipped against a customer delivery, **When** two are announced with a
   reference and a reason, **Then** the announcement holds both, names the delivery, and is open.
2. **Given** that announcement, **When** the delivery is read, **Then** the shipment, the
   commitment and every existing class are exactly as they were.
3. **Given** five shipped and two announced, **When** four more are announced, **Then** it is
   refused, because only three can still come back.
4. **Given** an announcement, **When** the customer changes their mind, **Then** it can be
   withdrawn, with what they said kept, and what may be announced returns to five.
5. **Given** a withdrawn announcement, **When** goods are recorded against it, **Then** it is
   refused.

### User Story 2 - The Parcel Arrives (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an open announcement for two, **When** two come back naming it, **Then** the
   announcement is fulfilled at that moment and the return is an ordinary return in every other
   respect.
2. **Given** an open announcement for two, **When** one comes back naming it, **Then** the
   announcement is still open for one.
3. **Given** an open announcement for two, **When** three come back naming it, **Then** it is
   accepted, the announcement is finished, and the third is recorded.
4. **Given** goods coming back naming no announcement, **When** they are recorded, **Then**
   nothing changes about how they are recorded today.
5. **Given** a return naming an announcement of another delivery, **When** it is recorded,
   **Then** it is refused.

### User Story 3 - Nothing Arrived (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an announcement whose stated day has passed with nothing arrived, **When** the
   queue is read, **Then** it is reported, saying the day the customer stated.
2. **Given** an announcement with no stated day, standing longer than this company's learned
   rhythm, **When** the queue is read, **Then** it is reported, saying the norm it was judged
   against.
3. **Given** a company with fewer than five arrived announcements and no stated days, **When**
   the queue is read, **Then** nothing is reported, because the rule cannot speak yet.
4. **Given** the goods arriving, **When** the queue is read, **Then** the entry is gone with
   nothing stored and no manual step.

### Edge Cases

- An announcement of zero or a negative quantity.
- An announcement against a delivery nothing was shipped against.
- An announcement against a supplier delivery.
- Two open announcements against one delivery, one of which arrives.
- A return naming both an announcement and a delivery that do not agree.
- An announcement on a cancelled commitment.
- A voided return movement that had fulfilled an announcement.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A customer's announced return MUST be recordable against the customer delivery the
  goods went out on, carrying the quantity, the reference and the reason as stated, the instant it
  was announced, and the day the customer said it would go where they said one.
- **FR-002**: One rule MUST answer what can still come back against a delivery, and both the
  return movement and the announcement MUST ask it. Nothing else may decide it.
- **FR-003**: An announcement MUST NOT exceed what can still come back, less what other open
  announcements against that delivery already claim.
- **FR-004**: An announcement of zero or less, against a supplier delivery, against a delivery
  nothing was shipped against, or against a cancelled promise MUST be refused.
- **FR-005**: A returning movement MUST be able to name the announcement it fulfils, and MUST
  still name the customer delivery it reverses.
- **FR-006**: A movement naming an announcement whose delivery is not the movement's own, or
  whose announcement is not open, MUST be refused.
- **FR-007**: An announcement MUST be settled as fulfilled at the moment what has arrived against
  it reaches what was announced.
- **FR-008**: More arriving than was announced MUST be accepted, within what the delivery still
  allows back.
- **FR-009**: An announcement MUST be withdrawable, keeping what was announced, and what may then
  be announced MUST return to what the delivery allows.
- **FR-010**: A goods movement recorded without an announcement MUST behave exactly as it does
  today.
- **FR-011**: One operational exception class MUST report an open announcement nothing has
  arrived against — past the day the customer stated where there is one, and past this company's
  own learned rhythm where there is not — and the entry MUST say which rule judged it.
- **FR-012**: That class MUST report nothing where neither a stated day nor enough history
  exists, rather than reporting everything or nothing arbitrarily.
- **FR-013**: The entry MUST clear when the goods arrive, with nothing stored and no manual step.
- **FR-014**: Every existing class, operation, register and projection MUST behave exactly as it
  does today for a company that announces nothing.

### Domain and Traceability Requirements

- **DR-001**: One migration: one new table for the announcement and one nullable reference on
  Movement. No change to any existing column.
- **DR-002**: The announcement MUST be a record of its own rather than a third `Commitment.type`,
  and the reason MUST be recorded with the measurement behind it.
- **DR-003**: What can still come back MUST be derived at read time by one shared rule and MUST
  NOT be stored.
- **DR-004**: The learned threshold MUST reuse the Spec 080 rule unchanged — the middle of the
  most recent twenty arrivals, three times over, never below a floor, and silent below five —
  and MUST share the rule and never the history.
- **DR-005**: Every read, derivation and write MUST be tenant-scoped.
- **DR-006**: Exactly one operational exception class and no new cause is added, and the closed
  registry MUST stay closed: catalog ids, class order and derivation registry agree.
- **DR-007**: Every quantity, reference and reason recorded MUST be one somebody stated; none may
  be derived, generated or adjusted.
- **DR-008**: Every new operation MUST be a declared command, so the reachability gate stays
  satisfied.

### Key Entities *(when data is involved)*

- **ReturnAnnouncement**: what a customer said they would send back, against the delivery it went
  out on. Reality, not Evidence: it is a promise the company now holds, and it is settled or
  withdrawn rather than corrected.
- **Movement**: unchanged, plus one optional reference saying which announcement these goods
  fulfil.
- **Commitment**: entirely unchanged. It is the semantically obvious home for an announcement and
  it is deliberately not used; the measurement behind that decision is in the plan.

## Success Criteria *(mandatory)*

- **SC-001**: What a customer said about sending goods back is in the product, not in an inbox.
- **SC-002**: A parcel arriving is a confirmation rather than a puzzle.
- **SC-003**: An announcement nobody acted on is visible, and stops being visible when the goods
  arrive.
- **SC-004**: Reality states no reference, quantity or reason that nobody stated.
- **SC-005**: Nothing about a company that announces nothing changes.
- **SC-006**: Two identical reads of an unchanged tenant return an identical, identically ordered
  queue.
- **SC-007**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- An announcement does not make the goods available. Nothing about supply, reservation or the
  fulfilment queue changes, because a customer's promise to send something back is not stock.
- The money half is untouched. A credit note still follows the goods, as Spec 079 decided.
- Reality does not tell the customer anything. It records that somebody said something; the
  conversation happens elsewhere.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | announcement records what was stated test |
| FR-002 | US1 scenario 3 | one returnable rule test |
| FR-003 | US1 scenario 3 | over-announcement refused test |
| FR-004 | Edge cases | refusals test with positive controls |
| FR-005 | US2 scenario 1 | the parcel names its announcement test |
| FR-005 (adapters) | US2 scenario 1 through MCP, web and CLI | `tests/test_return_announcement_adapters.py` |
| FR-006 | US2 scenario 5; Edge cases | mismatched announcement refused test |
| FR-007 | US2 scenarios 1, 2 | settled at that moment test |
| FR-008 | US2 scenario 3 | more than announced test |
| FR-009 | US1 scenarios 4, 5 | withdrawal test |
| FR-010 | US2 scenario 4 | the existing return suites, unchanged |
| FR-011 | US3 scenarios 1, 2 | derivation test, both rules |
| FR-012 | US3 scenario 3 | silent below the minimum test |
| FR-013 | US3 scenario 4 | the entry clears test |
| FR-014 | — | the existing suites, unchanged |
| DR-001 | — | one migration, one table, one column |
| DR-002 | — | the measurement in the plan |
| DR-003 | US1 scenario 3 | one shared rule test |
| DR-004 | US3 scenarios 2, 3 | learned threshold parity test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | — | the closed registry test |
| DR-007 | US1 scenario 1 | recorded-values-only test |
| DR-008 | — | the command reachability gate |

## Amendment 2026-09-11: the reference reaches the adapters

FR-005 was met in the service and missed in the adapters. `record_movement` accepted
`return_announcement_id`, but the MCP tool `movement_create_propose` did not name it, the web
endpoint accepted it and `resolves_movement_id` (spec 082) and passed neither on, and the CLI had
no flag for either. An agent could therefore never fulfil an announcement, and
`announced_return_not_arrived` kept reporting parcels that had arrived. The amendment adds the
field to the MCP schema, wires both references through the web write, read and list, and adds
both flags to the CLI. Refusals are unchanged: a foreign or closed announcement is refused by the
service through every adapter. No schema change, no derivation change.
