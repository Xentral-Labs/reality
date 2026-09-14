# Feature Specification: A Lot Can Expire

**Feature Branch**: `109-a-lot-can-expire`
**Created**: 2026-09-08
**Status**: Draft
**Language**: English
**Input**: "Shelf life is not in the model at all. `Lot` has a number and no expiry date. For food, pharma, cosmetics or chemicals, 'expiring in 30 days' and 'expired but still sellable' are among the most important conditions there are and cannot be expressed."

## Context and Intent

### Problem

`Lot` carries an item, a number, where it came from and when it was recorded. It does not carry a
best-before date, and **nothing anywhere in the schema does** — the three `expires_at` columns
belong to invitations and chat sessions.

For a company trading food, pharmaceuticals, cosmetics or chemicals that is not a missing report,
it is a missing sentence. The date is printed on the goods and stated on the delivery note. A
company can record the lot number and cannot record the one thing about the lot that decides
whether its contents may be sold.

The consequence is the worst kind: **expired stock looks exactly like good stock.** It counts as
available, it can be reserved, it can be picked and shipped, and the first person who learns
otherwise is the customer.

### Scope

- Let a lot carry the best-before date somebody stated.
- Report stock a company holds whose best-before has passed, and say when it is also reserved for
  a customer.

### Non-Goals

- **Computing an expiry date.** A shelf life in days multiplied out from a production date is a
  date nobody stated, and Principle VIII is the reason this product does not do that. The date is
  read off the goods or off the delivery note, and recorded as read.
- **Reporting stock that is *about to* expire.** This is the one that will be missed, so the
  reason matters: "about to" needs a horizon, and no horizon exists. Nothing on an item states a
  shelf life, no term states a minimum remaining life, and the learned-lag rule already governs
  ten of the thirty-four classes on numbers nobody has checked against a real business — making it
  eleven would be building further on the largest standing risk in this queue. What would unblock
  it is named in the assumptions.
- **Choosing which lot to pick.** First-expiring-first-out is an allocation policy. Reality
  records what moved and what is reserved; it has never chosen a lot and this does not start.
- **Blocking a shipment of expired stock.** Refusing a movement would make a company unable to
  record something that physically happened — the customer already has the goods. Reality reports
  it; it does not pretend it did not happen.
- **Correcting a best-before date once stated.** A date read off the goods is a received value.
  Two different dates for one lot means one of them is wrong in a way this product cannot
  adjudicate, so re-stating a different one is refused. Doing it properly needs the append-only
  shape Spec 093 built for a counterparty's restatement, and that is separable work.
- **Expiry on a serial unit.** A serial-tracked unit is one thing with one identity and it can
  carry its own date, but nothing today asks for it and adding a second column that nothing reads
  would be inventing. Named rather than half-built.

### Existing Contracts

- [`specs/009-inventory-execution/spec.md`](../009-inventory-execution/spec.md) — lots,
  reservations and tracked identities
- [`specs/080-learned-lag/spec.md`](../080-learned-lag/spec.md) — the rule this deliberately does
  not use
