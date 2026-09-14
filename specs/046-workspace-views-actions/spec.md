# Feature Specification: Workspace Views and Actions

**Feature Branch**: `[046-workspace-views-actions]`
**Created**: 2026-09-03
**Status**: Draft
**Language**: English
**Input**: "Classify projections and commands by business workspace and show appropriately named Views and Actions after a user selects Company Overview, Order Operations, Warehouse Operations, Finance Control, or Data Management. Provide safe manual intervention surfaces for eligible actions."

## Context and Intent

### Problem

Reality already separates task-oriented workspaces in the product shell and maintains validated Projection and Command catalogs. The workspace navigation, Projection consumers, and Command capabilities are nevertheless maintained as separate vocabularies. An operator can see registers but cannot reliably discover which read views and governed actions belong to the selected business area. Important manual interventions are therefore scattered across record pages, available only through another adapter, or visible only in technical documentation.

### Scope

- Give every user-facing workspace view and eligible business action an explicit, validated workspace classification and business label.
- Present the selected workspace navigation in distinct `Views` and `Actions` groups while preserving Home, Facts, Exceptions, and Ask Reality as persistent entry points.
- Place Activity once under Company Overview Views, opening the complete Activity page directly; remove the competing desktop/mobile header controls and global drawer.
- Treat `View` as the product term for both rebuildable Projections and authoritative Reality registers; do not imply that every view is a materialized Projection.
- Let operators start eligible actions from the selected workspace and complete them through shared application services, server validation, preview where the action is consequential, explicit confirmation, and an explainable result.
- Cover the core Warehouse Operations interventions discussed for this feature: reserve stock, record a receipt/transfer/shipment or adjustment, correct an eligible movement, hold or release a commitment, and create handling-unit, lot, or serial identities.
- In every workspace with actions, show the first two ordered actions directly and provide a searchable `More actions` launcher containing the complete classified, Web-executable action set.
- Keep contextual record actions on their record pages; workspace Actions are discoverable entry points into the same flows, not alternative business behavior.
- Expose the classification through the validated application reference so Web, documentation, Copilot, MCP, and future adapters can inspect one vocabulary.
- Update the durable Web product contract and localized visible labels.

### Non-Goals

- A generic workflow builder, arbitrary database editor, unrestricted command console, or emergency bypass around domain rules.
- Making every CLI, platform-administration, membership, setup, or integration command available in every business workspace.
- Treating workspace selection as authorization or changing tenant, calculation, or Reality state when a workspace changes.
- Replacing canonical register names with technical Projection or Command names.
- Adding business state fields, duplicating Source/Evidence links, or changing the domain schema.
- Completing unrelated missing pages named in the long-term Web UX matrix.

### Existing Contracts

