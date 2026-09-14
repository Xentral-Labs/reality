# Consistent register workbench
**Language**: English
## Context and Intent
The owner requests compact, screenshot-inspired table workspaces for Orders & deliveries, Warehouse, Finance, Facts and Master data. Tables, tabs, filters and actions should form one coherent workspace.
### Non-Goals
No new business mutations, bulk financial actions, schema changes or changes to dashboard/chat. CSV exports are presentation snapshots of selected visible rows, not lossless source exports.
## User Scenarios & Testing
US1: Switch compact tabs, search/filter on the left, start existing actions from the same toolbar on the right.
US2: Scroll rows with sticky headings and a persistent footer. Select rows on the current page and export their visible data columns as CSV.
## Requirements
- **FR-001**: Compact page title, horizontal tabs, unified table surface and toolbar. Existing page actions appear at the table toolbar right; row actions retain their contextual location.
- **FR-002**: Shared footer holds current-page selection/export and pagination/page size; visible columns, sorting, resizing, row density and detail navigation remain supported.
- **FR-003**: Selection applies only to the current loaded page, clears on tenant/view/filter/page changes and never implies all server rows. Export only selected visible non-action columns; escape CSV quotes/newlines and neutralize spreadsheet formulas. No network write.
- **FR-004**: Preserve existing financial summaries, explanations, errors, empty states, permission checks and reviewed command paths. Responsive wrapping at 390px, no document-wide horizontal overflow, light/dark and four languages.
## Assumptions and Dependencies
Existing tenant-scoped services, TableContext and RegisterTable remain authoritative. User approved this presentation scope; CSV is a bounded read-only batch utility. No new backend API.
## Success Criteria
Browser checks prove consistent toolbar, compact tabs, footer, selection/export reset and existing table controls. Build, frontend contracts, localization, formatting and spec gates pass.

## Requirement Traceability
FR-001: workspace/order/finance/facts browser layouts and action continuity. FR-002: table browser density, preferences, server sorting/paging, sticky geometry. FR-003: table browser CSV download content, formula neutralization, current-page selection/reset and no writes. FR-004: localized desktop/mobile screenshots, error/empty/tenant/Inspector checks. All map to T002..T004.

## Reference-style register chrome
- **FR-005**: Five workspaces use one compact title/tab strip inside the global header (placement refined by FR-006). Remove large introductory page blocks from the table path, retaining explanations in accessible expandable guidance. The table toolbar has search left and a single Actions group right; a second row holds existing filters plus shared column visibility and density controls; result counts follow above rows. Shared footer and current action permissions/confirmations remain. Facts search still submits explicitly. Menus support keyboard access, Escape and outside dismissal. Reflow at narrow widths without page overflow.
Acceptance: tab switching, toolbar positions, action-menu form entry, filter/table control continuity and footer geometry on desktop/mobile, with existing workspace/table fixtures.

## Single header and filter chips
- **FR-006**: On desktop, register title and tabs render inside the actual global header, between branding and company/utility controls. No second register heading row. Narrow screens may wrap inside the header to retain usable tabs. Filters use compact icon/label/current-value dropdown chips with no separate visible labels; preserve accessible names and existing native select behavior. Density becomes a Normal/Compact dropdown, Columns remains a dropdown with an icon. Search, actions, counts and footer keep their current semantics.

- **FR-007**: Reality Inspector and all Company destinations share the actual global-header title/tab placement used by operational registers. Inspector retains its group-local tabs; Settings moves its four section links out of the content sidebar; Data & sources moves its three tabs into the header; Master data retains its existing header. Nested Facts must not render a second header. Existing URLs, accessible names, selected state, company boundaries and action handlers remain. Narrow screens retain locally scrollable tabs.

- **FR-008**: Name the delivery tab Commitments, matching the Reservations and Movements terminology in Warehouse, retaining Orders & deliveries as the page/menu name and the existing deliveries route value. Replace its introductory hint with a concise explanation that commitments are promises to customers or from suppliers, reservations bind stock and movements record actual execution. Preserve all filters, calculations and actions. User accepted this wording.

