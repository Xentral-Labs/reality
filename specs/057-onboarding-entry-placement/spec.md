# Feature Specification: Onboarding Entry Placement

**Feature Branch**: `[057-onboarding-entry-placement]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "Currently this Get started is in the list on the left — can you put it on the right in place of Automation, and remove it on the left?"

## Context and Intent

### Problem

A company with nothing operational imported is addressed twice on the same screen, and neither address is where it is needed.

The sidebar carries a `Get started` navigation group holding a single link. A group header, a section label and one entry are spent on one destination, in the column whose job is to list the workspace's Views.

The fourth panel on Home, meanwhile, explains how far automation may eventually go. It is titled `Automation`, it names the stage the company is in, and it lists the record kinds Reality would observe. To a company that has imported nothing, none of that is answerable yet: automation is a question about records that do not exist. The panel that gets the most attention on the landing surface is spent on the question the reader cannot ask, while the question they do have — where do I begin — is a link in the navigation column.

### Scope

- Move the onboarding entry to Home's fourth panel while the company has no operational records.
- Restore that panel to `Automation` as soon as operational records exist.
- Remove the `Get started` navigation group from the sidebar.
- Keep every route that existed reachable.

### Non-Goals

- Changing the empty-company setup surface that Home already shows before any activity exists.
- Changing what `Sources & imports` is or does, or its route.
- Changing the Automation panel's own content for a company that has records.
- Adding a dismissible or step-tracking onboarding state; the panel is derived from capabilities, not from progress a person marks.

### Existing Contracts

- [Workspace Views and Actions](../046-workspace-views-actions/spec.md)
- [Complete Workspace Navigation](../056-complete-workspace-navigation/spec.md)
- [Web UI Specification](../../docs/WEB_SPEC.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Be told where to begin where the answer is read (Priority: P1)

As someone whose company has imported nothing operational yet, I find the first step on Home, in the panel that would otherwise discuss automation.

**Why this priority**: The landing surface is what a new company reads first; the first step belongs in it, not beside it.

**Independent Test**: Open Home for a company with no operational, warehouse or finance records and read the fourth panel.

**Acceptance Scenarios**:

1. **Given** a company with no operational records on the cross-functional default, **When** Home renders, **Then** the fourth panel is `Get started` and states the first step.
2. **Given** that panel, **When** it is read, **Then** it names what follows the first step: accepting records and verifying the derived facts.
3. **Given** that panel, **When** its footer control is used, **Then** the source-and-import surface opens.
4. **Given** an area is chosen explicitly rather than the cross-functional default, **When** Home renders, **Then** the onboarding panel is not shown for that area.

### User Story 2 - Meet the automation question when it is answerable (Priority: P1)

As someone whose company has operational records, I see the Automation panel unchanged.

**Why this priority**: The panel is correct once there is something to automate; only its timing was wrong.

**Independent Test**: Open Home for a company with operational, warehouse or finance records.

**Acceptance Scenarios**:

1. **Given** a company with operational records, **When** Home renders, **Then** the fourth panel is `Automation` with its stage, explanation and observed record kinds.
2. **Given** the first operational records arrive, **When** Home is loaded again, **Then** the panel has changed from `Get started` to `Automation` with no other change to the page.

### User Story 3 - Read navigation as workspace navigation (Priority: P2)

As any user, the sidebar lists the Views of the selected workspace and nothing else.

**Why this priority**: A one-entry group with its own header competes with the workspace it sits above and repeats what Home now says.

**Independent Test**: Open the sidebar for a company with no records and compare its groups against the workspace catalog.

**Acceptance Scenarios**:

1. **Given** a company with no records, **When** the sidebar renders, **Then** no `Get started` group appears.
2. **Given** the group is gone, **When** the source-and-import surface is looked for, **Then** it is reachable from Home and from company configuration.

### Edge Cases

- A company with activity but no operational, warehouse or finance capability — the state shown in the reported screen.
- A brand-new company with no activity at all, which keeps its existing setup surface rather than gaining a second one.
- A company whose first records arrive while Home is open.
- An area selected explicitly while the company is still empty.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Home MUST render the onboarding panel in place of the Automation panel while the company has no operational, warehouse or finance records and the cross-functional default area is selected.
- **FR-002**: Home MUST render the Automation panel unchanged in every other case.
- **FR-003**: The onboarding panel MUST state the first step, the steps that follow it, and a control that opens the source-and-import surface.
- **FR-004**: The sidebar MUST NOT render a `Get started` navigation group in any state.
- **FR-005**: The source-and-import surface MUST remain reachable without the removed group.
- **FR-006**: The panel condition MUST be derived from the same capability facts the rest of Home already reads, not from a second source of truth.
- **FR-007**: Every string the panel introduces MUST be covered in all supported interface languages.

### Domain and Traceability Requirements

- **DR-001**: The change is presentation only; it MUST NOT add or alter a route, command, projection, permission or Reality state.
- **DR-002**: It MUST add no table, column, endpoint or domain mutation.
- **DR-003**: No destination that was reachable before MUST become unreachable.
- **DR-004**: An automated contract MUST pin the entry to one place, forbidding the sidebar group and requiring the Home panel, so it cannot return to both.

### Key Entities *(when data is involved)*

- **Onboarding entry**: The single placement of the first-step invitation, derived from whether any operational capability exists.

## Success Criteria *(mandatory)*

- **SC-001**: A company with no operational records reads the first step in Home's fourth panel and reaches source configuration in one click from it.
- **SC-002**: A company with operational records sees the Automation panel exactly as before.
- **SC-003**: The sidebar shows only workspace Views, with no onboarding group in any state.
- **SC-004**: Interface-language coverage passes for every supported language with no missing string.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Operational, warehouse and finance capabilities remain the right signal for "nothing operational imported yet"; they are what the sidebar already used for this decision.
- The fourth panel remains the right place for whichever of the two questions is live; the panel count on Home does not change.
- `Sources & imports` remains company configuration and keeps its route.
- The existing empty-company setup surface on Home continues to cover a company with no activity at all.

## Open Questions

None. Which of the two panels is live is decided by whether operational records exist, which the dashboard already reports.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001-FR-002 | US1 scenario 1, US2 scenarios 1-2 | Home panel contract for both capability states |
| FR-003 | US1 scenarios 2-3 | Panel content and route contract |
| FR-004-FR-005 | US3 scenarios 1-2 | Sidebar contract forbidding the group; configuration route retained |
| FR-006 | US1 scenario 4, US2 scenario 2 | Condition derived from the dashboard capabilities Home already reads |
| FR-007 | US1 scenarios 1-3 | Interface-language audit across all supported languages |
| DR-001-DR-003 | US1-US3 | Diff review for presentation-only change and reachability of every route |
| DR-004 | US1 scenario 1, US3 scenario 1 | Workspace navigation contract test asserting the single placement |
| SC-001-SC-005 | All scenarios | Full required quality gates |
