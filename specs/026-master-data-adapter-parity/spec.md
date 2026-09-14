# Feature Specification: Master Data Adapter Parity

**Feature Branch**: `026-master-data-adapter-parity`
**Created**: 2026-09-02
**Status**: Approved
**Language**: English
**Input**: "Close `004/FR-016` with focused proof that supported CLI, JSON API, and Web master-data mutations produce equivalent domain state through shared services."

## Context and Intent

### Problem

Reality documents shared master-data behavior, and individual CLI and JSON API tests
already exist. The repository does not yet prove one complete operation matrix showing
that Party, Item, and Location lifecycle mutations initiated through CLI, JSON API, and
Web produce the same tenant-owned domain state. Without that proof, an interface may
silently normalize different values, omit supported fields, bypass business validation,
or expose a lifecycle action that behaves differently from the other surfaces.

Operators should be able to choose the interface appropriate to their work without
changing the business meaning of the result. Contributors need a durable parity test
that detects adapter drift while keeping business rules in the shared application
services.

### Scope

- Define the supported cross-interface lifecycle matrix for Party, Item, and Location:
  create, update, deactivate, and reactivate.
- Compare canonical persisted domain state after equivalent successful mutations from
  CLI, JSON API, and Web.
- Prove that each interface delegates mutations to the same shared application-service
  boundary and does not implement competing normalization or validation rules.
- Compare representative validation and cross-tenant failures, including their absence
  of partial domain mutations.
- Verify opaque identity, tenant ownership, lifecycle preservation, typed operational
  fields, and optional SourceRecord provenance where each surface supports them.
- Close only the documented `004/FR-016` adapter-equivalence gap.

### Non-Goals

- Adding new master-data fields, entities, lifecycle operations, or deletion behavior.
- Expanding CLI, JSON API, or Web into feature-for-feature presentation parity beyond
  the supported Party, Item, and Location lifecycle matrix.
- Requiring identical human wording, layout, HTTP envelopes, terminal formatting, or
  generated opaque IDs across interfaces.
- Treating browser-local form state or transport payloads as domain state.
- Covering PaymentTerm, pricing, integrations, documents, imports, or Reality execution;
  their behavior remains governed by their existing contracts and focused proofs.
- Creating direct Web-to-database, CLI-to-database, or test-only mutation paths.
- Closing the separate demo-equivalence, UX-matrix, or scale-benchmark gaps.

### Existing Contracts

