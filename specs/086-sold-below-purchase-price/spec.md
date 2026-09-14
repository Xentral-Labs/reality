# Feature Specification: Sold for Less Than It Costs to Buy

**Feature Branch**: `086-sold-below-purchase-price`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "Negative margin. Spec 076 reports a billed price differing from the agreed price, which is a different question."

## Context and Intent

### Problem

Reality can say that an invoice billed a different price from the one agreed. It cannot say
that the agreed price was a bad one.

A trading business lives on the difference between what it pays and what it charges, and the
oldest way to lose money is to sell below that line — a discount granted one afternoon, a price
list that was never updated after the supplier raised theirs, a rounding that went the wrong
way on a large order. Every figure involved is already recorded, and nothing compares them.

The reason it has not been built is that "margin" was assumed to need a cost model: landed
cost, freight, overhead, and a valuation method for deciding which of last month's receipts a
sale consumed. That assumption was wrong about this product. Reality already holds a **purchase
price list** — a first-class concept with its own direction — and the price on it is a figure
somebody stated, not one Reality worked out. Comparing it with the price somebody agreed to
sell at is a comparison between two received values, which is the one kind of arithmetic this
product encourages.

What that comparison is not is accounting margin. It carries no freight, no handling, no
overhead and no valuation method, and it is honest about that.

### Scope

- Report a sales order line agreed below the purchase price the company had standing for that
  item when the sale was agreed.
- Take both prices as they were stated: the agreed price on the line, and the entry on the
  default purchase price list.
- Say nothing where no purchase price was standing, because the company has not said what it
  pays.
- Give the class the identity, severity, impact, causal values, trace, explanation, ordering,
  tenant isolation and operator guidance every existing class carries.

### Non-Goals

- Accounting margin. Freight, handling, duty, overhead and the valuation of stock are outside
  this and outside Reality; the product records what businesses state and does not price
  inventory.
- Deciding which receipt a sale consumed. That is the valuation question this feature exists to
  avoid, and answering it would require Reality to choose a method nobody asked it to choose.
- Supplier-specific purchase prices. What one supplier charges is a negotiation; the standing
  default is the company's own statement of what an item costs it, and that is what a sales
  price should be judged against.
- Reporting a *sale* below cost after the fact from invoice lines. The agreed line is where the
  decision was made, and it is where an operator can still act.
