# Retained company census: storage review

Status: the owner explicitly approved this five-table storage model and staged implementation
on 2026-09-19. Implementation and verification evidence are tracked in tasks.md.

Scope: spec242 FR-007/012/014/018/019, continuation of T158–T165 and the approved staged
production model. This proposal adds storage for *unassessed current discovery*, which
is not the same authority or historical contract as the approved financial manifests.

## Decision to review

Add a dedicated census header and four typed member tables. Preserve exact observed
values of mutable movement/document/line records and exact immutable source/outcome
identities. Capture everything in one bounded REPEATABLE READ transaction. Never call
this a sealed financial manifest or infer that the captured inputs are approved.

The existing CostInputManifest remains unchanged. Its knowledge_at, sealed receipt-v1
membership and references from confirmed reviews retain their existing meaning.

Why this is necessary:

- cost_census currently returns IDs and hashes, not the values behind the hashes.
- DocumentLine does not have universal immutable history or recorded-at membership.
- Movement occurred_at is not a recorded knowledge timestamp.
- A later read of today's records cannot reconstruct what a prior census saw.
- A single fictitious policy or knowledge timestamp would bypass the new company guard.

This storage preserves observation evidence. It neither creates a new supplier amount
nor turns an unreviewed input into financial authority.

## Rejected alternatives

| Alternative | Reason for rejection |
|---|---|
| Reuse CostInputManifest without schema changes | Requires inventing historical knowledge and financial admission for unassessed inputs. |
| Retain IDs and hashes only | Detects change but cannot explain or replay the previous mutable values. |
| Copy the result into SourceRecord | Manufactures an external source and breaks source provenance. |
| Store the entire company in one JSON value | Loses typed membership constraints and requires loading the whole snapshot for member inspection. |
| Store only successful cost reviews | Excludes precisely the unreviewed subjects needed for honest coverage. |
| Introduce universal document/movement versioning first | Much broader than the bounded costing requirement; does not restore missing past history. |

## Proposed tables and shortest links

Implemented in migration 0077_company_cost_census after owner approval and a fresh
Alembic-head check (predecessor 0076_contribution_generations). All tables have opaque id, tenant_id, same-tenant uniqueness
and composite foreign keys. Monetary and quantity snapshot strings preserve exact normalized Decimal
values; original source payloads retain any additional received precision; no binary floats or amount recalculation are permitted.

### cost_company_census

- id, tenant_id.
- request_id: unique with tenant_id, internal retry identity, never a human document number.
- request_hash: canonical requested cutoff, capture version and explicit input bounds.
- effective_at: requested inventory cutoff, UTC.
- observed_at: time at which the current snapshot was observed, UTC.
- snapshot_identity: the PostgreSQL snapshot string for diagnosis, not a restorable snapshot.
- event_sequence: visible tenant event watermark, not proof of complete historical knowledge.
- input_schema_version: initially 1, fixed serialization allowlist.
- state: building or sealed; only sealed records can be read as a complete census.
- movement_count, document_count, line_count, source_count: verified member counts.
- content_hash: canonical header context plus ordered typed member identities and hashes.
- sealed_at: set only after all four families and bounds have been verified.

No knowledge_at, policy_revision_id, monetary total, financial completeness flag or
publication pointer. Sealed means complete capture of the specified census contract only.

### cost_company_census_movement

- id, tenant_id, census_id, movement_id.
- Unique (tenant_id, census_id, movement_id).
- observed_values: versioned canonical movement fields as read in the census transaction.
- provenance: exact observed recorded-event identities/sequences or explicit missing/
  ambiguous state, retained with the snapshot rather than followed through a latest link.
- content_hash: digest of the member identity, versioned values and provenance.

movement_id references the original physical record. The census snapshot retains its
observed values; it does not create a second Movement. Include all movements through the
effective cutoff, including corrections, zero/sold-out resulting item scopes and missing
provenance. Do not snapshot only the current remaining stock or compute FIFO here.

