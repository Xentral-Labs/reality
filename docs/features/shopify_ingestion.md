# Feature: Shopify ingestion

## Contract

1. Read and validate the input as JSON.
2. Persist the complete payload as an immutable SourceRecord before interpretation.
3. Map only stable fields needed by core behavior into Document/DocumentLine.
4. Create one outgoing delivery Commitment per relevant item line.

Shopify order and line IDs remain external references and never become internal IDs.
Unknown fields remain losslessly available in raw payloads.

Re-ingesting the identical `(tenant, source system, source type, external ID, payload)`
returns the existing interpretation. A changed payload creates a new SourceRecord
version; it never overwrites source truth. Interpretation failures retain the source
record and become explainable issues.

Idempotency is enforced by the database over the tenant-scoped source identity plus a
SHA-256 hash of canonical JSON. Source insertion and creation of a unique ImportJob are
one transaction. Interpretation is a separate retryable transaction.

A later version of an interpreted order is compared with the order's current Reality
(spec 296). It is applied automatically only when it reduces open, unshipped quantity:
a lower `current_quantity` (or `quantity`), a removed open line, or `cancelled_at` while
nothing has shipped. The reductions go through the ordinary revision and cancellation
services and cite the version as their source. Every other change (a higher quantity,
a new line, a price, address or currency change, a change on a closed line, a
cancellation after shipment, or a reduction that needs a reservation choice) is held
as `needs_review` with a coded reason, and nothing changes; a version is applied
completely or not at all. A version that changes only fields Reality does not
interpret is recorded without effect. A version whose order was never interpreted
still requires review, as does any change while the first version failed or is
pending. SourceStream points to the newest accepted source; an older version
processed after a newer one applies nothing.

The review explanation names every code and is visible through interpretation
coverage and ImportJob reads. Processing an already reviewed job is a no-op; explicit
retries record another review attempt but cannot bypass the guard. The synchronous
Shopify helper reports the review explanation instead of claiming stale delivery or
successful interpretation. First-version retries and already successful
interpretation replays remain supported.

An order line whose SKU matches no item no longer stops the order: the known lines
are interpreted and promised, and the unknown line is kept as a document line without
an item or promise. `order_line_item_unknown` reports it until a person assigns an
item with the reviewed `order_line_item_assign` tool, which creates its promise.

Refunds in an order payload are stored as their own `shopify/refund` source records
and become `sales_refund` evidence on the order without a posting; a refund of shipped
goods the shop says come back announces the return.
See `specs/081-shopify-update-guard/spec.md` and `specs/296-shop-order-changes/spec.md` for the contract.

A tenant-scoped SourceStream owns the external identity and points to its current
SourceRecord. Moving that pointer never mutates a SourceRecord and stale/conflicting
deliveries cannot accidentally become the current version.

When Shopify supplies `updated_at`, it orders source versions. An older delivery is
stored losslessly but is not interpreted over a newer version. Equal source timestamps
with different payloads are retained and reported as conflicts. Without an upstream
version timestamp, arrival order is authoritative.

One Shopify order interpretation may create only one sales-order Document per
SourceRecord, one DocumentLine per non-null source line ID, and one customer-delivery
Commitment per interpreted DocumentLine. These constraints make worker retries safe.

Tests compare the stored decoded JSON with the complete fixture and verify tenant-local
idempotency, changed-payload versioning, and no cross-tenant collision.
