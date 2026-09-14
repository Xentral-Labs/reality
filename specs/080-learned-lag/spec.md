# Feature Specification: Long by This Company's Own Standard

**Feature Branch**: `080-learned-lag`
**Created**: 2026-09-05
**Status**: Draft
**Language**: English
**Input**: "Two conditions that only exist once time has passed, judged against how long this company normally takes."

## Context and Intent

### Problem

Two things go wrong slowly, and Reality cannot see either of them because both need a
judgement about how long is too long.

**An order nobody promised a date for can stand forever.** Every delivery class Reality has
is anchored to `due_at`. `overdue_outgoing_customer_commitment` requires one and says nothing
without it; `outgoing_commitment_at_risk` fires only while the reservation is short. A
consumer order that arrives with no requested delivery date, is reserved in full, and is then
never picked produces **no entry of any kind**, however long it sits. For a shop that is not
an edge case — it is most orders, because a webshop customer states no date.

**Goods received and never invoiced stop being ordinary.** Spec 076 deliberately excluded
this: a supplier invoice arriving after the goods is the usual sequence, and reporting it
would flag every receipt. That is right for three days and wrong for six weeks, where it
becomes an accrual nobody has made and a supplier relationship nobody is watching. What
separates the two is time, and Reality has no way to say so.

Both need the same missing thing: a defensible answer to "how long is long here". Spec 072
answered exactly that question for a source that had stopped delivering, and answered it by
learning the rhythm the source itself had shown rather than by asking anybody to configure
one. The same answer works twice more.

### Scope

- Derive, per tenant, how long that tenant normally takes to ship an order and how long its
  suppliers normally take to invoice a receipt.
- Report a delivery promise with no date that has stood far longer than that tenant's own
  norm.
- Report goods received and unbilled far longer than that tenant's own norm.
- Say nothing at all where a tenant has too little history for a norm to be claimed.
- Give both classes the identity, severity, impact, causal values, trace, explanation,
  ordering, tenant isolation and operator guidance every existing class carries.

### Non-Goals

- Configurable thresholds. The four constants behind each judgement are product decisions
  identical for every tenant, recorded here rather than exposed as settings. Spec 072 set
  that precedent deliberately and this feature follows it.
- Reporting a promise that carries a date. That is `overdue_outgoing_customer_commitment`
  and belongs to it; the two classes are disjoint by construction.
- Working days, holidays and shipping calendars. A norm learned from a tenant's own history
  already contains its weekends, because every lag it learned from crossed the same ones.
- Predicting when an order will ship, or when an invoice will arrive. Both classes report
  what has already taken too long; neither forecasts.
