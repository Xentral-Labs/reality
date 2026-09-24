# Data Model V0

All business tables have `id`, `tenant_id`, `created_at`.

| Table | Purpose | Key fields / links |
|---|---|---|
| tenant | company boundary | name, immutable purpose (`business`/`playground`), archived_at? |
| playground_run | private learning orchestration metadata; a storyline run is one of these | unique tenant_id, owner_user_id, versioned preset/lesson or storyline key/version, branch choices (storyline_state), creation retry key, lifecycle |
| playground_step | historical learning observations, not operational truth | same-tenant run_id and proposal_id (null for read chapters), sequence, retry key, bounded before/receipt JSON, marker sequence and time of the confirmation (storyline) |
| storyline_trace_entry | bounded call trace of one storyline run: reads, proposals, confirmations, GET views, errors, inside or outside a chapter | same-tenant run_id and step_id?, ordinal, kind, name, access, actor, proposal_id?, marker sequence and time?, open findings before the confirmation?, bounded input and result JSON |
| interaction | engine-room telemetry (spec 266): one value-free observed use of the model through one channel, kept seven days, never a business record | cursor, channel, kind, operation (tool or route template), outcome, error_code?, actor_user_id?, same-tenant mcp_token_id? and proposal_id?, job_id?, correlation_id, committed event sequence ranges?, refresh, argument names and result count |
| storyline_package | a storyline an account imported, private to that account | owner_user_id, key, version, checksum, validated document JSON, imported_at, replaced_at? |
| tenant_membership | current account authority for one company | user_id, role (`owner`/`member`), status (`active`/`removed`) |
| company_invitation | administrative evidence that one normalized email may join a company | status, token_hash, token_generation, expiry and terminal timestamps, inviter/acceptor user links |
| invitation_delivery | retryable token-free invitation notification intent | invitation_id, generation, locale, retry/lease/delivery state, sanitized provider result |
| security_audit_event | immutable global or tenant-scoped access audit | tenant_id?, subject type/ID?, actor/user IDs?, event type, outcome?, redacted detail |
| party | customer/supplier/company | type, name, source_record_id? |
| party_email_address | exact correspondence address for one Party | party_id, email, normalized_email, label |
| item | product/service | sku, name, base_unit, source_record_id? |
| location | warehouse/bin/virtual | type, name, parent_location_id?, external_refs_json |
| source_system | one configured origin | code, name, description, connector_code?, base_url?, is_active |
| source_stream | stable external identity head | source_system, source_type, external_id, current_source_record_id? |
| source_record | immutable source truth | source_system, source_type, external_id, payload_hash, version, source_version_at?, supersedes_source_record_id?, received_at, payload_json |
| import_job | retryable source interpretation | source_record_id, status, attempts, input, error, next_attempt_at?, completed_at? |
| document | minimal evidence header | source_record_id?, type, number, party_id?, dates, currency, totals, source lifecycle status only |
| document_line | minimal evidence line | document_id, source_line_id?, item_id?, sku?, quantity/unit, agreed price/amounts, price_list_entry_id?, billed_document_line_id?, requested/promised time, payload_json? |
| commitment | directional promise | type, from/to party, item/location?, qty/unit?, amount/currency?, due_at?, status, document_id?, document_line_id?, fulfilled_at? |
| reservation | allocation | commitment_id, item_id, location_id, qty/unit, status, timestamps |
| movement | observed physical change | type, item_id, from/to location?, qty/unit, occurred_at, commitment_id?, source_record_id?, resolves_movement_id? |
| movement_correction | auditable physical correction relation | original/compensating/replacement Movement IDs, reason, corrected_at, actor context, semantic request fingerprint |
| shipment | real physical consignment | direction, purpose, counterparty, source_record_id? |
| shipment_package | carrier/tracking grain | shipment_id, carrier?, tracking_number?, source_record_id? |
| shipment_event | append-only logistics observation | shipment/package IDs, event type, reporter, occurred_at?, source_record_id? |
| shipment_event_supersession | append-only event correction | original/replacement event IDs, reason, actor context, source_record_id? |
| ledger_entry | observed financial posting | accounts, party?, amount/currency, debit_credit, effective_date, tax?, document_id?, source_record_id? |
| ledger_reversal | auditable financial correction relation | original/reversing posting-group IDs, reason, reversed_at, actor context, semantic request fingerprint |
| settlement_allocation | explicit settlement link | payment_ledger_entry_id, invoice_ledger_entry_id, amount/currency, allocated_at |
| fact | immutable source-supported observation, not operational state | opaque subject identity, cataloged predicate, canonical value, observed_at, recorded_at (when Reality wrote it, independent of business time), source_record_id, tenant-scoped retry fingerprint |
| interpretation outcome | immutable audit of one terminal source-processing attempt | source_record_id, import_job_id, attempt, classification, interpreter identity/version, safe reason, completed_at |
| interpretation record reference | produced or recognized identity from one successful interpretation | interpretation_outcome_id, controlled record type, opaque record ID |
| change proposal (`action` physical table) | audit of a prepared change, its approval decision, and execution | tool type, proposer, status, created/executed time, input/output JSON |
| chat session | retained tenant conversation, active or archived for presentation | title, created/updated time, archived_at? |
| chat message | durable message in one tenant conversation | chat_session_id, role, content, created_at |

