# Feature Specification: Serving Backorders on Receipt

**Feature Branch**: `305-backorder-allocation`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 11. Close the capability gap behind the partial journeys B08, H16, B07, R02, G13, B09 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

A receipt reserves nothing by itself, and nothing says which waiting order is served first. A customer-specific purchase is not reserved for its order on arrival, and nothing answers from when an item can be promised again. A partial receipt also leaves each assigned backorder counting its full assigned supply.

Since #205 a cancelled customer promise already ends its supply assignments at read time (`supply_assignments._effective_rows`). What G13 and R02 lack is a business story that proves it.

| Journey | Title | Status today |
|---|---|---|
| B08 | Receipt resolves backorders | partial |
| H16 | Receipt for a customer-specific purchase (cross-docking) | partial |
| B07 | Stock only on order (open purchase) | partial |
| R02 | Two customers wait for one item; under-delivery; key customer re-reserved; the other cancels | partial |
| G13 | Purchase reduced after the customer order was cancelled | partial |
| B09 | Receipt covers only part of the backorders | partial (added by spec 314) |

### Scope

- A reviewed step, "serve backorders", that proposes reservations for waiting customer promises of an item at a location in a stated serving order. It is offered right after a confirmed receipt and on demand for an item.
- The serving order: first the promises assigned to the received purchase, in the order of their assignment. Then the other waiting promises, by due date, then by when they were promised.
- A dated available-to-promise read per item, naming each open purchase and its date.
- Assigned supply split, at read time, into what has arrived and what is still to come.
- Business stories for B08, H16, B07, R02, G13 and B09, including the cancellation that already ends an assignment.

### Non-Goals

- Reserving without review, also for cross-docking.
- A stated priority per promise, or priority by customer value.
- Re-planning or reducing the purchase itself after a cancellation (the purchase amendment stays its own step).
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

- Q: What is the serving order? → A: Assigned first, then due date.
  1. The promises the received purchase is assigned to, in the order the assignments were made.
  2. Every other waiting promise of the item, by due date, then by when it was promised.

  The person may change quantities or drop lines before confirming. A promise counts as waiting when it is an open customer delivery for the item with an open quantity that is not yet reserved.
- Q: Where are reservations proposed, and what about cross-docking (H16)? → A: In a separate reviewed step, "serve backorders". The receipt confirmation offers it right away, and it can be opened for an item at any time. Cross-docking is the same case: the assigned order stands first. Nothing is reserved before a person confirms.
- Q: What does available-to-promise look like (B07)? → A: A read per item, at read time:
  - what is free now: physical stock less reservations, blocks and the unreserved open demand already waiting;
  - then each open purchase with its due date and what stays free of it after its customer assignments, as a running total, for example "from 12 Oct another 8 pcs (purchase X)".

  It is offered as a read tool (MCP, Web, CLI) and shown on the item in the warehouse.
- Q: How is assigned supply split after a partial receipt (B09)? → A: At read time, in assignment order. What a purchase has received covers its assignments in the order they were made. Each customer promise thus shows "arrived" and "still to come" of its protecting supply, with no new stored record. The promises left with supply still to come are named.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Serving Backorders on Receipt (Priority: P1)

As a warehouse lead, I receive goods and confirm which waiting orders they go to.

**Why this priority**: Rank 11 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** two waiting orders and a receipt that covers one (B08), **When** "serve backorders" is reviewed, **Then** the earlier-due order is proposed first. Nothing is reserved until a person confirms.
2. **Given** a purchase assigned to one customer order (H16), **When** it is received and "serve backorders" is reviewed, **Then** the assigned order stands first, even if another order is due earlier.
3. **Given** a receipt of 4 against assignments of 3 + 3 + 3 (B09), **When** coverage is read, **Then** the first customer shows 3 arrived, the second 1 arrived and 2 to come, and the third 3 to come.
4. **Given** no free stock and an open purchase due on 12 Oct (B07), **When** available-to-promise is read, **Then** it names that purchase, its date and what stays free of it.
5. **Given** two customers assigned to one purchase, an under-delivery, and one customer cancelling (R02, G13), **When** coverage and "serve backorders" are read, **Then** the cancelled promise has no assignment left and the remaining customer is served first.

### User Story 2 - Promise From Open Purchases (Priority: P2)

As a sales clerk, I ask when an item can be promised and see the purchase and date the answer relies on.

**Acceptance Scenarios**:

1. **Given** free stock of 5 and a purchase of 10 due 12 Oct with 4 assigned to a customer, **When** available-to-promise is read, **Then** it shows 5 now and from 12 Oct a total of 11, naming the purchase.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII). The split into arrived and to come and the available-to-promise answer are read-time observations and are never stored.
- "Serve backorders" never proposes more than is available at the location, and never more than a promise still needs.
- A confirmation after the stock or the promises changed since the review is refused, like other reviewed delivery actions.
- A purchase that is overdue still appears in available-to-promise with its stated date, marked overdue.
- Blocked stock (spec 304) is not available to serve.
- A promise in another unit (spec 301) is served in its held stock unit. A promise recorded before spec 301 and still held in its line's unit is not served and not counted in available-to-promise; it is named apart.
- Due dates are the stated ones, revisions included.
- A promise under a hold, or whose customer is under a delivery hold, is listed apart and not served.
- Supply still to come counts for a promise only up to what it still needs; once it is reserved or delivered, the rest of its assignment is promisable again.
- Lot- and serial-tracked items are not served by this step; they are reserved lot by lot.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: "Serve backorders" MUST propose reservations for the waiting promises of an item at a location in the stated serving order. It is offered after a confirmed receipt and on demand, and nothing is reserved before confirmation.
- **FR-002**: A cancelled customer promise MUST end its supply assignments. This already holds since #205; this feature proves it in the R02 and G13 stories.
- **FR-003**: Available-to-promise MUST name the purchase and date each later quantity relies on.
- **FR-006**: Supply coverage MUST split each customer's protecting supply into arrived and still to come, in assignment order, at read time.
- **FR-004**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-005**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Created as a short draft from the sales-gap roadmap; it must be clarified and accepted by the owner before planning.
- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.

## Open Questions

None; see Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003, FR-006 | US1, US2 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
