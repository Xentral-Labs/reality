# Feature Specification: Every business company knows its own business partner

**Feature Branch**: `289-costing-ready-companies`
**Created**: 2026-09-27
**Status**: Draft
**Language**: English
**Input**: The owner prioritized the follow-ups from the spec 282 and 284 live walk-throughs. A newly
created business company cannot finish its first cost review because the company itself is not
recorded as a business partner.

## Context and Intent

### Problem

Stock has an owner. The cost review draft (spec 282) takes that owner from the tenant's
business partner with the role `company` (`services/cost_review_draft.py`, `_company_parties`).
When there is none, the draft reports `company_party_missing`, and the person has to know to go
to master data and record their own company as a business partner before any stock value or DB1
can be proven.

Most company creation paths already create that partner. The Storyline companies, the playground
lessons and the international demo profile do ("Harbor Supply"), and so does Demo Data when it
connects to an empty sandbox. **An ordinary business company does not.** It is created with its
tenant and finance accounts only (`services/company_setup.py`, `core.create_tenant`). Every real
company therefore meets this hurdle at its first cost review. The 282 walk-through hit it
("Company party missing"). The sales order file import has the same need: it refuses when the
company has no company partner, or more than one ("Orders require exactly one company party in
the tenant.").

### Scope

- **At creation:** creating an ordinary business company also records the company itself as a
  business partner with the role `company`, named as the person named the company. The same
  confirmed creation request carries it, and its evidence is that request.
- **Existing companies:** where the cost review draft reports `company_party_missing` and no
  company partner exists, it offers one action, "Record my company as a business partner",
  prefilled with the company's name. The action is a proposal that an owner confirms in
  Decisions, and it records through the master data service. After confirmation the draft uses that partner.
- **Guidance:** the resolution guidance for `company_party_missing` points to this action
  instead of a general instruction to open master data.

### Non-Goals

- **Empty sandboxes and demo or practice companies.** They keep today's behaviour. Demo Data
  only connects to a sandbox without business partners and adds its own company partner (Harbor
  Supply). Giving empty sandboxes one would break that connection (owner decision 2026-09-27).
- **Backfilling existing companies by migration.** No partner is recorded without a person
  confirming it (owner decision).
- **Several company partners.** A company that has two or more keeps today's behaviour: the
  draft asks which one owns the stock.
- **Renaming.** The partner is master data. A later change of the company name does not rename
  it, and the person edits it in master data as any other partner.
- **Demo opening costs.** The draft reports `opening_cost_missing` for demo opening stock,
  whose source states a unit cost rather than a total. This affects nobody in practice: the demo
  seed confirms its cost reviews itself, and demo companies refuse cost decisions. It stays a
  known limitation (owner decision).

### Existing Contracts

- `docs/features/company-setup-demo.md` and spec 146: company creation, request replay and the
  durable completion marker, Demo Data connection rules.
- Spec 282: the cost review draft and `company_party_missing`.
- Spec 279: resolution guidance (`config/resolution_guidance.json`).
- `docs/features/master_data.md`: business partner creation through proposals.
- Constitution I (Source → Evidence → Reality), IV (shared services), X (mutating chat actions
  require confirmation).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A new company is ready for costing (Priority: P1)

An owner creates the business company "Lampenhaus Berg GmbH". Master data already lists
"Lampenhaus Berg GmbH" as a business partner with the role company. At the first cost review the
draft names it as the owner of the stock and does not ask for a company partner.

**Why this priority**: Every new real company meets the hurdle today. It is the first step
towards a proven stock value.

**Independent Test**: Create a business company through the shared creation service. Exactly
one business partner with the role `company` exists, named as the company, with the creation
request as its source. A cost review draft for one of its items does not report
`company_party_missing`.

**Acceptance Scenarios**:

1. **Given** an owner creating a business company named "Lampenhaus Berg GmbH", **When** the
   creation is confirmed, **Then** the company has exactly one business partner with the role
   company and that name, created with the company in the same step.
2. **Given** the same creation request replayed, **When** it completes again, **Then** there is
   still exactly one company partner.
3. **Given** an empty sandbox or a demo company being created, **When** it completes, **Then**
   its business partners are exactly as today.

---

### User Story 2 - An existing company records itself in one step (Priority: P1)

An owner of a company created before this change opens a cost review draft. The draft says the
company is not recorded as a business partner and offers "Record my company as a business
partner", prefilled with the company name. The owner reviews and confirms the proposal. The
draft then shows the company as the owner of the stock.

**Why this priority**: Existing companies are the ones using costing today.

**Independent Test**: In a company without a company partner, the draft's `company_party_missing`
input offers the action. Confirming the resulting proposal creates the partner through the same
master data service as the master data form, and a new draft no longer reports the input.

**Acceptance Scenarios**:

1. **Given** a company without a company partner, **When** the cost review draft is shown,
   **Then** it offers "Record my company as a business partner" with the company name prefilled.
2. **Given** the offered action, **When** the owner confirms the proposal, **Then** the partner
   is created with the role company, and the draft uses it as the stock owner.
3. **Given** the proposal not yet confirmed, **When** the draft is shown again, **Then** it names
   the waiting proposal instead of offering a second one.
4. **Given** a company with two company partners, **When** the draft is shown, **Then** it asks
   which one owns the stock, as today, and offers no creation.

---

### User Story 3 - Chat and guidance offer the same step (Priority: P2)

In the chat, an owner asks to prepare the cost review for an item. The agent reports that the
company is not recorded as a business partner and proposes recording it, and the owner confirms
it as any other proposal. The item's cost explanation offers the same step.

**Why this priority**: The chat and the cost explanation are the other two ways people reach
the draft (spec 279/282), and they must not fall back to a general instruction.

**Independent Test**: The resolution guidance for `company_party_missing` names the action.
Through MCP, the draft's open input carries the same prefilled proposal arguments as in the web.

**Acceptance Scenarios**:

1. **Given** a company without a company partner, **When** the guidance is read, **Then** the
   step for `company_party_missing` offers the prefilled action in the web and a chat prompt.
2. **Given** the chat, **When** the agent proposes the partner, **Then** it creates a
   confirmation-required proposal and records nothing before confirmation.

### Edge Cases

- **Company name that already exists as a customer or supplier:** the action still creates a
  separate company partner. Merging partners is not part of this feature.
- **A company partner created in master data meanwhile:** the draft uses it, and a waiting
  proposal from the action is refused as no longer needed when it is confirmed.
- **Company name changed after creation:** the prefilled name is the current company name.
- **Practice and demo companies:** the action is not offered; they refuse cost decisions anyway.
- **Tenant boundary:** the partner, the proposal and the draft stay within the tenant.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Creating an ordinary business company MUST create exactly one business partner
  with the role `company`, named as the company, in the same transaction as the company.
- **FR-002**: Replaying a company creation request MUST NOT create a second company partner.
- **FR-003**: Empty sandboxes, demo, practice and Storyline companies MUST keep their current
  business partners on creation.
- **FR-004**: When a company has no company partner, the cost review draft's `company_party_missing`
  input MUST offer a prefilled proposal that records the company as a business partner with the
  role company, named as the company.
- **FR-005**: The offered action MUST record through the same master data service as the
  master data form, after the same proposal review and confirmation as any other decision.
  Nothing is recorded before confirmation.
- **FR-006**: While such a proposal waits for confirmation, the draft MUST name it instead of
  offering another. Once a company partner exists, confirming a waiting proposal MUST be refused
  as no longer needed.
- **FR-007**: The resolution guidance for `company_party_missing` MUST offer the action in the
  web and as a chat prompt, and MCP and chat MUST receive the same prefilled arguments.
- **FR-008**: A company with two or more company partners MUST keep today's choice in the draft.

### Domain and Traceability Requirements

- **DR-001**: The company partner created with a company MUST carry a SourceRecord that states
  the name as given in the creation request. It is recorded, not derived.
- **DR-002**: No new table or column. The partner is an ordinary Party with a PartyRole.
- **DR-003**: Web, chat and MCP MUST use the same shared services for creation and the proposal.
  No adapter creates a party directly.
- **DR-004**: No existing company is changed without a person confirming the proposal.

### Key Entities

- **Company business partner**: the Party with the role `company` that represents the company
  itself and owns its stock.

## Success Criteria *(mandatory)*

- **SC-001**: A business company created after this change reaches a draft for its first cost
  review without `company_party_missing`, and nobody opens master data for it.
- **SC-002**: An existing company without a company partner records one from the draft with one
  confirmation, and the next draft uses it.
- **SC-003**: Sandbox, demo and Demo Data connection behave exactly as before (existing suites
  stay green).

## Assumptions and Dependencies

- The company name at creation is the name the person gives in the creation request
  (`services/company_setup.py`).
- The draft's owner lookup (`_company_parties`, role `company` or type `company`) stays as it is.
- The master data proposal tool `party_create` (`reference_workspace.prepare_reference`) accepts
  a party with the role company.
- The plan lists every path that creates an ordinary business company (company setup, the legacy
  company route and the CLI) and decides which of them count as ordinary.

## Open Questions

None. Decided by the owner on 2026-09-27:
- only the company business partner is in scope, and the demo opening cost is dropped;
- existing companies get it through one confirmed action in the draft, not a migration;
- empty sandboxes keep today's behaviour.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 1 | company setup service test: one company partner, named as the company |
| FR-002 | US1 2 | replay test |
| FR-003 | US1 3 | sandbox, demo, practice, Storyline creation tests unchanged |
| FR-004 | US2 1 | draft test: open input carries the prefilled proposal |
| FR-005 | US2 2 | proposal and confirmation test through the master data service |
| FR-006 | US2 3, Edge cases | waiting proposal named; stale confirmation refused |
| FR-007 | US3 1–2 | guidance catalog test; MCP parity test |
| FR-008 | US2 4 | draft test with two company partners |
| DR-001 | US1 1 | SourceRecord of the company partner states the requested name |
| DR-002 | — | plan schema review: no migration |
| DR-003 | US3 | MCP and web parity |
| DR-004 | US2 | no party created before confirmation |
