# Feature Specification: Complete Chat and MCP Command Coverage

**Feature Branch**: `042-chat-mcp-command-parity`
**Created**: 2026-09-02
**Status**: Draft — awaiting product approval
**Language**: English
**Input**: "Expose all business operations through Chat and MCP so capabilities are complete rather than discovered piecemeal; reuse existing commands and require proposal approval for mutations."

## Context and Intent

### Problem

Chat and MCP expose a useful but incomplete subset of Business Reality. Users can create and update core master data and perform selected operational actions, yet cannot reliably discover target records or execute many commands already supported by CLI, API, or Web. Orders, normal warehouse actions, financial postings, pricing, holds, source configuration, and several lifecycle operations are missing. Capability gaps are currently discovered accidentally because no executable parity rule prevents drift.

### Scope

- Provide direct, tenant-scoped Chat/MCP read tools needed to find, inspect, and explain records before acting.
- Provide confirmation-required Chat/MCP proposals for every eligible tenant business mutation in the canonical command catalog.
- Add explicit sales-order and purchase-order proposal workflows using Evidence and derived Reality rather than inventing an isolated Order authority.
- Preserve each command's existing validation, authorization, tenant, atomicity, audit, and immutable-record semantics.
- Add executable coverage metadata so a new eligible application command cannot silently omit Chat/MCP support.
- Present exact mutation previews and resulting record IDs through the existing proposal review and approval experience.

### Non-Goals

- Exposing unrestricted database, ORM, table, SQL, shell, or generic method-call tools.
- Exposing platform-wide tenant administration, permanent company deletion, authentication internals, projection maintenance, demo helpers, raw event emission, or other technical operations merely because they are callable.
- Weakening owner-only membership authorization, tenant isolation, human confirmation, stale guards, or immutable journal/movement/source rules.
- Making Documents the owner of fulfillment, reservation, inventory, or payment status.
- Automatically executing mutations from natural language without approval.
- Adding new business fields when existing canonical commands do not require them.

### Existing Contracts

