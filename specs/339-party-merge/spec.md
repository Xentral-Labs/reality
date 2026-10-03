# Feature Specification: Merging Duplicate Business Partners

**Feature Branch**: `339-party-merge`

**Created**: 2026-10-03

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 3. Close the capability gap behind the journeys L10 and O02 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

The same customer or supplier often exists twice: a shop guest order creates one business partner, the later customer account another, or a clerk creates a partner that already existed. Reality cannot say that two business partners are one. Their orders, invoices, payments and balances stay apart, the credit check sees only half of what the customer owes, and new orders keep landing on the duplicate.

| Journey | Title | Status today |
|---|---|---|
| L10 | Guest order, later with an account (duplicate party) | missing |
| O02 | Two parties merged as duplicates | missing |

### Scope

- A reviewed merge that states one business partner is a duplicate of another, the survivor, with a reason.
- Every history stays where it was stated: documents, promises, ledger entries and sources keep naming the duplicate. Reads that answer for the survivor add the duplicate's records at read time.
- The duplicate is no longer active, so pickers and active lists stop offering it.
- New shop orders and imported rows that name the duplicate land on the survivor.

### Non-Goals

- Undoing a merge. A wrong merge is a follow-up (an append-only unmerge record).
- Rewriting stated records to name the survivor (Constitution I and VIII).
- Settling one party's unused credit against the other party's invoice. A posting group names one party; a cross-party settlement needs its own reviewed design.
- Finding duplicates automatically. A person names the two partners.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-03

The owner delegated these decisions to the recommended options.

- Q: Is the merge a rewrite or a record? → A: A record. One append-only merge row per duplicate names the survivor, the reason and the confirming proposal. Nothing already stated is changed, except that the duplicate becomes inactive through the existing lifecycle event.
- Q: Which reads answer for the survivor with the duplicate's history? → A: The business partner detail and inspector, the customer and supplier balances, and the credit exposure. Each adds the records of every party merged into the one asked for, at read time. The duplicate's own detail still opens and names its survivor.
- Q: Where does new intake go? → A: To the survivor. A shop order whose import context names the duplicate is recorded for the survivor, and a file import row that matches the duplicate resolves to its survivor.
- Q: Can a merged party be merged further, or be a survivor? → A: No chains. A party already merged cannot be merged again or be chosen as a survivor; the refusal names the survivor to use instead. A survivor may absorb several duplicates.
- Q: What must the survivor and duplicate satisfy? → A: Both are business partners of the same company and distinct; the survivor is active. The survivor already carries every role the duplicate has (customer, supplier), so every promise and ledger entry of the duplicate reads correctly under it. The company's own business partner is never merged. A duplicate with an open delivery hold is refused until the hold is released, so no hold is silently dropped.
- Q: What about a duplicate's credit in another currency or its own credit limit? → A: The survivor's limit and currency apply. The duplicate's records in another currency are named as not counted, as for any customer (spec 298).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Guest Order, Later with an Account (Priority: P1)

As a sales clerk, I merge the guest business partner a shop order created into the customer's account, so that the customer's history, balance and credit read as one and the next order lands on the account.

**Independent Test**: A shop order under a guest partner is invoiced; the guest is merged into the account partner; the account's detail lists the guest order and invoice, its balance includes the guest's open invoice, the guest is inactive, and the next shop order whose context still names the guest lands on the account.

**Acceptance Scenarios**:

1. **Given** a guest partner with an open invoice and an account partner with its own order, **When** the guest is merged into the account, **Then** the account's detail and balance include both histories and the guest's invoice keeps naming the guest.
2. **Given** the merge, **When** a shop order arrives whose import context names the guest, **Then** the order is recorded for the account.

### User Story 2 - Two Partners Merged as Duplicates (Priority: P1)

As a bookkeeper, I merge a business partner created twice, so that both histories are kept and read under one partner.

**Independent Test**: Two customer partners with orders and invoices; the merge is proposed, reviewed and confirmed; the survivor's detail, balance and credit exposure include both, the duplicate's detail names the survivor, and refused merges (self, chain, missing role, open hold, company) change nothing.

**Acceptance Scenarios**:

1. **Given** two partners with history, **When** one is merged into the other, **Then** both histories read under the survivor and nothing stated changed.
2. **Given** a merged duplicate, **When** someone tries to merge it again or merge into it, **Then** the refusal names the survivor.

### Edge Cases

- Tenant isolation: a partner of another company is not found, and nothing crosses companies.
- A stated value is recorded as stated and never recomputed (Constitution VIII); the merge changes no amount.
- The duplicate's history in another currency is not counted in the survivor's exposure but is named.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A person MUST be able to state, through the review, that one business partner is a duplicate of another, with a reason; the confirmation records an append-only merge and makes the duplicate inactive.
- **FR-002**: The business partner detail, the balances and the credit exposure of a survivor MUST include the records of every partner merged into it, at read time; the duplicate's detail MUST name its survivor.
- **FR-003**: New shop orders and file import rows that name a merged partner MUST land on its survivor.
- **FR-004**: The merge MUST refuse a partner merged into itself, an already merged partner on either side, a survivor that is inactive or lacks a role of the duplicate, the company's own partner and a duplicate with an open delivery hold.
- **FR-005**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-006**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: L10 and O02 each have a passing business story with positive controls.
- **SC-002**: L10 and O02 are `supported` in the Business Journey Guide.
- **SC-003**: The business partner detail and balance reads add a bounded number of statements for merged partners, independent of how many records the duplicate holds.

## Assumptions and Dependencies

- Builds on business partner roles and holds, the party balances of spec 170, the credit exposure of spec 298 and the Shopify and file interpretations.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-004 | US2 | `tests/test_party_merges.py` |
| FR-002 | US1, US2 | `tests/test_party_merges.py`, `tests/scenarios/test_catalog_party_merges.py` |
| FR-003 | US1 | `tests/scenarios/test_catalog_party_merges.py` (L10) |
| FR-005 | All | `tests/test_party_merge_adapters.py` |
| FR-006, SC-001, SC-002 | US1, US2 | Catalog tests and Guide questions |
| SC-003 | US2 | Statement-count test in `tests/test_party_merges.py` |
