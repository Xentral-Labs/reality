# Feature Specification: One page action bar

**Language**: English

## Context and Intent

### Problem

The shared header of the unified application reserves one slot, right of the page title,
for the actions of the current page. Every page fills it differently. Companies and
Integrations show a blue primary button. Exceptions shows a grey button and Activity used
to show two. Decisions places a sorting note there that is not an action at all, and
Profile & preferences places the Save button of its form there. Master data hides its only
action, Create a record, inside a More actions menu with one entry; Sales and Purchasing
render that menu even when it is empty; Finance and Warehouse fold every action into it,
including the one a user comes for. Integrations renders the same menu in the header on two
of its views and beside the search field on the third. The same intent, "start the main
thing this page is for", therefore appears in four shapes, and the user cannot predict where
the next page keeps it.

### Scope

One shared page action bar for every page of the unified application: every page action
folds into one More actions menu, and a page without actions leaves the slot empty. Every
page reaches the header through that bar;
nothing else is rendered into the slot. On desktop, the heading and action bar stay inside
the middle content column and end at the left edge of the open chat panel.

### Non-Goals

No new commands, forms, reads, routes or discovery metadata. No change to the order,
placement or eligibility rules of `action_discovery.json`, to the global Actions launcher,
to record-level actions inside cards and dialogs, or to the confirmation flow behind any
action. No change to the register toolbar's search, filters or counts.

## User Scenarios & Testing

### US1 — Start the main action of a page

The user opens Master data, Sales, Purchasing, Warehouse, Finance, Integrations, Companies
or Exceptions and looks for the action the page exists for.
Acceptance: the header shows one More actions control whose first entry is the page's first
action (New customer, New order, Reserve stock, New customer invoice, Add integration, New
company, View all possible findings); selecting it starts the same flow as before.

### US2 — Reach the remaining actions

The user needs a less common action on Warehouse movements or Finance open items.
Acceptance: every action sits in the same More actions menu, which opens on click, closes
on Escape with focus returned to its trigger, and lists actions in catalog order.

### US3 — A page without actions

The user opens Home, Commitments, Reports, the Reality Inspector, Facts, Rules, Demo Data
or a company subpage, or opens Deliveries or a selected commitment under Sales.
Acceptance: the slot is empty; no empty menu and no placeholder appears.

### US4 — Notes and form buttons stay with their content

The user opens Decisions or Profile & preferences.
Acceptance: the Decisions sorting note reads next to the filters, the Save preferences
button sits at the end of its form with native form association, and the header slot of
both pages is empty.

## Requirements

- **FR-001**: Provide one shared page action bar. A page declares its actions as an ordered
  list of label and handler; the bar renders every available action inside the existing
  More actions disclosure. An empty list renders nothing. The bar is the only component
  that writes into the header action slot and it renders no separate primary action.
- **FR-002**: Preserve each page's first action as the first menu entry: Companies (New
  company), Integrations (Add integration or Register source), Master data (New customer,
  New supplier, New item or New location by family), Sales and Purchasing orders (the
  catalog's first order action), Warehouse and Finance (the catalog's first action for the
  current view), Rules (New rule, disabled exactly when the inline button was), and
  Exceptions (View all possible findings).
- **FR-003**: Move non-actions out of the slot: the Decisions sorting note joins the filter
  row; the Save preferences button returns to the end of its form and keeps its native form
  association. Neither page contributes header actions.
- **FR-004**: Remove the register toolbar's action slot and its header/inline switch, so
  every register page renders its actions only through the shared bar; a view without
  actions (Deliveries, a selected commitment, Facts, Inspector records) renders no bar. The
  explicit Search submit of Facts and Inspector records is part of the search form and
  stays beside its field.
- **FR-005**: Actions resolved from the validated discovery metadata keep their catalog
  order, placement filtering, form and destination handling, and Web eligibility. While the
  metadata is loading or unavailable the bar renders nothing; the global Actions launcher
  remains the place that reports that failure.
- **FR-006**: Buttons in the bar share one height and type size with each other and with
  the header's other controls; the More actions trigger keeps its accessible name and
  keyboard behavior. Retain four-language coverage for every label.
- **FR-007**: At desktop widths, the shell header MUST reserve the same navigation, content
  and optional chat columns as the body. The page heading and action bar occupy only the
  content column, ending at the chat's left edge when it is open. Closing chat restores the
  content column to the available width. Mobile keeps the existing overlay behavior.
- **FR-008**: At desktop widths, the active company switcher MUST appear at the top of the
  persistent navigation, before Daily work, because it scopes the navigation and page
  content. It MUST NOT consume space in the middle header action row. On mobile, where the
  navigation is collapsed by default, the switcher remains available in the header.
- **FR-009**: Desktop global utilities (activity, global Actions, appearance and chat)
  MUST remain right-aligned in the shell's right column, above the chat when it is open.
  They MUST NOT consume the middle content column reserved for the page heading and
  page-specific actions.
