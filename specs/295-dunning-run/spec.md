# Feature Specification: Dunning Run and Escalation

**Feature Branch**: `295-dunning-run`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 1. Close the capability gap behind the partial journeys N04 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Dunning notices at levels 1 to 3 with a fee can only be created one by one. There is no run over overdue open items, no escalation from one level to the next and no handover to collection, so every B2B company has to track reminders outside Reality.

| Journey | Title | Status today |
|---|---|---|
| N04 | Dunning in three levels, then collection | partial |

### Scope

- A reviewed dunning run proposes notices for overdue open items by level.
- A notice escalates to the next level after a stated waiting period.
- A final level can hand an item to collection as a recorded decision.
- Blocked items (paid or credited after the run was prepared, unapplied customer credit, already in collection) are left out and named.
- One dunning schedule per company: three levels, each with a waiting period and a fixed fee.
- A person starts the run over all customers or selected customers, reviews the proposed notices and confirms them.
- After the last level a person hands items to collection; the customer gets a delivery hold with the reason "collection".

### Non-Goals

- Sending letters or emails.
- Interest calculation.
- Integration with a collection agency.
- Anything that requires a document status field (Constitution II).
- Scheduled or automatic runs; a run is always started and confirmed by a person.
- Schedules per payment term or per party group.
- Percentage or amount-dependent fees; the fee is the fixed amount the schedule states.
- A dispute record: Reality has none today, so disputed items cannot be excluded by the run; a clerk deselects them in the review.
- Taking an item back from collection. The delivery hold is released with the existing release action.

## Clarifications

### Session 2026-09-29

- Q: Where are dunning levels, fees and waiting periods configured? → A: One schedule per company: levels 1 to 3, each with a waiting period in days and a fixed fee.
- Q: Does a run cover all customers or a selection, and who starts it? → A: A person starts the run over all or selected customers, reviews the proposals and confirms. There is no scheduled run.
- Q: Which record states "handed to collection"? → A: A new confirmed collection handover after the last level. The item is no longer dunned, and the customer gets a party delivery hold with the reason "collection" through the existing hold.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dunning Run and Escalation (Priority: P1)

As a receivables clerk, I run dunning over all overdue items and confirm the proposed notices, so no overdue invoice is forgotten.

**Why this priority**: Rank 1 of the sales-gap roadmap: it comes up in almost every evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** overdue open items at different ages, **When** a dunning run is prepared, **Then** each item is proposed at the level its last notice and waiting period allow, and nothing is recorded before confirmation.
2. **Given** an item paid or credited after the run was prepared, **When** the run is confirmed, **Then** that item is skipped and named.
3. **Given** an item at the last level, **When** the clerk hands it to collection, **Then** the handover is a recorded decision with a reason, the item is no longer proposed by later runs and the customer has a delivery hold with the reason "collection".
4. **Given** no dunning schedule, **When** a run is prepared, **Then** it is refused with a coded reason that names the missing schedule.
5. **Given** a run limited to one customer, **When** it is prepared, **Then** no other customer's items appear.
6. **Given** an item whose last notice was reversed, **When** a run is prepared, **Then** its level is derived from the remaining notices only.

### User Story 2 - Maintain the company dunning schedule (Priority: P1)

As a finance owner, I state the waiting period and fee for each of the three levels once, so every run applies the same rules.

**Why this priority**: The run cannot propose a level or a fee without it.

**Independent Test**: Set the schedule through the reviewed command, read it back, change it and prepare a run that uses the new values.

**Acceptance Scenarios**:

1. **Given** no schedule, **When** the owner confirms three levels with waiting days and fees, **Then** the schedule is recorded with its source and a later run uses exactly these values.
2. **Given** a schedule, **When** it is changed, **Then** notices already recorded keep the level and fee they were recorded with.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A customer with invoices in two currencies receives one notice per currency and level.
- A customer with invoices at different levels receives one notice per level.
- A partly paid invoice is dunned for its remaining open amount; the notice keeps linking the invoice.
- Two runs confirmed one after the other for the same date do not dun an item twice; the second skips it and names the reason.
- An item already handed to collection is never proposed again, even after the schedule changes.
- A zero fee at a level records a notice without a fee charge, as spec 247 does.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A dunning run MUST propose notices only for overdue, unsettled open customer items and MUST record nothing before confirmation.
- **FR-002**: Each proposed notice MUST state its customer, currency, level, fee, items with their open amounts and, per item, the previous notice and the waiting period that allowed the level.
- **FR-003**: Escalation MUST follow the company schedule: level 1 once an item is overdue by the level 1 waiting period, and each further level once the waiting period of that level has passed since the item's last non-reversed notice.
- **FR-004**: Handing items to collection MUST be a reviewed decision with a reason, allowed only for open items whose last non-reversed notice is at level 3, and MUST stop further notices for them.
- **FR-007**: A company MUST have at most one dunning schedule with exactly levels 1 to 3, each with a non-negative waiting period in days and a non-negative fee; it MUST be set through a reviewed command and kept with its source.
- **FR-008**: A person MUST start a run for a stated date over all customers or a stated selection of customers, and MAY deselect items in the review.
- **FR-009**: On confirmation, the run MUST re-derive every proposed item and record notices only for items still eligible at the proposed level; every other item MUST be skipped and named with a coded reason (paid, level changed, in collection, credit available). All recorded notices of one run MUST be one transaction.
- **FR-010**: The run MUST leave out and name items of customers with unapplied customer credit in the same currency.
- **FR-011**: A collection handover MUST place a party delivery hold with the reason "collection" in the same transaction, unless the customer already has an active delivery hold.
- **FR-012**: The run preview, the schedule, notices and handovers MUST be readable through tenant-scoped read tools and explain their link to items, notices and the confirmed request.
- **FR-005**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-006**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority. An item's current level is derived from its non-reversed notices; no level or "in collection" field is added to documents.
- **DR-003**: Notices recorded by a run MUST be ordinary spec 247 notices with the same document, fee posting, event and reversal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.
- **SC-003**: A run over 3 customers at three different levels is prepared, reviewed and confirmed in one reviewed action, and the business story checks every notice, fee and skipped item.

## Assumptions and Dependencies

- Created as a short draft from the sales-gap roadmap; clarified with the owner on 2026-09-29.
- Builds on spec 247 (manual notices, fee posting, reversal) and on the existing party delivery hold.
- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003, FR-008–FR-010 | US1 | Run service tests and the N04 business story (planned) |
| FR-004, FR-011 | US1 | Collection handover service tests and the N04 business story (planned) |
| FR-007 | US2 | Schedule service tests (planned) |
| FR-005, FR-012, DR-001–DR-003 | All | Adapter, isolation and catalog tests and diff review (planned) |
| FR-006, SC-001–SC-003 | US1 | Catalog tests and Guide questions (planned) |
