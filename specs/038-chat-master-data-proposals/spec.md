# Feature Specification: Chat Master Data Proposals

**Feature Branch**: `038-chat-master-data-proposals`
**Created**: 2026-09-02
**Status**: Approved
**Language**: English
**Input**: "Allow Chat to propose manual creation of Parties, Items, and Locations with the same optional source provenance and required fields as the existing application."

## Context and Intent

### Problem

Operators can manually create Parties, Items, and Locations through existing product
interfaces, but Ask Reality cannot prepare the same changes. Its mutation catalog only
offers source ingestion, so a model can incorrectly claim that master data requires an
external source or uploaded evidence. This blocks natural-language setup and contradicts
the established optional-provenance model.

### Scope

- Let an operator ask Chat to prepare creation of one or more Parties, Items, or
  Locations.
- Use the same required fields, defaults, validation, tenant boundary, and optional
  source provenance as the existing master-data lifecycle.
- Show an auditable proposal and require explicit human confirmation before any record
  is created.
- Ensure the Copilot describes manual master-data creation accurately when required
  details are missing.

### Non-Goals

- Adding or changing master-data fields, persistence schema, or identity rules.
- Adding Chat update, deactivate, or reactivate operations.
- Treating Parties, Items, or Locations as Documents, Evidence, or operational Reality.
- Requiring a SourceRecord, source system, external identifier, or uploaded artifact for
  manual creation.
- Building a generic arbitrary-record mutation tool.

### Existing Contracts