## Invariants
`Movement.shipment_package_id` is the shortest true link to exact physical Package contents.
Tracking observations do not change stock or fulfillment, and legacy Movements are not backfilled
into guessed Shipments.

Commitments may exist without Documents. Reservation has only `commitment_id` for provenance. Movement has no Document/Line FK in V0 unless a scenario proves it. Ledger defaults to Document-level provenance. A payment has its own evidence; SettlementAllocation links only the two relevant control-account entries and does not duplicate their document/source links. Stock derives from Movements, not Facts. Raw SourceRecord payload and version metadata are immutable/lossless. SourceStream alone moves its current-source pointer. SourceRecord and ImportJob are created atomically; Evidence and Reality interpretation is independently retryable.

ImportJob is mutable queue state, not interpretation history. Every terminal attempt
appends an InterpretationOutcome. A successful outcome may reference produced
Documents, DocumentLines, and Commitments by controlled type and opaque ID, but this is
audit metadata and never replaces their Source → Evidence → Reality provenance.
Historical sources without an outcome are shown honestly as `not_recorded`.

A Fact is an immutable observation about one existing opaque Reality subject, supported
directly by an immutable same-tenant SourceRecord. It is not current operational state
and never mirrors a value already owned by Commitment, Reservation, Movement,
LedgerEntry, Party, Item, or Location. New Facts use the shared `observe_fact`
operation with a reviewed predicate, canonical scalar value, observation time, and
idempotency identity. Agents and interpreters may propose an observation but never
write the table directly. Hypotheses, calculations, process rules, and mutation audit
belong in proposal, projection, policy, or BusinessEvent records. Legacy Facts remain
readable even when they predate this strict write contract.

DocumentLine pricing is immutable agreed Evidence. Its optional PriceListEntry link is
the shortest true pricing provenance; it does not duplicate PriceList, Party, Item, or
SourceRecord links. Current pricing is resolved on demand and never rewrites the line.

An invoice line's optional `billed_document_line_id` names the order line it bills. It is
Evidence about Evidence — which agreed line a billed line settles — and adds no status to
either document. The link is the shortest true one, from the billed line directly to the
agreed line and never through the Party, the Item or a date window, and it is refused
unless it points at a sales or purchase order line of the same tenant on the matching side
of the business. A null reference is a statement rather than a gap: the line bills nothing
an order promised, as freight, a service or a rounding line does. Nothing derives from the
link at write time; how much of an order line has been delivered and how much of it has
been billed remain read-time observations.

Movement correction uses one tenant-scoped ternary relation with opaque FKs to the
immutable original, exact compensating `correction` Movement, and optional replacement.
It duplicates no Document, DocumentLine, Commitment, or SourceRecord provenance.
Correction role, net stock, fulfilment, and tracked current location remain derived from
the append-only Movement journal and relation.

Membership invitations are tenant-scoped administrative Evidence, not business Reality.
They link to the company and normalized email before acceptance, never to a prospective
account or membership. Acceptance creates or reactivates the existing unique
tenant/account membership; neither record duplicates a link to the other. A delivery
links directly to its invitation and stores no clear token or rendered body. Minimal
token-free security audits outlive the 90-day terminal invitation retention window.

## Finance-specific external destinations

`accounting_target` owns an explicit tenant-local destination namespace.
`accounting_target_reference` defines its permitted account/tax-code references with
same-target typed foreign keys. Neither catalog contains financial amounts or tax
logic. `finance_target_mapping_revision` stores immutable reviewed local-account or
transaction/case/group routing decisions. Current markers support exact lookup;
append-only revisions retain snapshots, reason, actor and confirming action.
A tenant finance lock serializes catalog changes and activation. Composite tenant,
target and reference-kind constraints prevent invalid relationships. Refer to
spec 148 target-mappings.md for shapes and lifecycle. These catalogs deliberately
remain Finance-specific; no generic registry or polymorphic owner relation is added.

## Storyline records (spec 182)

A storyline run is a practice run. Its trace entries and the markers on its steps are
learning evidence about calls, never operational truth: a delta is read forward from a
marker at request time and stored nowhere. `fact.recorded_at` is the only business-table
change; it records when Reality wrote the Fact so a chapter's delta can list Facts observed
in the past but recorded now. Imported packages belong to the importing account, not to a
company, and are validated before they are stored.

## Private analytics configuration (spec 185)

`analytics_report` stores an opaque ID, tenant, authenticated AppUser owner, name,
versioned JSON definition with presentation, revision, payload-bound creation/last
request keys, timestamps and deletion tombstone. It contains no result rows and is
not business authority. Owner and active company membership constrain every read or
change; `(tenant_id, owner_user_id, create_request_id)` prevents duplicate retries.
Migration 0060 is additive and refuses destructive downgrade once reports exist.
See [Analytics](features/analytics.md).
