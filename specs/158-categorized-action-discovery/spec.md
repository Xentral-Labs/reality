# Feature Specification: Categorized Action Discovery

**Feature Branch**: Existing integration worktree; no branch switch
**Created**: 2026-09-10
**Status**: Implemented and verified locally on 2026-09-10; approved by the product owner ("ok mach"). See `verification.md`.
**Language**: English
**Input**: Group all Actions and Commands into a directory-like category tree, and include this in the same change as aligning global and contextual action entrypoints.

## Context and Intent

### Problem

The current Inspector lists 13 workspace Actions beside 65 Commands in long columns.
The global launcher separately lists 16 form entrypoints. Page menus are maintained
independently: Warehouse tabs show opening stock, while Finance exposes customer
credit/refund forms even in a supplier context. Users cannot infer completeness,
placement, or actual form availability from these surfaces.

### Scope

- Classify every current catalog Action and Command into a navigable business hierarchy.
- Replace the two long Inspector columns with one searchable, expandable directory.
- Align the global launcher and page/record entrypoints for existing forms using the
  same classifications and explicit contextual placements.
- Show cataloged capabilities without a current form honestly, retaining documentation.
- Include a checked coverage inventory for all catalog entries and current screens.

### Non-Goals

- Building every missing business form identified in the earlier audit.
- Adding business operations, tables, permissions, generic command execution, or
  changing source interpretation, accounting, inventory, company setup, or scheduling.
- Making every read Command an operational action or duplicating backend business rules.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Specification workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Web product contract](../../docs/WEB_SPEC.md), especially shared workspace ownership,
  complete contextual action menus, explicit forms and confirmation.
- [Classification inventory](inventory.md): proposed exhaustive primary placement.

## User Scenarios & Testing

### User Story 1 - Browse the complete capability directory (Priority: P1)

A user opens Action catalog, expands a business area and subgroup, and distinguishes
guided Actions from the Commands they use without scanning unrelated capabilities.

**Why this priority**: Directly addresses the requested directory structure.

**Independent Test**: Browse the fixture catalog containing all current entries and
verify each can be reached through its primary path with its original details intact.

**Acceptance Scenarios**:

1. **Given** the current catalog, **when** the directory opens, **then** business
   categories appear collapsed with separate Action and Command counts; expanding a
   category reveals subgroups and labeled entries, with every entry present once.
2. **Given** a selected entry, **when** it expands, **then** existing inputs, effects,
   adapters, confirmation information, and related Action/Command links remain reachable.
3. **Given** a Command without a form or a read-only Command, **when** inspected,
   **then** its execution availability and read/mutation mode are accurate; no generic
   execution button appears and no shipment-only form represents general movements.

### User Story 2 - Find a capability in a collapsed tree (Priority: P1)

A user searches by a business label, category, description, or technical command name.

**Why this priority**: Grouping must not make discovery harder.

**Independent Test**: Search for a hidden entry and navigate its details using only a keyboard.

**Acceptance Scenarios**:

1. **Given** collapsed branches, **when** a query matches an entry, **then** the matching
   entry and ancestor path are visible automatically and unrelated branches disappear.
2. **Given** a category-name match, **when** results render, **then** all entries under
   that category remain available; result counts count unique matching entries.
3. **Given** a query, **when** cleared, **then** the previous manual expansion state
   returns; no matches show an explicit empty state with a clear-search control.
4. **Given** a narrow viewport or keyboard-only use, **when** browsing, **then** all
   groups, entries, details and controls remain accessible with visible focus and
   announced expanded/collapsed states; localized labels are searchable.

### User Story 3 - Find the same supported action where work happens (Priority: P1)

A user starts an existing guided action from the global menu, relevant page, or eligible
record and receives the same form with appropriate customer/supplier and record context.

**Why this priority**: The requested combined step must fix fragmented entrypoints.

**Independent Test**: Compare launch results across Warehouse, Sales, Purchasing,
Commitments and Finance, including customer/supplier contexts and empty registers.

**Acceptance Scenarios**:

