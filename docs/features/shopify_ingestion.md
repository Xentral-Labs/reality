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


## Original selected GraphQL order intake (spec 388)

`shopify_order_graphql_capture` is a separately permissioned MCP evidence-capture tool.
It calls `capture_shopify_graphql_source` and canonical `enqueue_source`, hardcodes
`shopify/order_graphql`, derives the external identity and upstream version time from
the unchanged original `data.order` JSON entity, and returns source/job identities.
It accepts no arbitrary source type, no acceptance operation and no generic approval.
When supplied, acquisition metadata includes the exact shop hostname, API version, query digest, observation time and complete-selected-order coverage; it remains attributed host input, not independent vendor verification.
The authenticated MCP principal owns the destination tenant; host callers separately
pin the installed Shopify shop and exact order. Technical response cost/throttle
extensions are not part of this entity. This is lossless retention of the selected
entity fields, not the full upstream resource or HTTP envelope.

The supported first-order interpretation requires complete bounded line nodes,
matching currencies, original/current quantities equal, an uncancelled unfulfilled
order and explicit existing company/customer/location mappings. The internal projection
feeds existing reviewed intake without replacing the SourceRecord or original line
payloads. Received order totals and original unit prices are retained; unstated line
totals remain unknown. Unknown original fields remain in SourceRecord unchanged.

Call separately permitted `intake_prepare_propose` to prepare the exact business-effect
proposal. No apply or business effect happens during capture/preparation. Missing buyer
mapping retains `review_required` plus a named original-source interpretation outcome,
not an empty fake proposal, invented customer, or new master data. An accepted legacy or
GraphQL order with the same external identity blocks a second first-order interpretation.
Unsupported changes require a separate reviewed update route.

An identical source replay returns its original source/job; it does not rewrite frozen
mapping. Changed or newly supplied mapping on an existing job is refused explicitly.
A later mapping-resolution flow is separate scope. Raw sources may contain private
fields and must not be printed into chat merely to demonstrate successful capture.

## Explicit existing buyer mapping (Spec 389)

A retained `order_graphql` source with no explicit Reality buyer mapping can use
`shopify_source_buyer_candidates` to search bounded active existing customer-role
identities. `shopify_source_buyer_mapping_prepare` freezes exact original source,
job, hash, integer version and current customer digest. Tuesday Main presents the
actual customer and source for an explicit human confirmation; a trusted host
signs that exact review. Models and submission tokens cannot approve.

The narrow commit validates Ed25519 issuer/subject/key/expiry and all current
source/customer preconditions, then records a mapping-only Action and immutable
approval Source. Status preserves the original human approval UUID and compact
proof digest; unknown reconciliation must match its retained proof exactly. A
canonical mapping reader is used by candidates/status and current GraphQL intake.
The original source and ImportJob.input remain unchanged. Intake remains held as
`buyer_mapping_recorded_intake_pending`; no accepted order or full business
proposal, customer creation, payment, fulfillment or inventory effect follows.

The private host policy defaults to deny and pins one exact source/job/order/shop
and Main public issuer authority. The version-pinned schema99 overlay supports
only this mapping/receipt relationship, not the newer full intake subsystem.

## Read-only retained intake preflight (Spec390)

`shopify_source_intake_preflight` reads one exact current source/job/hash/integer
version. It recognizes the canonical reviewed buyer and diagnoses only retained
existing company/location references plus bounded exact active SKU/item evidence.
It neither chooses missing references nor accepts mapping overrides. First-order
interpretation remains unavailable when the external Shopify identity already has
an accepted sales order, using the same guard as canonical preparation.

Reference fingerprints bind the stable fields this report observes: identity,
label, active state and source link, company roles/type, location stock capability
and parent/type, or item SKU/unit/type/tracking. They are read fingerprints, not
new master versions or acceptance tokens. Selected master candidates and source/
buyer identity are checked again before return; changes refuse a mixed report.

A stock unit is not a received sales-unit statement. Unit, line-total and delivery
interpretation gaps describe selected/projection coverage, not missing facts in
the upstream order. Payment, credit exposure, stock, settlement and full intake
remain unassessed. At most100 lines and explicit selected-entity coverage are
returned; reports over24000 UTF-8 bytes refuse rather than silently remove facts.
The semantic SHA256 digest uses sorted compact JSON with literal Unicode UTF-8,
no normalization, excluding observation time and the digest itself.

The read issues no persistent write, preparation, proposal, interpretation outcome
or accepted business effect. Existing schema99 requires a separately hash-pinned
read-only overlay and proof; a current-code PR alone is not deployment evidence.

## Combined explicit order proposal (Spec391)

shopify_source_order_prepare retains existing company/location/item and explicit
same-unit selections together with source-linked prospective order meaning. Buyer
must match its separately verified mapping. Choices remain proposed, never approved
by a manual token or a buyer-only proof. No amount overrides or default units.

Stated source total/quantities are preserved; original unit price is evidence only,
not assumed final. Missing final/line/date/calendar/credit interpretation stays held.
Item type defines product kind; requiresShipping is not accounting classification.
Review exposes all prospective business arguments and source links; original line
evidence remains intact in retained meaning. Dedicated Action is not generically
executable; source and job.input remain unchanged and no business record is created.

Legacy GraphQL without explicit unit semantics now has a named review hold instead
of using the REST unit/price defaults. REST behavior stays unchanged. Exact issuer/
standing-mandate acceptance and preparation-origin adoption are successor work; no
fake Principal or broad confirmation grant. Old99 proposal proof is not full intake
application readiness.

## Exact source-backed order acceptance (Spec392)

The separate successor preparation/review/accept/status contracts support one
simple undiscounted source-v2 profile. They preserve391 proposal-only digests and
389 buyer-mapping wire contracts. One review freezes explicit existing buyer,
company, location, item/unit selections and all prospective business arguments.
Missing or unsupported financial/calendar/credit evidence is held, not guessed.

All persisted unit/line/order amounts are copied from source, with comparisons
only for eligibility and exact Numeric(18,4) representability. Complete explicit
zero ancillary money is required; provider-documented nullable fees with selected
empty additionalFees and nullable duties with ALL complete unchanged empty line
duties are retained as typed not_applicable evidence, never numeric0. The profile
requires explicit source-backed company timezone, reviewed processed-at day rule,
not_promised delivery terms and complete current canonical positive-limit credit.

Only a dedicated exact Ed25519 external human or current finite standing proof
may authorize canonical order Document/Line and customer-delivery Commitment
creation. Normal current MCP scope, private issuer/company/subject/token/profile/
limits policy, expiry, immutable source/reference digests and cumulative mandate
caps are checked under locks. Source/job.input remains unchanged; acceptance
completes the held import job and retains interpretation outcome plus atomic
original-proof receipt. No fake local Principal or generic confirmation is used.
No payment, stock movement, fulfillment or settlement is authorized here.

Buyer receipt evidence is explicitly historical mapping-only; its old remaining
review label is omitted from successor wire. Dedicated successor status is the
acceptance reconciliation authority, not an inference from a legacy buyer label.
Status waits an in-flight acceptance row and never repeats dispatch or renews an
expired approval. Lost responses reconcile the same original receipt; a different
proof cannot alias a completed intent. Accepted facts remain historical evidence,
not a new claim about current credit, payment, stock or delivery.

Current native code only: no schema99 application adapter, migration, runtime
installation, live grant/provider/company operation or full autonomous O2C claim
is implied. See specs/392-shopify-order-acceptance for implementation evidence and
remaining deployment/current-application gates.
