# Feature Specification: Say When the Units Do Not Meet

**Feature Branch**: `087-units-comparable`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "Seven classes skip any pair recorded in different units rather than converting. Safer and still a failure: an operator cannot tell a line nobody needs to look at from one the rule declined to judge."

## Context and Intent

### Problem

Four places in the operational queue quietly decline to judge, and nobody is told.

An order line in boxes and an invoice line in pieces cannot be compared, so
`shipped_not_billed`, `billed_not_received`, `receipt_unbilled`, `returned_not_credited`,
`credited_not_returned` and `invoice_price_differs` leave the pair alone — six classes, three
inline checks. A fourth place declines differently: `sold_below_purchase_price` looks for a
purchase price in the line's own unit and finds none, which is the same silence arrived at from
the other side. That was the right decision every time it was made — a converted figure would have been a guess and an unconverted
one would have been wrong — and it has an accumulating cost: **an operator cannot distinguish a
line nobody needs to look at from one the rules refused to look at.** Silence means both.

There is also a conversion that is not a guess and is going unused. An Item carries a
`purchase_unit` and a `conversion_factor` — a company stating "we buy this in boxes of twelve".
That is a received value like any other. Where a pair differs only by that stated relation, the
comparison can be made from figures somebody wrote down.

Where no such statement exists, the honest answer is not to convert and not to stay silent
either, but to say so.

### Scope

- Compare quantities across the item's own stated purchase and stock units, where the company
  has stated the relation and the conversion is exact.
- Leave every other pair uncompared, as today.
- Report one entry per item whose quantity comparisons are being declined for want of a
  reconcilable unit, naming which of the two reasons applies and how many lines are affected.
- Give the class the identity, severity, impact, causal values, trace, explanation, ordering,
  tenant isolation and operator guidance every existing class carries.

### Non-Goals

- A unit system. Reality does not know that a kilogram is a thousand grams and will not learn;
  it knows what a company has said about its own items.
- Converting prices. Turning a price per box into a price per piece is a division that produces
  money, and money is where this product refuses to compute. A price pair in different units
  stays uncompared however well the quantities convert.
- Inexact conversion. Seven pieces into boxes of twelve is not a quantity anybody stated, and a
  remainder is exactly the rounding this product exists to avoid.
- Converting between two units neither of which is the item's own stock or purchase unit.
- Giving movements a unit. A Movement records a quantity and no unit, and is counted in
  whatever unit the promise it settles was recorded in. That is why normalising billing lines to
  the agreed line's unit is the right target and not an arbitrary one, and it is also a real
  limitation of the model that this feature neither fixes nor worsens.
- Reporting a price comparison that was declined for units. No stated conversion would make it
  possible, because FR-006 refuses to convert prices at all, so an entry saying "state the
  relation" would be advice that does not work. `sold_below_purchase_price` is silent for a unit
  it holds no price in, and stays silent.
- Inferring a factor from history — from how many pieces have arrived per box, say. That is a
  guess wearing arithmetic.