- Purchase promises without a date, which `overdue_incoming_supplier_commitment` covers when
  dated and which say nothing about billing when not.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/072-silent-source/spec.md`](../072-silent-source/spec.md)
- [`specs/076-invoice-order-link/spec.md`](../076-invoice-order-link/spec.md)
- [`specs/008-commitments-holds/spec.md`](../008-commitments-holds/spec.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-05

- Q: Learned from what statistic? Spec 072 uses the longest pause a source has shown. → A:
  The median lag, not the longest. A source's longest pause is bounded by its rhythm — nights
  and weekends — so the longest is a safe anchor there. An order's lag has no such bound: one
  order that took eight months would set the bar at eight months forever and silence the
  class permanently. A median moves with the business and cannot be captured by a single
  outlier.
- Q: Which orders count towards the norm? → A: Only ones that finished. An order still
  sitting is exactly what the class is trying to judge, so including it would let a backlog
  raise the bar that measures the backlog.
- Q: Why a floor as well as a multiple? → A: Because a fast tenant would otherwise report
  everything. A shop whose median is four hours would flag an order at twelve, which is
  noise. The floor is the shortest span in which "stuck" means anything in trade, and it is
  different for the two conditions because the businesses are.
- Q: What happens on a tenant with no history? → A: Nothing is reported. A norm claimed from
  three orders is a guess, and this line of work has repeatedly chosen silence over a guess.
- Q: Do the two delivery classes overlap? → A: No, and by construction rather than by
  precedence. This class considers only promises with no date at all; the moment a promise
  has one, the overdue class owns it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the Order That Quietly Stopped (Priority: P1)

An operator sees delivery promises with no agreed date that have stood far longer than this
company normally takes, with how long they have stood and what normal is.

**Why this priority**: It is the largest blind spot in consumer trade. Most webshop orders
carry no date, and today none of them can ever be reported however long they sit.

**Independent Test**: Build a history of orders shipped quickly, leave one unshipped far
longer, and verify only that one is reported.

**Acceptance Scenarios**:

1. **Given** a tenant with a history of orders shipped in about a day and one undated promise
   standing for weeks, **When** the queue is listed, **Then** one entry appears with the age
   of the promise and the norm it is judged against.
2. **Given** the same promise, **When** the goods ship, **Then** the entry disappears without
   any manual step.
3. **Given** a promise that carries a due date, **When** the queue is listed, **Then** no
   entry of this class appears, whatever its age.
4. **Given** a tenant with fewer completed orders than the minimum history, **When** the
   queue is listed, **Then** no entry appears, however long anything has stood.
5. **Given** a tenant whose orders normally take minutes and a promise standing a few hours,
   **When** the queue is listed, **Then** no entry appears, because the floor has not been
   passed.

### User Story 2 - See the Receipt No Supplier Ever Invoiced (Priority: P1)

An operator sees goods received and still unbilled far longer than this company's suppliers
normally take, with how long they have stood and what normal is.

**Why this priority**: It is an accrual nobody has made and a supplier nobody is chasing, and
Spec 076 deliberately left it open pending exactly this rule.

**Acceptance Scenarios**:

1. **Given** a history of receipts invoiced within days and one receipt unbilled for months,
   **When** the queue is listed, **Then** one entry appears with the age and the norm.
2. **Given** the same receipt, **When** an invoice line bills it, **Then** the entry
   disappears without any manual step.
3. **Given** a receipt unbilled for two days on a tenant whose suppliers take a week, **When**
   the queue is listed, **Then** no entry appears.
4. **Given** a tenant with too few invoiced receipts to claim a norm, **When** the queue is
   listed, **Then** no entry appears.

### Edge Cases

- A tenant whose entire history is one very slow order, so the median is that order.
- A promise created and cancelled without ever shipping, which is neither reported nor
  learned from.
- A promise partly shipped long ago and never finished.
- A receipt whose purchase order line is billed in a different unit.
- A receipt against a promise that carries no order line at all.
- A tenant whose median lag is zero because everything ships the moment it is ordered.
- Clock skew: a shipment recorded as occurring before the promise was created.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST derive a per-tenant fulfilment norm from the lag between a
  delivery promise being created and its last shipment, over completed promises only.
- **FR-002**: The system MUST derive a per-tenant billing norm from the lag between the last
  receipt against a purchase order line and the date of the first invoice line billing it,
  over billed lines only.
- **FR-003**: Each norm MUST be the median of the most recent completed cases, and MUST NOT
  be the longest or the mean. A single outlier MUST NOT be able to move it.
- **FR-004**: Where a tenant has fewer completed cases than the minimum history, no norm MUST
  be claimed and nothing MUST be reported for that condition.
- **FR-005**: The system MUST report one entry for every open delivery promise that carries
  no due date, has quantity outstanding, and has stood longer than the fulfilment norm
  multiplied by the product factor.
- **FR-005a**: A cancelled promise MUST be excluded from both the reporting and the norm. It
  will never ship, so counting it as outstanding would report something nobody is waiting for,
  and counting it as completed would teach the norm a lag that never happened.
- **FR-006**: A promise that carries a due date MUST NOT be reported by this class, whatever
  its age.
- **FR-007**: The system MUST report one entry for every purchase order line with goods
  received, an unbilled remainder, and a last receipt older than the billing norm multiplied
  by the product factor.
- **FR-007a**: A quantity comparison MUST be made only between lines recorded in the same
  unit, as it is for every other class that compares a received quantity with a billed one. A
  pair in different units is left alone rather than converted.
- **FR-008**: Neither class MUST report anything below its absolute floor, however small the
  learned norm is.
- **FR-009**: Each entry MUST state how long the condition has stood, the norm it is judged
  against, and the threshold that norm produced.
- **FR-010**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace, in
  the same shape as every existing class.
- **FR-011**: Each entry MUST disappear as soon as its condition ends, without acknowledgement
  or any other manual step.
- **FR-012**: The explanation of an entry MUST re-derive the current condition, and a
  malformed, unknown, cleared or foreign identity MUST produce the same not-found response
  the queue already returns.
- **FR-013**: Both classes MUST be declared in the closed catalog with an authority
  reference, named executable evidence, and the description, owner and clearing path every
  class carries.
- **FR-014**: Every surface that consumes the queue MUST receive both classes through the
  existing shared list and explanation contract.
- **FR-015**: The queue MUST remain deterministically ordered for identical data, with the
  longest-standing condition first.
- **FR-016**: A lag that would be negative MUST be treated as zero rather than recorded as
  negative, so a clock skew cannot drag a norm below nothing.

### Domain and Traceability Requirements

- **DR-001**: No schema changes. Both norms are derived at read time from Commitments,
  Movements and DocumentLines the tenant already owns.
- **DR-002**: Neither class writes anything, and neither stores a norm. The norm is
  recomputed per read, which is what keeps it a description of the tenant rather than a
  configured value with a life of its own.
- **DR-003**: Delivered and received quantities MUST reuse the existing correction-aware
  movement quantity, never a second count.
- **DR-004**: Traces MUST reach their records by opaque identity and MUST NOT restate
  business fields.
- **DR-005**: Every read, derivation and explanation MUST be tenant-scoped, including the
  norms, which MUST NOT be derived across tenants.
- **DR-006**: No cause is introduced; the closed cause vocabulary is untouched.
- **DR-007**: The constants behind both judgements MUST be recorded in the code with the
  reasoning, as Spec 072's are, and MUST NOT become tenant settings.

### Key Entities *(when data is involved)*

- **Commitment**: The delivery promise whose age is judged, and the completed promises the
  fulfilment norm is learned from.
- **DocumentLine (order)**: The purchase order line whose receipt is judged, and the billed
  lines the billing norm is learned from.
- **Movement**: The shipments and receipts both lags are measured from.

## Success Criteria *(mandatory)*

- **SC-001**: A consumer order that nobody dated and nobody shipped becomes visible, which it
  is not today at any age.
- **SC-002**: A receipt no supplier invoiced becomes visible once it stops being ordinary,
  without every receipt becoming visible.
- **SC-003**: Neither class fires on a tenant too young to have a norm.
- **SC-004**: Neither class fires on a tenant that is simply fast.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- A tenant's own recent history describes it better than any number a person would type. That
  is the assumption Spec 072 rests on and it is the same one here.
- The median is the right statistic for a lag with no upper bound. If a business turns out to
  be bimodal — express orders and slow special orders in one tenant — the median describes
  neither well, and the rule to revisit is FR-003.
- Spec 076's billed-line reference is in place, so which invoice line bills which receipt is
  answerable at all.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | fulfilment norm test |
| FR-002 | US2 scenario 1 | billing norm test |
| FR-003 | Edge cases | outlier resistance test |
| FR-004 | US1 scenario 4; US2 scenario 4 | minimum history test |
| FR-005 | US1 scenarios 1, 2 | stalled order derivation test |
| FR-005a | Edge cases | cancelled promise test |
| FR-006 | US1 scenario 3 | dated promise exclusion test |
| FR-007 | US2 scenarios 1, 2 | unbilled receipt derivation test |
| FR-007a | Edge cases | mismatched unit test |
| FR-008 | US1 scenario 5; US2 scenario 3 | floor test |
| FR-009 | US1 scenario 1 | causal values test |
| FR-010 | US1 scenario 1 | entry shape and trace test |
| FR-011 | US1 scenario 2; US2 scenario 2 | clearing test per class |
| FR-012 | Edge cases | explanation not-found parity test |
| FR-013 | US1 scenario 1 | catalog coverage and guidance gate test |
| FR-014 | US1 scenario 1 | shared list and explanation contract test |
| FR-015 | US1 scenario 1 | deterministic ordering test |
| FR-016 | Edge cases | clock skew test |
| DR-001 | — | no migration added |
| DR-002 | US1 scenario 2 | read-time derivation test |
| DR-003 | US2 scenario 1 | shared movement path test |
| DR-004 | US1 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test, including the norms |
| DR-006 | US1 scenario 1 | existing cause-vocabulary drift gate |
| DR-007 | — | constants review |
