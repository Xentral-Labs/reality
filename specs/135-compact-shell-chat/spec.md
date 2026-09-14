# Compact shell and persistent chat
**Language**: English
## Context and Intent
The owner explicitly requests these UI changes now, superseding the prior order that postponed UI changes until functional closure. Use the supplied screenshot as a layout reference.
### Non-Goals
No new business logic, analytics metrics, provider, chat authority, legacy retirement or practice admission changes.
## User Scenarios & Testing
US1: An operator scans dense navigation and scrolls a register while the slim header stays visible.
US2: An operator chats alongside work, hides/reopens the panel without losing a draft, changes workspace, and opens existing proposal reviews. Changing company clears chat state.
US3: An operator finds a dedicated Analytics navigation section before the Reality Inspector and Company groups, with Reports as its first destination.
## Requirements
- **FR-001**: Header is 56px and sticky at top; desktop sidebar is 200px with approximately 36px navigation rows, smaller group spacing and independent sticky scrolling below the header.
- **FR-002**: Desktop chat is initially open as a right column, approximately 400px wide, toggleable from the header. Closing expands content; navigation and hide/reopen retain the same chat instance and draft. Company change remounts it. At less than 1024px it is initially closed and opens as a full-width panel below the header, with an accessible close control. No horizontal page overflow.
- **FR-003**: Reuse ChatPage and existing tenant-scoped APIs, sessions, contextual links, send recovery and proposal confirmation boundaries. Exactly one global chat instance; /app/copilot opens the dock with the home workspace behind it. The contextual delivery button opens this same dock with the selected delivery context; it does not create a second inline chat. Hidden chat is not keyboard accessible. Chat and workspace scroll independently.
- **FR-004**: Analytics is a dedicated navigation section before the Reality Inspector and Company groups, styled like the other section headings. Its first and currently only destination Reports opens existing analytics content at /app/analytics. Analytics itself is not a duplicate destination. The Analytics group name remains Analytics in every language; report labels are localized. Legacy exits are removed under FR-008.
- **FR-005**: Preserve light/dark, four languages, mobile navigation, existing shared ERP table semantics and accessible labels.
## Requirement Traceability
FR-001..005: new isolated browser acceptance in apps/web/scripts/unified-shell-chat-browser.mjs; existing unified app/delivery/activity browser, all frontend contracts/localization/build/format. Existing service contracts unchanged; no new domain test required.
## Assumptions and Dependencies
All repository content is English. Existing timeline, chat and app services remain authoritative. This implements only the four requested UI changes; completion plan functional gates remain open.
## Success Criteria
Browser proves 56px sticky header, compact rows, nav order, draft retention across hiding and navigation, company isolation, one global composer and 390/1440/1920px layouts. Required checks pass.

## Company selector refinement
- **FR-006**: Replace the native header company select with a compact custom popover inspired by the existing application: company initials, full names, selected checkmark and explicit practice labels. Duplicate names expose opaque IDs for disambiguation. Support a scrollable list, keyboard access, Escape and outside dismissal, focus return, mobile viewport bounds and all themes/languages. Use the existing switchCompany callback and tenant isolation unchanged. Remove the redundant Company settings header button; settings remain reachable in the sidebar.
Acceptance: open, dismiss, select another tenant and verify chat reset; active company is marked, duplicate/practice labels are visible and the menu fits 390px.

## Single chat entry refinement
- **FR-007**: Daily work navigation contains only Home, Your work, Exceptions and Decisions. Remove the redundant Ask Reality sidebar destination. Keep the header chat toggle, contextual entry points, conversation history and existing /app/copilot deep links.

## Remove legacy exits
- **FR-008**: Remove all twelve audited legacy/Playground exit sites from the unified UI: sidebar support links, advanced order/warehouse/finance links, master-data advanced link, technical explorer, delivery fallback, decision fallback, chat fallback, sandbox-company exit and role-less party receipt fallback. Unsupported proposals remain visible with a localized unavailable-review explanation; chat opens Decisions. Sandbox companies remain blocked from unified operations with an explanation and buttons to switch to an available non-sandbox company. Unknown-role party receipts open the scoped Inspector record search. Preserve underlying records, old routes and existing supported action confirmation flows. This removes navigation, not the legacy application or practice data.
Acceptance: no audited legacy destinations in unified source, shell has no migration links, unsupported decisions explain availability, and practice selection offers a non-legacy way back. Build/localization/contracts and existing shell/application browser checks apply.
