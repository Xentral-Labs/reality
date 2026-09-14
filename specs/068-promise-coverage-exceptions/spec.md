# Feature Specification: Customer Promise and Stock Coverage Exceptions

**Feature Branch**: `068-promise-coverage-exceptions`
**Created**: 2026-09-04
**Status**: Approved
**Language**: English
**Input**: "Close the two outgoing-promise coverage gaps in the operational exception queue: a customer delivery commitment that is already late, and reserved quantity that exceeds the stock actually observed."

## Context and Intent

### Problem

A trading business lives on kept delivery promises. The current operational exception
queue watches the supplier side of a promise for lateness but not the customer side, and
it judges promise coverage per commitment instead of against observed stock. Two
conditions therefore stay invisible until a customer calls.

First, lateness is asymmetric. `overdue_incoming_supplier_commitment` compares the due
date against the evaluation instant. `outgoing_commitment_at_risk` never evaluates the
due date at all; it reports only whether reserved quantity covers the remaining
quantity. An open customer-delivery commitment that is fully reserved but was never
shipped stays absent from the queue however long it is overdue. The operator sees a
supplier who is late and no customer who is waiting.

Second, coverage is judged once and never re-checked. Reservation quantity is compared
against the remaining quantity of the same commitment, never against the stock that still
exists. Making a reservation is safe: the shared reserve operation allocates at most the
available quantity, so the same goods cannot be promised twice at write time. Keeping one
is not. Nothing stops stock from leaving afterwards — a stocktake adjustment, a write-off,
a shipment on another promise — and no rule re-examines the reservations left behind.

The result is a promise that reports coverage it no longer has. Ten units reserved against
ten in stock, then an adjustment removes four: the commitment still holds an active
reservation for ten and its remaining quantity is ten, so the reservation covers the
remainder and no exception is raised, while only six units exist. The queue does not merely
stay silent here; it reports coverage that is not real. The Inventory view already derives
available quantity as observed stock minus active reservations and can display a negative
value, so the condition is observable today and simply never reaches the decision queue.

Both gaps hide a broken promise until it is too late to act on it, which is the exact
purpose the queue exists for.

### Scope

- Report an open customer-delivery commitment whose due date has passed while quantity
  remains unfulfilled as its own exception class.
- Report an item whose active reservations exceed observed stock as its own exception
  class.
- Guarantee that one outgoing commitment produces at most one queue entry, with the
  reservation shortfall carried as a cause rather than as a second entry.
- Give both new classes the same identity, severity, impact, causal values, trace,
  explanation, ordering, and tenant isolation behavior as every existing class.
- Extend the closed catalog and its drift gate to cover both classes and their causes.

### Non-Goals

- Overdue receivables, unpaid invoices, and any other financial lateness condition.
- Attribution of an over-subscribed item to a specific commitment, and any allocation,
  ranking, or priority rule that such attribution would require.
- Location-level coverage; this feature judges coverage per item across the tenant.
- Configurable grace periods, tenant-specific severity, thresholds, notification,
  escalation, or scheduling.
