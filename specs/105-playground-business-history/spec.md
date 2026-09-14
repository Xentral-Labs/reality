# Playground Business History

**Language**: English

## Context and Intent
Replace the flat Playground Journal with Business history: searchable, bounded
activity and an adjacent relationship inspector inside the existing cockpit.

### Non-Goals
No new business authority, inferred links, workflow status, persistence, undo,
global force-directed graph, or production navigation changes.

## Requirements
- **FR-013**: Business history leads with localized business actions and structured
  recorded party/item/quantity/amount/reference context, not technical processed titles.
  Business filters (Sales, Purchasing, Warehouse, Finance, Master data) apply before
  pagination through the shared service. Sales/purchase selection follows exact
  document/SourceRecord links, never temporal proximity. Other categories retain
  defined event families; unknown records stay available in all activity.
  Show tenant-wide counts of sales-order documents, purchase-order documents,
  shipment/receipt movement records and sales/supplier invoice documents. These
  count records, not inferred unique orders or complete deliveries; explain scope.
  Right pane presents recorded business steps, linked records and authoritative
  inspector metrics/guidance when available. Never invent current open state from
  missing events. Raw events, identifiers and source payload remain in Technical
  details. Existing shared record inspectors outside history retain their behavior.
- **FR-012**: Inventory begins directly with its table, without Stock by item / Current
  projection captions or the generic action-effect footer. Other registers retain
  meaningful filter, count, empty/error and partial-history guidance, not duplicate
  tab headings. No record or navigation behavior changes.
- **FR-011**: All existing central register searches share a compact search-icon field
  with an accessible name and contextual placeholder instead of a detached visible
  Search label. Preserve current live-search versus submitted-search behavior and
  page reset. The settled-items filter is a clearly outlined toggle with visible
  checked state and accessible pressed state; history Search is an outlined button.
  Controls wrap within narrow panes and remain readable in both themes. No search
  capability, endpoint or business semantics change.
- **FR-010**: Central register rows use consistent plain record labels and a rightmost
  Actions column. Details controls use a shared “Details” label and chevron, matching
  typography, focus and hover states without underlines. Business action buttons
  remain visibly distinct, compact and disabled under existing rules. Preserve all
  callbacks, confirmation boundaries and disclosures; no business behavior change.
- **FR-009**: Add a Documents primary tab to the sandbox cockpit. List all sandbox
  documents through the shared paginated evidence register, with server-side search
  by document, party ID or source reference. Display number, type, party, date and received gross
  amount/currency. Selecting a document opens the existing relationship inspector
  inside the cockpit with Back. Preserve search/page on closing details; reset on
  sandbox change. Loading, no records, no matches, retry and pagination are explicit.
  Reads must never mutate records or expose another tenant's documents.
- **FR-001**: Rename the Playground tab Business history. Provide server-side search,
  business-area and time-window filters, all-history default, and cursor loading.
  Search matches recorded references plus exact linked item/party names.
- **FR-002**: Offer grouped activities and raw events. Reuse canonical correlation/source
  grouping, never temporal proximity. Groups describe the loaded matching events,
  not a guaranteed complete order lifecycle; state this boundary visibly.
- **FR-003**: Show tenant-wide business record counts defined in FR-013,
  calculated in SQL, independent of the visible event page. Present as
  non-interactive, outlined metrics under Data overview; use business-readable labels
  for orders, deliveries and invoices. Business-area selection remains separate.
  An accessible info disclosure explains scope independently of search. A separate
  info disclosure beside Transactions explains partial correlation/source groups,
  replacing the permanently visible explanatory paragraph.
- **FR-004**: Selecting an event/group shows chronological events and clickable existing
  Inspector relationships in the adjacent pane. Follow links with Back navigation;
  source payload and technical fields remain available. No guessed graph edges.
  Unsupported subjects show their recorded event data without a fabricated inspector.
- **FR-005**: Highlight the selected group's exact event IDs in the bottom timeline.
  Preserve actions, independent scrolling, responsive layout, theme tokens, loading,
  empty, error/retry states and tenant isolation. Read operations perform no writes.
- **FR-006**: Central cockpit search/select filters use compact 34px controls,
  readable select widths and wrapping on narrow panes. Left operation forms and
  setup dialogs retain their normal sizes. Themes and focus states stay unchanged.

## User Scenarios & Testing
- **FR-008**: Central registers and history share a quiet, borderless state message
  with consistent spacing and typography. Distinguish empty data, filtered no-match,
  loading and errors; expose search reset or retry where applicable. Hide pagination
  for zero matching records. Preserve filters and shared business services.
- **FR-007**: Central secondary view selectors share one compact filled-selection
  style, distinct from underlined primary tabs. Registers share header typography,
  spacing and text/numeric alignment. Pagination is not styled as view selection.
  The exception catalog icon sits beside its heading with a generous hit target.
  Existing switching, filtering, inspection and business behavior remain unchanged.
1. Search a linked item name, filter movements, load older events: correct tenant-only
   results, no duplicates; clearing filters restores history.
2. Grouped events share stored identity; isolated master records stay separate.
3. Select a commitment, follow its document and return; exact shared links and details
   remain in the cockpit. Counters do not change merely by loading another page.
4. Empty/error and narrow/light/dark views are usable. Existing guided flow works.

## Assumptions and Dependencies
Reuse shared timeline_activity and tenant Inspector endpoints. Correlation/source
groups are not whole-order graphs. Full order relationships are explored through
the canonical inspector. Existing membership and sandbox read allowlists apply.
Owner approved the split-view concept. No unresolved clarification.

## Success Criteria
Search/cursor tests find old named-reference events without duplicates; tenant counts
do not depend on pagination. Browser verifies links and Back without mutations,
with selected event highlighting and usable responsive presentation.

## Requirement Traceability
| Requirement | Task | Proof |
|---|---|---|
| FR-001–003 | T002–003 | test_history_search_cursor_and_record_counts; existing timeline tests |
| FR-004–005 | T004–005 | playground-workspace-browser.mjs and existing API boundary tests |