### cost_company_census_document

- id, tenant_id, census_id, document_id.
- Unique (tenant_id, census_id, document_id).
- observed_values, provenance, content_hash with the same versioned serialization rules.

Capture sales invoices and credit notes including headers without lines. Preserve stated
amounts and the observed source relationship. Invoice date is not economic-scope admission.

### cost_company_census_line

- id, tenant_id, census_id, document_line_id, document_member_id.
- Unique (tenant_id, census_id, document_line_id).
- Composite (tenant_id, census_id, document_member_id) references the retained document
  member's matching census; a line cannot point to another capture's header.
- observed_values and content_hash.

The original document_line_id identifies evidence; document_member_id identifies its
frozen header version. These links have distinct meanings. Do not duplicate a live
Document FK. Resolve the original header through the line, and the frozen one through
its census member. Preserve service/freight/unmatched lines and explicit unassessed
history/economic-scope state. Missing/foreign parents refuse capture, never silently omit.

### cost_company_census_source

- id, tenant_id, census_id, source_record_id.
- Unique (tenant_id, census_id, source_record_id).
- interpretation_outcome_id: nullable exact same-tenant accepted/current outcome identity.
- observed_values: source hash/version/received time and observed import attempt/status/
  classification, plus explicit absent-outcome state.
- content_hash.

SourceRecord already retains the immutable payload. Reference it; do not duplicate its
raw payload. Capture the latest visible source version per source identity, using the
existing census rule. Preserve older versions through their original SourceRecords.
Outcome references use RESTRICT. Capture does not declare all unresolved sources relevant
to cost, or an interpreted source fully assigned to financial inputs.

## Capture service and transaction

1. A shared internal costing service validates tenant, request identity, aware cutoff,
   input version and strict bounds. No public chat/tool or automatic scheduling entry is
   introduced in this stage. Existing read-only census remains read-only.
2. Require a clean, dedicated REPEATABLE READ transaction. Do not autoflush unrelated
   pending caller changes or commit inside the service. Refuse dirty sessions explicitly.
3. A same-tenant request replay returns the original sealed census only when request_hash
   matches. It never recaptures new input under the old identity. Changed request arguments
   refuse. A failed/rolled-back attempt leaves no partial durable census.
4. Reuse the current census queries with an internal record collector. Capture records
   and construct discovery metadata from the same query results, not two separate passes.
5. Insert typed members and verify their exact identities/counts/hashes. Enforce a combined
   maximum of 100,000 input records, 1 MiB canonical data per member and 64 MiB canonical
   data per capture. Refuse overflow, never truncate or report completeness. These are
   initial operational bounds, not fixture-J performance claims.
6. Seal only after every family passes verification. Return the opaque capture identity
   and summary. The caller owns commit/rollback. No financial review, event-derived
   amount, valuation cache, company publication or worker enqueue is produced.
7. Concurrent identical requests are serialized by the unique request key. Any PostgreSQL
   serialization/unique conflict requires rollback and a fresh transaction before loading
   the winner. Do not catch a failed transaction and continue reading inside it.

A capture is complete only for the current discovery contract. It does not capture all
purchase components, policy revisions, ownership, revenue matching or selling allocations.
Those admitted financial inputs need a separate resolver and retained manifest before
company valuation can use this population.

## Reads, integrity and retention

- Header and member inspection require tenant scope; foreign IDs behave as absent.
- Member pages use stable opaque member ordering, bounded limits (maximum 500) and a
  capture-bound cursor. No report read runs capture, resolves FIFO or schedules work.
- Page reads validate the header/version and returned member hashes. They do not claim
  whole-capture integrity from a page. Full integrity verification is bounded builder work
  and checks exact family membership, counts and content hash before financial resolution.
- Historical inspection reads frozen values, never silently joins current line amounts.
  Original evidence/source links remain available alongside the observed version.
- Sealed headers and members are immutable. Mutation/delete guards must cover direct SQL,
  not only service conventions; table ownership privileges are outside this guarantee.
