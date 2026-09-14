# Feature Specification: Inventory Execution Baseline

**Baseline ID**: `009-inventory-execution`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline reservations, append-only physical movements, derived inventory, and optional warehouse tracking identities."

## Context and Intent

### Problem

Warehouse operators need trustworthy stock, allocation, and execution without a mutable
balance becoming authority. This baseline defines Reservations and Movements, derives
inventory quantities, and constrains optional handling-unit, lot, and serial identity
through tenant-scoped operational services.

### Scope

- Physical, reserved, available, incoming, and projected inventory calculations.
- Reservation of available stock to outgoing customer Commitments, including shortage,
  release, and consumption.
- Append-only opening, receipt, shipment, transfer, return, and adjustment Movements.
- Partial execution and Commitment fulfilment integration.
- Location stock eligibility and prevention of negative outbound stock.
- Optional HandlingUnit/NVE, Lot, and SerialUnit identity on Reservations/Movements.
- Tenant-scoped registers, actions, timeline events, and explanation paths.

### Non-Goals

- An authoritative editable stock-balance field.
- Warehouse task orchestration, picking routes, packing, carrier, or barcode workflows.
- Costing, valuation, general-ledger posting, or financial inventory reconciliation.
- Forecast algorithms beyond open incoming Commitments.
- Making pallet, lot, or serial tracking mandatory for untracked items.

### Existing Contracts