## FR-009: Consistent page introductions
Approved by the product owner on 2026-09-09. Every authenticated application page has one short translated description directly below the global title/tabs and before filters/content. The text follows the active subview. Titles use the shared global header; duplicate in-content page introductions are removed. The introduction is a compact full-width information box at the start of the middle content area, with a subtle surface, fine border, 8px corners and 12px/16px padding. It has no heading or disclosure and wraps naturally on narrow screens. Header and tabs retain their existing placement. Preserve contextual accounting, correction, provenance and interaction help.

Acceptance: navigating every primary route and subview changes the description appropriately; legacy aliases remain meaningful; no duplicate page title appears; descriptions remain visible during loading/error/empty states; all four languages are supported. Keyboard navigation, filters, graph controls, business actions and tenant scope remain unchanged. Public/auth pages and modal redesign are outside this change.

The information strip directly adjoins the content for simple registers (Warehouse, Finance, operational Facts, Master data, Inspector All records and Fact rules): one outer border, a subtle divider and no inter-box gap. Multi-section and visualization pages retain a separate compact intro box so unrelated panels are not enclosed in a second frame.

## FR-010: Two-line global header
The owner approved moving the explanation into the existing application header.
Its first line holds title, tabs and existing page actions; the second line holds the
short view description. There is no extra information box or duplicate content title.
This supersedes FR-009's box variants. Header height follows wrapping text/actions;
sticky navigation and chat follow its measured height. Mobile keeps usable controls
without overlap. Search-submit buttons remain in their forms. Page actions preserve
handlers, native form association, authorization and confirmation boundaries.
General duplicate introductions are removed; specific warnings and source/correction
semantics remain near their content.

Owner explicitly removes the general Finance posting/currency paragraph, Facts About this view, Warehouse introduction and other repeated view explanations. Current errors, selected-record guidance and operational restrictions are retained.

### FR-010 placement correction
The owner now selects the middle content area as the final location. Its first element
is one white rounded introduction surface with a small accent icon, view title and
subtitle on the left, existing page actions on the right. The global header returns
to its compact title/tab layout. No explanation is repeated in the header or body.
Actions wrap under the introduction on mobile; form and action behavior is unchanged.
This explicitly supersedes the preceding two-line global placement.

## FR-011: Underlined header tabs
Format all existing global-header subview controls as tabs: transparent background,
no rounded pill or shadow, and a 2px accent underline for the active view. Inactive
labels are muted, with clear hover/focus feedback. Preserve labels, click handlers,
selected attributes, native keyboard behavior and horizontal scrolling on narrow
screens. Only presentation changes; the middle introduction stays unchanged.

FR-012: Outer content cards use consistent 12px corners, including painted toolbar/header/footer children. Menus must remain unclipped. Embedded event history omits the redundant company name; the standalone activity drawer retains it.

FR-013: Page registers with pagination footers fill the available viewport below their controls, keeping the footer at the bottom and scrolling rows independently. Account for wrapped footers and changing summaries. Dialog tables retain their existing layout; on short screens preserve at least 160px for rows and allow page scrolling.

FR-013 clarification: the fixed footer spans the entire center column, outside the inset table card, from sidebar to chat or to the right viewport edge when chat is closed. Recompute on center-column resize; dialogs keep local footers.

FR-014: Remove redundant general explanatory notes from Decisions, Exceptions, Reports, Context timeline, Home activity and Event history. Preserve Reports observation timestamp and operational errors, limitations and history-boundary indicators. Shared page introductions remain.

FR-015: Replace Orders & deliveries navigation with Sales and Purchasing (German Verkauf and Einkauf). Each opens its own customer/supplier orders and offers a Deliveries tab limited to the corresponding direction. Existing URLs and record links remain valid; Commitments stays a shared open-work list. Switching workspaces clears record, search and paging scope.

FR-016: Profile timezone uses a native select with readable city/region labels and UTC. Offer browser-supported IANA zones, retain the saved zone, and persist the canonical zone identifier through the existing preferences form.