1. **Given** existing launchable forms, **when** the global menu opens, **then** grouped
   searchable entries cover every registered form variant; dedicated management flows
   have labeled navigation destinations rather than pretend generic forms.
2. **Given** Warehouse Stock, Reservations or Movements, **when** the page loads, **then**
   Stock has no contextual action menu, while Reservations and Movements offer the forms
   they create; empty owning registers do not hide creation actions, and record-specific
   actions retain their context.
3. **Given** supplier Finance, **when** selecting a contextual action, **then** invoice
   and payment start supplier flows; customer credit/refund actions are absent rather
   than opening an incorrect process. Journal prioritizes reversal; Payments prioritizes
   payment; Open items prioritizes applicable invoice/payment/credit/refund actions.
4. **Given** a missing prerequisite, insufficient access, company switch or failed
   catalog load, **when** a user tries to launch, **then** existing access, validation,
   confirmation and recovery behavior remains authoritative; no stale-company target
   is reused and no business write occurs merely from browsing or opening a form.
5. **Given** all application screens, **when** the coverage inventory is reviewed,
   **then** each existing form has explicit global/page/record placement or a reason
   for exclusion, and backend-only capabilities are distinguished from missing links.

### Edge Cases

- A shared order Command covers Sales and Purchasing: one primary catalog entry,
  multiple contextual placements, direction selected by the page.
- A general movement Command supports more operations than an existing shipment form.
- Actions and Commands have identical labels but distinct identities and counts.
- Related service aliases remain details of their Command, not duplicate Commands.
- Unknown future entries remain visible under an explicit Unclassified group; catalog
  validation fails until a reviewed classification is assigned.
- Hidden or unavailable actions must not expose tenant records or bypass owner checks.
- A row changes eligibility between opening the form and confirming: shared services
  remain authoritative, with existing stale-state rejection and reconciliation.

## Requirements

### Functional Requirements

- **FR-001**: Every catalog Action and Command MUST have one primary business category
  and subgroup, following the complete inventory; contextual placements MAY be multiple.
- **FR-002**: The catalog MUST use one expandable directory with category, subgroup,
  and entry levels; entries MUST identify Action or Command, and Commands their mode.
- **FR-003**: Counts MUST distinguish Actions and Commands, count unique entries, and
  reflect search results; entries MUST retain their existing detail information.
- **FR-004**: Search MUST traverse collapsed content, category paths, names, descriptions
  and technical identities; reveal ancestors; support clearing and no-result states.
- **FR-005**: The directory MUST support expand/collapse all, keyboard operation,
  visible focus, accessible disclosure state, responsive layout and existing locales.
- **FR-006**: Classification, ordering, explicit form support and contextual placements
  MUST have one shared definition across the directory, global and contextual launchers.
  Adapter support alone MUST NOT be interpreted as form support.
- **FR-007**: The global launcher MUST expose all registered guided form variants in
  grouped searchable form and provide explicit navigation to existing dedicated
  management flows; unsupported catalog capabilities remain discoverable in the catalog.
- **FR-008**: Existing Warehouse forms MUST have one operational home: Stock is a read-only
  derived position and offers no contextual actions; Reservations offers reserve and
  release; Movements offers opening stock, receipt, shipment and correction. Eligible
  reservation/movement rows retain preselected release/correction actions. Empty owning
  registers still expose their creation actions; missing prerequisites are handled by the
  existing form rather than inferred by empty register contents. The global launcher
  continues to expose all eligible forms.
- **FR-009**: Sales/Purchasing MUST retain direction-specific order creation and existing
  delivery-detail actions; Commitments MUST retain the existing customer/supplier
  detail actions. Shared classification MUST record these placements explicitly.
- **FR-010**: Finance contextual actions MUST respect both tab and direction, including
  customer credit/refund exclusions on supplier pages; global forms may still allow
  explicit direction selection. Backend-only supplier-credit/refund operations MUST
  NOT be represented as supported customer forms.
