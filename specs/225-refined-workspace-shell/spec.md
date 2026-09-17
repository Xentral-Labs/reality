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
No further navigation taxonomy changes, report redesign, business rules, API changes,
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
An operator finds Activities in the Inspector navigation, Actions at the bottom and Appearance
inside the profile menu; company and simulation controls stay together.
**Independent Test**: Open each relocated control with a keyboard.
**Acceptance Scenarios**:
1. Activities opens the existing current-company history page; no duplicate Activity
   utility remains. Actions opens the existing catalog launcher without clipping at the sidebar edge; Escape restores launcher focus.
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
- **FR-003**: Keep Actions in sidebar utilities and Appearance in Profile;
  preserve catalog permissions, errors, action confirmation and keyboard dismissal.
- **FR-008**: Rename the Inspector history destination and tab to Activities (German:
  Aktivitäten), retaining history URLs. Remove the duplicate bottom Activity trigger
  and its shell-only state/drawer. Preserve shared timeline services and other consumers.
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

## Follow-up scope review
The owner requested the Activities rename and complete removal of the duplicate lower
entry. There are no unresolved clarifications. Its backend and drawer component also
serve the main history page, Home and graph inspection; they are not exclusive code.

| Requirement | Story | Tasks | Verification |
|---|---|---|---|
| FR-008 | US2 | T010–T012 | Navigation contract, shell browser, shared drawer browser |

## Action translation regression
FR-007 requires localized control names. Five shipping/tracking entries loaded from
`action_discovery.json` lack translations and fall back to English even when German
is selected. Restore the existing requirement in all supported dictionaries. A
regression test must cover every category, group and entry label from the executable
discovery catalog, including future additions. No API or command definitions change.

## Command palette presentation follow-up
FR-009: Replace the bottom Actions navigation item with a quiet search trigger and
platform shortcut hint in the company area. Cmd+K on macOS and Ctrl+K elsewhere open
a centered, viewport-bounded action palette. Show all currently permitted global
launcher entries grouped as before; search continues matching translated labels.
Focus search on opening, clear previous queries, support Escape and restore focus.
Keep a pointer/touch entrypoint in expanded, collapsed and mobile navigation. Do not
intercept the shortcut while another modal is open. Preserve existing action forms,
permissions, catalog shortcut and confirmation. No new command execution or search
scope; future palette capabilities belong to a separate specification.

## Quiet shell boundaries follow-up
FR-010: Remove horizontal rules below the workspace and docked chat headers, the
sidebar's right border and the full-width page-tab baseline. Retain the active tab
indicator and subtle vertical divider between content and chat. Sidebar background,
spacing and existing focus styles preserve orientation. Content tables, lists and
forms keep their existing boundaries; no layout geometry or behavior changes.

## Sidebar head grouping follow-up
FR-011: Treat logo and company name/context as one switcher target in a compact head
row, with desktop collapse control at its right and mobile close control retained.
Below it, present the existing action palette trigger as a quiet search field with
short Search wording and platform shortcut. Remove the visible Daily work heading;
retain its navigation landmark label. Tighten secondary company-context spacing.
Preserve rail access, company menu, simulation eligibility, routes and action scope.

## Unified tab header follow-up
FR-012: Pages with multiple register tabs show those tabs in the workspace header
instead of a duplicate visible title. Pages without multiple tabs retain the title.
Keep one accessible page heading and the existing page-information disclosure.
Move existing page actions to the right of the same header, with an icon-only chat
toggle and tooltip. The current register count appears beside the active tab; pages
without tabs keep their title count. Tabs scroll horizontally when space is limited;
mobile uses a compact labeled action-menu trigger. Preserve routes, tab selection,
filters, permissions, action confirmation, counts and chat drafts. Apply through the
shared register/header contract, including integrations where multiple tabs exist.

## Commitments header regression
FR-012 also applies to the Commitments customer/supplier direction tabs. Route this
legacy inline strip through RegisterHeader. Keep direction selection and service
reads unchanged. The active side uses the shared filtered list count; the inactive
side retains its existing unfiltered overview count, without duplicating the active
count. No other top-level inline page tabs were found; row-level filters stay local.

## Inbox navigation consolidation
FR-013: Replace the three daily-work sidebar entries with one Inbox entry, without
an aggregate badge. Inbox defaults to Commitments and is active for all three existing
routes. Its header tabs are Commitments, Exceptions and Decisions. Preserve existing
URLs, tenant scope, side/filter navigation, action confirmation and back/reload behavior.
Customer/supplier direction and exception finding/rule selection become subordinate
local controls, retaining their existing reads and overview counts. The header count
belongs to the active register, not a sum of unlike queues. Home and Chat remain separate.
Inbox is the product label in all supported languages. No new AI behavior or backend.

## Empty standalone chat history
FR-014: Hide the standalone conversation column when no active or archived sessions
exist. Base automatic desktop visibility on the first successful history read for
this company/page visit. Creating the first session must not automatically change
layout; a history button then permits explicit opening. Reopening the page with saved
history restores desktop history. Keep New chat accessible independently of the column,
preserve mobile overlay behavior, drafts, archived access and company isolation.
