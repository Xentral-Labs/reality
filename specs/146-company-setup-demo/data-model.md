# Data Model: Company Setup and Demo Connection

Status: approved on 2026-09-09 and implemented by migration 0046; local migration and constraint tests recorded in quickstart.md.

## Existing authorities retained

`Tenant.purpose` remains immutable business/playground; no new business environment flag. `PlaygroundRun` owns Sandbox setup status, owner/request identity, preset/version, ready/error state and bounded initialization progress. Existing source, document, commitment, reservation, movement and ledger tables keep their business meanings.

## Proposed ordinary_company_creation

Only ordinary empty-company creation needs this new receipt; Sandbox requests already have a PlaygroundRun receipt.

| Field / constraint | Use and proof |
|---|---|
| id: opaque PK | Stable setup result identity; FR-006 |
| tenant_id: required FK, unique | Exactly one created company for this receipt; tenant-scoped access and deletion behavior; FR-002/006, DR-001 |
| actor_id: required AppUser FK | Account-owned recovery and current authorization; FR-005/006 |
| request_key: bounded 128 chars; unique(actor_id, request_key) | Lost-response/concurrent retry returns same company; FR-006 |
| request_fingerprint: 64 chars | Same key with changed name/environment/content conflicts; FR-003/006 |
| created_at: UTC | Actual setup audit time; DR-003 |

Create Tenant, owner membership and receipt in one transaction. No progress/status column is needed for ordinary empty creation: rollback leaves nothing, commit creates a ready company. Scope initial requests by verified actor; scope result reads by both current actor authority and tenant. Platform admins do not inherit another user's setup request.

Cross-kind requests serialize through the existing AppUser row and check both this receipt and PlaygroundRun request identity before dispatch. Reusing a key for a changed environment/content must conflict across tables, not produce a second company. Retain receipts while the company exists; permanent deletion follows existing tenant deletion policy. No cascade deletes unrelated history.

## Proposed demo_data_connection

| Field / constraint | Use and proof |
|---|---|
| id: opaque PK | Connection controls, registered job configuration and safe links; FR-014/017 |
| tenant_id: required FK, unique | One persistent connection per Sandbox, reconnect same identity; DR-001, FR-014 |
| source_system_id: required same-tenant FK | Normal integration registry identity; FR-014/018 |
| current_schedule_id: nullable same-tenant ScheduledJob FK | Current continuous run identity and inherited actor/version/configuration; FR-016/017 |
| state: stopped/running/paused/disconnected | Different Start/resume/stop/reconnect behavior; FR-017 |
| revision: positive integer | Stale control refusal; FR-017 |
| last_request_key, last_request_fingerprint: nullable bounded pair | Exact control replay; FR-017 |
| created_at, updated_at: UTC | Connection lifecycle audit, distinct from source business dates; DR-003 |

Add `UniqueConstraint(SourceSystem.tenant_id, SourceSystem.id)` solely to support the connection's composite FK. ScheduledJob already has this uniqueness. Tenant ID remains mandatory on every query and relationship validation.

Require a current schedule for running/paused state; enforce paired control key/fingerprint nullability. No actor duplicate on connection: current recurring authority is ScheduledJob.actor_id; initial connection creation is audited through SecurityAuditEvent. No stored counters, last-import timestamp, error authority, rate or catalog mappings on connection: derive source progress from SourceRecord/ImportJob/InterpretationOutcome; configured intent and exact references live in the validated current schedule configuration. Before first Start, the preview uses fixed default 60 and the existing profile manifest.

## Existing JSON contracts

- PlaygroundRun progress preserves immutable `creation_intent` (canonical name/environment/content fingerprint) across initialization/retries and holds `{profile, version, anchor, windows, catalog_refs, case_refs, capabilities}` within existing 64 KiB cap. Store bounded key references, not every historical position or a copy of operational aggregates. Empty profile contains no synthetic references.
- `demo.generate_orders` configuration holds connection ID, profile version, deterministic seed, selected rate and exact authorized catalog/customer/location references. Validate <=16 KiB under spec 147 and freeze per delivery. Register the job's narrow owner/source policy.
- Existing SecurityAuditEvent records setup and connection controls (actor, safe IDs, old/new rate/revision), never credentials or order payloads. SourceRecord retains each full synthetic order payload losslessly. Generated source identities include the continuous schedule and logical delivery IDs.
- A new continuous run is a new ScheduledJob; do not add a third new table for run metadata. Paused/resumed/rate-updated schedule history is evidenced by run snapshots plus control audit. Stop preserves all old schedules, runs, sources and outcomes.

## State and transaction rules

| Control | Effect |
|---|---|
| Connect | Validate/reuse compatible profile or explicitly provision minimal prerequisites in empty Sandbox; stopped; no historical orders |
| Start from stopped | Create new disabled schedule with seed/config, then resume; first future interval; running |
| Pause | Pause timing and cancel only undispatched pending/retry occurrence; retain history; paused |
| Resume | Revalidate actor/source/catalog, resume same run from a fresh interval; running |
| Rate change | Pause, settle/cancel undispatched work, audit and update config under expected revision, resume after new interval if previously running |
| Stop | Pause/cancel undispatched work; stopped; next Start allocates new run identity |
| Disconnect | Stop intake and deactivate SourceSystem; retain evidence; disconnected |
| Reconnect | Revalidate prerequisites and reactivate source; stopped; explicit Start required |

Running work is never cancelled mid-transaction. Controls lock schedule → unfinished run → connection, then recheck the pointer/revision. Unknown outcomes block restart until reviewed. A failed import does not erase generated source evidence; backlog limit 20 prevents further generation and is visible as derived throttling/error state.

## Schema gate and rollback

Allocate the next unused Alembic revision at implementation time (0045 belongs to spec 147). Add two tables plus the supporting SourceSystem uniqueness; no data backfill or automatic connection. Stop relevant schedules and disable entry before rollback; retain additive metadata and evidence. Destructive schema downgrade is for disposable tests only, never an operational recovery recipe.
