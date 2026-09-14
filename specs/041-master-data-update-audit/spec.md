# Feature Specification: Auditable Master Data Updates

**Feature Branch**: `041-master-data-update-audit`
**Created**: 2026-09-02
**Status**: Approved — product scope approved by the owner on 2026-09-02
**Language**: English
**Input**: "Allow every supported Party, Item, and Location adjustment through tools and Chat, and record before/after values in the event history."

## Context and Intent

### Problem

Users can edit Parties, Items, and Locations through existing application surfaces, but Chat and MCP currently expose creation proposals only. Update events also record an incomplete current-state summary rather than an exact field-level change, so a user cannot reliably answer what changed, when it changed, and through which action.

### Scope

- Expose confirmed update proposals for Parties, Items, and Locations through Chat and MCP.
- Keep every field already supported by the canonical update operation consistently available through CLI, API, Web, MCP, and Chat where that surface supports mutations.
- Record immutable, field-level `before` and `after` values for every effective Party, Item, Location, and master-data lifecycle change.
- Make the resulting audit detail available through the existing event/inspection path.

### Non-Goals

- Adding new Party, Item, or Location business fields.
- Treating human-readable names, SKUs, or external numbers as identity.
- Replacing immutable SourceRecord versioning with mutable audit events.
- Adding generic update tools that can mutate arbitrary tables or fields.
- Reconstructing field-level diffs for historical events created before this feature.
- Changing operational Reality or derived inventory merely because descriptive master data changes.

### Existing Contracts

