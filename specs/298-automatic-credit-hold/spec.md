# Feature Specification: Automatic Credit Hold

**Feature Branch**: `298-automatic-credit-hold`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 1, rank 4. Close the capability gap behind the partial journeys C07, C08, R08 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

The credit-limit finding exists, but it holds nothing. It counts open invoices only, ignoring the new order, open orders and available credits, and it names all open invoices rather than the overdue ones. A hold with the reason `credit_check` exists, but nothing places it, and releasing a hold records who released it but not why.

| Journey | Title | Status today |
|---|---|---|
| C07 | Credit limit exceeded: order held, released by a person | partial |
| C08 | Limit exceeded by overdue items, not by order value | partial |
| R08 | Customer is also a supplier, with an overdue receivable, an open credit and a new order above the credit limit | partial |

### Scope

- One shared credit exposure per customer: open invoices plus the value of open, not yet invoiced orders, minus available credits, in the customer's own currency.
- A new order that would take the exposure past the limit is held at entry, whatever path records it, with a hold that names the facts.
- The hold names the overdue items and, for a customer who is also a supplier, the open payables, without netting them.
- A company owner releases a credit hold with a stated reason, recorded with the person.
- The credit-limit finding reads the same exposure.

### Non-Goals

- Credit insurance, scoring or external credit checks.
- Netting receivables against payables (journey O06); payables are named, not subtracted.
- Converting between currencies; exposure in another currency than the customer's own is named, not counted.
- Holding orders already recorded when a limit is lowered; the finding reports them.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-09-30

- Q: When does the credit hold apply? → A: At order entry. A new order whose value would take the exposure past the limit gets a `credit_check` hold on its promises at once, whether it is entered by hand, by chat or arrives from Shopify or a file; nothing is reserved or shipped until a person releases it.
- Q: What counts towards the exposure? → A: Open invoices plus the value of open orders not yet invoiced, the new one included, minus available credits (credit notes and unallocated payments), in the customer's currency, each named in the reason.
- Q: Do payables to the same party reduce the exposure? → A: No. They are named in the reason but not netted; netting needs an agreement (O06).
- Q: Who may release a credit hold? → A: A company owner, with a mandatory reason recorded with the person. Other holds keep today's rule.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An order over the limit is held and released by a person (Priority: P1)

As a sales clerk, I see a new order held because the customer would be over their limit, with the reason spelled out, and an owner releases it with a reason.

**Why this priority**: Rank 4 of the sales-gap roadmap: it comes up in almost every evaluation.

**Independent Test**: A business story per journey, through the reviewed tools and the shop intake, with a positive control for every "nothing held" assertion.

**Acceptance Scenarios**:

1. **Given** a customer with a limit of 1,000 and 700 open, **When** an order of 400 is entered, **Then** its promises are held with `credit_check`, and the reason names the limit, the 700 open, the 400 ordered and the resulting exposure.
2. **Given** the same customer, **When** an order of 200 is entered, **Then** nothing is held (positive control for 1).
3. **Given** a held order, **When** an owner releases it with a reason, **Then** the release records the person and the reason, and the order can be reserved and shipped.
4. **Given** a held order, **When** a member who is not an owner, or an owner without a reason, tries to release it, **Then** the release is refused with a code.

---

### User Story 2 - The hold names what caused it (Priority: P1)

As a credit manager, I see which overdue items and which offsets are behind a hold.

**Acceptance Scenarios**:

1. **Given** a customer whose open invoices include two overdue ones, **When** an order is held, **Then** the reason names the two overdue invoices and their amounts, separately from the ones not yet due (C08).
2. **Given** a customer with an open credit note and an unallocated payment, **When** the exposure is read, **Then** both reduce it and both are named.
3. **Given** a customer who is also a supplier with an open supplier invoice, **When** an order is held, **Then** the reason names the payable without subtracting it (R08).
4. **Given** open orders not yet invoiced, **When** a new order is entered, **Then** their value counts towards the exposure, and an invoiced order is counted once, as its invoice.

---

### User Story 3 - One exposure everywhere (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a customer over the limit, **When** the credit-limit finding is read, **Then** it reports the same exposure the hold used, and names the overdue items.
2. **Given** a customer without a limit (0), **When** any order is entered, **Then** nothing is held.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- An order in another currency than the customer's own is not converted: it is neither counted nor held, and the reason of any later hold names it as not counted.
- A cancelled order, or the cancelled part of one, no longer counts.
- Replaying an order intake does not place a second hold.
- Releasing a credit hold releases only that hold; other holds on the promise stay.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII); the exposure is derived at read time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The credit exposure MUST be open invoices plus the value of open, not yet invoiced orders, minus available credits, in the customer's currency, derived at read time from Reality; each part MUST be shown.
- **FR-002**: A new order whose value would take the exposure past a positive limit MUST have its promises held with the reason `credit_check` at entry, through every order entry path, until released.
- **FR-003**: The hold MUST name the limit, the exposure parts, the overdue invoices with their amounts and, for a customer who is also a supplier, the open payables, which MUST NOT reduce the exposure.
- **FR-004**: Only a company owner MUST be able to release a credit hold, and only with a stated reason, recorded with the person; other holds keep their current rule.
- **FR-005**: The credit-limit finding MUST read the same exposure and name the overdue items.
- **FR-006**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-007**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: The exposure MUST be derived at read time and never stored as a new authority; the hold stores only what the decision was based on, for the record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: C07, C08 and R08 each have a passing business story.
- **SC-002**: C07, C08 and R08 are `supported` in the Business Journey Guide.
- **SC-003**: The hold and the credit-limit finding report the same exposure for the same customer and instant.

## Assumptions and Dependencies

- Builds on commitment holds (`credit_check`), the shared open-item derivation, available credits, the decision trail (spec 263) and the order entry paths (manual, reviewed tool, Shopify, file import).
- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.

## Open Questions

None. The owner decided the scope on 2026-09-30.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, DR-002 | US2 2–4, US3 | Exposure service tests (planned) |
| FR-002 | US1 1–2 | Hold-at-entry tests per entry path (planned) |
| FR-003 | US2 1, 3 | Hold reason tests (planned) |
| FR-004 | US1 3–4 | Release tests (planned) |
| FR-005 | US3 1 | Finding tests (planned) |
| FR-006 | All | Adapter tests and diff review (planned) |
| FR-007, SC-001, SC-002 | All | Business stories, catalog tests and Guide questions (planned) |
