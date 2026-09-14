# Feature Specification: Physical Shipments and Tracking

**Feature Branch**: `173-physical-shipments-tracking`
**Created**: 2026-09-11
**Status**: Product/domain scope and architecture plan approved 2026-09-11; ready for implementation
**Language**: English
**Input**: "Represent real outgoing and incoming shipments, including what moved, when, tracking identifiers and delivery observations, consistently across Web, CLI, API, MCP and Chat."

## Context and Intent

### Problem

The Sales and Purchasing delivery registers show delivery Commitments: promises with
Movement-derived fulfilled and remaining quantities. A row with zero fulfilled quantity is
therefore an open promise, not a physical shipment. Physical execution exists only as
individual Movements. Reality cannot state that several Movements travelled together, which
package or tracking identifier carried them, or when a carrier reported delivery.

### Scope

- One physical-shipment vocabulary for outgoing customer delivery, incoming supplier
  delivery, incoming customer return and outgoing supplier return.
- Packages, tracking identifiers and append-only logistics events.
- Exact Package-to-Movement contents and full Source → Evidence → Reality explanation.
- Derived dispatch, receipt and externally reported delivery observations.
- Shared reads and reviewed commands across Web, CLI, HTTP API, MCP and Chat.
- Clear UI separation between delivery Commitments and actual Shipments.

### Non-Goals

- Carrier label purchase, rates, pickup booking, address validation, customs, routing,
  proof-of-delivery files, webhooks or background carrier polling.
- Inferring delivery from dispatch, or inventory receipt from a carrier event.
- Replacing Commitment, Reservation, ReturnAnnouncement, Movement or MovementCorrection.
- Delivery/tracking/fulfillment fields on Documents or DocumentLines.
- Picking, packing, scanning or HandlingUnit redesign.
- Financial behavior or wholesale mapping of provider payloads.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Movements](../../docs/features/movements.md)
- [Operational fields](../../docs/features/operational_fields.md)
- [Data model](../../docs/DATA_MODEL.md)
- [Web](../../docs/WEB_SPEC.md)
- [Inventory execution](../009-inventory-execution/spec.md)
- [Unified orders and deliveries](../113-unified-orders-deliveries/spec.md)
- [Customer returns](../099-a-return-can-be-announced/spec.md)
- [Supplier returns](../090-supplier-returns/spec.md)

## Canonical Meaning

- **Delivery commitment**: a promise; it may have no physical execution.
- **Shipment**: one real-world consignment in one direction, for one purpose and counterparty.
- **Package**: one tracked or untracked physical package in a Shipment.
- **Movement**: immutable warehouse stock observation and the only stock/fulfillment authority.
- **Shipment event**: append-only, attributed logistics observation.
- **Delivered**: external delivery observation, never a synonym for dispatch or receipt.
- **Received**: company warehouse observation through inbound Movement(s).

Direction and purpose are explicit because users repeatedly filter and act on them. Direction
alone MUST NOT imply customer or supplier.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dispatch and Follow a Customer Shipment (Priority: P1)

An operator dispatches promised quantities and later sees exactly what left, when, in which
Package, under which tracking identifier, and whether a carrier reported delivery.

**Independent Test**: Dispatch ten units in two Packages, append carrier events, and reproduce
package contents and partial/final fulfillment.

**Acceptance Scenarios**:

1. **Given** an open customer Commitment and stock, **When** a reviewed dispatch is confirmed,
   **Then** Shipment, Package and Movements commit atomically.
2. **Given** two item Movements in one Package, **When** detail is read, **Then** their exact
   quantities, Location, Commitment, occurrence, carrier and tracking are shown.
3. **Given** dispatch without a carrier event, **Then** it is not claimed delivered.
4. **Given** a later source-backed delivery event, **Then** its time, reporter, Package,
   evidence and history are shown.

### User Story 2 - Announce and Receive a Supplier Shipment (Priority: P1)

An operator records a supplier shipment statement without changing stock, then receives the
actual quantities and compares announcement with warehouse Reality.

**Independent Test**: Record an inbound notice, prove zero stock effect, receive partially,
and prove only receipt Movements affect stock and fulfillment.

**Acceptance Scenarios**:

1. **Given** a supplier notice, **Then** its SourceRecord remains lossless and only proven
   operational fields are typed.
2. **Given** an announced or carrier-delivered Package without receipt Movements, **Then**
   stock and supplier fulfillment remain unchanged.
3. **When** exact quantities are received, **Then** receipt Movements link to the Package and
   applicable Commitments.
4. **Given** conflicting external and warehouse statements, **Then** both remain visible and
   their difference is derived rather than either overwriting the other.

