# Playground Interface and Learning Contract

## Supplier finance and returns (FR-022–023)

The same reviewed step endpoint accepts supplier_invoice_record and
sales_credit_record with order_line_id, number, positive quantity, stated gross_amount
and optional aware effective_at. Supplier invoices require a purchase order line and
received, unbilled goods; credit requires returned, uncredited sales goods. Both
create Source/Evidence and balanced postings through common application commands.
supplier_payment_post uses invoice_id/payment_number/amount; customer_refund_post
uses credit_note_id/refund_number/amount. Both use the common atomic settlement path.
Wrong document types, foreign IDs and excess amounts are rejected before proposal.

movement_create(type=return) requires the original customer Commitment, matching
item and to_location, positive quantity and optional aware occurred_at. from_location
is null. Shared movement rules cap returns at shipped-minus-returned goods; original
fulfillment stays intact. A return receipt carries the shortest order-line link for
the subsequent credit review. It never creates financial records implicitly.

Exact decision intent, trusted action IDs, immutable receipts and generic-route
denials remain in force. Selecting the cockpit return card requires an existing
shipment; historical shipment selection never starts a new sandbox. Supplier invoice
and credit lines preserve stated amounts instead of calculating them from unit price.

## Purchase/receipt continuation (FR-020)

The existing step endpoint accepts order_create with direction=purchase and the
same single-line inputs as sales. It delegates to the ordinary atomic manual-order
command. movement_create additionally accepts movement_type=receipt, a required
supplier commitment_id, item_id, to_location_id, positive quantity and optional UTC
occurred_at. from_location_id must be absent/null; unknown fields are forbidden.
Preparation validates the supplier commitment's item/location and current open
quantity. Confirmation binds the reviewed values and action identity, rechecks
the fingerprint and executes the shared Movement command. The receipt contains
correlated events, the Movement ID and shared before/after stock and open quantity.
Partial receipts can be followed by another receipt against the same commitment.
These operations neither replace the sandbox nor create payable/payment records.
Returns and supplier finance remain unavailable. Owner/admission and generic-write
restrictions remain unchanged.

## Approved invoice/payment extension (FR-018)

The existing step prepare/confirm/read endpoints additionally accept
`sales_invoice_record` (order_line_id, positive quantity, positive stated gross_amount,
number, optional UTC effective_at) and `customer_payment_post` (invoice_id, positive
amount, payment_number, optional UTC effective_at). Unknown fields remain forbidden.
The owner/run resolver supplies tenant identity. Generic sandbox tools stay denied.
Invoice quantity is limited to delivered, not previously billed goods in this lesson;
payment cannot exceed the current receivable. Stale financial state invalidates review.
One shared invoice command creates Source, Document/Line and balanced LedgerEntries;
the payment command creates payment Evidence, LedgerEntries and SettlementAllocation.
Each operation requires a separate confirmed proposal, and each financial record/event
is attributed to that action. Replayed confirmations retain the write-once receipt.
Existing trading histories can continue after shipment without rewriting prior steps.
Partial-delivery histories keep their four-step presentation. This is not a general
invoice generator, split-billing workflow or external payment integration.

Status: target contract. Entry GET, run detail GET and confirmed start POST are implemented;
remaining endpoints are planned. No public activation. Every adapter delegates to shared services.

Historical first milestone (extended by FR-018–020): authenticated private HTTP exposes `/api/playground/runs/{id}/steps`
prepare, detail, confirm and reject endpoints. The first slice supported only `movement_create` with
`movement_type=opening_stock`; no CLI/MCP/chat preparation adapter is exposed yet.
The HTTP layer resolves the owner from the account cookie and the run on the server; no tenant
ID is accepted. It returns proposal/step IDs, sequence, original proposal status, resolved arguments and
labelled reference preview. Internal confirm_step/reject_step/read_step now support this one
action, with explicit confirmation, preview revision and actual correlated Movement verification.
No CLI/MCP/chat adapter is exposed yet. Proposal/step creation is atomic and
same-key normalized request replay preserves the original timestamp. Exact requested intent
is retained in the preview and copied into the step's before-observation metadata before execution.
Replaying missing identity fails closed. Execution and observation availability remain separate:
an interrupted executing proposal stays unsettled, even when its exact effect is visible.
It blocks further mutations, never retries blindly, and still permits owner reads. A completed
proposal with an unavailable observation can retry that observation without reexecuting.