- **FR-010**: Page-specific More actions MUST appear right-aligned in the local view-tab
  row rather than in the global header. A page with actions but no tabs retains the same
  local row with an empty left side; it MUST NOT invent a single non-navigating tab.
- **FR-011**: Exceptions MUST present View all possible findings beside its search and
  severity filters rather than as a page action. Search occupies the first row; severity
  and the catalog control share the second row. The control continues to open the complete
  exception-class catalog and is not represented as another filter.
- **FR-012**: The company switcher option list MUST show a compact Sandbox badge beside
  the name of every sandbox/practice company, while retaining its Practice company
  description and leaving ordinary companies unbadged.
- **FR-013**: Decisions MUST place an information control beside its action-type filter.
  The control opens an accessible explanation of who can prepare proposals, how workspace
  and agent proposals enter the queue, and why pending or rejected proposals do not change
  business records. It uses the same centered information-dialog treatment as the
  Exceptions catalog. The redundant Oldest first and Pending note is not shown beside the
  filter. The explanation includes a concrete external MCP read-to-proposal walkthrough,
  copyable prompts, the actual relevant tool names, and an explicitly non-committed note
  that an in-product agent builder is only a possible future direction.
- **FR-014**: Inspector All records MUST use the shared register toolbar's single 16-pixel
  horizontal inset for both its toolbar and table. Its search form MUST NOT add a second
  surface inset, and its table MUST NOT touch the card edge. This applies to every
  record-family filter rendered through Inspector records and aligns it with Sales,
  Purchasing, Warehouse, Finance, Master data and Facts registers. Table insets MUST use
  an inner padded wrapper like Purchasing, never margins on a full-width table that cause
  right-edge overflow.
- **FR-015**: Inspector Actions MUST use the shared register toolbar inset and the same
  16-pixel content inset as Purchasing. Search occupies the first row; expansion controls
  use the shared filter/tool row beneath it. It MUST NOT introduce a separate responsive
  spacing scale or compound the surface inset with utility padding for its catalog tree.
  Rules MUST inset its table by the same 16 pixels as
  its toolbar. The All records form reset MUST have enough specificity to prevent the
  generic surface-child inset from adding a second 16 pixels.
- **FR-016**: The embedded Actions Event history MUST use the same register surface,
  search-first shared toolbar, filter/tool row and padded table wrapper as Purchasing.
  It MUST participate in RegisterWorkbench so Row density and Columns appear in that
  shared filter/tool row rather than in a separate right-aligned row above the table.
  The global Activity drawer retains its drawer-specific presentation. Shared surface
  padding MUST explicitly exclude toolbar forms and table-inset wrappers so neither can
  receive a second horizontal inset.
- **FR-017**: Every Reality Inspector table that exposes pagination, page-size or load-more
  controls MUST render them through the shared `erp-register-footer`, fixed to the bottom
  of the desktop content column like Purchasing. Cursor-based Inspector tables MUST NOT
  render a raw footer inside the card. Event history's load-older/end state is its table
  footer; drawer activity keeps its inline controls.
  Inspector callers MUST pass only footer controls, without a nested border or padding
  wrapper, so the shared footer has the same height and single separator as Purchasing.

## Assumptions and Dependencies

Owner reported the inconsistent header controls (New company versus More actions) and asked
for one treatment in conversation on 2026-09-10; the survey of all pages in that
conversation is the inventory above. The owner then clarified that even a single secondary
action belongs in More actions and that the desktop action row must end at the open chat's
left edge. Builds on the compact header and its action slot from spec 160 and on the
discovery metadata from spec 158. Uses the existing `PageActions` portal and
`RegisterActions` disclosure; no API or persistence change. No unresolved clarifications.

## Success Criteria

- SC-001: Every page action in `apps/web/src/unified` reaches the header through the shared
  bar; no page renders buttons, text or a disclosure into the slot directly.
- SC-002: Every page with at least one page action shows exactly one More actions control,
  no page action is a separate header button, and no page shows an empty menu.
- SC-003: At supported desktop widths with chat open, the header action boundary and body
  content boundary share the same horizontal coordinate without overlap.
- SC-004: Frontend contracts, the action-discovery, register and page browser suites,
  production build, four-language localization audit and the spec gate pass.

## Requirement Traceability

FR-001, FR-004–006 → US1–US3, T001–T003. FR-002 → US1, US2, T002. FR-003 → US4, T002.
FR-007 → US1–US3, T004–T005. FR-008 → US1–US4, T006. FR-009 → US1–US4, T007.
FR-010–011 → US1–US4, T009. FR-012 → US1–US4, T010.
FR-013 → US4, T011. FR-014 → US1–US4, T012. FR-015 → US1–US4, T013.
FR-016 → US1–US4, T014. FR-017 → US1–US4, T015.
SC-001–004 → T003, T005–T007, T009–T015.
