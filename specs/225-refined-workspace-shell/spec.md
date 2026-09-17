# Feature Specification: Refined workspace shell

**Feature Branch**: `225-refined-workspace-shell`
**Language**: English
**Created**: 2026-09-17
**Status**: Implemented and verified (web scope)
**Input**: Implement the approved Lightfield-inspired concept in an isolated worktree.

## Context and Intent

### Problem
The continuous global header mixes company context, page context, simulation state
and global actions. Heavy outlines, accent colors and stacked descriptions compete
with operational content.

### Scope
Move company context into the primary sidebar; give content and side chat aligned,
compact headers; relocate global utilities; refine shared shell typography and spacing.
The owner approved this concept with “ok mach in einem worktree”.

### Non-Goals
No navigation taxonomy changes, report redesign, business rules, API changes,
new data, migrations, chat behavior changes or simulated report content in the product.

## User Scenarios & Testing

### User Story 1 - Focus on the workspace (Priority: P1)
An operator sees company context in the sidebar and a quiet title above their work.
**Independent Test**: Open Home, a register and standalone Chat at desktop widths.
**Acceptance Scenarios**:
1. Given an expanded desktop sidebar, when a page opens, then the company switcher
   is inside the sidebar and only page context and chat access occupy its 48px header.
2. Given the side chat is open, its header and the page header start at the same
   vertical position; opening or hiding chat preserves the draft and page state.
3. Given a page description, it remains keyboard-accessible through a disclosure,
   without permanently adding a subtitle row.

### User Story 2 - Reach global functions (Priority: P1)
An operator finds Activity and Actions at the bottom of navigation and Appearance
inside the profile menu; company and simulation controls stay together.
**Independent Test**: Open each relocated control with a keyboard.
**Acceptance Scenarios**:
1. Activity opens the current-company drawer and Actions opens the existing catalog
   launcher without clipping at the sidebar edge; Escape restores launcher focus.
2. Profile exposes the existing appearance toggle; themes persist as before.
3. Company switching resets company-scoped context; the simulation link retains its
   eligibility, freshness, destination and reduced-motion behavior.

### User Story 3 - Use compact and mobile layouts (Priority: P2)
An operator can collapse the sidebar or use a narrow screen without losing controls.
**Independent Test**: Exercise 320, 390, 1024 and 1440px layouts in both themes.
**Acceptance Scenarios**:
1. The 60px rail retains company switching, navigation, global utilities and profile
   with accessible labels; expanding retains draft, selection and stored preference.
2. Mobile offers navigation and chat directly in the header, with company context and
   utilities inside the labeled drawer. Menus fit the viewport and can be dismissed.
3. Long company names and localized labels do not cause page-level horizontal overflow.

### Edge Cases
Short desktop height scrolls navigation while keeping utilities usable. The action
launcher and company/profile popovers stay visible outside scroll containers.
Hidden or unauthorized simulation state shows nothing. Standalone Chat and Storyline
never reserve an empty side-chat column. Blocked preference storage keeps the existing
safe navigation fallback. Touch targets remain at least 44px. Company-scoped menus
close on company change. Browser zoom follows the responsive layout.

## Requirements

### Functional Requirements
- **FR-001**: Place company identity/switching in a full-height desktop sidebar;
  preserve all existing destinations and company-management actions.
- **FR-002**: Use a 48px single-row page header with title, inline count, optional
  description disclosure and direct chat toggle; remove decorative page icon and
  permanent subtitle. Open side chat starts at the top of the workspace on desktop.
- **FR-003**: Move Activity and Actions to sidebar utilities and Appearance to Profile;
  preserve catalog permissions, errors, action confirmation and keyboard dismissal.
- **FR-004**: Place the existing live simulation indicator below company identity,
  retaining all data, polling and eligibility semantics.
- **FR-005**: Preserve collapse persistence, draft/page state, company isolation,
  standalone chat sizing and mobile labeled navigation; keep all moved controls usable.
- **FR-006**: Use neutral active navigation and tabs, 13px navigation/tabs, 14px page
  titles, 12px secondary shell text, regular/medium weight and consistent small icons.
  Keep body and business-table typography intact. Light and dark surfaces remain legible.
- **FR-007**: Preserve localized names, keyboard focus visibility, meaningful accessible
  names, 44px coarse-pointer targets and viewport-bounded menus at widths from 320px.

## Success Criteria
- **SC-001**: Desktop page and side-chat headers are 48px high and top-aligned.
- **SC-002**: Every relocated control is reachable in expanded, collapsed and mobile modes.
- **SC-003**: The four supported languages and both themes have no page-level overflow
  at 320, 390, 1024 and 1440px in the acceptance fixtures.
- **SC-004**: Hiding chat or collapsing navigation preserves drafts; company switch
  clears prior-company chat context.

## Assumptions and Dependencies
The existing React shell, native popovers, company switcher, action discovery,
activity drawer and shared chat services are reused. Existing 200px expanded/60px
collapsed sidebar widths and chat widths remain, avoiding unnecessary layout churn.
This supersedes the placement/visual portions of specs 135, 173, 188, 203 and 207,
not their functional or authorization contracts. Implementation uses origin/main;
uncommitted work in the original checkout is not imported.

## Requirement Traceability

All repository artifacts are written in English; UI translations remain localized.

| Requirement | Story | Tasks | Verification |
|---|---|---|---|
| FR-001 | US1 | T002, T005 | Refined shell browser: company placement |
| FR-002 | US1 | T002, T005 | Refined shell browser: alignment, description, chat |
| FR-003 | US2 | T003, T006 | Refined shell browser: utilities and theme |
| FR-004 | US2 | T003, T006 | Simulation browser: state, stale response, visibility |
| FR-005 | US3 | T002, T004, T005, T007 | Refined shell and navigation browsers |
| FR-006 | US3 | T004, T007 | Layout matrix and screenshot review |
| FR-007 | US3 | T004, T007 | Keyboard and localized layout matrix |