- No automatic purge/TTL is introduced. Unreferenced-capture cleanup requires its own
  reviewed retention contract before scheduling. Do not use valuation-cache garbage
  collection for potentially sole retained observed input history.
- Downgrade refuses when any retained capture exists; an empty schema can be removed.
  Forward service rollback is the default once history exists. No migration runs at startup.

## Financial resolver boundary

The census proves the observed current input population; it does not supply PopulationBasis
knowledge_at or ExpectedPopulation financial input fingerprints. A later resolver must:

1. Resolve each member against retained admitted receipt, ownership, policy, matching and
   selling revisions, including explicit unadmitted states and each subject's own basis.
2. Prove a common supported financial knowledge boundary or return unsupported/pending.
   observed_at and pg_current_snapshot are not substitutes for that proof.
3. Retain all resolved input identities/versions and required missing-input explanations.
   Mutable financial fields cannot be fetched from today's records after capture.
4. Account explicitly for candidate exclusions, header/source gaps and unsupported scopes;
   do not quietly turn the census candidate count into the financial population count.
5. Construct the trusted ExpectedPopulation, then use exact closure and company publication
   guards with persisted-output verification and transactional worker fencing.

This proposal does not close T080/T081/T089 or establish HGB suitability.

## Required test-first evidence

| Layer | Required proofs |
|---|---|
| Serialization/domain | Exact Decimal/UTC preservation, canonical hashes, unsupported type/version, per-member and total byte bounds, no derived financial amounts. |
| Migration | ORM/schema parity; all tenant/composite/uniqueness constraints; immutable sealed rows through direct SQL; populated downgrade refusal; empty upgrade/downgrade/upgrade. |
| Capture/service | Current discovery parity, unreviewed subjects and gaps, atomic rollback on failure/overflow, caller-owned transaction, clean-session refusal, same-request replay, changed-request refusal. |
| Concurrency | Intake does not change an in-progress snapshot; concurrent retry returns one capture after fresh-transaction retry; no partially sealed result. |
| Historical inspection | Later permitted manual evidence edits and later source versions do not alter prior retained values or links; separate new capture sees new values. |
| Integrity/isolation | Foreign capture and FK refusal, missing/replaced members, corrupt payload/hash/count, invalid cross-capture header link, version refusal, bounded page reads without recalculation. |
| Integration | Tenant catalog classification, data-model/resource vocabulary, documentation generator reproducibility, existing selected cost/finance regression. |

## Approval boundary

The earlier approved financial model does not explicitly authorize this separate storage
family for unassessed mutable observations. Owner approval of these five tables was explicitly granted on 2026-09-19. The approval covers this dedicated typed census storage and its
non-financial, current-only, immutable-retention contract. This authorizes the staged
implementation/tests, not migration of a live company, deployment, financial confirmation
or release. The implementation follows the test-first plan above.

## Delivered implementation

The five tables and immutable SQL guards are implemented in migration 0071. Shared
costing services expose retain_company_cost_census, company_cost_census,
company_cost_census_members and verify_company_cost_census to trusted internal callers.
No public write adapter or scheduled job was added. The original discovery service
remains read-only and supplies the retained collector from the same snapshot queries.

Version 1 fixes the allowed observed fields. Original record values and recorded-event
metadata are preserved in observed_values; absent/ambiguous provenance stays explicit
through event_count and event identity/sequence rather than a fabricated event. Full UUIDs
identify captures/members. Typed FK lookup indexes support original-evidence retention
checks. Manual line removal refuses with domain guidance; otherwise permitted edits can
continue without altering prior observations.

Whole verification is required for idempotent replay and after capture before returning.
Paginated inspection validates returned members and explicitly does not certify the whole
capture. The 64 MiB limit bounds canonical retained member data, not PostgreSQL query peak
memory: current discovery still materializes the bounded row set before byte checks.
Chunked reference-scale capture and financial input resolution remain separate work.