## Account and route boundary

Scenario-library increment: `GET /api/playground` advertises executable `trading/1`
and `partial-delivery/1` presets. Other learning goals are presentation-only and
cannot be started. `POST /runs/{id}/restart` optionally accepts preset_key,
preset_version and request_key in addition to strict confirmed=true. Unsupported
versions are rejected before archiving. A repeated owner/request key with identical
preset returns the original replacement, including after a lost response. Original
runs and their tenants remain available for inspection; no record is deleted.

Product route `/playground`, optional `/playground/runs/{run_id}`. No tenant ID from local storage
selects the target of a Playground command. Run ownership and purpose resolve it on the server.
Login/signup return destinations use a fixed local allowlist, not arbitrary redirect URLs.
Pending production accounts may access only this lane and allowlisted run-local reads/actions.
All other existing production admission checks stay unchanged. Archived runs are read-only.

## Proposed HTTP surface

| Operation | Contract |
|---|---|
| GET /api/playground | Own run summaries, supported preset/lesson version, remaining quotas, provider availability |
| POST /api/playground/runs | Confirmed start; request_key, preset_key/version; create a new personal sandbox only |
| GET /api/playground/runs/{id} | State, progress/error, lesson position and run-local references; not-ready status only during setup |
| POST /api/playground/runs/{id}/restart | Confirmed fresh run with request_key; activate only after successful seed; archive predecessor |
| GET /api/playground/runs/{id}/steps?cursor=... | Ordered receipts and proposal verification states; bounded page size 25, max 100 |
| POST /api/playground/runs/{id}/steps | Prepare one allowed operation, typed arguments, request_key and optional lesson_step_key; never executes |
| POST /api/playground/runs/{id}/steps/{step}/confirm | Explicit human confirmation of exact proposal/preview revision; standard executor and verification |
| POST /api/playground/runs/{id}/steps/{step}/reject | Standard rejection; no business effect |
| GET /api/playground/runs/{id}/position | Current shared-reader inventory, commitments, active Reservations, Facts, Exceptions and freshness |
| POST /api/playground/runs/{id}/messages | Persist user text, quota check, bounded managed read/propose loop; no execute tool |

Reference picker uses the existing tenant-scoped suggestions/discover service behind run ownership
checks. Existing Inspector and read-only Views use the same policy, sandbox banner and back link.
Preparation returns proposal_id, step_id, normalized intent, defaults, exact target references
and confirmation affordance. Duplicated request_key with same payload returns the same step;
changed payload with the same key returns conflict. Opaque IDs never come from name guessing.

Results: unauthenticated 401; unavailable admission 403; inaccessible run/record 404 without
existence leakage; invalid action 422; changed preview/run-busy/idempotency conflict 409;
quota exhausted 429 with remaining/reset guidance. Error messages expose no credentials.
Execution failures use the standard proposal status and explicit verification state, not HTTP
success alone. A 2xx receipt must not imply domain execution when status is proposed/unknown.

Current entry list defaults to 25 rows, at most 100, with a non-negative offset and total.
Creation quotas include remaining daily/retained capacity and the next UTC-day reset.
`entry_enabled` reflects the deployment flag; reads remain available when it is off.
`chat_available` is false until the managed Playground path exists. Not-ready run details
return null references and tenant_id; they never expose partial setup for generic inspection.
Start rejects unknown fields and requires an actual boolean confirmation, not a truthy string.
Owned run detail includes its original request_key so interrupted setup can be explicitly
retried after a reload without relying on browser storage or creating another run.

