# Research: Physical Shipments and Tracking

## Shipment context, Movement authority

**Decision**: Shipment/Package groups execution; each Movement may link to a Package; dispatch and
receipt derive from effective Movements.
**Rationale**: Movements answer stock but not consignment/tracking grouping.
**Alternatives**: Tracking on every Movement duplicates data; shipment lines as stock truth create
a second ledger; Commitment inference cannot represent splits.

## Package is the tracking grain

**Decision**: Carrier/tracking live on Package, with multiple Packages per Shipment.
**Rationale**: One consignment may have several identifiers and each needs exact contents.
**Alternatives**: Shipment per tracking loses grouping; bare identifiers cannot bind contents.

## Events are append-only observations

**Decision**: ShipmentEvent records attributed statements; correction appends supersession.
**Rationale**: Carrier values may be duplicate, late, wrong or retracted and must stay explainable.
**Alternatives**: Mutable status destroys evidence; generic Fact lacks required filtering,
idempotency and action semantics.

## No typed announced lines in V1

**Decision**: Announced content stays in lossless SourceRecord; actual contents use Movements.
**Rationale**: A second expected-quantity authority lacks repeated core use today.
**Alternatives**: ShipmentLine is premature; pre-receipt Movement would invent stock.

## Shared reviewed commands

**Decision**: Notice, dispatch, receive, event and supersede use existing proposal/receipt flow in
all adapters; dispatch/receive invoke existing Movement behavior transactionally.
**Alternatives**: CRUD bypasses confirmation; generic Movement cannot represent notices/events.