- Automatic remediation: re-reservation, release, cancellation, or rescheduling.
- Persisted exception tickets, acknowledgement, assignment, manual closure, or history.
- New operational state on Documents or other Evidence records.
- Schema changes, migrations, or typed fields added solely for exception derivation.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/020-exception-class-coverage/spec.md`](../020-exception-class-coverage/spec.md)
- [`specs/013-explain-projections/spec.md`](../013-explain-projections/spec.md)
- [`specs/008-commitments-holds/spec.md`](../008-commitments-holds/spec.md)
- [`specs/009-inventory-execution/spec.md`](../009-inventory-execution/spec.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-04

- Q: Should an overdue customer promise and an insufficient reservation on the same
  commitment appear as one queue entry or two? → A: One entry. The overdue class is
  emitted and carries the reservation shortfall as its cause, following the precedent set
  for `insufficient_reservation` in Spec 020.
- Q: Should lateness allow a grace period? → A: No. Lateness stays a strictly past due
  date, matching the supplier-side class. A tolerance would be the first tenant-tunable
  threshold in the product, and a promise date that is not meant literally is a data
  problem to correct at the source.
- Q: Should over-subscribed stock be reported per item or per competing commitment?
  → A: Per item, without naming which promise fails. The explanation lists the competing
  reservations and commitments so a human can decide.
- Q: Should the overdue class use the unused `critical` severity? → A: No. Both new
  classes are `high`. Introducing `critical` without a stated rule separating it from
  `high` would silently demote every existing class, and ordering already places overdue
  ahead of at-risk.

Product scope for all four decisions was accepted on 2026-09-04.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Which Customer Promises Are Already Late (Priority: P1)

An operator opens the decision queue and sees every open customer delivery promise whose
date has passed and whose quantity is still unfulfilled, with how much remains and how
long it has been late, without inspecting individual orders.

**Why this priority**: A late promise to a paying customer is the most expensive
condition a trading business can fail to see, and the queue is currently blind to it.

**Independent Test**: Create open customer-delivery commitments with past, future, and
absent due dates, ship some fully and some partially, then verify exactly the overdue
unfulfilled ones appear with correct remaining quantity and lateness context.

**Acceptance Scenarios**:

1. **Given** an open customer-delivery commitment whose due date has passed and whose
   quantity is not fully shipped, **When** the queue is listed, **Then** one
   `overdue_outgoing_customer_commitment` entry appears with the remaining quantity, the
   due date, and the evaluation instant.
2. **Given** the same commitment, **When** the outstanding quantity is shipped,
   **Then** the entry disappears from the queue without any manual closure.
3. **Given** a customer-delivery commitment whose due date has not passed, **When** the
   queue is listed, **Then** no overdue entry appears for it.
4. **Given** a customer-delivery commitment with no due date, **When** the queue is
   listed, **Then** no overdue entry appears for it, whatever its age.
5. **Given** an overdue commitment whose remaining quantity is also unreserved,
   **When** the queue is listed and the entry explained, **Then** the insufficient
   reservation appears as a cause of the overdue entry and not as a second entry, and the
   queue row states both the overdue remainder and the unreserved portion of it.
7. **Given** an overdue commitment with no reservation at all, **When** the queue is
   listed, **Then** the row states the overdue remainder once and does not repeat the
   same quantity as an unreserved clause, while the cause remains attached.

### User Story 2 - See Reservations That No Longer Have Goods Behind Them (Priority: P2)

An operator sees when the active reservations for an item exceed the stock actually
observed, so a reservation that lost its goods is visible before the order it protects
becomes late.

**Why this priority**: It removes a false assurance rather than adding a new warning —
today such a promise is reported as covered by a reservation that no longer has goods
behind it — but it is only actionable once the late-promise view above exists.

**Independent Test**: Reserve an item fully, remove stock through an adjustment, verify one
item-level entry with the correct shortfall while the commitment itself still reports no
risk, then receive stock or release the reservation and verify it clears.

**Acceptance Scenarios**:

1. **Given** an item whose active reservations exceed its observed stock, **When** the
   queue is listed, **Then** one `reservation_exceeds_stock` entry appears for that item
   with observed stock, reserved quantity, the shortfall, and how many promises compete
   for it.
2. **Given** the same item, **When** enough stock is received, **Then** the entry
   disappears.
3. **Given** the same item, **When** enough reservations are released or cancelled,
   **Then** the entry disappears.
4. **Given** an item whose reservations exactly equal observed stock, **When** the queue
   is listed, **Then** no entry appears for it.
5. **Given** an over-subscribed item, **When** the entry is explained, **Then** the
   contributing active reservations and their commitments are identified without
   asserting which promise will fail.
6. **Given** a commitment whose active reservation covers its full remaining quantity,
   **When** stock is adjusted below the reserved quantity, **Then** no at-risk entry
   appears for that commitment and one `reservation_exceeds_stock` entry appears for the
   item.

### User Story 3 - Keep the Queue Readable (Priority: P3)

An operator reviewing the queue sees each affected record once, in a stable order, with
the more urgent condition first.

**Why this priority**: The queue only stays a decision surface if adding classes does
not multiply rows for the same record or reshuffle results between two identical reads.

**Independent Test**: Construct a tenant where one commitment is simultaneously overdue
and under-reserved and its item is over-subscribed, then verify the exact entry set,
count, and order for repeated reads.

**Acceptance Scenarios**:

1. **Given** a commitment that is both overdue and under-reserved, **When** the queue is
   listed, **Then** exactly one entry exists for that commitment.
2. **Given** an at-risk commitment whose due date then passes, **When** the queue is
   listed again, **Then** it holds one overdue entry for that commitment and the former
   at-risk identity is no longer explainable.
3. **Given** an unchanged tenant, **When** the queue is listed twice, **Then** both
   reads return the same entries in the same order.
4. **Given** entries of the same severity, **When** the queue is listed, **Then** an
   already-late promise is ordered before a promise that is only at risk.
5. **Given** two tenants with comparable data, **When** either lists or explains,
   **Then** it sees only its own entries.

### Edge Cases

- A commitment is overdue and under-reserved at the same time.
- A commitment is overdue but already fully shipped, so nothing remains.
- The due date equals the evaluation instant exactly.
- A commitment has no due date, or is cancelled or closed rather than open.
- An item carries active reservations while no movement has ever been recorded for it.
- Observed stock is affected by a corrected or compensating movement.
- An item is over-subscribed while every individual commitment still looks covered.
- Stock leaves through an adjustment, a write-off, or a shipment on another promise while
  a reservation stays active.
- Reservations exist for an item in one location while the stock sits in another.
- A commitment crosses its due date, so the condition reported about it changes class
  while the underlying record stays the same.
- A first import of an existing business brings in historical orders that were never
  closed at the source, so many promises are overdue at the same instant.
- The identity of an entry that has since cleared is submitted for explanation.
- A commitment or item belongs to another tenant, or does not exist at all.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST report one `overdue_outgoing_customer_commitment` entry for
  every open customer-delivery commitment whose due date precedes the evaluation instant
  and whose committed quantity is not fully shipped.
- **FR-002**: The system MUST NOT report an overdue entry when the due date is absent,
  the due date has not passed, the commitment is not open, or nothing remains
  unfulfilled.
- **FR-003**: When an outgoing commitment is overdue and its remaining quantity is also
  unreserved, the system MUST report exactly one entry for that commitment, carry the
  reservation shortfall as a stable cause of that entry, and MUST NOT emit a separate
  at-risk entry for the same commitment.
- **FR-003a**: The impact summary of an entry MUST state the condition of its own class,
  and MUST append a clause for an attached cause only where that clause carries a value
  the condition does not already state. A reservation shortfall smaller than the overdue
  remainder is therefore named in the queue row, so it stays readable without opening the
  explanation; a shortfall equal to the whole remainder is not repeated.
- **FR-004**: The system MUST continue to report `outgoing_commitment_at_risk` unchanged
  for an open customer-delivery commitment that is not overdue and whose remaining
  quantity exceeds its active reservations.
- **FR-005**: The system MUST report one `reservation_exceeds_stock` entry for every item
  whose active reserved quantity exceeds its observed stock, and MUST NOT report one when
  the two are equal or stock is sufficient.
- **FR-005a**: The stock entry MUST state the shortfall and the number of commitments
  holding an active reservation for the item, so an operator can judge the size of the
  decision before opening the explanation.
- **FR-006**: Each new entry MUST carry a stable derived identity, severity, title,
  impact summary, authoritative record type and identity, causal values, and the shortest
  available Source → Evidence → Reality trace, in the same shape as every existing class.
- **FR-007**: Each new entry MUST disappear as soon as the condition it reports no longer
  holds, without acknowledgement, closure, or any other manual step.
- **FR-008**: The explanation of a new entry MUST re-derive the current condition, and an
  identity that is malformed, unknown, cleared, or owned by another tenant MUST produce
  the same not-found response the queue already returns.
- **FR-009**: The queue MUST remain deterministically ordered for identical data, with an
  already-late outgoing promise ordered ahead of an at-risk one of the same severity.
- **FR-010**: Both classes and every cause MUST be declared in the closed product
  catalog with an authority reference and named executable evidence, and any drift
  between the catalog, the derivations, and the declared order MUST fail the existing
  coverage gate.
- **FR-011**: Every surface that consumes the queue MUST receive both classes through the
  existing shared list and explanation contract, without surface-specific derivation.

### Domain and Traceability Requirements

- **DR-001**: Both classes MUST be derived from existing tenant-owned Commitment,
  Reservation, and Movement records at read time. They add no schema, no persisted
  exception state, and no operational state to Documents or any other Evidence record.
- **DR-002**: The overdue class MUST carry the commitment's existing trace and MUST NOT
  duplicate Document, DocumentLine, or SourceRecord provenance already reachable through
  it.
- **DR-003**: The stock class MUST reference its item and the contributing reservations
  and commitments by opaque identity only, and MUST NOT restate their authoritative
  business fields or become an authority on availability.
- **DR-004**: Observed stock and reserved quantity MUST come from the existing shared
  inventory derivation, so the queue and the Inventory view can never disagree about the
  same item.
- **DR-005**: Every read, derivation, and explanation MUST be tenant-scoped, and no entry
  may reference a record outside its own tenant.
- **DR-006**: A cause identifier names a business reason and MUST stay stable and
  comparable wherever it appears, so that the same reservation shortfall reads as the
  same reason on an at-risk and on an overdue entry. The cause vocabulary is closed:
  introducing a new reason requires the same specification authority and executable
  evidence as introducing a class.
- **DR-007**: The stock class MUST NOT assert which commitment will fail; blame
  attribution would require an allocation priority that the domain model does not define
  and that belongs in a policy decision, not in a derived observation.

### Key Entities *(when data is involved)*

- **Commitment**: The directional promise whose date and unfulfilled remainder decide
  whether an outgoing promise is late. No new field is introduced.
- **Reservation**: The active allocation whose quantity, summed per item, decides whether
  the tenant has promised the same goods more than once.
- **Observed stock**: The quantity derived from Movements for an item; not a stored
  balance and not authority for anything beyond this observation.
- **Exception class and cause**: The catalog vocabulary that gains two classes and the
  reuse of the existing reservation-shortfall reason.

## Success Criteria *(mandatory)*

- **SC-001**: Every open customer delivery promise that is past its date with quantity
  outstanding is visible in the decision queue without opening a single order.
- **SC-002**: No commitment ever contributes more than one entry to the queue, whatever
  combination of conditions applies to it.
- **SC-003**: An item promised beyond its observed stock is visible before any of the
  competing promises has become late.
- **SC-004**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-005**: A resolved condition leaves the queue on the next read with no manual
  action, and its former identity is no longer explainable.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Lateness is strictly a past due date at the evaluation instant, with no grace period,
  matching the existing supplier-side class. A due date equal to the evaluation instant
  is not yet late.
- A commitment without a due date carries no date promise, so no lateness can be
  asserted about it.
- The shared reserve operation already allocates at most the available quantity, so this
  class does not detect goods promised twice at write time. It detects reservations that
  lost their backing afterwards, which is why a commitment-level check cannot find it: the
  reservation still exists and still covers the remaining quantity.
- Stock coverage is judged per item across the tenant, reusing the existing derivation of
  observed stock minus active reservations. Location-level coverage is deliberately
  deferred; an item whose stock sits in the wrong location is a separate condition and
  would need its own class.
- Over-subscription is reported once per item rather than once per competing commitment,
  because the model defines no allocation priority and inventing one here would create a
  process rule inside a derived observation.
- Both classes are severity `high`, consistent with every existing promise-related and
  financial class. The unused `critical` level stays unused: promoting one class into it
  would silently demote every existing `high`, and the product has no stated rule for
  what separates the two. Defining that rule is its own decision and must not happen as a
  side effect of this feature. Ordering already places an overdue promise ahead of an
  at-risk one without touching severity.
- A first import of an established business can make many promises overdue at once, when
  orders that are dead in practice were never closed in the source. This is treated as a
  true finding rather than noise to be suppressed: the honest remedy is closing or
  correcting those orders at the source, not a tolerance inside the derivation. No
  backlog suppression, ageing rule, or import cut-off date is part of this feature.
- The existing coverage gate must be extended before these classes can be declared: it
  currently fixes the class order and the permitted cause set, and it requires a cause
  identifier to be unique across the whole catalog, which conflicts with reusing the
  reservation-shortfall reason on a second class. Resolving that constraint is
  implementation work for the plan, not a change to the business rules above.
- No financial lateness condition is in scope. Overdue receivables remain a separate,
  later specification.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | overdue outgoing commitment derivation test |
| FR-002 | US1 scenarios 3, 4; Edge cases | overdue boundary and status test |
| FR-003 | US1 scenario 5; US3 scenario 1 | single-entry exclusivity test |
| FR-003a | US1 scenarios 5, 7 | impact clause-per-cause test |
| FR-004 | US3 scenario 4 | unchanged at-risk regression test |
| FR-005 | US2 scenarios 1, 4, 6 | reservation over-subscription derivation test |
| FR-005a | US2 scenario 1 | shortfall and competing-promise count test |
| FR-006 | US1 scenario 1; US2 scenario 1 | entry shape and trace test |
| FR-007 | US1 scenario 2; US2 scenarios 2, 3 | clearing test per class |
| FR-008 | US3 scenario 2; Edge cases | explanation not-found parity test |
| FR-009 | US3 scenarios 3, 4 | deterministic ordering test |
| FR-010 | US3 scenario 1 | catalog coverage and drift gate test |
| FR-011 | US1 scenario 1 | shared list and explanation contract test |
| DR-001 | US1 scenario 2; US2 scenario 2 | read-time derivation and no-persistence test |
| DR-002 | US1 scenario 1 | commitment trace test |
| DR-003 | US2 scenario 5 | opaque reference test |
| DR-004 | US2 scenario 1 | queue and inventory agreement test |
| DR-005 | US3 scenario 5 | tenant isolation test |
| DR-006 | US1 scenario 5 | shared cause vocabulary test |
| DR-007 | US2 scenario 5 | no-attribution test |