- [`docs/features/inventory.md`](../../docs/features/inventory.md)
- [`docs/features/reservations.md`](../../docs/features/reservations.md)
- [`docs/features/movements.md`](../../docs/features/movements.md)
- [`docs/features/operational_fields.md`](../../docs/features/operational_fields.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

Movement is the append-only physical journal. Physical stock is the signed sum of
Movements by tenant, item, and location; no separate balance owns truth. Reservation
allocates currently available stock at one location to one outgoing customer
Commitment and links only to that Commitment for provenance. Availability subtracts
active Reservations, while incoming and projected quantities use open supplier
Commitments.

Lot- and serial-tracked items enforce their required identities. Serial execution is
one exact unit. Handling units are optional physical grouping identities and may carry
a tenant-unique NVE/SSCC. Current warehouse location is derived from Movement history.
Spec 023 implements the compensating-Movement correction principle as an append-only,
tenant-scoped void/replacement workflow with shared preview, confirmation, audit, and
explanation behavior.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explain Current and Projected Inventory (Priority: P1)

As an operator, I can see physical, reserved, available, incoming, and projected
quantities and reproduce every number from Reality records.

**Why this priority**: Inventory is trustworthy only when its calculation is explicit.

**Independent Test**: Create opening stock, active/released Reservations, and partial
supplier receipts; compare each displayed quantity with its underlying records.

**Acceptance Scenarios**:

1. **Given** Movements into and out of a location, **When** physical stock is read,
   **Then** it equals inbound minus outbound quantities.
2. **Given** active Reservations, **When** availability is read, **Then** it equals
   physical minus active reserved quantity.
3. **Given** an open supplier Commitment, **When** inventory is projected, **Then** open
   incoming quantity is added to available stock.
4. **Given** records in another tenant, **When** inventory is calculated, **Then** they
   have no effect.

### User Story 2 - Reserve Stock and Expose Shortage (Priority: P1)

As an operator, I can allocate available stock to an outgoing customer Commitment and
see any uncovered quantity without creating negative availability.

**Why this priority**: Reservation makes promised stock operationally actionable.

**Independent Test**: Reserve more than available, release it, reserve again, and ship
partially while inspecting shortage, states, and quantities.

**Acceptance Scenarios**:

1. **Given** 20 available for a promise of 30, **When** 30 is requested, **Then** 20 is
   reserved and shortage is 10.
2. **Given** an active Reservation, **When** released, **Then** history remains and
   availability returns without changing physical stock.
3. **Given** linked shipment, **When** executed, **Then** active allocation is consumed
   up to shipped quantity and stock falls through a Movement.
4. **Given** an incoming or cancelled Commitment, **When** Reservation is attempted,
   **Then** it is rejected.

### User Story 3 - Record Physical Execution (Priority: P1)

As a warehouse operator, I can record receipts, shipments, transfers, returns, opening
stock, and reasoned adjustments as immutable physical events.

**Why this priority**: Movements are the sole physical stock authority.

**Independent Test**: Execute every Movement type and verify location requirements,
stock arithmetic, Commitment fulfilment, reason enforcement, and retained history.

**Acceptance Scenarios**:

1. **Given** opening 20, receipt 10, and shipment 7, **When** stock is read, **Then** it
   equals 23.
2. **Given** a transfer of 3, **When** both locations are read, **Then** source falls and
   destination rises by 3 while total stock is unchanged.
3. **Given** an adjustment without reason, **When** recorded, **Then** it is rejected.
4. **Given** insufficient physical stock, **When** outbound execution is attempted,
   **Then** it is rejected without creating a Movement.
5. **Given** a linked partial receipt or shipment, **When** recorded, **Then** the
   Commitment's fulfilment derives from that Movement.

### User Story 4 - Track Lots, Serials, and Handling Units (Priority: P2)

As a warehouse operator, I can allocate and execute the exact physical identity required
by an item's tracking policy and optionally identify its pallet.

**Why this priority**: Traceable goods need identity precision without burdening all stock.

**Independent Test**: Receive/reserve/ship lot and serial items with and without a
HandlingUnit and attempt invalid identity combinations across items and tenants.

**Acceptance Scenarios**:

1. **Given** a lot-tracked item, **When** Movement or Reservation omits the lot, **Then**
   it is rejected.
2. **Given** a serial-tracked item, **When** execution identifies its SerialUnit, **Then**
   quantity is exactly one and its applicable lot follows the identity.
3. **Given** an untracked item, **When** a foreign/inapplicable lot is supplied, **Then**
   it is rejected.
4. **Given** a HandlingUnit, **When** several item Movements reference it, **Then** the
   pallet association is retained without becoming mandatory.
5. **Given** a tenant-local NVE, **When** duplicated in that tenant, **Then** creation is
   rejected; the same human value in another tenant remains independent.

### Edge Cases

- Concurrent Reservations compete for the last available quantity.
- Shipment quantity exceeds stock, Reservation, or Commitment open quantity.
- Transfer source and destination are equal or a location disallows stock.
- A negative/zero quantity is submitted; direction is encoded inconsistently.
- Released or consumed Reservations are released again.
- Lot/serial/handling-unit identity belongs to another tenant, item, or location.
- A serialized unit moves twice without an intervening inbound transition.
- An incorrect historical Movement requires correction without mutation/deletion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Physical stock MUST derive from append-only Movements into minus Movements
  out of each tenant/item/location; no editable balance may be authoritative.
- **FR-002**: Reserved MUST equal active Reservations; available MUST equal physical
  minus reserved; incoming MUST equal open supplier-delivery quantity; projected MUST
  equal available plus incoming.
- **FR-003**: Inventory calculations and records MUST use Decimal quantities and enforce
  tenant, item, and location scope.
- **FR-004**: Reservation MUST link only to its outgoing customer Commitment and MUST
  allocate no more than currently available stock or Commitment open quantity.
- **FR-005**: Reservation requests beyond availability MUST allocate the safe amount and
  report explicit shortage.
- **FR-006**: Reservation release MUST be idempotent and historical; shipment MUST
  consume applicable active Reservation without deleting it.
- **FR-007**: Movement MUST support opening stock, receipt, shipment, transfer, return,
  and adjustment with type-appropriate source/destination locations.
- **FR-008**: Movement quantity MUST be positive; outbound Movement MUST NOT exceed
  physical stock; adjustment MUST include a reason/source trail.
- **FR-009**: Movement MUST be immutable under normal services; correction MUST use an
  auditable compensating Movement rather than update or deletion.
- **FR-010**: Linked receipt/shipment MUST fulfil only the applicable supplier/customer
  Commitment and MUST respect execution holds.
- **FR-011**: Physical Movement MUST use a location that allows stock and all linked
  item, locations, Commitment, SourceRecord, and tracking identities MUST be tenant-owned.
- **FR-012**: Lot-tracked items MUST identify a matching Lot for Reservation/Movement;
  serial-tracked items MUST identify one matching SerialUnit with quantity one.
- **FR-013**: HandlingUnit MUST be optional, tenant-scoped, and optionally carry a
  tenant-unique NVE; Reservations/Movements MAY reference it without duplicated provenance.
- **FR-014**: Current location of tracked warehouse identity MUST derive from its newest
  Movement; outbound Movement means no tenant location remains.
- **FR-015**: Web, CLI, API, Chat, and MCP MUST use shared tenant-scoped services;
  interactive mutating actions MUST require confirmation.
- **FR-016**: Inventory, Reservation, and Movement views MUST expose underlying records
  sufficient to reproduce displayed quantities and state.

### Domain and Traceability Requirements

- **DR-001**: Movement, not Fact or a balance column, is physical stock authority.
- **DR-002**: Reservation → Commitment is shortest provenance; it MUST NOT duplicate
  Document, DocumentLine, or SourceRecord links.
- **DR-003**: Movement MAY link to Commitment or SourceRecord when those are direct
  evidence, but MUST NOT gain Document/Line links without a proven scenario.
- **DR-004**: HandlingUnit, Lot, and SerialUnit are physical identities, not alternate
  stock ledgers; current state remains derived from Movements.
- **DR-005**: Operational interfaces MUST not implement alternative inventory,
  allocation, fulfilment, or tracking rules.

### Key Entities

- **Movement**: Immutable observed physical quantity transition.
- **Reservation**: Historical allocation of available stock to one Commitment.
- **HandlingUnit**: Optional tenant-scoped physical grouping, optionally identified by NVE.
- **Lot**: Tenant/item-scoped batch identity for lot-tracked goods.
- **SerialUnit**: Tenant/item-scoped identity for one serialized physical unit.
- **Commitment**: Incoming/outgoing promise used for projected inventory and fulfilment.

## Reality Applicability

- **Source**: Optional direct SourceRecord on a Movement where it is the shortest
  physical evidence; imports retain original source/artifact separately.
- **Evidence**: Documents may support Commitments but are not required for Reservation
  or stock provenance.
- **Reality**: Movements, Reservations, Commitments, and tracking identities are the
  operational basis of inventory execution.
- **Shortest links**: Reservation → Commitment; Movement → optional Commitment/Source;
  Movement/Reservation → optional HandlingUnit/Lot/SerialUnit.
- **Stored/derived**: Movement/Reservation history and identities are stored. Physical,
  reserved, available, incoming, projected, fulfilment, and current location are derived.
- **Shared boundary**: All interfaces call tenant-scoped application services;
  interactive mutations require proposal/confirmation.
- **Web explanation**: Inventory detail expands each quantity into Movements,
  Reservations, and open incoming Commitments; registers remain append-only truth views.

## Success Criteria *(mandatory)*

- **SC-001**: Every inventory row reconciles exactly to its underlying Movements,
  active Reservations, and open incoming Commitments.
- **SC-002**: Reservation never makes available stock negative and reports 100% of
  uncovered requested quantity as shortage.
- **SC-003**: Opening 20, receiving 10, and shipping 7 yields physical stock 23; every
  transfer preserves total stock exactly.
- **SC-004**: Invalid outbound, location, tenant, quantity, or tracking combinations
  create zero Movements.
- **SC-005**: Release and consumption preserve Reservation history while only active
  Reservations reduce availability.
- **SC-006**: Lot/serial execution identifies the required physical unit or batch in all
  covered cases, while untracked items remain usable without those identities.
- **SC-007**: Every displayed inventory quantity and tracked current location is
  reproducible from authoritative Reality records.

## Assumptions and Dependencies

- Concurrency-sensitive allocation is serialized by the existing persistence boundary.
- Incoming projection uses open supplier Commitments and excludes speculative forecasts.
- Financial inventory value belongs to the Ledger/Finance baseline.
- Movement correction uses the explicit compensation type, reason, direct correction
  relation, shared permissions, and full-chain explanation defined by Spec 023 without
  mutating the original Movement.

## Open Questions

The product owner approved this baseline on 2026-08-31. Spec 023 closed the former
FR-009 gap on 2026-08-31 after implementation, executable proof, and final review.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-003 | Verified as-is | Inventory, Movement, and Data Model contracts | stock/inventory query services | `tests/test_inventory_and_fulfillment.py`; tenancy tests | — |
| FR-004–FR-006 | Verified as-is | Reservations contract | reserve/release/consumption services | inventory, tracking-reservation, and cancellation tests | — |
| FR-007–FR-008 | Verified as-is | Movements contract | `services/core.py:record_movement` | `tests/test_inventory_and_fulfillment.py` | — |
| FR-009 | Verified as-is | Movements contract; Constitution; Spec 023 | `services/core.py:correct_movement` and shared adapters | `tests/test_movement_corrections.py`; inventory, API, tool, catalog, and migration suites | Append-only void/replacement workflow approved 2026-08-31 |
| FR-010–FR-011 | Verified as-is | Commitments, Holds, Movements, and operational-fields contracts | Movement validation services | fulfilment, hold, party-hold, and operational-field tests | — |
| FR-012–FR-013 | Verified as-is | Movements contract | lot/serial/handling-unit services | `tests/test_inventory_tracking_reservations.py`; `tests/test_handling_units.py` | — |
| FR-014 | Verified as-is | `docs/WEB_SPEC.md:Workspace views` | warehouse identity read models | tracking and Web register tests | — |
| FR-015–FR-016 | Verified as-is | Constitution; Web contract | shared services, tools, read models, Inspector | API, Chat tool, application-tool, and Web tests | — |
| DR-001–DR-005 | Verified as-is | Constitution; Architecture; Data Model | relationships and application services | inventory, tracking, tenancy, and Inspector tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Inventory arithmetic and tenancy tests |
| FR-004–FR-006 | US2 | Reservation shortage, release, consumption, and cancellation tests |
| FR-007–FR-011 | US3 | Movement type, stock, reason, hold, and fulfilment tests; FR-009 gap |
| FR-012–FR-014 | US4 | Lot, serial, HandlingUnit, and warehouse-location tests |
| FR-015–FR-016 | All stories | Shared tool/API/Web and explanation tests |
| DR-001–DR-005 | All stories | Constitution and relationship review |
