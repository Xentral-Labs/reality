# Feature Specification: Free Playground Operations

## Approved progressive disclosure refinement

FR-014: A fresh operation chooser shows four guided examples and two individual
order-creation actions. The remaining fourteen actions remain available under a
default-collapsed, keyboard-operable “More operations” disclosure, grouped by
Master data, Warehouse and Finance. Returning to the chooser restores its compact
default. Opening or closing the disclosure never prepares or executes an action.
Existing confirmation, availability checks and tools remain unchanged.

## Approved master-data increment

FR-013: Individual operations include creating and editing one Party, Item or
Location through existing shared tools. Basic fields are name and customer/supplier
roles for Parties, SKU/name/unit for Items, and name/type for Locations. Editing
preserves fields not exposed in the form. Selection and Back never write. A readable
review precedes explicit confirmation; updates use the shared revision check and
foreign/stale records cannot execute. Each receipt exposes record and event IDs.
Refresh existing reference lists after settlement so new records can be selected in
later operations. Sandbox ownership, archived restrictions, exact intent, pending
recovery and ordinary API write denial remain unchanged. No schema changes.

Acceptance: create then edit each family; reject without effects; reload review;
repeat confirmation without duplicates; refuse extra fields, foreign IDs and stale
updates; retain unchanged inventory/ledger. Four-language forms and review fit the
existing action pane with Back and fixed action footer.

Source-import simulation is the next separately implemented increment, not included
in FR-013. It must distinguish receiving, interpretation and booking; no generic
import worker permission is granted with these master-data operations.

## Independent fulfillment entry refinement
FR-012: Select an active reservation and explicitly review/confirm its full release.
Use the shared reservation_release tool, binding exact reservation and action IDs.
Refresh the reservation state before execution; stale/consumed/released/foreign
targets cannot execute. Receipt links reservation and recorded event; physical
stock and commitment remain unchanged. Back/reject do not release anything.
Group individual entries under Sales, Purchasing, Warehouse and Finance; preserve
the same operation callbacks and bounded, scrollable cockpit layout.
FR-011: Independent customer/supplier invoice and payment entries select existing
tenant evidence before preparing the existing finance tool. Invoice selection uses
bounded searchable order pages and exact document-line IDs exposed by the existing
Inspector. Payment selection uses outstanding Open items. Amounts are entered or
copied from received amounts, never recomputed; partial payment is supported.
Back and selection perform no writes. Explicit review/confirmation and server
eligibility/staleness checks remain authoritative. No schema or new finance rules.
FR-010: Individual reservation, shipment and receipt shortcuts open the existing
Open deliveries view with the correct customer/supplier scope and action. User
selects an authoritative commitment before editing quantity; review/confirmation
remain mandatory. Back restores the chooser without writes. No mutation shortcuts
or guessed targets. Independent invoicing, settlement and reservation release are
covered by FR-011 and FR-012.

**Feature Branch**: `feature/playground-free-operations`
**Created**: 2026-09-07
**Status**: Approved for the first independent increment
**Language**: English
**Input**: Owner approved independently creating orders, returning later to open work,
then adding bulk processing and configurable Shopify examples.

## Context and Intent

### Problem

The cockpit ties action selection to the most recent guided lesson. Learners cannot
leave several orders open, switch to purchasing and later receive or ship an earlier
order even though the shared Reality services support these operations.

### Scope

The first independently testable increment delivers free single actions alongside
the existing guided lessons, and an open-work register inside the same cockpit.

### Non-Goals

- No second business engine, stored workflow state, schema or migration.
- No actual Shopify connection, automatic shipping, or external notifications.
- Bulk review/execution, consolidated picking and configurable Shopify sample imports
  are subsequent increments; they are not represented as available controls here.
- No redesign of the existing finance, return or guided-example behavior.

### Existing Contracts

- [Learning Playground](../096-learning-playground/spec.md)
- [Web contract](../../docs/WEB_SPEC.md)
- [Playground boundaries](../../docs/features/learning-playground.md)

## User Scenarios & Testing

### User Story 1 - Create only the order (Priority: P1)

Create a customer order or supplier order, with selected party, item, location,
quantity and price, without advancing into shipment or receipt.

**Why this priority**: Orders must exist independently of their later fulfillment.
**Independent Test**: Create sales A, purchase B and sales C in one sandbox; no stock
changes merely because orders were recorded. Return to the action chooser each time.

**Acceptance Scenarios**:

1. Given an active sandbox, a grouped list offers separate customer-order and
   supplier-order actions alongside guided examples; selecting or cancelling creates
   no business records.
2. Reviewing an order changes no Reality; explicit confirmation records the existing
   Source → Evidence → Commitment chain and returns to free selection.
3. Guided lessons remain selectable and retain their current progression.

### User Story 2 - Return to open work (Priority: P1)

Select an earlier open goods commitment from a compact register, then reserve, ship,
or receive a chosen quantity independently of intervening activity.

