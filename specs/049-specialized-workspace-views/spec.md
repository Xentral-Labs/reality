# Feature Specification: Specialized Workspace Views

**Feature Branch**: `[049-specialized-workspace-views]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "Classify the missing user-facing projections first, then add a generic More views launcher like More actions."

## Context and Intent

### Problem

The workspace catalog exposes common registers but omits several existing operational projections that answer specialized order and warehouse questions. Users cannot discover those read models from their selected workspace, while adding every view directly to the sidebar would make daily navigation increasingly noisy.

### Scope

- Classify every existing user-facing operational projection that currently lacks a workspace destination.
- Give each classified projection a canonical business label, workspace membership, deterministic order, and navigable bounded read surface.
- Show the first five ordered workspace Views directly and expose the complete ordered set through one shared searchable `More views` launcher.
- Keep persistent navigation and the existing generic `More actions` behavior unchanged.

### Non-Goals

- Exposing platform administration projections such as tenant usage in a business workspace.
- Presenting the on-demand price-resolution cache as a complete register; price resolution remains part of Commercial terms until a dedicated user journey is specified.
- Adding new projections, domain state, database tables, or browser-side calculations.
- Completing every aspirational register named in the broader Web specification when no corresponding read service exists yet.

### Existing Contracts

- [Web UI Specification](../../docs/WEB_SPEC.md)
- [Workspace Views and Actions](../046-workspace-views-actions/spec.md)
- [Explain Projections](../013-explain-projections/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover specialized operational views (Priority: P1)

As a Head of Operations, I can find existing specialized order and warehouse projections in the business workspace where I would naturally look for them.

**Why this priority**: Existing operational answers provide no product value when they are only discoverable through technical tooling.

**Independent Test**: Inspect the application reference and select Order Operations and Warehouse Operations; every in-scope specialized projection has a canonical, deterministic workspace entry and an accessible destination.

**Acceptance Scenarios**:

1. **Given** Order Operations is selected, **When** the complete View catalog is opened, **Then** Orders, Fulfillment blockers, and Supply & demand are discoverable with business labels and their registered projection identity remains available in reference metadata.
2. **Given** Warehouse Operations is selected, **When** the complete View catalog is opened, **Then** Warehouse Queue, Fulfillment blockers, and Supply & demand are discoverable without duplicating projection logic.
3. **Given** a company has no matching projection rows, **When** a specialized View is opened, **Then** the page shows a clear empty state and remains navigable.

### User Story 2 - Keep workspace navigation compact (Priority: P1)

As a daily operator, I see the most important Views immediately and can search the complete selected-workspace View set without scanning a long sidebar.

**Why this priority**: Classification and disclosure must ship together so the additional views do not degrade routine navigation.

**Independent Test**: Select each of the five workspaces on desktop and mobile; exactly the first five ordered Views are direct links when available, and `More views` searches and opens the complete ordered View set.

**Acceptance Scenarios**:

1. **Given** a workspace has more than five Views, **When** its navigation renders, **Then** only its first five ordered Views appear directly and `More views` is present.
2. **Given** `More views` is open, **When** the user searches by a partial label or description, **Then** the matching complete-workspace results remain selectable.
3. **Given** a result is selected, **When** navigation completes, **Then** the launcher and mobile navigation close and the canonical destination opens.

### User Story 3 - Read a specialized projection safely (Priority: P2)

As an operator, I can scan a specialized projection as business data without loading an unbounded tenant dataset or seeing raw storage records as the primary interface.

**Why this priority**: Discovery must lead to a usable and operationally safe read surface.

**Independent Test**: Open each specialized View for populated and empty tenants; it returns a stable bounded page, presents readable columns, supports search, and does not mutate business state.

**Acceptance Scenarios**:

1. **Given** more rows exist than fit on one page, **When** a specialized View opens, **Then** at most 50 rows are returned with stable paging controls and a total count.
2. **Given** a search term is submitted, **When** results are returned, **Then** filtering occurs inside the tenant boundary before pagination and the search remains in the URL.
3. **Given** an unknown or excluded projection is requested through the specialized surface, **When** the request is handled, **Then** it is rejected without exposing another tenant's data or an internal record dump.

### Edge Cases

- A materialized projection is rebuilding, stale, empty, or unavailable.
- One materialized projection supports two differently named business destinations, such as Orders and Warehouse Queue.
- The active route is available through `More views` but is not one of the five direct links.
- A workspace contains five or fewer Views.
- Search returns no matching Views or no matching projection rows.
- A bookmarked specialized destination is opened while a different workspace preference is selected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The catalog MUST classify `fulfillment_queue`, `fulfillment_blockers`, and `item_supply_demand` through canonical business Views in every relevant Order Operations and Warehouse Operations workspace.
- **FR-002**: A materialized projection MAY back more than one View when the Views answer distinct workspace jobs, but every View MUST keep a unique stable key, canonical label, route, description, and deterministic workspace order.
- **FR-003**: `tenant_usage` and `price_resolution` MUST NOT appear as standalone business workspace Views in this feature.
- **FR-004**: Each workspace MUST render at most its first five ordered Views directly.
- **FR-005**: Every workspace with Views MUST expose a generic `More views` control containing its complete ordered View set, including direct entries, so search behavior is consistent with `More actions`.
- **FR-006**: The View launcher MUST search case-insensitively across canonical labels and descriptions, show a no-results state, and allow keyboard and pointer selection.
- **FR-007**: Selecting a View MUST close the launcher and mobile navigation and navigate to the catalog-declared route without changing tenant, permissions, calculations, or Reality state.
- **FR-008**: Specialized materialized View pages MUST read the catalog-declared projection through a shared tenant-scoped service boundary and MUST NOT calculate business results in the browser.
- **FR-009**: Specialized pages MUST return stable server-side pages of at most 50 rows, expose a total count, apply search before pagination, preserve active search and page state in the URL, and provide loading, empty, no-results, and error states.
- **FR-010**: Specialized pages MUST lead with readable business columns and keep opaque identifiers or raw values secondary to the operational answer.
- **FR-011**: Catalog validation MUST reject unknown projection names, routes, workspace references, duplicate keys, and duplicate ordering entries before the application reference is served.
- **FR-012**: Desktop and mobile navigation MUST preserve visible focus, dialog semantics, readable labels, and accessible expanded and close states.

### Domain and Traceability Requirements

- **DR-001**: Specialized Views are disposable read models derived from authoritative Reality; they MUST NOT become operational authority or add state to Documents.
- **DR-002**: Displayed projection rows MUST preserve their existing shortest links and identifiers for subsequent explanation without duplicating Source, Document, or Reality relationships.
- **DR-003**: Every read MUST enforce tenant membership and tenant-scoped filtering through the shared projection service; the Web adapter and browser MUST NOT implement parallel business rules.
- **DR-004**: This feature MUST add no tables, columns, domain mutations, or alternate Projection builders.

### Key Entities *(when data is involved)*

- **Workspace View definition**: Presentation metadata connecting a stable business destination to its workspace order and, when applicable, an existing materialized projection.
- **Specialized projection page**: A bounded tenant-scoped result containing readable projection rows and paging metadata.

## Success Criteria *(mandatory)*

- **SC-001**: A user can find any classified View in the selected workspace within 10 seconds on desktop and mobile.
- **SC-002**: All five workspaces show no more than five direct View links and expose 100% of their classified Views through one searchable launcher.
- **SC-003**: Every in-scope specialized projection can be opened for empty and populated companies without a mutation or unbounded tenant read.
- **SC-004**: Invalid workspace, route, and projection references fail automated catalog validation before release.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Existing projection builders remain the calculation authority for fulfillment queue, fulfillment blockers, and item supply/demand.
- Existing tenant authentication, application-reference composition, shared navigation, and projection storage remain available.
- Five direct Views keep the complete Company Overview, including Activity, immediately visible while longer workspaces remain progressively disclosed.

## Open Questions

None. Product scope is explicitly approved by the user and bounded by existing catalogs and read services.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001-FR-003, FR-011 | US1 scenarios 1-3 | Catalog composition and invalid-reference tests |
| FR-004-FR-007, FR-012 | US2 scenarios 1-3 | Frontend navigation and accessibility contracts |
| FR-008-FR-010 | US3 scenarios 1-3 | Tenant-scoped HTTP and frontend projection-page tests |
| DR-001-DR-004 | US3 scenarios 1-3 | Service-boundary, no-schema, and diff review |
| SC-001-SC-005 | All scenarios | Quickstart acceptance matrix and full required quality gates |