### User Story 3 - Trace Customer and Supplier Returns (Priority: P2)

The same logistics vocabulary covers an incoming customer return and outgoing supplier
return while retaining existing return provenance and bounds.

**Independent Test**: Receive a tracked customer return and dispatch a tracked supplier
return, following each through existing Commitment/ReturnAnnouncement links.

**Acceptance Scenarios**:

1. An announced customer-return Package changes no stock before its return Movement.
2. A received customer return preserves existing bounds and ReturnAnnouncement fulfillment.
3. A supplier-return Package uses `supplier_return` Movement and existing supplier bounds.
4. Neither flow reopens an already fulfilled original delivery Commitment.

### User Story 4 - Find and Explain Shipments Everywhere (Priority: P1)

Operators and authorized agents list and inspect the same physical shipments through Web,
CLI, API, MCP and Chat using shared services and opaque identities.

**Independent Test**: Query the same Shipment by ID and tracking search through every adapter
and compare results and trace links.

**Acceptance Scenarios**:

1. Filters for direction, purpose, counterparty, date, carrier, tracking and derived
   observation apply before pagination in every adapter.
2. Package inspection follows Shipment, effective Movements, Commitments/return links,
   events and SourceRecords through shortest true links.
3. Foreign tenant identity produces not-found behavior without disclosure.
4. Empty UI distinguishes no physical Shipments from open Commitments with zero fulfillment.

### User Story 5 - Mutate Safely (Priority: P1)

An authorized operator prepares, reviews, confirms, retries and reconciles shipment mutations
without duplicate logistics or stock effects.

**Independent Test**: Exercise stale state, replay, concurrency and lost response for every
command; observe one effect or none.

**Acceptance Scenarios**:

1. Preparation creates no Shipment, Package, Event, Movement or fulfillment effect.
2. Confirmation commits the reviewed atomic effect once and returns exact record IDs.
3. Changed stock, capacity, source, Package or event state rejects stale with no partial effect.
4. Replay/reconciliation returns the prior receipt without duplicate effects.
5. Chat/MCP mutations cannot execute without explicit confirmation; reads need none.

### Edge Cases

- Multiple items per Package and one item split across Packages.
- Multiple Packages/carriers/tracking identifiers per Shipment.
- Missing carrier and/or tracking; absence is not invented.
- Reused tracking text; human numbers never become identity.
- Duplicate, late, out-of-order or retracted carrier events.
- External delivery with partial/no warehouse receipt.
- Corrected/replaced Movements; contents use effective Movements.
- Mixed Package delivery observations; Shipment is not wholly delivered prematurely.
- Shipments without Documents; no synthetic Evidence is created.
- Mixed tenant, direction, purpose or counterparty is rejected atomically.
- UTC normalization preserves raw offsets; date-only input does not invent an instant.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `Shipment` MUST be tenant-scoped with opaque identity, inbound/outbound
  direction, business purpose, tenant-owned counterparty, recording time and optional direct
  SourceRecord; it MUST have no status field.
- **FR-002**: Purposes MUST distinguish outgoing customer delivery, incoming supplier
  delivery, incoming customer return and outgoing supplier return, constraining compatible
  direction, party role, Movement type and existing operational links.
- **FR-003**: A Shipment MUST have one or more `ShipmentPackage` records. A Package MAY carry
  source-stated carrier and tracking text; neither is identity or a foreign key.
- **FR-004**: A Movement MAY link to one Package, meaning its exact quantity travelled in that
  Package. Movement MUST NOT duplicate Shipment, party, carrier, tracking, Document or Source
  fields.
- **FR-005**: Contents, dispatch/receipt quantities and fulfillment MUST use effective
  Movements after correction. Shipment records/events alone have zero stock effect.
- **FR-006**: Packaged execution MUST reuse all existing stock, Location, Commitment,
  Reservation, hold, item, lot, serial, HandlingUnit, return and correction validation.
- **FR-007**: `ShipmentEvent` MUST be append-only with opaque identity, Shipment/Package
  target, kind, stated time if present, reporter, recording time, optional location text,
  optional SourceRecord and external idempotency identity when supplied.
- **FR-008**: Event kinds MUST cover announced, handed over, in transit, delivered, delivery
  exception and received. Event kind never determines inventory.
- **FR-009**: Current logistics observations MUST derive from effective Movements and
  non-superseded events. Shipment, Package, Document and DocumentLine MUST NOT store mutable
  authoritative dispatch/receipt/delivery status or timestamps.
- **FR-010**: Correcting an external event MUST append an explicit supersession with reason
  and actor/source evidence; original events are never updated/deleted.
