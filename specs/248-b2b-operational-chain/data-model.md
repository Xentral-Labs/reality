# Data Model: Explainable B2B Operational Chain

## Existing records reused unchanged

### SourceRecord → Document → DocumentLine

Source payloads remain immutable and lossless. Invoice headers retain stated dates, numbers, parties,
currencies and totals. Invoice lines retain stated quantities, units and values. A billed invoice
line uses `billed_document_line_id` to point to the narrowest agreed line it bills. Contribution and
reconciliation remain observations over these records and operational Reality.

### Commitment and Movement

Customer and supplier promises remain `Commitment` records. Physical receipt, delivery, return,
transfer and adjustment remain immutable `Movement` records. A return-disposition movement points
directly to the inbound customer-return movement through `resolves_movement_id`; arrival retains the
`return_announcement_id`. Corrections use the existing explicit correction relationship.

## New entity: SupplyAssignment

One append-only statement assigning supplier-commitment quantity to customer demand or stock.

| Field | Meaning and validation |
|---|---|
| `tenant_id` | Company scope; part of every key and relationship |
| `id` | Opaque identity |
| `supplier_commitment_id` | Required supplier-delivery commitment |
| `customer_commitment_id` | Required only for `customer_demand`; customer-delivery commitment with the same item and compatible location |
| `purpose` | `customer_demand` or `stock_replenishment` |
| `quantity` | Positive Decimal in the commitment base unit |
| `source_record_id` | The immutable operator/integration statement that authorized the assignment |
| `reverses_assignment_id` | Optional link to an earlier effective assignment; same tenant and supplier commitment |
| `created_at` | UTC creation instant |

### Database constraints

- Composite foreign keys enforce tenant-scoped links to both commitments, source and reversal.
- A check requires a customer commitment exactly when purpose is `customer_demand`.
- Quantity is strictly positive; a row cannot reverse itself.
- An index begins with tenant and supplier commitment for reconciliation/locking; another begins with
  tenant and customer commitment for protected-demand reads.

### Service invariants

- Supplier side has type `supplier_delivery`; customer side has type `customer_delivery`.
- Items match. Locations must be compatible under the existing commitment/location rules.
- Effective non-reversed assignment cannot exceed supplier quantity in force less fulfilled or
  cancelled quantity as defined by the service contract.
- Effective customer assignments cannot exceed remaining customer demand.
- A reversal cannot exceed the still-effective quantity of the row it reverses. Reversing a reversal
  is not allowed; a new assignment expresses the new statement.
- Rows are immutable after insertion. Assignment, reversal and referenced commitments are locked and
  revalidated in the confirming transaction.
- Absence is `unassigned`; it is never interpreted as stock replenishment.

## Derived observations

### Supply coverage

For each supplier commitment: quantity in force, received quantity, open quantity, effective
customer-assigned quantity, explicit stock-replenishment quantity and unassigned quantity. For each
customer commitment: demand in force, delivered quantity, open demand, active reservation and
effective protecting supply. These figures are calculated at read time without becoming authority.

### Return resolution

For an inbound return movement: arrived quantity, effective resolving movements, disposition label,
resolved quantity and unresolved quantity. Corrections remove superseded movements from the effective
set. Credit/settlement state is read independently from document and ledger evidence.

### Movement explanation

A structured read containing the movement, effective/corrected state, explanation kind, shortest
primary record, supporting records, source link, human reason when stated and Inspector targets. It
stores nothing.

### Contribution

Revenue, consumed retained acquisition cost, DB1, reviewed selling costs and DB2 are derived for a
supported invoice line. Missing, stale, ambiguous, unreviewed or incompatible evidence produces an
unavailable result with stable reason codes, not a numeric zero.

## State transitions

- Supply assignment: absent → stated → partially/fully reversed; replacement is a separate new row.
- Customer return: announced → partially/fully arrived; each arrival → partially/fully resolved;
  goods and financial credit advance independently.
- Invoice action: previewed → confirmed/recorded or unresolved outcome; replay returns the recorded
  outcome.
- Projection: due → running → completed/failed; readers retain the last completed version while due
  or running.