- Changing what any existing class means. Where a conversion applies, the same comparison is
  simply possible; where it does not, the same silence holds and is now reported.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/features/master_data.md`](../../docs/features/master_data.md)
- [`specs/076-invoice-order-link/spec.md`](../076-invoice-order-link/spec.md)
- [`specs/079-returns-connect/spec.md`](../079-returns-connect/spec.md)
- [Constitution](../../.specify/memory/constitution.md), principle VIII

## Clarifications

### Session 2026-09-06

- Q: Is converting a quantity not exactly the computing this product refuses? → A: No, and the
  distinction is the one principle VIII draws. Recomputing means producing a second authority
  for a figure a source stated. Multiplying a stated quantity by a stated factor at read time,
  storing nothing, is an observation over facts held — which that principle allows in as many
  words.
- Q: Then why not convert prices too? → A: Because it divides, and a division that does not come
  out produces a money figure nobody stated. Quantities of goods are counted; prices are agreed.
  The line is drawn where the product has always drawn it.
- Q: What about an inexact conversion? → A: Not made. Seven pieces are not a number of boxes,
  and a remainder is the rounding this product exists to avoid. Such a pair is declined and
  reported like any other.
- Q: One entry per line, or per item? → A: Per item. Every line for that item is affected by the
  same missing statement, and the thing an operator does about it — state the relation once — is
  a property of the item. Per line it would be a wall; per item it is a task.
- Q: An inexact conversion is declined — is it reported the same way as a missing one? → A:
  Reported, but not the same way. They are different problems with different exits: one is
  master data nobody filled in, the other is a relation that is stated and does not divide. The
  entry says which, because "state the relation" is useless advice to somebody who already has.
- Q: Is "we cannot judge this" a business condition at all? → A: It is. The company's master
  data is incomplete in a way that blinds several checks, the owner is whoever maintains items,
  and the way out is to state the relation. That is as actionable as any other class here.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare What the Company Has Explained (Priority: P1)

An order line in boxes and an invoice line in pieces are compared, because the item says how
many pieces are in a box.

**Why this priority**: The figures exist and the company has already said how they relate;
declining to use that is throwing away a stated fact.

**Independent Test**: Record an item with a stated conversion, order in boxes, bill in pieces,
and verify the quantity classes judge the pair.

**Acceptance Scenarios**:

1. **Given** an item bought in boxes of twelve, an order line for ten boxes and invoice lines
   for a hundred and eight pieces, **When** the queue is listed, **Then** the shortfall is
   reported as the twelve pieces it is.
2. **Given** the same pair billed in full, **When** the queue is listed, **Then** nothing is
   reported.
3. **Given** an item that states no conversion, **When** the queue is listed, **Then** no
   quantity comparison is made for it.
4. **Given** a pair whose conversion leaves a remainder, **When** the queue is listed, **Then**
   no comparison is made.
5. **Given** a price in boxes and a price in pieces, **When** the queue is listed, **Then** they
   are not compared, however well the quantities convert.

### User Story 2 - See What Could Not Be Judged (Priority: P1)

An operator sees the items whose lines the queue is declining to compare, and how many lines
that affects.

**Why this priority**: A silent decline is indistinguishable from nothing being wrong, and
today every one of them is silent.

**Acceptance Scenarios**:

1. **Given** order and invoice lines for one item in units that cannot be reconciled, **When**
   the queue is listed, **Then** one entry appears for that item stating the two units and the
   number of lines affected.
2. **Given** the item's conversion stated afterwards, **When** the queue is listed, **Then** the
   entry disappears without any manual step.
3. **Given** several items in that state, **When** the queue is listed, **Then** one entry
   appears per item and none per line.
4. **Given** lines whose units match, **When** the queue is listed, **Then** no entry appears.
5. **Given** an item whose stated conversion leaves a remainder for its lines, **When** the queue
   is listed, **Then** the entry says the relation does not divide evenly rather than that none
   was stated.
6. **Given** only a price pair in differing units, **When** the queue is listed, **Then** no
   entry appears, because stating a relation would not make that comparison possible.

### Edge Cases

- An item whose purchase unit equals its stock unit.
- A stated conversion factor of zero, or a negative one.
- A line in a unit that is neither the item's stock unit nor its purchase unit.
- Lines for one item in three different units.
- A conversion that is exact in one direction and not the other.
- An item with a stated conversion whose lines all already match.
- A line naming no item at all, which has nothing to state a relation on and therefore no entry
  to carry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A quantity comparison MUST be made across an item's stock unit and its stated
  purchase unit, using the conversion factor recorded on the item.
- **FR-002**: The conversion MUST use only figures the company stated — the quantity on the line
  and the factor on the item — and MUST store nothing.
- **FR-003**: A conversion MUST be made only where it is exact. Where it leaves a remainder, the
  pair MUST be treated as not comparable.
- **FR-004**: A conversion factor of zero or less MUST be treated as no stated relation.
- **FR-005**: A pair in units other than the item's stock and purchase units MUST NOT be
  converted.
- **FR-006**: Prices MUST NOT be converted between units under any circumstances, and a price
  pair in differing units MUST remain uncompared.
- **FR-007**: The system MUST report one entry per item for which a comparison was declined
  because its units cannot be reconciled.
- **FR-008**: That entry MUST state the units involved, which of the two reasons applies — no
  stated relation, or a stated relation that does not divide evenly — and the number of lines
  affected, and MUST NOT be repeated per line.
- **FR-008a**: A price comparison declined for differing units MUST NOT produce an entry, since
  no stated relation would make it possible.
- **FR-009**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace, in
  the same shape as every existing class.
- **FR-010**: Each entry MUST disappear as soon as the relation is stated or the lines agree,
  without acknowledgement or any other manual step.
- **FR-011**: The explanation of an entry MUST re-derive the current condition, and a malformed,
  unknown, cleared or foreign identity MUST produce the same not-found response the queue
  already returns.
- **FR-012**: The class MUST be declared in the closed catalog with an authority reference,
  named executable evidence, and the description, owner and clearing path every class carries.
  Its guidance MUST name the checks that are being declined.
- **FR-013**: Every surface that consumes the queue MUST receive the class through the existing
  shared list and explanation contract.
- **FR-014**: The queue MUST remain deterministically ordered for identical data.
- **FR-015**: Every existing class MUST keep reporting exactly what it reports today for pairs
  whose units already match.

### Domain and Traceability Requirements

- **DR-001**: No schema changes. `purchase_unit` and `conversion_factor` exist on the Item.
- **DR-002**: The class MUST be derived at read time from DocumentLines and Items the tenant
  already owns, and MUST store nothing.
- **DR-003**: One shared decision MUST answer whether two quantities are comparable, used by
  every class that asks, so no two can disagree about it.
- **DR-004**: Traces MUST reach their records by opaque identity and MUST NOT restate business
  fields beyond the units themselves, which are what the entry is about.
- **DR-005**: Every read, derivation and explanation MUST be tenant-scoped.
- **DR-006**: No cause is introduced; the closed cause vocabulary is untouched.

### Key Entities *(when data is involved)*

- **Item**: Carries the stock unit, the purchase unit and the stated relation between them.
- **DocumentLine**: The quantities being compared, each in whatever unit it was recorded in.

## Success Criteria *(mandatory)*

- **SC-001**: A company that has stated how it buys an item gets its comparisons made.
- **SC-002**: A company that has not is told which items are blinding which checks.
- **SC-003**: No figure in any comparison is one nobody stated, and no money is converted.
- **SC-004**: A declined quantity comparison is never silent again, and says which of the two
  things went wrong.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- The stated conversion relates an item's purchase unit to its stock unit and nothing else. A
  company selling in a third unit is outside it, and the class will say so rather than guess.
- Reporting per item assumes an operator fixes the item rather than the line, which is what the
  data supports: the relation lives on the item.
- The new class will be loud on a tenant whose master data has never carried conversions, and
  that is the point rather than a defect. Its volume is bounded by items, not by lines.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1, 2 | conversion comparison test |
| FR-002 | US1 scenario 1 | stated-figures test |
| FR-003 | US1 scenario 4 | remainder test |
| FR-004 | Edge cases | zero factor test |
| FR-005 | Edge cases | third unit test |
| FR-006 | US1 scenario 5 | price conversion refusal test |
| FR-007 | US2 scenarios 1, 3 | declined derivation test |
| FR-008 | US2 scenarios 1, 3, 5 | one entry per item test; stated-but-inexact reason test |
| FR-008a | US2 scenario 6 | price decline is not reported test |
| FR-009 | US2 scenario 1 | entry shape and trace test |
| FR-010 | US2 scenario 2 | clearing test |
| FR-011 | Edge cases | explanation not-found parity test |
| FR-012 | US2 scenario 1 | catalog coverage and guidance gate test |
| FR-013 | US2 scenario 1 | shared list and explanation contract test |
| FR-014 | US2 scenario 3 | deterministic ordering test |
| FR-015 | US1 scenario 2; US2 scenario 4 | the existing suites, unchanged |
| DR-001 | — | no migration added |
| DR-002 | US2 scenario 2 | read-time derivation test |
| DR-003 | US1 scenario 3 | one shared decision test |
| DR-004 | US2 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US2 scenario 1 | existing cause-vocabulary drift gate |