- **FR-011**: External logistics payloads MUST enter as immutable SourceRecords. Only fields
  repeatedly filtered, joined, constrained, displayed as core answers or used for idempotency
  become typed; all remaining provider fields stay in payload.
- **FR-012**: A shared paged list MUST filter by direction, purpose, counterparty, date,
  carrier, tracking and derived observation before count/pagination; unknown filters fail.
- **FR-013**: Shared detail MUST distinguish promised, announced, dispatched, externally
  delivered and warehouse-received quantities/times and expose their derivation and traces.
- **FR-014**: Canonical reviewed commands MUST record a no-stock shipment notice, dispatch an
  outgoing Package, receive an incoming Package, append an event and supersede an event.
  Existing Movement correction remains the physical correction path.
- **FR-015**: Multi-line execution MUST atomically commit or roll back Shipment, Package,
  Event, Movements, Reservation effects, fulfillment events, audit and receipts.
- **FR-016**: Every mutation MUST support no-effect preparation, state-bound review, explicit
  confirmation, actor attribution, semantic request identity, replay, lost-response
  reconciliation, stale rejection and exact receipts.
- **FR-017**: Web, CLI, API, MCP and Chat MUST call the same tenant-scoped application
  services/tools and contain no alternative logistics or inventory rules.
- **FR-018**: Reads require no confirmation. All Chat/MCP mutations and interactive adapter
  mutations MUST use the reviewed confirmation boundary.
- **FR-019**: Web MUST qualify current Commitment registers and add separate Incoming and
  Outgoing Shipments views with purpose/search/filter/paging and honest UI states.
- **FR-020**: Web detail MUST show party, direction, purpose, packages, carrier/tracking,
  effective contents, warehouse/external events, discrepancies, evidence and Inspector links.
- **FR-021**: Web forms MUST use existing action discovery, proposal/review, stale, retry and
  reconciliation patterns; eligibility comes from services, never browser rules.
- **FR-022**: CLI MUST provide equivalent list/detail and five reviewed mutations using opaque
  IDs, UTC-aware input, scriptable output where established, and non-zero failures.
- **FR-023**: HTTP API MUST expose versioned equivalent reads, prepare, confirmation, receipt
  and reconciliation contracts with existing auth/error/idempotency conventions.
- **FR-024**: MCP MUST expose `shipments_list` and `shipment_explain` plus proposals for the
  five canonical commands. Guidance MUST distinguish promises, execution and carrier delivery.
- **FR-025**: All new tables, queries and association validation MUST enforce tenant scope;
  cross-tenant reads are not found and writes fail without disclosure.
- **FR-026**: Shipment/events MUST be cataloged BusinessEvents and invalidate affected
  logistics, fulfillment, inventory, activity, explanation and projection reads.
- **FR-027**: Existing un-packaged Movements remain valid. Migration fabricates no historical
  Shipment, Package, tracking, carrier or event; rollback preserves prior Movement truth.
- **FR-028**: User-facing terminology is canonical and localized in en/de/nl/es where used.
- **FR-029**: Lists MUST be deterministic, page-bounded and indexed for tenant plus primary
  filters; tracking search is tenant-bound before matching human text.
- **FR-030**: Existing authorization applies and audit identifies tenant, actor, command,
  target, request identity, result and links without logging payload secrets.

### Domain and Traceability Requirements

- **DR-001**: The chain is SourceRecord → optional Document/Line → Commitment or
  ReturnAnnouncement → Shipment/Package context → Movement physical truth; ShipmentEvent is
  a separately attributed observation. Not every source needs a Document.
- **DR-002**: Movement remains stock/fulfillment authority; Shipment never becomes a ledger.
- **DR-003**: Movement → Package → Shipment is the shortest contents/consignment path;
  existing Movement → Commitment/ReturnAnnouncement/settled-return links retain purpose truth.
- **DR-004**: Shipment MUST NOT duplicate Document or DocumentLine FKs; evidence is reached
  through direct existing links or its optional SourceRecord.
- **DR-005**: Party, direction, purpose, tracking, event and warehouse Movement are distinct
  assertions; comparisons never manufacture one from another.
- **DR-006**: Carrier/tracking are typed because core behavior searches, filters, constrains,
  reconciles and acts on them. Provider-specific metadata remains lossless payload.
- **DR-007**: Shipment state is a read-time explanation, never persisted authority.
- **DR-008**: An announced Shipment before execution proves logistics intent only.
- **DR-009**: Existing fulfillment, return, correction and Reservation rules are reused.
- **DR-010**: All relationships use opaque IDs; human references never identify records.

### Canonical Application Capability Inventory