- **FR-011**: Every current screen and registered form MUST appear in a coverage review,
  with present/missing/unavailable or intentionally excluded placements distinguished.
  Facts, Rules, Reports, administration and integrations MUST NOT gain fabricated forms.
- **FR-012**: Existing permissions, tenant scope, previews, explicit confirmations,
  idempotency, stale-state checks, post-action navigation and evidence links MUST remain
  intact; catalog navigation and form opening MUST perform no business mutation.

### Domain and Traceability Requirements

- **DR-001**: Classification describes application capabilities; it creates no business
  authority and MUST NOT add Source, Evidence, or Reality records by browsing.
- **DR-002**: Contextual references MUST use existing opaque identities and shortest
  true links; classification MUST NOT become document-owned fulfillment state.
- **DR-003**: Every launched action MUST use its existing shared application service
  and tenant-scoped confirmation path, regardless of its entrypoint.

### Key Entities

- **Category/Subgroup**: A business-oriented directory path, distinct from navigation routes.
- **Capability entry**: One existing Action or Command with a stable identity and primary path.
- **Placement**: A context where an existing form or dedicated management destination is useful.
- **Availability**: Actual form/destination support, separate from documented adapter support.

## Success Criteria

- **SC-001**: All Commands present on the target branch and 13 current workspace Actions have one reviewed
  primary classification; new entries cannot silently disappear or become unclassified.
- **SC-002**: Every FR and DR has a mapped acceptance scenario and executable proof
  before implementation is marked complete.
- **SC-003**: Every catalog entry is reachable within three directory expansions, and
  searching its exact name exposes it even when every branch started collapsed.
- **SC-004**: Every existing guided form has reviewed contextual/global placement,
  with zero customer-only credit/refund launchers presented as supplier operations.
- **SC-005**: Browser verification covers expanded/collapsed/search/empty states,
  keyboard and narrow-screen use, Warehouse tabs and both Finance directions.

## Assumptions and Dependencies

- The combined port-8080 worktree is the target; root frontend and migration history
  are not substitutes. Implementation and local rollout are subsequent work.
- The tree is business-area-first. Actions and Commands share categories and retain
  type labels, rather than remaining separate long columns.
- Shared order/commitment commands use Sales & Purchasing as their primary area and
  explicit Sales/Purchasing/Commitments placements; financial commands live under Finance.
- The combined change covers classification and existing entrypoints. New business
  forms are a separately reviewable follow-up, not implied by complete classification.
- Exact category names and this boundary are proposed for product review. No schema
  expansion is expected. Existing WEB_SPEC obligations remain applicable.

## Open Questions

None requiring discovery; the concrete scope and taxonomy are ready for product review.

## Requirement Traceability

| Requirement        | Scenario(s)  | Planned test/evidence                                                  |
| ------------------ | ------------ | ---------------------------------------------------------------------- |
| FR-001             | US1.1, US3.5 | Complete inventory, unique identity and category validation            |
| FR-002, FR-003     | US1.1–3      | Directory hierarchy, counts and detail preservation checks             |
| FR-004             | US2.1–3      | Hidden match, category match, reset and empty-result checks            |
| FR-005             | US2.4        | Keyboard, localized search and narrow-screen browser checks            |
| FR-006, FR-007     | US1.3, US3.1 | Shared definition and form/destination coverage checks                 |
| FR-008             | US3.2        | Warehouse tabs, empty list and contextual row browser checks           |
| FR-009             | US3.5        | Sales/Purchasing and Commitment placement checks                       |
| FR-010             | US3.3        | Finance tab/direction launch matrix and negative supplier checks       |
| FR-011             | US3.5        | Every-screen and every-form coverage review                            |
| FR-012, DR-001–003 | US3.4        | No-write browsing, tenant/access and existing confirmation regressions |

## PR integration boundary

The isolated PR targets main at `2bc3a65`, which contains 60 Commands. All 60 and
13 Actions are classified, with 18 form variants and eight management links.
The deployed integration worktree additionally contains seven unmerged Finance
Commands. Their classifications and two management links remain there until the
Finance feature is integrated; this PR does not introduce its schema or services.
