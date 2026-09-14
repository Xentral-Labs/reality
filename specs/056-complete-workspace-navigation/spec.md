# Feature Specification: Complete Workspace Navigation

**Feature Branch**: `[056-complete-workspace-navigation]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "In Data Management, can you not do this Views and Actions thing, but really just show everything directly?" / "I also don't need actions there, and not Sources & imports either — just the data things, all of them."

## Context and Intent

### Problem

Progressive disclosure is applied to every workspace at the same fixed limits — four Views, two Actions — whether or not there is anything worth hiding.

Two consequences follow. A launcher is offered whenever a workspace has any Action at all, so Data Management shows a single Action and a `More actions` control beneath it that holds nothing the reader cannot already see. And a workspace of five Views renders four of them plus a launcher row: the same five rows as before, for the price of a click.

Only the two long workspaces, Order Operations at seven Views and five Actions and Warehouse Operations at eight and seven, genuinely gain from the limit. Data Management is a reference surface whose point is exactly to have all of it in view.

Its membership was also wrong for that purpose. It carried `Sources & imports`, which configures how source records arrive rather than holding any, and a single Action whose section header cost a row to announce one entry. A workspace of registers should list registers.

### Scope

- Let a workspace declare that it lists its whole navigation directly.
- Mark Data Management as that workspace, and only that one.
- Offer a launcher only when it holds something not already listed.
- Reduce Data Management to its registers: no Actions, and no source-intake configuration.
- Show no Actions section at all for a workspace that commands nothing.

### Non-Goals

- Changing the limits for workspaces that keep progressive disclosure; four Views and two Actions remain the rule.
- Removing the launchers, their search, or their complete listings.
- Reordering, adding, or removing any View or Action.
- Making the exception derivable from a count; it is a declared property of a workspace, not a threshold.

### Existing Contracts

- [Workspace Views and Actions](../046-workspace-views-actions/spec.md)
- [Specialized Workspace Views](../049-specialized-workspace-views/spec.md)
- [Web UI Specification](../../docs/WEB_SPEC.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See a reference workspace whole (Priority: P1)

As someone maintaining master data, I see every register and every action of Data Management in the sidebar, because working across all of them is the job.

**Why this priority**: Hiding a third of a reference surface behind a click makes the surface harder to work with and saves nothing.

**Independent Test**: Select Data Management and count the sidebar entries against the catalog.

**Acceptance Scenarios**:

1. **Given** Data Management is selected, **When** the sidebar renders, **Then** all five of its registers are direct entries.
2. **Given** Data Management is selected, **When** the sidebar renders, **Then** no `More views` control is shown, because it would hold nothing.
3. **Given** Data Management is selected, **When** the sidebar renders, **Then** no Actions section appears at all, rather than a header over an empty state.
4. **Given** source intake is needed, **When** it is looked for, **Then** it is reachable as company configuration rather than as a register of this workspace.
5. **Given** another workspace is selected, **When** the sidebar renders, **Then** it still shows four Views and two Actions directly with its launchers intact.

### User Story 2 - Never meet an empty launcher (Priority: P1)

As any user, I am not offered a control that repeats the list it sits under.

**Why this priority**: A control that adds nothing teaches the reader that controls may add nothing.

**Independent Test**: Select each workspace and compare each launcher's presence against the number of entries it would hold beyond those already listed.

**Acceptance Scenarios**:

1. **Given** a workspace has one Action and shows it, **When** the sidebar renders, **Then** no Action launcher is offered.
2. **Given** a workspace has more Views than it lists directly, **When** the sidebar renders, **Then** the View launcher is offered and holds the complete ordered set, including the direct entries.

### Edge Cases

- A workspace declares complete navigation but has no Actions at all.
- A workspace grows past the point where listing everything is comfortable.
- The application reference is unavailable and no workspace can be resolved.
- A workspace has exactly as many entries as the direct limit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A workspace MUST be able to declare that it lists its complete navigation directly, as an explicit catalog property rather than a count-derived guess.
- **FR-002**: The property MUST be present on every workspace in the served reference, so the browser never has to assume a default.
- **FR-003**: Catalog validation MUST reject a non-boolean value for the property.
- **FR-004**: Data Management MUST declare it, and no other workspace MAY declare it.
- **FR-005**: A workspace that declares it MUST render all of its Views and all of its Actions as direct entries.
- **FR-006**: A workspace that does not declare it MUST keep rendering four Views and two Actions directly.
- **FR-007**: A launcher MUST be offered only when the workspace holds at least one entry of that kind beyond those listed directly.
- **FR-008**: When a launcher is offered, it MUST continue to hold the complete ordered set including direct entries, with its existing search and no-results behavior.
- **FR-009**: A workspace with no Actions MUST render no Actions section, rather than a section header above an empty state.
- **FR-010**: Data Management MUST list only authoritative registers of business data, and MUST NOT carry source-intake configuration or any Action.
- **FR-011**: Source intake MUST remain reachable as company configuration, so removing it from a workspace strands nothing.

### Domain and Traceability Requirements

- **DR-001**: The property is presentation metadata only; it MUST NOT change routes, permissions, ordering, projections, or Reality state.
- **DR-002**: It MUST add no table, column, endpoint, or domain mutation.
- **DR-003**: The complete View and Action sets MUST remain reachable in every workspace, whether directly or through a launcher.
- **DR-004**: Removing a View from a workspace MUST NOT remove its route or its page; it changes navigation only.

### Key Entities *(when data is involved)*

- **Workspace navigation disclosure**: A boolean on each workspace stating whether its navigation is listed whole or progressively.

## Success Criteria *(mandatory)*

- **SC-001**: Data Management reaches each of its five registers in one click, with no launcher and no Actions section shown.
- **SC-002**: No workspace anywhere offers a launcher that holds nothing beyond what is already listed.
- **SC-003**: The four remaining workspaces keep exactly the navigation they had.
- **SC-004**: A non-boolean value for the property fails automated catalog validation before release.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Four Views and two Actions remain the right limit where disclosure applies; this feature does not retune them.
- Data Management stays a reference workspace; if it grows substantially, the declaration is reconsidered rather than automatically outgrown.
- Observing a source-supported fact remains an Action of Company Overview and remains a registered command; removing it from Data Management's sidebar removes neither.
- The workspace catalog remains the single source of navigation composition.

## Open Questions

None. Which workspace lists everything is a product decision, taken explicitly and recorded in the catalog.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001-FR-004 | US1 scenarios 1-3 | Catalog validation tests and the single-declaration assertion |
| FR-005-FR-006 | US1 scenarios 1, 3 | Sidebar disclosure contracts for both kinds of workspace |
| FR-007 | US2 scenarios 1-2 | Launcher-presence contract tied to hidden-entry counts |
| FR-009-FR-011 | US1 scenarios 3-4 | Empty-section contract, workspace membership contract, company configuration route |
| FR-008 | US2 scenario 2 | Existing launcher search and complete-set contracts |
| DR-001-DR-003 | US1-US2 | Diff review for presentation-only change and reachability of complete sets |
| SC-001-SC-005 | All scenarios | Full required quality gates |