- [`docs/features/chat.md`](../../docs/features/chat.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`packages/reality-core/config/command_catalog.yaml`](../../packages/reality-core/config/command_catalog.yaml)
- [`specs/038-chat-master-data-proposals/spec.md`](../038-chat-master-data-proposals/spec.md)
- [`specs/041-master-data-update-audit/spec.md`](../041-master-data-update-audit/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and inspect business records (Priority: P1)

A tenant user asks Chat to find a Party, Item, Location, Document, Commitment, Reservation, Movement, warehouse identity, payment, pricing record, source definition, or other eligible business object. Chat returns bounded matching records and opaque IDs, then can inspect the selected object before proposing an action.

**Why this priority**: Mutation tools that require opaque IDs are not usable safely unless the agent can resolve targets without guessing.

**Independent Test**: For every mutation family, demonstrate a bounded tenant-scoped discovery/detail path that supplies the opaque IDs and current values required by its proposal.

**Acceptance Scenarios**:

1. **Given** a unique matching tenant record, **When** a user searches by a supported human reference, **Then** Chat/MCP returns its display summary and opaque ID without mutation.
2. **Given** multiple matches, **When** a user searches, **Then** the system presents bounded candidates and does not choose a mutation target silently.
3. **Given** an absent or foreign-tenant record, **When** it is searched or inspected, **Then** no foreign information is disclosed.
4. **Given** a large tenant, **When** a discovery tool is called, **Then** filtering and bounded pagination occur before results are returned.

### User Story 2 - Create sales and purchase orders (Priority: P1)

A user asks Chat to create a customer or supplier order. Chat resolves the parties, items, locations, quantities, prices, currency, and requested or promised times, previews the complete Evidence and resulting obligations, and creates them only after approval.

**Why this priority**: Order entry is a core business operation and is currently absent from Chat/MCP.

**Independent Test**: Create one sales and one purchase order through approved proposals and trace each from optional manual Source context through Document/DocumentLines to the correct outgoing or incoming Commitments.

**Acceptance Scenarios**:

1. **Given** valid opaque references and complete required values, **When** an order proposal is prepared, **Then** no Evidence or Reality record exists before approval and the preview shows the complete intended order and derived obligations.
2. **Given** explicit approval of a current proposal, **When** it executes, **Then** Document and DocumentLines are created atomically and canonical interpretation creates the correct Commitments.
3. **Given** an unknown item/party/location, invalid quantity, currency, time, or stale referenced record, **When** approval is attempted, **Then** the whole order fails without partial Evidence or Reality.
4. **Given** the resulting order, **When** it is explained, **Then** the user can traverse Source when applicable, Evidence, Commitments, reservations, movements, and current fulfillment derivation.

### User Story 3 - Perform warehouse and commitment operations (Priority: P1)

A warehouse or operations user can propose normal movements, create handling units/lots/serial units, reserve or release stock, and set or release eligible commitment, document, and party delivery holds using the same application rules as other surfaces.

**Why this priority**: Current MCP supports selected corrections but not the normal operational workflow.

**Independent Test**: Complete a receiving/reservation/holding/release/shipping scenario using discovery plus confirmed proposals and verify authoritative append-only records and event traces.

**Acceptance Scenarios**:

1. **Given** valid inventory identities and quantities, **When** approved, **Then** normal Movement and identity records are created through canonical services without directly editing stock.
2. **Given** an eligible Commitment, **When** reserve, release, hold, or release-hold is approved, **Then** the canonical Reality records change atomically and derived availability/fulfillment follows them.
3. **Given** an immutable Movement or already-corrected chain, **When** correction is requested, **Then** existing compensation/replacement and stale-confirmation rules remain authoritative.

### User Story 4 - Perform finance and pricing operations (Priority: P2)

A finance user can discover relevant evidence and references, propose supported customer/supplier payments, allocations, ledger actions, payment terms, price lists, tiers, and pricing assignments, and approve exact previews.

**Why this priority**: Financial actions are valuable but require stronger context and exact debit/credit or allocation previews.

**Independent Test**: Execute representative receivable, payable, allocation, ledger reversal, payment-term, and pricing changes with balanced/eligible previews and immutable audit evidence.

**Acceptance Scenarios**:

1. **Given** valid financial evidence, **When** a payment/allocation/posting proposal is reviewed, **Then** it shows amounts, currency, affected documents/parties, and resulting balanced entries before approval.
2. **Given** valid pricing inputs, **When** approved, **Then** canonical pricing records and assignments are created or changed without bypassing precedence or tenant rules.
3. **Given** an invalid, duplicate, stale, unbalanced, over-allocated, or cross-tenant request, **When** approval is attempted, **Then** nothing is partially posted or assigned.

### User Story 5 - Configure sources and governed membership actions (Priority: P2)

An authorized user can discover and propose eligible source-system, capability, connector, and membership operations while retaining existing role checks and immutable intake behavior.

**Why this priority**: Complete operation through Chat requires setup and governed administrative actions, but authority must not be broadened.

**Independent Test**: Configure a source/capability and execute representative owner-only membership actions through proposals, proving confirmation and authorization are rechecked at execution.

**Acceptance Scenarios**:

1. **Given** valid source configuration, **When** approved, **Then** the same source registry and capability services used by Web/API are called.
2. **Given** an owner-only membership proposal, **When** a non-owner or stale owner confirms it, **Then** execution is rejected without membership change.
3. **Given** an uploaded artifact, **When** source ingestion is approved, **Then** immutable SourceRecord and import behavior remains unchanged.

### User Story 6 - Prevent capability drift (Priority: P2)

A maintainer can see which canonical commands are eligible, available, deliberately excluded, or blocked, and automated checks fail when the catalogs and Chat/MCP exposure diverge.

**Why this priority**: Completeness must remain a contract rather than another one-time tool expansion.

**Independent Test**: Add a synthetic eligible command without an MCP/Chat mapping and verify the parity validator reports the exact omission; verify every exclusion has a reason.

**Acceptance Scenarios**:

1. **Given** the canonical command catalog, **When** parity is validated, **Then** every eligible mutation maps to one explicit proposal tool and every required discovery capability maps to a read tool.
2. **Given** an excluded command, **When** catalogs are inspected, **Then** its security/domain reason is explicit and testable.
3. **Given** a tool without a canonical application operation, **When** parity is validated, **Then** validation fails rather than accepting transport-owned business logic.

### Edge Cases

- A human reference matches several active and inactive records.
- A target changes after preview but before confirmation.
- A batch contains duplicate, invalid, inactive, or cross-tenant targets.
- An operation is irreversible or append-only and therefore must use correction/reversal instead of update/delete.
- A financial proposal becomes invalid because settlement or balances change.
- An order contains mixed valid and invalid lines or produces no operational Commitment.
- A permission changes between proposal preparation and confirmation.
- A source artifact is already attached or a source identity/payload version already exists.
- An eligible command has no safe preview representation.
- A read result would exceed bounded large-tenant limits.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain an explicit machine-readable classification of every canonical application command as Chat/MCP eligible, deliberately excluded, or temporarily blocked with a reason.
- **FR-002**: Every eligible read capability MUST execute immediately through a tenant-scoped shared application service and MUST NOT require approval.
- **FR-003**: Every eligible mutation MUST be exposed as an explicit typed proposal and MUST require human approval before execution.
- **FR-004**: Chat/MCP MUST provide bounded discovery and detail reads sufficient to resolve every opaque target and current value required by an eligible mutation.
- **FR-005**: Discovery MAY accept documented human references, but every mutation MUST execute only against opaque IDs.
- **FR-006**: Every proposal MUST preview the exact intended records, values, effects, and irreversible append/correction/reversal semantics relevant to the command.
- **FR-007**: Confirmation MUST recheck tenant scope, authorization, target existence, eligibility, and stale business state before executing.
- **FR-008**: Proposal execution MUST call the same canonical application service used by existing adapters and MUST NOT duplicate business rules in Chat, MCP, or the browser.
- **FR-009**: Multi-record and multi-line mutations MUST be atomic across business records, Evidence, Source versions, Reality records, events, and proposal status.
- **FR-010**: The system MUST provide explicit sales-order and purchase-order create proposals that create Document/DocumentLine Evidence and derive outgoing or incoming Commitments through canonical interpretation.
- **FR-011**: Order proposals MUST require opaque Party, Item, and Location references, positive quantities, supported currency/time/value semantics, and complete line previews.
- **FR-012**: Warehouse proposals MUST cover normal Movement creation, Handling Unit, Lot, and Serial Unit creation, reservation creation/release, and eligible hold/release operations without mutable stock fields.
- **FR-013**: Finance proposals MUST cover currently canonical payment, allocation, correction/reversal, payment-term, price-list, tier, group, and assignment operations with exact financial previews.
- **FR-014**: Source-configuration proposals MUST cover currently canonical connector-shell, source-system, source-capability, activation, and ingestion operations while preserving immutable payload/version behavior.
- **FR-015**: Membership proposals MUST preserve current owner authorization and MUST reauthorize the confirming principal at execution.
- **FR-016**: Commands that delete tenant data, administer the platform globally, expose authentication/secrets, rebuild projections, seed demos, emit raw events, or provide generic persistence access MUST remain excluded unless separately specified and approved.
- **FR-017**: Existing master-data create/update, reservation, movement correction, ledger reversal, source ingestion, exception, inventory, fulfillment, order-explanation, and finance-balance tools MUST remain compatible.
- **FR-018**: Every executed mutation MUST retain its canonical Business Event and Change Proposal audit path, including actor/action context when available.
- **FR-019**: A parity validator MUST fail with the exact missing, stale, duplicate, or unjustified command/tool mapping.
- **FR-020**: Public tool metadata and Chat guidance MUST explain required fields, defaults, opaque identities, confirmation, and relevant safety semantics without relying on hidden prompt knowledge.
- **FR-021**: MCP and managed Chat providers MUST derive their exposed schemas from the same canonical tool registry and access classification.
- **FR-022**: Failed, rejected, unauthorized, stale, or replayed proposals MUST persist no successful business mutation and MUST provide actionable safe errors.

### Domain and Traceability Requirements

- **DR-001**: Source-backed flows MUST preserve immutable lossless SourceRecord versions; manual operations MUST NOT fabricate Source/Evidence layers that do not apply.
- **DR-002**: Orders MUST preserve Source when applicable → Document/DocumentLine Evidence → Commitment Reality; operational status remains derived from Reality.
- **DR-003**: Reservations link to Commitments, movements remain append-only physical truth, ledger entries remain balanced immutable financial truth, and corrections use existing shortest relationships.
- **DR-004**: Every record, search, relationship validation, preview, proposal, execution, and audit read MUST enforce tenant scope without foreign-record disclosure.
- **DR-005**: CLI, API, Web, MCP, and Chat MUST share canonical application services; adapter catalogs describe reachability but do not become a second rule engine.
- **DR-006**: Human numbers, names, SKUs, emails, and external IDs MAY support discovery but MUST NOT replace opaque internal identity for mutation relationships.

### Key Entities *(when data is involved)*

- **Command capability**: Classification linking a canonical application operation to eligible adapters, access mode, preview contract, permissions, and explicit exclusions.
- **Change Proposal**: Immutable reviewed mutation intent awaiting explicit approval.
- **SourceRecord**: Immutable lossless external input version.
- **Document/DocumentLine**: Typed Evidence for manual or sourced orders and financial documents.
- **Commitment/Reservation/Movement/LedgerEntry**: Authoritative Reality primitives affected through their canonical commands.
- **Master and configuration records**: Party, Item, Location, warehouse identity, payment term, price configuration, source definition, and membership targets retaining stable opaque IDs.

## Success Criteria *(mandatory)*

- **SC-001**: Automated parity reports 100% classified canonical commands and 100% Chat/MCP mappings for eligible commands, with zero unexplained exclusions.
- **SC-002**: A user can discover the target and complete at least one representative operation in every in-scope family without supplying an opaque ID in the initial natural-language request.
- **SC-003**: No eligible mutation changes business state before approval, and all failure/rollback acceptance scenarios persist zero partial business effects.
- **SC-004**: Sales and purchase order stories are fully traceable from Source when applicable through Evidence to derived Commitments.
- **SC-005**: Equivalent operations through Chat/MCP and another supported adapter produce equivalent authoritative state, audit events, and errors.
- **SC-006**: Large-tenant discovery returns bounded, filtered results under the existing register limits.
- **SC-007**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- “Complete” covers tenant-scoped business commands in the canonical command catalog plus discovery reads required to use them safely.
- Existing application services are reused where they form a complete command. Missing order orchestration may add the smallest canonical service that composes existing Evidence and interpretation behavior.
- Platform-global/destructive and technical maintenance operations remain out of scope by default as listed in FR-016.
- Membership operations remain available only to authorized principals even if their proposal tools are advertised.
- All mutations use proposal/approval; reads do not.
- Delivery may be phased internally, but the feature is complete only when the executable parity contract is green.

## Open Questions

None. The bounded completeness definition above is ready for owner review.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-009 | US1, US6; all mutation scenarios | Registry parity, discovery, proposal, stale, tenant, and atomicity tests |
| FR-010–FR-011 | US2 | Sales/purchase Evidence-to-Reality business stories |
| FR-012 | US3 | Warehouse and Commitment lifecycle story |
| FR-013 | US4 | Finance and pricing story |
| FR-014–FR-015 | US5 | Source configuration and owner-authorization stories |
| FR-016–FR-022 | US1–US6 | Exclusion, compatibility, provider schema, audit, and error tests |
| DR-001–DR-006 | US1–US6; Edge Cases | Provenance, shortest-link, tenant, adapter-parity, and identity tests |