- Suggesting a price. Reality reports the comparison and recommends nothing.
- Tax, currency conversion, and quantity breaks beyond those the price list itself states.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/features/master_data.md`](../../docs/features/master_data.md)
- [`specs/076-invoice-order-link/spec.md`](../076-invoice-order-link/spec.md)
- [`specs/004-master-data/spec.md`](../004-master-data/spec.md)
- [Constitution](../../.specify/memory/constitution.md), principle VIII

## Clarifications

### Session 2026-09-06

- Q: Does this need a cost model? → A: No, and that assumption is what kept it unbuilt. A
  purchase price list is a received value; comparing it with an agreed sales price computes
  nothing. A cost model would make Reality the author of a number nobody stated, which
  principle VIII forbids and which the product has refused everywhere else.
- Q: Which purchase price, when a supplier has its own? → A: The standing default. A
  supplier-specific price is what one negotiation produced; the default list is the company's
  own statement of what the item costs it, and a sales price is judged against that.
- Q: Which moment's purchase price? → A: The one valid when the sale was agreed. Judging a
  six-month-old order against today's purchase price would report every line a supplier has
  since raised, which is a fact about the supplier rather than about the sale.
- Q: What if no purchase price is standing? → A: Nothing is reported. The company has not said
  what the item costs it, and inventing a figure is exactly what this feature exists not to do.
  A business that keeps no purchase price list will never see this class, and that is correct
  rather than a limitation to work around.
- Q: The order line or the invoice line? → A: The order line. That is where the price was
  agreed and where somebody can still change it; by the time it is invoiced the decision has
  been made.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the Order That Loses Money (Priority: P1)

An operator sees sales order lines agreed below what the company says the item costs it, with
both prices and the difference.

**Why this priority**: It is the oldest way a trading business loses money, and every figure
needed to see it has been recorded all along.

**Independent Test**: Record a purchase price for an item, agree a sales line below it, and
verify the entry states both prices and the shortfall; raise the sales price and verify it
clears.

**Acceptance Scenarios**:

1. **Given** a standing purchase price of 10 and a sales order line agreed at 8, **When** the
   queue is listed, **Then** one entry appears with both prices and a shortfall of 2.
2. **Given** a sales order line agreed at exactly the purchase price, **When** the queue is
   listed, **Then** no entry appears, because selling at cost is a decision rather than a
   mistake.
3. **Given** the same line corrected to a price above the purchase price, **When** the queue is
   listed, **Then** the entry disappears without any manual step.
4. **Given** an item with no purchase price standing, **When** the queue is listed, **Then** no
   entry appears, whatever the sales price.
5. **Given** a purchase price that rose after the sale was agreed, **When** the queue is
   listed, **Then** the sale is judged against the price that was standing when it was agreed.
6. **Given** a purchase order line, **When** the queue is listed, **Then** it is never
   reported, because buying is not selling.

### Edge Cases

- A sales line and a purchase price in different currencies.
- A sales line and a purchase price in different units.
- A purchase price list that is not the default, or is inactive, neither of which is read.
- A price list entry with a quantity break the line does not reach, so no price is standing.
- A sales order line with no item, such as freight or a service.
- A sales order line agreed at zero, such as a sample or a replacement.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST report one entry for every sales order line whose agreed unit
  price is below the purchase price standing for that item when the sale was agreed.
- **FR-002**: Both figures MUST be taken as stated — the agreed price from the line, the
  purchase price from the price list — and neither MUST be computed, adjusted or converted.
- **FR-003**: The purchase price MUST come from the default purchase price list, active and
  valid at the moment the sale was agreed, for the same currency and the same unit. Where the
  list states quantity breaks, the applicable entry MUST be the highest break at or below the
  line's quantity, which is the rule the existing price resolver uses; where no break applies,
  no price is standing and nothing is reported.
- **FR-004**: Where no such purchase price is standing, nothing MUST be reported.
- **FR-005**: A line agreed at exactly the purchase price MUST NOT be reported.
- **FR-006**: A line agreed at zero MUST NOT be reported, because a sample or a replacement is
  a decision rather than a mispriced sale.
- **FR-007**: Only sales order lines MUST be considered.
- **FR-008**: A comparison MUST be made only where the currency and the unit match, and a pair
  that differs in either MUST be left alone rather than converted.
- **FR-009**: A line with no item MUST NOT be reported, because freight and services have no
  purchase price of their own here.
- **FR-010**: Each entry MUST state the agreed price, the purchase price and the shortfall.
- **FR-011**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace, in
  the same shape as every existing class.
- **FR-012**: Each entry MUST disappear as soon as its condition ends, without acknowledgement
  or any other manual step.
- **FR-013**: The explanation of an entry MUST re-derive the current condition, and a
  malformed, unknown, cleared or foreign identity MUST produce the same not-found response the
  queue already returns.
- **FR-014**: The class MUST be declared in the closed catalog with an authority reference,
  named executable evidence, and the description, owner and clearing path every class carries.
  Its guidance MUST say plainly that it compares an agreed sales price with an agreed purchase
  price and is not accounting margin.
- **FR-015**: Every surface that consumes the queue MUST receive the class through the existing
  shared list and explanation contract.
- **FR-016**: The queue MUST remain deterministically ordered for identical data.

### Domain and Traceability Requirements

- **DR-001**: No schema changes. Sales order lines, purchase price lists and their entries all
  exist.
- **DR-002**: The class MUST be derived at read time from DocumentLines and price lists the
  tenant already owns, and MUST store nothing.
- **DR-003**: Neither price MUST be recomputed, which Constitution principle VIII requires and
  which is the reason this feature is possible at all.
- **DR-004**: Traces MUST reach their records by opaque identity and MUST NOT restate business
  fields.
- **DR-005**: Every read, derivation and explanation MUST be tenant-scoped, including the
  price-list lookup.
- **DR-006**: No cause is introduced; the closed cause vocabulary is untouched.

### Key Entities *(when data is involved)*

- **DocumentLine (sales order)**: The agreed sale, carrying the price a person decided.
- **PriceList (purchase) and PriceListEntry**: The company's own statement of what an item
  costs it.

## Success Criteria *(mandatory)*

- **SC-001**: A company that keeps purchase prices is told when it agrees to sell below them.
- **SC-002**: No figure in the comparison is one Reality worked out.
- **SC-003**: A company that keeps no purchase prices sees nothing, rather than a guess.
- **SC-004**: An operator reading the class is told it is not accounting margin.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- The value of this class depends entirely on a company maintaining a default purchase price
  list. Many will not, and for them it is silent. That is the honest shape of a feature built
  from received values rather than computed ones, and it is stated here rather than discovered.
- The default purchase price is a reasonable stand-in for what an item costs. It ignores
  freight, duty and handling, so a line agreed slightly above it may still lose money and will
  not be reported. The class understates rather than overstates, which is the safer direction.
- Spec 076's price comparison remains a different question: it asks whether an invoice matches
  the agreement, this asks whether the agreement was sound.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | derivation test |
| FR-002 | US1 scenario 1 | stated-prices test |
| FR-003 | US1 scenario 5 | validity-at-agreement test |
| FR-004 | US1 scenario 4 | no-purchase-price test |
| FR-005 | US1 scenario 2 | at-cost test |
| FR-006 | Edge cases | zero-price test |
| FR-007 | US1 scenario 6 | purchase-line exclusion test |
| FR-008 | Edge cases | currency and unit test |
| FR-009 | Edge cases | itemless line test |
| FR-010 | US1 scenario 1 | causal values test |
| FR-011 | US1 scenario 1 | entry shape and trace test |
| FR-012 | US1 scenario 3 | clearing test |
| FR-013 | Edge cases | explanation not-found parity test |
| FR-014 | US1 scenario 1 | catalog coverage and guidance gate test |
| FR-015 | US1 scenario 1 | shared list and explanation contract test |
| FR-016 | US1 scenario 1 | deterministic ordering test |
| DR-001 | — | no migration added |
| DR-002 | US1 scenario 3 | read-time derivation test |
| DR-003 | US1 scenario 1 | stated-prices test |
| DR-004 | US1 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US1 scenario 1 | existing cause-vocabulary drift gate |