## Tools and transport parity

Register run start/status/restart and step prepare/status as named application services/tools
with explicit account actor context. Existing approval service remains the execution authority.
Do not expose run creation as an unauthenticated CLI command or widen normal MCP tenant authority.
Authenticated internal CLI/API tests may target an owned run; public MCP token creation is denied
for playground tenants in V1. A service-level operation policy blocks bypass via generic routes.
Account-level start/restart is an explicit lifecycle operation; startup seed capability is internal,
short-lived and bound to the initializing run, not granted to the model or frontend.

## Receipt shape and proof hierarchy

- Identity: run, step, proposal; evaluated_at and exact event watermark.
- Execution: original proposal state and execution evidence status.
- Effects: created/changed records with opaque IDs, automatic/manual cause, correlated event IDs.
- Before/after: bounded derived measurements, units and record provenance; unavailable != zero.
- Exceptions: added/still-present/no-longer-derived by normal issue identity and current read.
- Unchanged: supported assertions such as physical stock unchanged by reservation; no inference
  that every unlisted business field stayed unchanged.
- Verification: verified, pending/unavailable, or unknown; explicit next safe read/check.
- Links: existing record Inspector destinations, optional source/evidence where genuinely present.

Do not assert an action produced zero Facts from a model's expectation; determine effects from
supported returned IDs/events and verified readers. Do not count automatic active-remainder
creation as a new user reservation. Source payloads never become editable through receipts.

## Golden learning sequence: order-stock-v1 / trading-v1

Preset creates only reference data. Explicit sample order input: 12 BIKE-LIGHT at EUR 49,
line amount EUR 588 and total EUR 588 as supplied fixture values (not recomputed by Reality).
Lesson order date is the run's UTC date, requested delivery is next day; timestamp defaults are
shown before confirmation. Tests fix the date. No clock-advance control in V1.

| Confirmed action | Physical | Reserved | Available | Customer open | Required record effect |
|---|---:|---:|---:|---:|---|
| Record opening stock 20 | 20 | 0 | 20 | 0 | Movement |
| Create customer order 12 | 20 | 0 | 20 | 12 | SourceRecord, Document, DocumentLine, Commitment |
| Reserve 12 | 20 | 12 | 8 | 12 | Reservation |
| Record shipment 5 | 15 | 7 | 8 | 7 | Movement, consumed original Reservation, active remainder 7 |
| Record shipment 7 | 8 | 0 | 8 | 0 | Movement, consumed remainder, fulfilled Commitment |

After each row read actual Exceptions; expected identities are pinned from current catalog and
service behavior in the scenario test. Do not invent a shortage merely because demand is unreserved.
A supported free-form variant can order 30 against 20; reserve returns 20 allocated and 10 unmet.
Purchasing to resolve it is out of V1; explain this instead of pretending to execute it.

## UX contract

No blank company form before the first lesson. One visible Start playground confirmation explains
that synthetic reference records will be created and no real business effects will be sent.
Persistent sandbox label, run name, restart and archived state live in normal shell space.
Desktop shows Try / What happened / What is true now together; mobile has labelled accessible
tabs or stacked regions with selected step preserved. No fixed overlay obscures confirmations.
Both chat and buttons enter the identical preview. Ambiguous references use the existing keyboard
combobox. Loading/busy/provider-unavailable/unknown/stale/empty/archived states are distinguishable.
Record names are bold or badges; calculated numbers never masquerade as stored records.
At most five business measurements shown initially; expanded Inspector supplies technical detail.
No placeholder conversational answer is presented as newly queried evidence.

Public Docs preview shows the five-step sequence without user data or API calls and links to
APP_URL/playground. Site adds a restrained discovery link using configured product origin and
language. The existing 15/30/60-minute learning paths remain intact.