- [Web UI Specification](../../docs/WEB_SPEC.md)
- [Web UX Matrix](../../docs/WEB_UX_MATRIX.md)
- [CLI Specification](../../docs/CLI_SPEC.md)
- [Core Catalogs baseline](../007-core-catalogs/spec.md)
- [Explain Projections baseline](../013-explain-projections/spec.md)
- [Business Reality Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover the selected workspace (Priority: P1)

As an operations leader, I can select a business workspace and immediately see the views and actions relevant to that area, using the same business language as the rest of the product.

**Why this priority**: The selected area is only useful if its navigation communicates both what can be inspected and what can be done.

**Independent Test**: Select each workspace with an empty and populated company and verify that its classified Views and Actions render in stable groups without changing company data or permissions.

**Acceptance Scenarios**:

1. **Given** an authenticated member has selected Warehouse Operations, **When** the sidebar renders, **Then** it shows persistent entries followed by Warehouse `Views` and eligible Warehouse `Actions` with canonical business labels.
2. **Given** a company has no warehouse records, **When** Warehouse Operations is explicitly selected, **Then** the area and its stable navigation remain discoverable and actions that lack required inputs explain what is needed rather than disappearing unpredictably.
3. **Given** a user switches between workspaces, **When** the selected preference changes, **Then** only navigation, landing context, and labels change; the active company, permissions, calculations, and business records do not.

### User Story 2 - Perform a governed warehouse intervention (Priority: P1)

As a warehouse operator, I can begin a relevant action from Warehouse Operations, supply its business inputs, review the server-evaluated effect when required, confirm the mutation, and see the resulting Reality through the affected view.

**Why this priority**: A list of actions without safe executable flows would advertise unavailable behavior and would not solve the manual-intervention need.

**Independent Test**: From the Warehouse Actions group, complete representative reservation, movement, hold/release, identity creation, and movement-correction stories and verify their resulting authoritative records, events, views, and traces.

**Acceptance Scenarios**:

1. **Given** eligible tenant-scoped records, **When** an operator starts an action, **Then** the form uses bounded business selectors and opaque identities while showing recognizable names and codes.
2. **Given** a mutating action is ready, **When** the operator submits it, **Then** no mutation occurs until the required preview and explicit confirmation have completed.
3. **Given** the underlying records changed after preview, **When** confirmation is attempted, **Then** execution is refused with refresh guidance and no partial mutation occurs.
4. **Given** a confirmed action succeeds, **When** the result is shown, **Then** the affected authoritative register or derived view refreshes and the user can trace the result through Reality, Evidence, and Source where those stages apply.
5. **Given** the active user or selected record is not authorized for the requested company, **When** the action is attempted, **Then** it behaves as unavailable or not found without exposing another tenant's records.

### User Story 3 - Keep catalogs and product navigation aligned (Priority: P2)

As a product maintainer or agent, I can inspect one validated application reference to learn which workspaces consume each Projection or expose each Command, so documentation and UI cannot silently invent a separate classification.

**Why this priority**: Central classification prevents the new navigation from becoming another manually drifting business vocabulary.

**Independent Test**: Introduce an invalid workspace, route, service, adapter, or duplicate ordering entry in a catalog fixture and verify that validation fails before the reference is served or the product build is accepted.

**Acceptance Scenarios**:

1. **Given** valid catalogs, **When** the application reference is composed, **Then** every user-facing workspace View and Action has a stable key, canonical label, workspace membership, order, and executable or navigable target.
2. **Given** a classified action is not available through the declared product adapter, **When** catalogs are validated, **Then** validation fails instead of showing a dead action.
3. **Given** a classified view reads authoritative Reality rather than a materialized Projection, **When** it is shown, **Then** it remains labelled as a View and its technical kind remains available only in explanation/reference detail.

### User Story 4 - Find every eligible order intervention (Priority: P1)

As an order operator, I see a small set of frequent actions directly and can open a searchable launcher to find and start every other eligible Order Operations action.

**Independent Test**: Select Order Operations, open `More actions`, search by action label, and start each listed action through its explicit confirmed Web flow.

**Acceptance Scenarios**:

1. **Given** any workspace with actions is selected, **When** the sidebar renders, **Then** at most its first two ordered actions are shown directly and a `More actions` control is available.
2. **Given** the launcher is open, **When** the user searches, **Then** matching classified actions are filtered without changing business state.
3. **Given** an action is listed, **When** it is selected, **Then** the launcher closes and the existing governed confirmation flow starts.
4. **Given** a command is not Web-eligible or not classified for Order Operations, **When** the launcher renders, **Then** that command is absent.

### Edge Cases

- A view belongs to more than one workspace but has a different relative order in each.
- An action belongs to more than one workspace without receiving conflicting business labels or safety rules.
- Required selectable records do not exist, are inactive, become stale, or belong to another tenant.
- A materialized Projection is rebuilding, stale, or failed while authoritative command validation remains available.
- A command exists for CLI, Chat, or MCP but is deliberately not eligible for direct Web execution.
- A user opens a bookmarked register that is not part of the currently selected workspace.
- Mobile navigation must expose the same hierarchy and confirmation path without covering content or losing the selected area.
- Localization is missing or a canonical business term is accidentally translated inconsistently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST use the five canonical workspace keys Company Overview, Order Operations, Warehouse Operations, Finance Control, and Data Management as presentation preferences rather than authorization boundaries.
- **FR-002**: The validated application vocabulary MUST classify every workspace-visible View by stable key, canonical product label, one or more workspaces, order within each workspace, destination, and technical kind.
- **FR-003**: The validated application vocabulary MUST classify every workspace-visible Action by stable key, business label, one or more workspaces, order, owning shared application command, availability requirements, and confirmation policy.
- **FR-004**: The Web sidebar MUST render classified `Views` and `Actions` for the selected workspace while retaining Ask Reality, Home, Facts, and Exceptions in their prescribed persistent positions.
- **FR-004a**: Activity MUST appear exactly once under Company Overview Views, MUST open the complete Activity page directly, MUST NOT appear in other workspace View lists, and MUST NOT have a competing desktop/mobile header control or global drawer.
- **FR-004b**: Empty-company onboarding navigation MUST be additive and MUST NOT replace or hide the catalog-defined Company Overview Views.
- **FR-005**: Visible View labels and destination page titles MUST use the canonical nouns defined by the Web contract; technical Projection names may appear only as supporting explanation.
- **FR-006**: The same View or Action MAY belong to multiple workspaces, but each workspace MUST present a deterministic, duplicate-free order.
- **FR-007**: Explicitly selected workspaces MUST remain visible for empty companies; unavailable Actions MUST provide concise prerequisite guidance and MUST NOT imply that business state already exists.
- **FR-008**: Workspace selection MUST NOT change tenant, permissions, calculations, Projection contents, or authoritative Reality records.
- **FR-009**: Every displayed Action MUST resolve to an executable shared application service exposed through the Web application boundary; validation MUST reject dead, missing, or adapter-ineligible entries.
- **FR-010**: Mutating Actions MUST require explicit confirmation, and consequential correction or snapshot-sensitive Actions MUST confirm the exact server-produced preview or revision.
- **FR-011**: Action forms MUST use tenant-scoped bounded selectors or exact opaque identifiers and MUST never preload an unbounded business register.
- **FR-012**: Warehouse Actions MUST support stock reservation, physical movement recording, eligible movement correction, commitment hold/release, and creation of handling-unit, lot, and serial identities without direct ORM writes or alternative browser business rules.
- **FR-013**: Successful Actions MUST expose the created or affected authoritative record, refresh affected Views, and provide the existing explain/inspect path to Reality, Evidence, and Source where applicable.
- **FR-014**: Failures, stale confirmations, invalid state, and cross-tenant references MUST produce consistent safe feedback and MUST leave no partial business mutation.
- **FR-015**: The composed application reference MUST expose workspace classifications to authorized tenant product consumers without revealing tenant data in the classification itself.
- **FR-016**: English, German, Dutch, and Spanish product catalogs MUST contain the new visible group labels, action labels, prerequisite guidance, confirmation copy, and result states, and the localization audit MUST remain strict.
- **FR-017**: Desktop and mobile navigation MUST preserve the selected workspace, View/Action distinction, readable labels, keyboard focus, and accessible expanded/disabled/dialog states.
- **FR-018**: Automated drift checks MUST reject unknown workspace keys, destinations, services, technical kinds, duplicate workspace order, missing canonical labels, and unsafe confirmation declarations.
- **FR-019**: Every workspace with actions MUST render at most the first two actions in canonical workspace order directly and MUST expose its complete ordered action set through the same searchable launcher.
- **FR-020**: Order Operations MUST classify reserve stock, commitment hold/release, document commitment hold/release, and party delivery hold/release as explicit Web-backed confirmed actions.
- **FR-021**: The action launcher MUST support keyboard-accessible open, search, selection, empty-result, and close behavior on desktop and mobile.
- **FR-022**: The Web boundary MUST expose confirmed, tenant-scoped adapters for manual sales/purchase order creation, source-supported Fact observation, customer payment posting, and supplier payment posting through their existing shared services.
- **FR-023**: Manual order creation MUST atomically preserve Source → Evidence → Reality by using the canonical order service that creates immutable source evidence, Document/Lines, and Commitments; it MUST NOT substitute the Document-only correction path.

### Domain and Traceability Requirements

- **DR-001**: Actions MUST preserve Source → Evidence → Reality whenever those stages apply; manual interventions MUST create only the Evidence and Reality records established by their existing domain command.
- **DR-002**: The feature MUST add no business-state fields and MUST retain shortest true relationships such as Reservation → Commitment and Movement → optional Commitment/Source evidence.
- **DR-003**: Every query, selector, preview, and mutation MUST enforce tenant scope and use the same application services/tools as CLI, API, Chat, and MCP.
- **DR-004**: Materialized Projections remain disposable read accelerators; command validation and confirmation MUST read authoritative Reality rather than trusting stale Projection rows.
- **DR-005**: The browser MUST contain presentation and interaction orchestration only; eligibility, invariants, preview calculation, and mutation remain server-owned.
- **DR-006**: Human-readable names, codes, SKUs, lot numbers, serial numbers, and document numbers MUST remain display/search values and MUST NOT become identity.

### Key Entities *(when data is involved)*

- **Workspace classification**: Product metadata connecting a stable View or Action to one or more task-oriented workspaces and an ordered presentation position; it is not tenant business state.
- **View definition**: A navigable business read surface backed either by authoritative Reality services or a rebuildable Projection.
- **Action definition**: A discoverable business intervention backed by one canonical application command and its confirmation contract.
- **Action preview**: Server-evaluated, non-mutating representation of the exact intended effect or authoritative revision used for confirmation.
- **Action result**: The authoritative record references, affected views, and trace entry returned after successful execution.

## Success Criteria *(mandatory)*

- **SC-001**: A user can select any workspace and identify its Views and Actions within 10 seconds on both desktop and mobile.
- **SC-002**: All five workspaces render deterministic, duplicate-free classified navigation in empty and populated company scenarios.
- **SC-003**: Each core Warehouse intervention can be started from Warehouse Operations and completed without using CLI, MCP, Chat, a technical console, or direct database access.
- **SC-004**: In automated stale-preview, invalid-state, and cross-tenant scenarios, zero unintended business records are created or changed.
- **SC-005**: One catalog validation run detects every tested invalid workspace, destination, service, adapter, ordering, or confirmation reference before it reaches users.
- **SC-006**: Every successful tested mutation exposes its affected Reality record and an explanation path, and the refreshed view agrees with authoritative service output.
- **SC-007**: The complete backend, frontend, localization, specification, and production-build verification suite required by this feature passes.
- **SC-008**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The five existing workspace choices and canonical navigation nouns remain authoritative.
- Workspace classifications are version-controlled product metadata, not tenant-configurable records.
- `Views` and `Actions` are the initial English product group names; translations use natural equivalents while domain record names follow existing localization policy.
- Existing dedicated record-page actions remain available and are reused rather than duplicated.
- A workspace action may open a focused dialog or navigate to a dedicated form; the catalog describes capability and destination, not browser-rendering details.
- Membership and company-role authorization remain governed by existing application boundaries; this feature does not introduce a new role model.
- Existing preview/confirmation infrastructure is reused where available and extended through shared services for the Warehouse actions that do not yet have a direct Web flow.

## Open Questions

None. The requested behavior is bounded by the existing workspace, catalog, Web safety, and domain contracts.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-008 | US1 scenarios 1-3 | Workspace selection and persistence stories |
| FR-002-FR-007 | US1 scenarios 1-3; US3 scenarios 1-3 | Catalog, API-reference, desktop, mobile, empty-state, and navigation tests |
| FR-009-FR-14 | US2 scenarios 1-5; US3 scenario 2 | Service, API, confirmation, tenancy, business-story, and Web interaction tests |
| FR-015-FR-018 | US3 scenarios 1-3 | Reference contract, localization audit, accessibility, build, and drift tests |
| DR-001-DR-006 | US2 scenarios 1-5 | Domain/service invariants, trace, tenant, and no-browser-rule tests |
| SC-001-SC-008 | All stories | Quickstart acceptance run and required repository gates |
