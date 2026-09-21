# Research: Explainable B2B Operational Chain

## Decision 1: Preserve invoice lines in the existing confirmed invoice workflow

**Decision**: Extend the existing order/invoice review and execution path so its reviewed snapshot
contains and creates every stated line, including `billed_document_line_id` where the source or
confirmed action identifies the billed order line.

**Rationale**: `DocumentLine` already stores quantity, price, gross amount, item, unit, payload,
source-line identity and the shortest billed-line relationship. Partial/multiple invoicing and
commercial matching already read this structure. The observed failure is a broken ordinary path,
not a missing invoice model.

**Alternatives considered**: A separate billing-allocation table was rejected because the existing
billed-line link already answers the proven one-line scope. Generating lines from invoice totals was
rejected because it invents source evidence and rounding rules.

## Decision 2: Add one append-only supply-assignment relationship

**Decision**: Persist explicit quantity assignments from a supplier commitment either to a customer
delivery commitment or to the stock-replenishment purpose. Represent corrections as linked reversal
rows and derive the effective quantity.

**Rationale**: Operations repeatedly joins, constrains and acts on this relationship to answer which
supply protects demand, what remains for stock and whether a later reduction creates a shortage.
Neither reservations nor movements represent intent before stock exists. The relationship therefore
passes the proven-schema rule.

**Alternatives considered**: A field on the supplier commitment cannot support split supply. A link
to order/document lines is longer and duplicates commitment evidence. Reusing Reservation is false
because no owned physical stock is reserved. Inferring from dates/items is unsafe. Mutable assignment
rows would erase the statement history.

## Decision 3: Model return disposition with resolving movements

**Decision**: Reuse `Movement.resolves_movement_id` and existing movement types/locations. Provide a
guided service and read model that labels the physical result as restocked, quarantined, scrapped or
returned to supplier.

**Rationale**: The current model explicitly documents that the settling movement is what happened to
returned goods. Tests already prove partial resolution, over-resolution protection and corrections.
A second disposition record could disagree with physical truth.

**Alternatives considered**: A `ReturnDisposition` table and a status enum on `ReturnAnnouncement`
were rejected as duplicate operational state. A free-text disposition was rejected because stock
effects and constraints could not act on it.

## Decision 4: Derive one movement explanation read model

**Decision**: Build a shared read service over existing correction, return, commitment, shipment,
source and action/audit relationships. Preserve adjustment reason from existing evidence and warn
before an otherwise unexplained mutation.

**Rationale**: Explanation is a read-time traversal of authoritative relationships. Storing a second
reason on every movement would duplicate evidence and create drift.

**Alternatives considered**: A generic polymorphic `reason_type/reason_id` pair was rejected because
typed existing foreign keys are safer and shorter. Browser-only assembly was rejected because tools,
agents and CLI require the same explanation.

## Decision 5: Trigger existing projections; do not create a finance queue

**Decision**: Covered confirmed actions use the shared job registry/projection lifecycle, and company
setup waits on the existing durable readiness marker.

**Rationale**: The repository contract prohibits browser timers and subsystem-specific queues.
Finance and contribution projections already have freshness semantics and last-completed results.

**Alternatives considered**: Synchronous browser calculation would duplicate rules and block UX.
An API-process background loop would violate the scheduling contract. A mandatory manual Refresh
does not meet the accepted readiness requirement.

## Decision 6: Prove behavior with a service-driven acceptance story

**Decision**: Add a deterministic multi-day scenario starting with an empty company and executing
normal application services for customer order, fulfilment, procurement, invoicing, settlement,
cancellation, return, disposition and credit.

**Rationale**: Existing broad demo data proves many isolated cases, but the reported gap occurred on
the ordinary live path. One coherent story detects missing adapter/service links and produces exact
references for documentation and browser verification.

**Alternatives considered**: Direct ORM fixtures are faster but would hide the failed user path.
Expanding the canonical demo profile alone would make demos richer without proving an empty company
can operate correctly.
