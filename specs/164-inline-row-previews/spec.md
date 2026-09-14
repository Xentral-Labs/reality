# Feature Specification: Inline Row Previews

**Feature Branch**: `164-inline-row-previews`
**Created**: 2026-09-10
**Status**: Approved for implementation
**Language**: English
**Input**: "Start with Commitments, Exceptions, Decisions, Sales, Purchasing, Warehouse, Finance, and Master Data. Open view-only previews below the selected row and clearly distinguish preview from navigation, filtering, editing, and other actions with icons. Prepare the complete change in a worktree."

## Context and Intent

### Problem

Daily-work and workspace registers currently use similar right-pointing affordances for materially different outcomes: opening a read-only explanation, navigating to another workspace, applying a filter, or entering an edit or confirmed-action flow. Read-only detail often appears in a right-side drawer or centered inspector, which removes visual continuity between the selected row and its explanation. Operators must infer what a control will do and repeatedly shift attention away from the register they are scanning.

### Scope

- Introduce one consistent inline disclosure pattern for read-only row previews in Commitments, Exceptions, Decisions, Sales, Purchasing, Warehouse, Finance, and Master Data.
- Place an opened preview immediately below its originating row or list item while preserving the surrounding register context.
- Give preview, navigation, filter, edit, and operational-action affordances distinct, accessible icon-and-label semantics.
- Keep deeper traceability from each preview to Reality, Evidence, and Source where the underlying record supports it.
- Define responsive, keyboard, loading, error, selection, pagination, and filter behavior for the shared pattern.

### Non-Goals

- Replacing edit forms, confirmation flows, financial workflows, operational execution, or destructive-action dialogs with inline content.
- Removing dedicated workspace pages, the global Activity drawer, or the full Reality Inspector.
- Changing business calculations, application services, APIs, persistence, tenant boundaries, or the domain model.
- Applying the pattern to Data Sources, Facts, Analytics, Activity, Playground, or the technical Inspector record catalog in this first slice.
- Making every table row expandable when no useful read-only preview exists.

### Existing Contracts

- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/WEB_UX_MATRIX.md`](../../docs/WEB_UX_MATRIX.md)
- [`docs/TAILADMIN_UI_AUDIT.md`](../../docs/TAILADMIN_UI_AUDIT.md)
- [Business Reality Constitution](../../.specify/memory/constitution.md)
- Spec 137 register workbench and Spec 152 daily work lists

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview a daily-work record in context (Priority: P1)

As an operations user scanning Commitments, Exceptions, or Decisions, I can expand a read-only preview directly below a row so I understand the record without losing its position in the work list.

**Why this priority**: These compact queues are the clearest and most frequent expression of the requested interaction.

**Independent Test**: On each daily-work page, open a row by mouse and keyboard, verify that its preview appears immediately below it, then close it without page navigation or horizontal displacement.

**Acceptance Scenarios**:

1. **Given** a collapsed daily-work row, **When** the user activates its preview affordance, **Then** a read-only preview appears immediately below that row and the affordance announces the expanded state.
2. **Given** one expanded row, **When** the user previews another row in the same list, **Then** the first preview closes and the second opens without losing the user's list position.
3. **Given** an expanded preview whose data cannot be loaded, **When** the failure is returned, **Then** the row remains identifiable and the preview offers a non-mutating retry and close path.

### User Story 2 - Distinguish preview from navigation and work (Priority: P1)

As an operator, I can tell before activating a control whether it reveals a preview, navigates or filters, starts editing, or begins an operational action.

**Why this priority**: Inline disclosure is only trustworthy if adjacent controls do not reuse its visual language for different outcomes.

**Independent Test**: Review the included pages at desktop and mobile widths and verify every relevant control against the shared action-semantic matrix and its accessible name.

**Acceptance Scenarios**:

1. **Given** a row with preview and navigation options, **When** it is rendered, **Then** preview uses a disclosure chevron, navigation uses a directional navigation icon, and both retain visible text where ambiguity would otherwise remain.
2. **Given** a row with edit or operational actions, **When** it is rendered, **Then** those actions use their own explicit labels and icons and do not look like disclosure controls.
3. **Given** an icon-only control at a constrained width, **When** assistive technology reads it or the user hovers it, **Then** its accessible name and tooltip communicate the resulting action rather than only the object name.

### User Story 3 - Preview workspace register rows (Priority: P2)

As a user scanning Sales, Purchasing, Warehouse, Finance, or Master Data, I can inspect a concise record summary beneath its row and deliberately choose a separate link when I need a focused workspace, filtered register, edit form, or full trace.

**Why this priority**: These denser registers benefit from contextual inspection but contain more actions that must remain separate.

**Independent Test**: In every included workspace, expand records with and without secondary actions and verify that the preview is read-only, row-aligned, responsive, and does not trigger navigation or mutation.

**Acceptance Scenarios**:

1. **Given** a dense table row, **When** its preview opens, **Then** a full-width detail row appears immediately after it and spans the table's currently rendered columns.
2. **Given** a preview with related-register links, **When** a link is activated, **Then** the intended workspace or filter opens and the control is visually distinct from the disclosure affordance.
3. **Given** a Master Data row, **When** the preview is opened, **Then** read-only identity, status, and provenance are shown inline while editing remains a separately labelled action.

### User Story 4 - Preserve scanning and responsive behavior (Priority: P2)

As a desktop or mobile user, I can open and close previews without unexpected scroll jumps, stale selection, inaccessible focus, or an unusably wide detail surface.

**Why this priority**: The pattern must remain faster than a drawer across the supported layouts.

**Independent Test**: Exercise disclosure, filters, pagination, reload, and viewport changes using keyboard-only, desktop, and mobile browser checks.

**Acceptance Scenarios**:

1. **Given** an open preview, **When** a filter, tab, page, tenant, or register family changes, **Then** the stale preview closes unless the same record is explicitly preserved by the destination.
2. **Given** an open preview, **When** it closes, **Then** focus returns to its disclosure control and the originating row remains in view where practical.
3. **Given** a narrow viewport, **When** a preview opens, **Then** its content reflows within the register surface and does not create additional horizontal overflow beyond genuinely tabular content.

### Edge Cases

- The selected row disappears after a refresh, status change, filter change, or action completion.
- A preview target exists but its explanation endpoint returns not found or forbidden.
- A register has selectable rows; selection checkboxes must not toggle disclosure and disclosure must not toggle selection.
- A nested button, link, filter value, or action inside a clickable row must perform only its own declared behavior.
- Pagination or incremental loading introduces another record with the same human-readable number; opaque record identity controls disclosure state.
- A preview contains long external references, translated labels, monetary amounts, quantities, or source values.
- A row has no deeper preview beyond information already visible; it must not receive a misleading disclosure control.
- An inline preview links to a mutating workflow; opening the workflow does not count as confirmation and cannot itself mutate business state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST use an inline disclosure immediately below the originating row for read-only previews in Commitments, Exceptions, Decisions, Sales, Purchasing, Warehouse, Finance, and Master Data.
- **FR-002**: The product MUST permit at most one expanded preview per visible register or work list.
- **FR-003**: A preview disclosure MUST expose its collapsed or expanded state visually and programmatically and MUST be operable with pointer, Enter, and Space.
- **FR-004**: Preview content MUST remain read-only; editing, confirmation, correction, allocation, posting, release, receipt, refund, and other operational mutations MUST remain separate workflows.
- **FR-005**: The included surfaces MUST consistently distinguish five interaction meanings: disclose preview, navigate to another destination, apply a related-record filter, edit a record, and begin an operational action.
- **FR-006**: Each interaction meaning MUST have an accessible name describing its outcome; icon-only presentation MUST be limited to contexts where a tooltip and accessible name remove ambiguity.
- **FR-007**: Preview controls MUST use a chevron that changes orientation with disclosure state; navigation, filtering, editing, and operational actions MUST NOT reuse that disclosure-state icon.
- **FR-008**: Dense table previews MUST occupy a detail row immediately following the source row and span all currently rendered columns, including selection or responsive action columns.
- **FR-009**: List previews MUST appear immediately following the source list item within the same bordered list surface.
- **FR-010**: Changing tenant, page, primary tab, workspace, register family, search query, or material filter MUST close a preview that no longer belongs to the current result context.
- **FR-011**: Opening, closing, loading, retrying, or failing a preview MUST NOT change business data or invoke a mutating application operation.
- **FR-012**: Closing a preview MUST restore focus to its disclosure control; opening and switching previews MUST avoid unexpected page-level scroll jumps where practical.
- **FR-013**: Preview content MUST reuse the authoritative read model or explanation data already used by the page or Inspector and MUST NOT reproduce business rules in the browser.
- **FR-014**: Each preview MUST provide an explicitly labelled route to deeper explanation or the full Reality Inspector when additional Source → Evidence → Reality detail is available.
- **FR-015**: On narrow screens, preview content MUST reflow inside the page surface, while genuinely tabular content may retain the existing bounded horizontal scroll behavior.
- **FR-016**: Rows without additional useful read-only content MUST not display a preview affordance.
- **FR-017**: The implementation MUST preserve explicit confirmation for every mutating action and MUST not make row activation itself a mutation.
- **FR-018**: The shared visual semantics MUST be documented in the durable Web UI contract and applied consistently across all included surfaces.
- **FR-019**: The preview disclosure MUST occupy the same trailing action position in every dense register row, regardless of which secondary actions the row offers.
- **FR-020**: Desktop previews MUST organize operational information into a compact two-column hierarchy when at least two meaningful groups are available; narrow viewports MUST reflow the same groups to one column without changing their order or meaning.
- **FR-021**: Dense register rows MUST show only the trailing disclosure chevron for preview. They MUST NOT add a generic eye or unlabeled right-arrow action; any additional icon MUST represent a distinct, outcome-named navigation, filter, edit, source, or operational action.
- **FR-022**: Inline previews MUST use a compact, left-aligned header. The record title and short counterparty or context label SHOULD share one wrapping line, and a generated description MUST be omitted when it merely repeats both values.
- **FR-023**: Sales, Purchasing, Warehouse, Finance, and Master Data register rows MUST keep secondary navigation, filtering, editing, and operational actions out of the dense action cell. Those actions MUST appear as visibly labelled buttons inside the expanded preview; the collapsed row action cell MUST contain only the preview disclosure.
- **FR-024**: Inspector dates and instants MUST retain their exact API values while carrying typed presentation metadata. The web presentation MUST format them with the operator's selected locale and display timezone instead of exposing raw ISO timestamps in business-facing preview rows.
- **FR-025**: All actions belonging to an inline preview MUST share one wrapping footer row when space permits. These buttons MUST use visible outcome labels without decorative or category-only icons.
- **FR-026**: The inline-preview action footer MUST align to the trailing edge near its disclosure control on wide layouts. The disclosure control MUST remain visually transparent without a filled hover or focus background.

### Domain and Traceability Requirements

- **DR-001**: The feature MUST preserve the existing SourceRecord → Document/DocumentLine → Reality trace and only change how existing explanations are presented.
- **DR-002**: The feature MUST introduce no business fields, statuses, relationships, schema changes, stored derivations, or alternative authority.
- **DR-003**: Preview reads MUST continue through existing tenant-scoped application services and endpoints; the frontend MUST NOT perform direct persistence access or business calculations.
- **DR-004**: Human-readable numbers and labels MUST remain presentation values; preview identity and selection MUST use opaque tenant-scoped record identifiers.
- **DR-005**: Values stated by a source MUST remain distinguishable from derived observations within preview content and MUST not be recomputed for display.

## Success Criteria *(mandatory)*

- **SC-001**: In browser verification, 100% of sampled read-only preview activations on the eight included surfaces open directly below their originating row without opening a right-side or centered overlay.
- **SC-002**: In an interaction inventory of the included surfaces, 100% of preview, navigation, related-filter, edit, and operational-action controls match the documented semantic icon-and-label category.
- **SC-003**: Keyboard-only verification can open, switch, retry, and close previews on every included surface with visible focus and correctly announced expanded state.
- **SC-004**: Desktop and mobile visual verification shows no new page-level horizontal overflow and no preview detached from its originating row.
- **SC-005**: Existing tests for confirmation, tenant isolation, calculations, traceability, and application-service boundaries remain green with no database migration.
- **SC-006**: Every FR and DR has an acceptance scenario and executable proof or a documented static-review proof in the plan and tasks.

## Assumptions and Dependencies

- “Master Data” means the customer, supplier, item, and location registers; specialized settings catalogs and source-system configuration are excluded from this first slice.
- A preview is concise operational context, not an unbounded copy of the full inspector. Technical fields and original payload remain behind an explicit deeper-inspection route.
- The entire row may remain a disclosure target in simple work lists. Dense tables use an explicit disclosure control so links, filters, selection, and actions remain predictable.
- Existing APIs are expected to provide sufficient preview data. Any discovered API gap must be returned to product review rather than silently expanding backend scope.
- The global Activity drawer remains unchanged because it is shell-level context rather than row-local preview.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-002, FR-009 | US1 scenarios 1–2 | Daily-work disclosure component and browser matrix |
| FR-003, FR-006, FR-007, FR-012 | US1 scenario 1; US2 scenarios 1–3; US4 scenario 2 | Component accessibility tests and keyboard browser journey |
| FR-004, FR-011, FR-017 | US2 scenario 2; edge-case mutation link | Confirmation regressions and static handler review |
| FR-005, FR-006, FR-007, FR-018 | US2 scenarios 1–3 | Interaction inventory and Web contract review |
| FR-008, FR-015 | US3 scenario 1; US4 scenario 3 | Register component tests and desktop/mobile visual matrix |
| FR-010 | US4 scenario 1 | Routing/filter/pagination component tests |
| FR-013, FR-014 | US3 scenario 2 | Read-model reuse tests and traceability browser journey |
| FR-016 | Edge case: no additional content | Static inventory and component test |
| DR-001, DR-002, DR-005 | US3 scenarios 1–3 | Constitution review and inspector-content regression tests |
| DR-003, DR-004 | US1 scenario 3; identity edge case | Tenant/API boundary regressions and opaque-ID component test |
