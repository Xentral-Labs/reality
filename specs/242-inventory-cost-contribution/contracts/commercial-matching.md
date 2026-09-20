# Partial commercial matching contract

## Status and boundary

This contract refines T085, FR-002/003/007/010/011/017 and SC-001/003/004/005.
The owner approved this exact three-table, append-only authority on 2026-09-20.
Existing full-line contribution reviews and historical replay remain valid without rewrite.

The current `cost_revenue_match_basis` binds one complete sales invoice line to one
complete shipment. Its uniqueness and required single movement/member links are truthful
for legacy reviews and must not be weakened into ambiguous nullable compatibility fields.
Partial matching therefore uses a separate revisioned authority instead of changing the
meaning of retained rows.

## Proposed retained authority

### `cost_commercial_match_revision`

One immutable, tenant-scoped owner decision for one sold `DocumentLine`:

- opaque id, tenant id, sold document-line FK and optional ordered document-line FK;
- positive revision, nullable unique supersedes FK, introduced event, confirmed action
  and reason;
- exact source-stated signed net amount, nullable signed non-zero source quantity when the
  source states quantity, currency, nullable unit and evidence hash;
- `goods_cost_disposition`: `inventory`, `direct_evidence`, `not_applicable` or
  `unresolved`;
- profile, input-schema version and canonical content hash.

The source-stated amount and quantity are copied losslessly from the admitted evidence;
they are never recomputed from match parts. Sales invoice, credit-note, free-goods and
service/shipping-only semantics come from the source document type and explicit
disposition, not the sign or product description alone.

### `cost_commercial_inventory_part`

One immutable exact portion of reviewed inventory consumption or return assigned to the
match revision:

- match-revision FK and frozen `cost_inventory_member` FK;
- nullable original-issue `cost_inventory_member` FK, required only for a customer return;
- entry and receipt `cost_movement_basis` FKs naming the exact retained cost portion;
- exact positive quantity in that inventory item's base unit;
- unique match/member/entry/receipt identity and schema version.

The linked inventory member determines shipment versus customer return. Cost is observed
from that member's frozen inventory review at read time. No unit cost or allocated amount
is stored. A sales credit can therefore carry negative received revenue and exact negative
return cost without rewriting the original sale.

### `cost_commercial_direct_part`

One immutable source-backed direct cost portion for a sold service, shipping-only line or
an explicitly evidenced kit/production input that is not represented by an admitted
inventory consumption:

- match-revision FK and existing `cost_attribution_revision` FK;
- explicit semantic input role and schema version;
- unique revision/attribution/input-role identity.

This table does not accept or copy caller-authored amount, share, currency or calculated
cost. It observes the complete existing retained source-backed attribution revision.
Partial/weighted component allocation remains T087 work. General overhead, inferred
production cost and arbitrary cross-currency allocation remain unsupported.

## Conservation and admission

The confirmed request supplies the complete disjoint match set for the sold line. For an
`inventory` disposition, exact inventory portions must conserve the sold line's admitted
quantity after applying the document's explicit invoice/credit direction. A frozen
inventory portion may be shared across several sold lines only when the sum of all active
match revisions does not exceed its reviewed quantity. For `direct_evidence`, every part
must share the sold currency and the request must explicitly close any residual.
`not_applicable` requires zero active goods-cost evidence. `unresolved` remains visible and
cannot produce a complete DB1/DB2 result.

Rematching appends a revision and supersedes the prior decision. It never mutates or
deletes prior parts. Current admission checks the latest non-superseded revisions across
all affected lines and inventory portions in one tenant-serialized transaction. Historical
reads use only their frozen revision and inventory/component references.

The header is created with an internal `building` hash, accepts its parts only in that
state, then seals through the sole permitted header update to a 64-character canonical
digest. Sealed headers and every part are SQL-immutable. This is lifecycle integrity, not
a second business status or calculated financial authority.

Split invoices, partial shipments and many-to-many matching are therefore represented by
several line revisions whose exact parts conserve both sides. No order/document status,
human number, location, settlement link or mutable latest row becomes match authority.

## Services and adapters

Extend the existing `cost.change` proposal with explicit commercial match portions and
expected candidate hash. Preview remains SELECT-only. Confirmation uses the existing
owner authorization, tenant lock, event, action, replay and rollback services. CLI, MCP,
chat and web continue calling those shared tools; no direct ORM mutation or automatic
matching job is introduced.

The first implementation sequence is domain conservation, retained schema/migration,
candidate admission, confirmed replay, contribution calculation, then existing adapters.
Unsupported WIP, inferred conversions and incomplete evidence refuse with named gaps.

## Test-first acceptance matrix

- split and partial billing/fulfilment in both directions, with exact quantity and amount
  conservation and deterministic Decimal rounding;
- signed sales credit with exact original return portions and unchanged historical sale;
- free goods, direct service and shipping-only line with explicit disposition;
- evidenced kit/direct input, unresolved residual and unsupported WIP refusal;
- duplicate, overlap, gap, excess, currency/unit/item/customer and foreign-tenant refusal;
- append-only rematch, stale confirmation, same-request replay, hash tampering and old
  historical replay;
- migration FK/constraint parity, immutable retained rows, empty round trip and populated
  downgrade refusal;
- contribution/generation/graph/Inspector/tool/MCP/catalog/generated-doc regression.

## Approval question

Owner approval covers the three new tenant-scoped tables and their exact links, plus
append-only superseding revisions. It does not activate an accounting policy, perform a
live migration, seed demo data, deploy code or authorize inferred matching.