- `docs/features/chat.md`
- `docs/WEB_SPEC.md`
- `specs/026-master-data-adapter-parity/spec.md`
- `.specify/memory/constitution.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Propose manual master data creation (Priority: P1)

An operator asks Ask Reality to create a Party, Item, or Location. When all required
business details are present, Chat prepares the exact creation proposal without
requiring source provenance and creates nothing until the operator confirms it.

**Why this priority**: It removes the incorrect import-only limitation while preserving
the mandatory human approval boundary.

**Independent Test**: For each master-data family, submit a complete natural-language
request, inspect the pending proposal, confirm it, and verify that exactly one
tenant-owned record with the proposed canonical values exists and has no SourceRecord.

**Acceptance Scenarios**:

1. **Given** a tenant with no matching master record, **When** an operator requests a
   Party with a name and role, **Then** Chat prepares a Party creation proposal and
   creates nothing before confirmation.
2. **Given** a tenant with no matching master record, **When** an operator requests an
   Item with an SKU and name but no unit, **Then** Chat prepares an Item creation
   proposal using the established `pcs` default and no source requirement.
3. **Given** a tenant with no matching master record, **When** an operator requests a
   Location with a name but no type, **Then** Chat prepares a Location creation proposal
   using the established `warehouse` default and no source requirement.
4. **Given** a pending master-data proposal, **When** the operator explicitly confirms
   it, **Then** the application creates the record through the authoritative shared
   service and returns its opaque identity.
5. **Given** a pending master-data proposal, **When** it is not confirmed or is rejected,
   **Then** no Party, Item, Location, or SourceRecord is created.

### User Story 2 - Collect missing required details (Priority: P2)

An operator gives an incomplete creation request. Ask Reality identifies only the
missing required business details and does not redirect the operator to source
ingestion.

**Why this priority**: A creation tool is useful only when the Copilot can distinguish
required business data from optional provenance.

**Independent Test**: Ask to create each family without one required value and verify
that the response requests that value, makes no proposal, and does not claim that an
artifact or external system is required.

**Acceptance Scenarios**:

1. **Given** a Party request without a name or role, **When** Chat responds, **Then** it
   asks for the missing value and creates no proposal.
2. **Given** an Item request without an SKU or name, **When** Chat responds, **Then** it
   asks for the missing value and creates no proposal.
3. **Given** a Location request without a name, **When** Chat responds, **Then** it asks
   for the name and creates no proposal.
4. **Given** any manual master-data request without provenance, **When** Chat responds,
   **Then** it does not require a source system, external ID, artifact, or Document.

### User Story 3 - Preserve optional source provenance (Priority: P3)

An operator may include a source system and external identifier when the new reference
originates elsewhere. The confirmed creation retains that provenance losslessly through
the existing source mechanism.

**Why this priority**: Manual creation must not remove the existing option to trace
source-backed master references.

**Independent Test**: Prepare and confirm one source-backed proposal for each family and
verify the created record links to the immutable tenant-owned SourceRecord containing
the submitted payload.

**Acceptance Scenarios**:

1. **Given** a complete creation request with both source system and external ID,
   **When** the proposal is confirmed, **Then** the record links to the existing
   immutable source representation.
2. **Given** a request with only one member of the source identity pair, **When** the
   proposal is confirmed, **Then** validation rejects the mutation without partial
   master-data or source writes.

### Edge Cases

- A proposal may contain multiple records; confirmation is all-or-nothing so a failing
  record cannot leave a partially created batch.
- A parent Location or default Location from another tenant is treated as not found.
- Empty or whitespace-only required strings are rejected by authoritative service
  validation.
- Reconfirming an executed proposal cannot duplicate records.
- Optional source provenance requires source system and external ID together.
- A proposed role, item type, tracking type, or relationship outside existing accepted
  values is rejected without bypassing the shared service.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Chat MUST expose proposal capabilities for creating Parties, Items, and
  Locations.
- **FR-002**: A Party creation request MUST require name and at least one established
  role; all other accepted Party values MUST follow the authoritative service contract.
- **FR-003**: An Item creation request MUST require SKU and name, default unit to `pcs`,
  and follow the authoritative service contract for all other accepted Item values.
- **FR-004**: A Location creation request MUST require name, default type to
  `warehouse`, and follow the authoritative service contract for all other accepted
  Location values. A new hierarchy in one batch MUST use proposal-local references
  that resolve to generated opaque parent IDs; names MUST NOT be treated as identity.
- **FR-005**: Source system, external ID, and source payload MUST remain optional for
  all three creation families; Chat MUST NOT require source ingestion or Evidence for a
  manual creation request.
- **FR-006**: Every Chat master-data mutation MUST produce an inspectable pending
  proposal and MUST create no business or source records before explicit confirmation.
- **FR-007**: Explicit confirmation MUST execute the exact proposed values through the
  same authoritative creation services used by existing interfaces and return created
  opaque identities.
- **FR-008**: One request for multiple records MUST be represented by one atomic
  proposal whose confirmation creates all records or none.
- **FR-009**: Incomplete requests MUST result in a concise request for missing required
  values rather than an incorrect source or artifact prerequisite.
- **FR-010**: Proposal listing and metadata MUST clearly identify the master-data family,
  proposed canonical values, and confirmation requirement.
- **FR-011**: The Proposal card MUST label its first action as review when a separate
  confirmation dialog owns the final approve-and-execute action.

### Domain and Traceability Requirements

- **DR-001**: Party, Item, and Location MUST remain tenant-owned operational reference
  identities; this feature introduces no Document, Evidence, Commitment, Reservation,
  Movement, or LedgerEntry.
- **DR-002**: When provenance is supplied, the created master record MUST use its single
  existing shortest link to an immutable SourceRecord; source identity or payload MUST
  NOT be duplicated onto new relationships.
- **DR-003**: Chat, MCP catalog dispatch, proposal execution, CLI, API, and Web MUST
  delegate to the same tenant-scoped application services and MUST NOT perform direct
  ORM writes in the agent or transport layer.
- **DR-004**: Foreign-tenant relationship identities MUST be handled as not found without
  disclosing the foreign record.
- **DR-005**: The feature MUST add no schema fields or alternate master-data service.

### Key Entities *(when data is involved)*

- **Party**: A tenant-owned business actor identified by an opaque ID and one or more
  roles; it may optionally link to source provenance.
- **Item**: A tenant-owned product or service reference identified by an opaque ID and
  business SKU; it may optionally link to source provenance.
- **Location**: A tenant-owned physical or logical place, optionally nested under another
  Location and optionally linked to source provenance.
- **Change Proposal**: An auditable, tenant-owned preview of one exact requested mutation
  that requires explicit human confirmation and cannot be replayed after execution.
- **SourceRecord**: Optional immutable, lossless provenance created only when a complete
  external source identity is supplied.

## Success Criteria *(mandatory)*

- **SC-001**: In acceptance testing, operators can prepare and confirm Party, Item, and
  Location creation from Chat in 100% of complete representative requests without
  providing source provenance.
- **SC-002**: In all incomplete representative requests, Chat identifies the missing
  required business value and never states that an external source or artifact is
  mandatory.
- **SC-003**: Before confirmation and after rejection, acceptance tests observe zero new
  Party, Item, Location, and SourceRecord rows.
- **SC-004**: Multi-record acceptance stories either create every proposed record or
  leave the tenant unchanged.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The existing Party, Item, and Location service validation and defaults remain the
  authoritative contract.
- Existing proposal approval and replay protection remain authoritative.
- A single natural-language request may include one or multiple records of one family;
  mixed-family batches are outside the initial implementation.
- Existing permissions that allow proposal creation govern these new proposal tools;
  execution still requires the separately permissioned confirmation capability.
- The model provider supports structured tool calls.

## Open Questions

No unresolved product questions remain.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-005 | US1 scenarios 1–3; US2 scenarios 1–4 | Catalog schemas and Chat tool regression stories |
| FR-006–FR-007 | US1 scenarios 4–5 | Proposal-before-confirmation and confirmed execution tests |
| FR-008 | Edge case 1; SC-004 | Atomic batch execution test |
| FR-009 | US2 scenarios 1–4 | Provider prompt and tool-selection tests |
| FR-010 | US1 scenarios 1–3 | Catalog metadata and proposal listing tests |
| FR-011 | US1 scenarios 1–5 | Proposal-card review and confirmation-dialog execution-label contract |
| DR-001–DR-005 | US1 scenarios 4–5; US3 scenarios 1–2; Edge Cases | Service delegation, tenant isolation, provenance, and schema-diff proofs |