**Why this priority**: Operational work arrives and is fulfilled at different times.
**Independent Test**: After reload, partially receive purchase B, reserve and ship
sales A, then receive B's remainder. C remains unchanged.

**Acceptance Scenarios**:

1. Open work shows direction, counterparty, item, ordered, open and reserved quantity,
   with paging/search and an opaque-identity-backed selection.
2. Supplier rows offer receipt; customer rows offer reservation and shipment. Each
   uses the row's own item/location rather than the last lesson's selected references.
3. Partial fulfillment keeps remaining work visible; completed work disappears after
   the server refresh. Unavailable data is not presented as an empty work queue.
4. Archived runs remain read-only. Pending or uncertain actions block switching into
   a competing mutation. Reload restores pending review rather than silently retrying.

### Edge Cases

Foreign, deleted or stale commitments; unavailable location; insufficient stock;
holds; overfulfillment; double click; lost response; rejected proposal; more than one
page of commitments; switching sandboxes; errors while refreshing after confirmation.

## Requirements

### Functional Requirements

- **FR-001**: Offer one action list with simultaneously visible Guided examples and
  Individual operations groups, without mode tabs. Individual orders return to the
  grouped list after confirmation, rejection or cancellation. Guided lessons retain
  progression and return on completion. Pending review cannot be bypassed.
- **FR-002**: Free customer and supplier orders MUST stop after confirmed creation and
  allow party/item/location/quantity/price selection using prepared sandbox references.
- **FR-003**: Show a bounded server-filtered/paginated open goods work register in the
  central cockpit, including enough reference and quantity context to select work.
- **FR-004**: Free reservation/shipment/receipt MUST target the selected commitment's
  actual item/location and allow a positive quantity, with server validation.
- **FR-005**: All mutations retain separate server review and explicit confirmation,
  replay protection, ownership, archived-run and uncertainty boundaries.
- **FR-006**: Refresh open work and existing inventory/obligations/timeline after each
  settled action; preserve readable errors, four languages and viewport-contained UX.
- **FR-007**: Reserve the right pane for Needs attention and exception inspection.
  Central Open deliveries separates customer and supplier commitments. Central Open
  items separates customer receivables and supplier payables using shared server
  filters and pagination, hides settled items by default, supports showing all,
  search, loading/error/empty states and record inspection. No duplicate obligation
  or money lists remain on the right.

- **FR-008**: Guided continuation and reload use the selected order quantity or
  observed remaining quantity, never stale editor defaults. Shipment overfulfillment
  is refused before preparation/claim through shared quantity validation. Rejected
  proposals permit another operation in the same sandbox. A legacy executing
  overdelivery may be explicitly discarded only under run serialization, with a
  saved pre-execution overdelivery proof and no action events or commitment movements.
  Preserve its original request and decision attribution; never replay it. Other
  unknown executions remain blocked. Recovery navigation stays in the sandbox.

- **FR-009**: Pending execution uses automatic read-only status checks, never repeat
  confirmation. Distinguish execution being checked, unverified outcome, recorded
  action awaiting its observation, and proven non-execution. Rejected actions return
  to operations. Show manual status retry only after a read failure, keep the current
  sandbox, stop checks on settlement/unmount, and ignore late responses. Only the
  server-proven discard path may offer Return to operations for a failed action.

### Domain and Traceability Requirements

- **DR-001**: Reuse shared order/reservation/movement services and derive open state
  from Reality. Do not add document fulfillment fields or browser balance calculations.
- **DR-002**: Existing tenant-scoped query paths supply reference IDs; selection is
  not authority. Revalidate selected targets and freshness at confirmation.

## Success Criteria

- **SC-001**: Sales A → purchase B → sales C → reload → partial receipt B → reserve A
  → ship A → final receipt B works in one sandbox without silently affecting C.
- **SC-002**: All FR/DR have executable proof; selected actions and cancellation do
  not mutate Reality before confirmation. No page-wide scrolling at 1280×800.

## Assumptions and Dependencies

Owner approved the staged sequence with "ja mach das ist gut". A single selected
order line is the unit of this increment, visibly labelled as open goods work.
Bulk order counts/mixed baskets and Shopify import need a separately reviewed
multi-action/import boundary. Existing Shopify interpretation has intermediate
commits and its own proposal chain; no allowlist shortcut is acceptable.

## Open Questions

None for this increment. The later batch/import scope remains explicit follow-up work.

## Requirement Traceability

| Requirement | Scenario | Planned proof |
|---|---|---|
| FR-001–002 | US1 | Free-operation browser and component contracts |
| FR-003–004, DR-001–002 | US2 | Commitment response, selected intent and backend story tests |
| FR-005–006, SC-001–002 | Both | Reload/confirmation isolation tests and viewport browser journey |
| FR-007 | Register separation | Web contracts and browser finance/filter/inspection checks |