- [`docs/features/chat.md`](../../docs/features/chat.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`specs/038-chat-master-data-proposals/spec.md`](../038-chat-master-data-proposals/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Propose a master-data update in Chat (Priority: P1)

An authenticated tenant user asks Chat to change one or more supported fields on a Party, Item, or Location. The assistant identifies the intended tenant-scoped record, presents the exact proposed changes without mutating business state, and executes them only after explicit human confirmation.

**Why this priority**: Chat cannot be a complete operational interface while existing master data can be created but not maintained.

**Independent Test**: For each of Party, Item, and Location, request one valid update, inspect the proposal, verify that state is unchanged before approval, approve it, and verify the canonical record changed through the shared application operation.

**Acceptance Scenarios**:

1. **Given** one unambiguous tenant-scoped record and valid replacement values, **When** the user requests a change through Chat or MCP, **Then** the system returns a confirmation-required proposal containing the opaque record ID and exact intended values without changing the record.
2. **Given** an approved, still-current proposal, **When** the user confirms execution, **Then** the same canonical update rules used by the other application surfaces validate and apply the change exactly once.
3. **Given** a name, SKU, or other human reference that matches zero or multiple tenant records, **When** the user requests a change, **Then** no mutation proposal is executed and the user receives safe guidance to identify the intended record.
4. **Given** a record from another tenant, **When** its opaque ID is supplied, **Then** the operation behaves as not found and discloses no cross-tenant data.

### User Story 2 - Inspect exact before/after history (Priority: P1)

An operations or support user inspects an updated Party, Item, or Location and can see exactly which supported fields changed, their prior values, their resulting values, the change time, and the responsible action context.

**Why this priority**: Editable business references are not adequately auditable when an event records only that an update occurred.

**Independent Test**: Change multiple fields, then inspect the emitted event and verify that it contains only effective changed fields with exact normalized `before` and `after` values plus stable subject and action context.

**Acceptance Scenarios**:

1. **Given** a successful update changing one or more fields, **When** its immutable business event is inspected, **Then** every effective changed field has an exact `before` and `after` value.
2. **Given** an input value that normalizes to the stored value, **When** an update is submitted, **Then** that field is not represented as changed.
3. **Given** an update that fails validation or authorization, **When** the transaction ends, **Then** neither the master-data change nor a successful update event persists.
4. **Given** an activation or deactivation, **When** its lifecycle event is inspected, **Then** the event records the previous and resulting active state using the same diff contract.

### User Story 3 - Keep mutation surfaces consistent (Priority: P2)

A user receives the same validation and audit semantics whether a supported update originates in Web, API, CLI, MCP, or Chat.

**Why this priority**: Surface-specific business rules create inconsistent state and unreliable audit history.

**Independent Test**: Exercise representative updates through each public mutation adapter and verify delegation to the canonical application operation and an equivalent event diff.

**Acceptance Scenarios**:

1. **Given** equivalent valid inputs through two supported surfaces, **When** each update is performed, **Then** normalization, validation, persisted state, and audit-diff structure are equivalent.
2. **Given** an unsupported or read-only field, **When** any adapter receives it, **Then** it is rejected rather than silently stored or mapped.

### Edge Cases

- A proposal becomes stale because the record changes between preview and confirmation.
- A batch contains a mix of valid and invalid record IDs or values.
- An update changes roles, nullable relationships, decimals, booleans, or normalized strings.
- A Location update would create a self-parent or hierarchy cycle.
- An Item default Location or Party payment term belongs to another tenant or does not exist.
- Source provenance changes and creates a new immutable SourceRecord version while the master-data identity remains stable.
- Event values must remain serializable without losing decimal, boolean, null, list, or opaque-ID meaning.
- A submitted update produces no effective field change.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose explicit Party, Item, and Location update proposal operations to MCP and Chat.
- **FR-002**: Every update proposal MUST identify its target by the target record's opaque tenant-scoped ID; display values MAY assist discovery but MUST NOT become mutation identity.
- **FR-003**: A Chat/MCP update MUST show the exact intended replacement values and require explicit human confirmation before changing business state.
- **FR-004**: The proposal operations MUST support every field accepted by the corresponding canonical Party, Item, or Location update operation, without introducing new typed business fields.
- **FR-005**: The system MUST apply the same normalization, validation, relationship, hierarchy, and tenant rules regardless of mutation surface.
- **FR-006**: Multi-record update proposals MUST be atomic: either all records and their audit events persist, or none do.
- **FR-007**: Confirmation MUST reject a stale proposal when a target's relevant current state no longer matches the state reviewed by the user.
- **FR-008**: Every effective Party, Item, and Location update MUST emit one immutable tenant-scoped event containing the stable subject ID and a field-level change set.
- **FR-009**: Each changed field in the event MUST contain its normalized `before` value and normalized `after` value; unchanged fields MUST NOT appear in the change set.
- **FR-010**: Activation and deactivation events for Party, Item, and Location MUST use the same `before`/`after` change-set contract.
- **FR-011**: Failed or rolled-back updates MUST NOT persist a successful update or lifecycle event.
- **FR-012**: Event inspection MUST expose event type, subject type and ID, occurrence time, source record when applicable, action/proposal context when available, and the exact field change set.
- **FR-013**: Existing update behavior in CLI, API, and Web MUST continue to use the canonical application services and gain the same audit semantics without transport-specific diff logic.
- **FR-014**: An update with no effective changes MUST be handled consistently as a no-op and MUST NOT claim that fields changed.

### Domain and Traceability Requirements

- **DR-001**: Direct manual changes MAY update the current master-data record and MUST append an immutable Business Event; externally sourced changes MUST additionally preserve the immutable SourceRecord version chain and lossless payload.
- **DR-002**: The Party, Item, or Location retains its stable opaque identity across updates; the Business Event links directly to that subject and does not create duplicate master-data rows or redundant ancestry links.
- **DR-003**: All reads, proposal preparation, stale checks, writes, and event inspection MUST be tenant-scoped and use shared application services across CLI, API, Web, MCP, and Chat.
- **DR-004**: Event history is audit evidence of changes, not operational authority; inventory, commitments, reservations, movements, ledger state, and document fulfillment state remain governed by their existing Reality records and derivations.

### Key Entities *(when data is involved)*

- **Party**: A stable tenant-scoped business actor whose supported current attributes and roles may change.
- **Item**: A stable tenant-scoped product or service reference whose supported commercial and inventory-planning attributes may change.
- **Location**: A stable tenant-scoped warehouse node whose supported name, type, hierarchy, and stock eligibility may change.
- **Change Proposal**: A confirmation-required, immutable preview of exact intended updates and the reviewed target state.
- **Business Event**: An immutable tenant-scoped record of an effective mutation, including stable subject identity and field-level before/after changes.
- **SourceRecord**: Immutable lossless provenance that is versioned when an externally sourced master-data representation changes.

## Success Criteria *(mandatory)*

- **SC-001**: A user can propose and confirm a valid Party, Item, or Location update through Chat without using CLI, API, or direct database access.
- **SC-002**: In acceptance testing, 100% of effective supported field changes appear with exact normalized before/after values in the corresponding event, and 0 unchanged fields are reported as changed.
- **SC-003**: Equivalent representative updates through every supported mutation surface produce equivalent stored state and audit semantics.
- **SC-004**: Invalid, cross-tenant, stale, or partially invalid batch updates persist zero target changes and zero successful update events.
- **SC-005**: A support user can determine what changed, when, on which stable record, and through which available action context from the normal inspection path without direct database access.
- **SC-006**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Scope is limited to Party, Item, and Location because these are the master-data families currently exposed for Chat creation and already have canonical update operations.
- “All adjustments” means every field in the current canonical update contracts plus activation/deactivation; it does not authorize new domain fields.
- Existing Business Event storage can carry the structured change set without a new business table; the plan must verify this before implementation.
- Existing actor/action metadata is reused where available. This feature does not introduce a new authorization model.
- Historical events remain unchanged; the richer contract applies to events emitted after deployment.
- Proposal discovery may use names and human references, but execution always uses an opaque ID and a reviewed-state guard.

## Open Questions

None. The product scope above is ready for owner review.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-005 | US1 scenarios 1–4; US3 scenarios 1–2 | MCP catalog, Chat orchestration, and adapter parity tests |
| FR-006–FR-007 | US1 scenario 2; Edge Cases | Atomic batch and stale-confirmation service tests |
| FR-008–FR-012 | US2 scenarios 1–4 | Event diff, rollback, lifecycle, and inspection tests |
| FR-013–FR-014 | US2 scenario 2; US3 scenarios 1–2 | CLI/API/Web delegation, parity, and no-op tests |
| DR-001–DR-004 | US1–US3; Edge Cases | Source versioning, identity, tenant isolation, and business-story tests |