- [`docs/features/inventory.md`](../../docs/features/inventory.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [Constitution](../../.specify/memory/constitution.md), principles II, III and VIII

## Clarifications

### Session 2026-09-08

- Q: A date or an instant? → A: A date. A best-before is a calendar day and storing it as an
  instant would invent a time of day nobody stated, which is the same objection as inventing a
  figure. It is the first date-typed column in the schema and that is named in the plan.
- Q: Can the date be stated after the lot exists? → A: Yes, once. Goods arrive before somebody
  reads the label, and refusing would mean recreating the lot. Re-stating a *different* date is
  refused, because a received value is not adjusted.
- Q: Why no "expiring soon" class? → A: Because the horizon would be a number nobody has stated.
  The alternative — learning it from this company's own turnover — would put an eleventh class on
  a rule whose numbers have never been checked against a real business, which is the largest
  standing risk in this queue. Reporting what has actually expired needs no invented number at
  all.
- Q: Is expired-and-reserved a second class or a cause? → A: A cause. It is the same condition on
  the same record with the same owner; what differs is urgency, and that is exactly what a cause
  is for. Two classes would have been two ids for one lot.
- Q: Does anything stop expired stock shipping? → A: No. Refusing the movement would stop a
  company recording something that already happened. The entry appears while the stock is held and
  goes when it is written off, returned or gone.
- Q: Which items expire? → A: Nothing says. Only a lot with a stated date is judged, and a lot
  with no date asserts nothing — there is no way to tell "no shelf life" from "nobody wrote it
  down", and inventing that distinction would be worse than the silence.
- Q: What about a lot that expired but has no stock left? → A: Not reported. Nothing is held, so
  there is nothing for anybody to do, and it would be a wall of history.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The Date On The Delivery Note (Priority: P1)

An operator records the best-before date the supplier stated, on the lot the goods arrived in.

**Why this priority**: It is the whole gap. The sentence has nowhere to live.

**Independent Test**: Create a lot with a date, and a lot without, and read them both.

**Acceptance Scenarios**:

1. **Given** a lot-tracked item, **When** a lot is created with a best-before date, **Then** the
   lot carries exactly that date.
2. **Given** a lot with no date, **When** the date is stated afterwards, **Then** it is recorded.
3. **Given** a lot whose date is already stated, **When** a different date is stated, **Then** it
   is refused; re-stating the same date is accepted and changes nothing.
4. **Given** a lot with no date, **When** anything is asked about its expiry, **Then** nothing is
   asserted, because "no shelf life" and "nobody wrote it down" cannot be told apart.
5. **Given** a date that cannot be read, **When** it is stated, **Then** it is refused.

### User Story 2 - Stock That Cannot Be Sold (Priority: P1)

**Acceptance Scenarios**:

1. **Given** stock on hand in a lot whose best-before has passed, **When** the queue is read,
   **Then** it is reported with the date, how many days ago it passed, and the quantity still held.
2. **Given** the same lot with a best-before still ahead, **When** the queue is read, **Then**
   nothing is reported.
3. **Given** an expired lot with nothing left on hand, **When** the queue is read, **Then**
   nothing is reported.
4. **Given** an expired lot whose stock is written off, **When** the queue is read, **Then** the
   entry is gone with nothing stored and no manual step.
5. **Given** stock in several expired lots, **When** the queue is read, **Then** one entry per lot,
   ordered by the day each expired and then by identity.

### User Story 3 - About To Be Shipped (Priority: P1)

**Acceptance Scenarios**:

1. **Given** expired stock with an active reservation naming its lot, **When** the queue is read,
   **Then** the entry carries the reserved-for-delivery reason and names how much is reserved.
2. **Given** expired stock with no reservation, **When** the queue is read, **Then** the entry
   appears without that reason.
3. **Given** the reservation being released, **When** the queue is read, **Then** the reason goes
   and the entry stays, because the stock is still expired.

### Edge Cases

- A lot on an item that is not lot-tracked.
- A best-before date in the past, stated for goods that arrived late.
- Stock of an expired lot spread across two locations.
- A reservation naming an expired lot on a cancelled promise.
- An expired lot whose stock went back to the supplier.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A lot MUST be able to carry a best-before date exactly as stated, and the date MUST
  be a calendar date rather than an instant.
- **FR-002**: The date MUST be statable when the lot is created and once afterwards, and MUST NOT
  be derived from any other value.
- **FR-003**: Re-stating a different date MUST be refused; re-stating the same date MUST be
  accepted and change nothing.
- **FR-004**: An unreadable date MUST be refused.
- **FR-005**: A lot with no stated date MUST assert nothing about expiry.
- **FR-006**: One operational exception class MUST report every lot whose stated best-before has
  passed and which still has stock on hand, naming the date, how long ago it passed and the
  quantity held.
- **FR-007**: That class MUST report nothing for a lot with no stock left, and MUST clear when the
  stock is written off, returned or otherwise gone.
- **FR-008**: One cause MUST say that expired stock is reserved for a delivery, and MUST name how
  much is reserved.
- **FR-009**: Entries MUST be ordered by the day each lot expired and then by identity, so two
  identical reads return an identical answer.
- **FR-010**: Nothing MUST be blocked, chosen or released because a lot has expired.
- **FR-011**: Every existing class, operation, register and projection MUST behave exactly as it
  does today for a company whose lots state no date.

### Domain and Traceability Requirements

- **DR-001**: One migration adding one nullable date column to the lot record. No other schema
  change and no backfill.
- **DR-002**: Exactly one operational exception class and exactly one cause are added, and the
  closed registry and closed cause vocabulary MUST stay closed.
- **DR-003**: No threshold, horizon or learned statistic is added. The stated date and the day the
  queue is read are the only measurements.
- **DR-004**: The quantity held MUST come from the one stock rule the product already uses for a
  tracked identity, not from a second count.
- **DR-005**: Every read, derivation and write MUST be tenant-scoped.
- **DR-006**: Every date recorded MUST be one somebody stated; none may be computed or adjusted.

### Key Entities *(when data is involved)*

- **Lot**: gains one nullable best-before date, stated and never computed.
- **Reservation** and **Movement**: unchanged. Both already name a lot, which is what makes the
  cause and the quantity held answerable without any new relation.

## Success Criteria *(mandatory)*

- **SC-001**: A company can write down the one fact about a lot that decides whether it may be
  sold.
- **SC-002**: Expired stock stops looking exactly like good stock.
- **SC-003**: Stock about to be shipped to a customer after it expired is distinguishable from
  expired stock sitting still.
- **SC-004**: Reality states no expiry date, horizon or threshold that nobody stated.
- **SC-005**: Nothing is blocked or chosen because of an expiry date.
- **SC-006**: Two identical reads of an unchanged tenant return an identical, identically ordered
  queue.
- **SC-007**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- **What would unblock an "expiring soon" class**: a stated minimum remaining life — the
  commercial term a customer imposes — or a measured turnover from a real tenant. Either is a
  received or measured figure. Neither exists today, and inventing a horizon is the one thing this
  specification refuses hardest.
- A lot with no stated date is silent, in both directions. There is no way to tell an item without
  a shelf life from one whose label nobody read.
- Serial units carry no date. Nothing asks for it yet.
- Reality does not choose which lot ships. First-expiring-first-out is a policy, not a record.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | the stated date is recorded test |
| FR-002 | US1 scenario 2 | stated afterwards test |
| FR-003 | US1 scenario 3 | re-stating refused test |
| FR-004 | US1 scenario 5 | unreadable date refused test |
| FR-005 | US1 scenario 4 | an undated lot is silent test |
| FR-006 | US2 scenarios 1, 2 | derivation test |
| FR-007 | US2 scenarios 3, 4 | nothing held, and cleared, tests |
| FR-008 | US3 scenarios 1, 2, 3 | the cause test |
| FR-009 | US2 scenario 5 | ordering test |
| FR-010 | Edge cases | nothing blocked test |
| FR-011 | — | the existing suites, unchanged |
| DR-001 | — | one migration, one nullable column, no backfill |
| DR-002 | — | the closed registry and cause vocabulary tests |
| DR-003 | — | no threshold in the diff |
| DR-004 | US2 scenario 1 | one stock rule test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US1 scenarios 1, 3 | recorded-dates-only test |