| Capability | Kind | Confirm | Surfaces | Effect |
|---|---|---:|---|---|
| `shipments_list` | read | No | Web, CLI, API, MCP, Chat | Filtered Shipment register |
| `shipment_explain` | read | No | Web, CLI, API, MCP, Chat | Shipment/Package derivation and trace |
| `shipment_notice_record` | mutation | Yes | all | Notice, Shipment/Package/event; no Movement |
| `shipment_dispatch` | mutation | Yes | all | Outgoing Package and Movements |
| `shipment_receive` | mutation | Yes | all | Incoming Package and Movements |
| `shipment_event_record` | mutation | Yes | all | Append attributed logistics event |
| `shipment_event_supersede` | mutation | Yes | all | Append event correction/supersession |

Names may be aligned with catalog conventions during planning, but one canonical capability
must serve every adapter. All mutations use prepare → review → confirm → receipt → reconcile.

### Adapter Contract Inventory

| Surface | Reads | Mutations | Required parity |
|---|---|---|---|
| Web | Incoming/Outgoing registers, detail, Inspector | Five discovered forms | Shared eligibility, preview, receipts, stale/retry, four locales |
| CLI | `shipment list/show` | notice/dispatch/receive/event/supersede | Same results/failures, opaque IDs |
| HTTP API | paged list, exact explain | prepare plus existing proposal flow | Versioned schemas, tenant auth/error/idempotency |
| MCP | `shipments_list`, `shipment_explain` | five command proposals | reads direct; mutations confirmed |
| Chat | shared tool use | proposal and explicit confirm | canonical terminology |

### Key Entities

- **Shipment**: consignment direction, purpose, party and optional direct source; no status.
- **ShipmentPackage**: package with optional carrier/tracking statement.
- **ShipmentEvent**: append-only attributed logistics statement.
- **ShipmentEventSupersession**: immutable event correction relation.
- **Movement**: existing stock transition, optionally linked to one Package.
- **Commitment / ReturnAnnouncement / SourceRecord**: existing promise and evidence records.

## Success Criteria *(mandatory)*

- **SC-001**: Each of four flows exposes direction, purpose, party, packages, effective
  contents, warehouse time, carrier/tracking and external observation on every surface.
- **SC-002**: Notices/events change stock/fulfillment by zero; valid Movements change each
  exactly once under existing rules.
- **SC-003**: Every quantity/observation is reproducible from effective Movements and current
  events with shortest trace links.
- **SC-004**: Replay, concurrency and reconciliation create at most one semantic effect.
- **SC-005**: Any invalid tenant/domain combination leaves every involved table unchanged.
- **SC-006**: Existing un-packaged Movement, fulfillment, return and correction stories pass
  without fabricated history.
- **SC-007**: Paged reads meet the repository's reviewed interactive budget on representative
  data, with filters before pagination and no cross-tenant matches.
- **SC-008**: Web at 390/1440 px, light/dark, keyboard and en/de/nl/es clearly separates
  Commitments, Shipments, dispatch/receipt and carrier delivery.

## Assumptions and Dependencies

- First delivery supports manual and already-ingested source statements; live carrier
  integration is later scope.
- One Shipment has one direction, purpose and party; mixed cases use separate Shipments.
- One Package may contain many Movement quantities; one Movement belongs to at most one Package.
- Carrier/tracking are optional received values; absence says nothing beyond missing evidence.
- Announced content remains lossless payload until a later repeated use proves a typed
  announcement-line model; actual contents are authoritative only through Movements.
- Existing proposals, receipts, catalogs, tenant policy, Inspector and corrections are reused.
- Planning chooses the existing interactive-read benchmark and representative dataset.
- Product/domain approval is required before planning because this adds business schema.

## Requirement Traceability

| Requirements | Stories | Planned evidence |
|---|---|---|
| FR-001–011, DR-001–010 | US1–US3 | domain/migration/service tests for four flows, append-only evidence and shortest links |
| FR-012–013, FR-025, FR-029–030 | US4 | list/detail, tenant, filter, ordering, authorization and query-plan tests |
| FR-014–018 | US1–US3, US5 | prepare/confirm/replay/stale/concurrency/lost-response/atomicity tests |
| FR-019–021, FR-028 | US1–US5 | Web contracts and localized responsive browser journeys |
| FR-022–024 | US4–US5 | CLI/API/MCP contract and capability-guidance parity tests |
| FR-026–027 | all | catalogs, invalidation, migration/rollback and legacy regressions |

## Open Questions

The specification has no unresolved product questions. The owner approved the product/domain
scope on 2026-09-11, including the schema direction, shortest links, command inventory and
decision not to type announced contents. The owner approved the architecture/domain plan on
2026-09-11.