- [`specs/004-master-data/spec.md`](../004-master-data/spec.md)
- [`docs/features/master_data.md`](../../docs/features/master_data.md)
- [`docs/features/operational_fields.md`](../../docs/features/operational_fields.md)
- [`docs/CLI_SPEC.md`](../../docs/CLI_SPEC.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [Business Reality Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choose Any Supported Interface (Priority: P1)

As an operator, I can create and maintain the same Party, Item, or Location through CLI,
JSON API, or Web and receive the same business result.

**Why this priority**: Interface choice must not change tenant ownership, normalized
business values, operational fields, source trace, or lifecycle state.

**Independent Test**: Starting from equivalent isolated tenants, perform the same
create, update, deactivate, and reactivate sequence for each record family through each
supported interface, then compare canonical domain snapshots while excluding generated
identity and transport-only presentation.

**Acceptance Scenarios**:

1. **Given** three equivalent empty tenant contexts, **When** an equivalent valid Party
   is created through CLI, JSON API, and Web, **Then** all canonical Party fields, roles,
   tenant ownership, lifecycle state, and optional source trace are equivalent.
2. **Given** equivalent Items, **When** supported typed fields are updated through each
   interface, **Then** all canonical Item values and constraints produce equivalent
   domain state.
3. **Given** equivalent Locations, **When** name, type, parent, stock permission, and
   lifecycle changes are applied through each interface, **Then** the resulting
   tenant-scoped Location state is equivalent.
4. **Given** an active record from each family, **When** it is deactivated and then
   reactivated through each interface, **Then** every path preserves the same opaque
   record identity and historical relationships while changing only lifecycle state.

---

### User Story 2 - Receive the Same Business Protection (Priority: P1)

As an operator, I receive the same validation and tenant protection regardless of the
interface used for a master-data mutation.

**Why this priority**: An interface-specific bypass could corrupt operational references
or disclose another tenant's records even when successful paths appear equivalent.

**Independent Test**: Submit equivalent invalid and foreign-identity mutations through
all three interfaces and compare the resulting business outcome plus before/after
tenant snapshots.

**Acceptance Scenarios**:

1. **Given** equivalent invalid required values, **When** creation or update is attempted
   through CLI or JSON API and the corresponding Web action contract is evaluated,
   **Then** backend paths reject without partial state and Web demonstrably delegates the
   same input to the API and renders the API-owned failure without a local fallback.
2. **Given** a foreign tenant's opaque Party, Item, or Location identity, **When** update
   or lifecycle mutation is attempted through each interface, **Then** every path behaves
   as not found and discloses no foreign values.
3. **Given** an invalid operational relationship such as a foreign parent/default
   Location or a Location hierarchy cycle, **When** submitted through each interface,
   **Then** shared validation rejects it and both tenants remain unchanged.
4. **Given** an inactive record, **When** an unsupported operation tries to use it for
   new work, **Then** interface choice does not weaken the existing lifecycle rule.

---

### User Story 3 - Detect Adapter Drift (Priority: P2)

As a contributor, I can review one explicit capability matrix and executable proof that
shows which interface owns transport concerns and which shared service owns business
behavior.

**Why this priority**: Durable parity evidence prevents later UI, API, or CLI work from
quietly creating a second implementation of master-data rules.

**Independent Test**: Review the declared matrix against registered commands, routes,
and Web actions, then deliberately vary transport-only output while proving canonical
domain comparison remains stable and any missing/delegating path is detected.

**Acceptance Scenarios**:

1. **Given** the supported lifecycle matrix, **When** a command, endpoint, or Web action
   is missing, **Then** the parity proof fails with the uncovered record family and
   operation identified.
2. **Given** equivalent mutations, **When** opaque IDs, response envelopes, messages, or
   display formatting differ, **Then** parity still passes if canonical domain state is
   equivalent.
3. **Given** an adapter attempts an independent persistence or business-rule path,
   **When** the boundary proof runs, **Then** the divergence is detected.

### Edge Cases

- A Party has both customer and supplier roles plus a role-specific default Location.
- A manual record has no SourceRecord while an otherwise equivalent source-backed
  record retains the full immutable payload.
- Input differs only by supported whitespace, case normalization, decimal formatting,
  or boolean representation across transports.
- Generated opaque IDs and event timestamps differ between isolated parity runs.
- Deactivate or reactivate is repeated when the record already has the requested state.
- A record remains referenced by historical Evidence or Reality while its lifecycle is
  changed.
- Web performs a mutation through the JSON API boundary rather than owning a separate
  server-side business operation.
- One transport cannot represent an optional field that the shared lifecycle contract
  declares supported.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The proof MUST define an explicit Party, Item, and Location matrix covering
  create, update, deactivate, and reactivate across CLI, JSON API, and Web.
- **FR-002**: Equivalent successful operations through every supported interface MUST
  produce equivalent canonical tenant-owned domain state.
- **FR-003**: Canonical comparison MUST include all supported business fields,
  relationships, lifecycle state, roles, and source provenance, while excluding only
  generated identities, timestamps, and transport/presentation fields that do not alter
  business meaning.
- **FR-004**: CLI, JSON API, and Web mutations MUST delegate to shared tenant-scoped
  application services; adapters MUST NOT persist master data directly or implement
  competing business normalization, validation, or lifecycle rules.
- **FR-005**: Equivalent invalid-input cases through CLI and JSON API MUST be rejected
  without partial Party, PartyRole, Item, Location, SourceRecord, Evidence, or Reality
  mutation; the corresponding Web action MUST delegate the same business input to the
  JSON API and retain API-owned failure handling without a local mutation fallback.
- **FR-006**: Equivalent foreign-identity cases MUST behave as not found through every
  interface without disclosing or mutating foreign tenant state.
- **FR-007**: Deactivation and reactivation through every interface MUST preserve the
  existing opaque record identity, SourceRecord provenance, and historical Evidence and
  Reality links.
- **FR-008**: The parity proof MUST distinguish domain equivalence from identical
  transport output; terminal formatting, HTTP envelopes, Web presentation, generated
  IDs, and timestamps MAY differ without constituting drift.
- **FR-009**: The capability matrix MUST fail when a declared interface/operation is
  absent or no longer delegates to the authoritative mutation boundary.
- **FR-010**: Web mutation proof MUST use an executable structural contract over the
  actual operator-facing create, edit, and lifecycle handlers, their API-client methods,
  tenant-scoped HTTP method/path/body mappings, and API-owned error presentation;
  directly calling a service or checking an unused helper while labeling it “Web” is
  insufficient.
- **FR-011**: The feature MUST close only `004/FR-016` after all matrix, failure, tenant,
  and boundary proofs pass and final product-owner review is approved.

### Domain and Traceability Requirements

- **DR-001**: Party, Item, and Location remain operational reference identities;
  Documents remain Evidence and Commitments, Reservations, Movements, and LedgerEntries
  remain Reality. Adapter parity MUST NOT move operational state onto master data.
- **DR-002**: Optional source-backed records MUST continue to use the shortest true link
  to immutable SourceRecord payloads; parity support MUST NOT duplicate source fields.
- **DR-003**: All compared mutations and reads MUST be tenant-scoped, use opaque
  relationship identities, and treat foreign identities as not found.
- **DR-004**: Domain state MUST be observed from authoritative stored records and shared
  reads, not inferred from CLI text, HTTP response shape, or browser-local state.
- **DR-005**: No new schema, master-data capability, or alternative service abstraction
  MAY be added solely to make interface comparison easier.

### Key Entities

- **Party / PartyRole**: One tenant-owned business actor and its canonical operational
  capabilities.
- **Item**: A tenant-owned product or service identity with proven operational fields.
- **Location**: A tenant-owned hierarchical place and its stock permission.
- **SourceRecord**: Optional immutable, lossless provenance for source-backed master
  data.
- **Adapter capability matrix**: The reviewed mapping of record family, lifecycle
  operation, interface, authoritative shared behavior, and executable evidence. It is
  proof metadata, not business state.

## Success Criteria *(mandatory)*

- **SC-001**: 100% of the 36 declared lifecycle cells (3 record families × 4 operations
  × 3 interfaces) have executable coverage or an explicit owner-approved correction to
  the declared supported surface.
- **SC-002**: Successful parity scenarios show zero canonical field, relationship,
  provenance, tenant, or lifecycle differences across CLI, JSON API, and Web.
- **SC-003**: Invalid and foreign-identity CLI/API scenarios produce zero partial
  mutations and zero foreign-value disclosure, and every corresponding Web action is
  proven to delegate to the same API-owned protection without local persistence.
- **SC-004**: Every supported mutation path is traceable to one authoritative shared
  application-service behavior, with zero direct adapter persistence paths.
- **SC-005**: Repeated lifecycle transitions retain 100% of existing opaque identities
  and historical Source, Evidence, and Reality links.
- **SC-006**: Every FR and DR maps to an acceptance scenario and executable proof or an
  explicit product-owner-approved reason why automation is inappropriate.
- **SC-007**: `004/FR-016` moves from `Documented gap` to `Verified as-is` without schema
  growth, new master-data behavior, or closure of any unrelated accepted gap.

## Assumptions and Dependencies

- “Web” means the actual operator-facing React handler and API-client request contract
  using the tenant-scoped JSON API; it is not a third server-side mutation
  implementation. Stored state is proven at the real HTTP boundary rather than through
  a second browser-specific backend path.
- Equivalent scenarios use isolated tenants because opaque IDs and event timestamps are
  intentionally different between runs.
- Canonical snapshots compare business meaning after reloading authoritative state.
- The existing supported lifecycle surface is Party, Item, and Location create, update,
  deactivate, and reactivate. Other master-data configuration remains outside this
  focused baseline closure.
- Existing domain services, routes, CLI commands, and Web actions are expected to be
  reused and changed only when the parity proof exposes a real contract gap.
- `004/FR-016` remains open until implementation evidence and final owner review pass.

## Approval

The product owner approved this specification on 2026-09-02. Planning and design may
proceed without changing the approved 36-cell scope.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 scenarios 1–4; US3 scenarios 1–2 | Complete capability matrix and canonical snapshot parity stories |
| FR-004, FR-009–FR-010 | US3 scenarios 1 and 3; Web edge case | Adapter delegation and actual Web request-boundary proof |
| FR-005 | US2 scenarios 1 and 3 | Invalid-input and atomic before/after stories |
| FR-006 | US2 scenario 2 | Two-tenant non-disclosure and non-mutation stories |
| FR-007 | US1 scenario 4; lifecycle edge cases | Identity/provenance/historical-link lifecycle snapshots |
| FR-008 | US3 scenario 2 | Canonical-versus-transport difference proof |
| FR-011 | Final review | Baseline evidence and coverage-matrix closure gate |
| DR-001–DR-005 | All stories | Constitution, schema, tenant, provenance, and authoritative-state review |
| SC-001–SC-007 | All stories | Matrix completeness, parity, regression, policy, and final review gates |
