# Feature Specification: Collapsible primary navigation

**Created**: 2026-09-15
**Language**: English
**Status**: Scope authorized by user request and supplied collapsed/expanded sidebar references.

## Context and Intent

### Problem
The primary sidebar consumes horizontal space even when a user already knows the navigation icons.

### Scope
An explicit desktop toggle switches the main sidebar between its existing labeled navigation and a narrow icon rail, preserving every destination and profile access.

### Non-Goals
Changing business behavior, rearranging navigation, collapsing conversation history, changing mobile navigation, or introducing server preferences.

## User Scenarios & Testing

### User Story 1 - Make room while keeping navigation (Priority: P1)
A user collapses the primary navigation to icons and expands it when labels are useful.

**Why this priority**: More space for operational pages and Chat without losing navigation.
**Independent Test**: Toggle the sidebar, navigate with an icon, open Profile, reload and expand.

**Acceptance Scenarios**:
1. Given a desktop without a saved preference, when opened, then labeled navigation and a collapse button appear.
2. Given expanded navigation, when the button is activated by mouse or keyboard, then a 60px icon rail frees horizontal content space, retaining all links and the active indication.
3. Given the icon rail, when a link is hovered, then its localized name is available; keyboard/screen-reader users retain each link's accessible name and visible focus.
4. Given collapsed navigation, when reloading or changing company/page, then it remains collapsed; Profile and the company switcher remain usable.
5. Given the icon rail, when Expand sidebar is activated, then the original labeled navigation returns.
6. Given a narrow screen, when opening the mobile navigation, then all labels remain visible regardless of the saved desktop preference.

### Edge Cases
Invalid or inaccessible browser storage defaults to expanded without preventing toggling. Resizing between desktop and mobile preserves the desktop preference. Navigation groups and all destinations remain scrollable on shorter screens. Existing chat drafts survive toggling.

## Requirements

- **FR-001**: At desktop widths (1024px and above), an accessible toggle MUST switch primary navigation between existing 200px width and a 60px icon rail; content MUST use the released width with or without the chat dock.
- **FR-002**: Collapsed links MUST retain localized accessible names, hover labels, icons, active state and keyboard focus. Profile MUST remain accessible, and the company switcher MUST remain beside the logo in the header.
- **FR-003**: The selected desktop state MUST persist locally across reloads and navigation; blocked or invalid storage MUST safely fall back. Toggling MUST preserve page and chat draft state.
- **FR-004**: Mobile navigation MUST retain its labeled overlay behavior independently of desktop state. Toggle labels MUST support English, German, Dutch and Spanish.

- **FR-005**: Sidebar icon hints MUST use application-rendered dark rounded tooltips with white readable text on hover and keyboard focus, outside the scroll container. Escape, scrolling and navigation MUST dismiss them; native title tooltips MUST be absent.
- **FR-006**: The toggle MUST share the Daily work heading row in expanded navigation and use a plain sidebar icon, avoiding an isolated control row. Collapsed mode retains a centered toggle.

## Success Criteria

- **SC-001**: One activation releases 140px for content; one further activation restores the original width.
- **SC-002**: All previously available destinations and profile actions remain reachable in both states.
- **SC-003**: Reload preserves the desktop choice; mobile navigation remains fully labeled at 390px.

## Assumptions and Dependencies

The user requests the primary sidebar, using supplied images as interaction references. Expanded remains default; local browser persistence is a routine preference. Existing services, company selection and navigation are reused. This is presentation-only, with no domain/schema/tool changes.

## Requirement Traceability

| Requirement | Acceptance | Test | Implementation |
|---|---|---|---|
| FR-001 | 1, 2, 5 | T003 | T004 |
| FR-002 | 3, 4 | T003 | T004 |
| FR-003 | 4 and edge cases | T003 | T004 |
| FR-004 | 6 | T003 | T004, T005 |
| FR-005 | Hover/focus, Escape and scroll acceptance | T007 | T008 |
| FR-006 | Heading-row geometry acceptance | T007 | T008 |
