# Data Model: Playground Metadata, Not Another Reality

All names are proposed. Existing business records and foreign keys remain authoritative.

## Tenant purpose

Add immutable `purpose` = business | playground, default business. Repeatedly read by admission,
operation authorization, credential/egress policy and selectors. A name or membership cannot
prove sandbox identity; therefore the typed field has an explicit constraint/security use case.
Existing rows remain business. No conversion command or migration heuristic.

## PlaygroundRun

Fields: opaque id; tenant_id (FK, unique); owner_user_id (FK); preset_key/version;
lesson_key/version; client_request_key; status initializing|active|initialization_failed|archived;
created_at/ready_at/archived_at UTC; bounded initialization progress/error code.
Unique (owner_user_id, client_request_key); at most one active run per owner, enforced under
owner lock and a partial unique index. Ownership and tenant purpose are checked together.
No redundant separate tenant link on ordinary domain records. Owner FK is required for private
entry, pending-account access, quotas and resume; membership still authorizes ordinary readers.

State: initialize atomically creates tenant/member/run; deterministic setup applies real master
data via shared services. Step progress references created opaque IDs so initialization retry
can reconcile. An unready run exposes status only. Old active run stays active until replacement
is ready; then archive and activate in one locked transition. Failure never deletes the old run.
Archived means no business mutations, not forbidden derived-cache rebuilding on a read.

The bounded V1 reference preset commits atomically: initialization_progress is empty before
success and contains the complete party/location/item ID map after success. Failure never
leaves a committed per-record subset. Retrying the same key therefore either returns the
ready run or repeats an unapplied setup transaction; it does not infer identity from names.

## PlaygroundStep

Fields: opaque id; tenant_id; run_id FK; sequence; request_key; proposal_id FK unique;
lesson_step_key nullable; before_observation JSON; receipt_observation JSON nullable;
created_at and observed_at UTC. Unique (run_id, sequence), (run_id, request_key).
Validate run.tenant_id = step.tenant_id = proposal.tenant_id, with composite constraints where
supported and mandatory repository scope. proposal_id is authoritative for intent/execution state;
do not duplicate its status on the step. Rejected and failed proposals remain inspectable.

Before observation is nullable until captured once at execution claim (not editable preview data), including
relevant measurement labels/values, target record versions and event watermark. Receipt includes
verified record IDs, correlated event IDs, effects and shared-reader observation metadata.
Receipt is bounded to supported lesson subjects; no whole-tenant dump, secrets or raw model history.
Each observation and initialization-progress JSON object is limited to 64 KiB in PostgreSQL.
Once verified it is append-only; failed verification remains retriable from proposal evidence,
never by repeating the action. Unknown execution is derived from proposal_execution_status.

Why persist: reload/crash recovery, accurate before-state comparison and exact per-step attribution
cannot be reconstructed from the current mutable Reservation/Commitment rows alone. These values
are historical observations, never used as present stock, a new Fact or mutation permission.
Typed identity/order fields support constraints, joins and pagination; explanation JSON stays untyped.

## Reused entities

ChangeProposal is the only execution decision lifecycle. BusinessEvent action/correlation links
tie events to it. Extend event emission for actual automatic side effects of supported operations.
ChatSession/ChatMessage persist conversation within the run tenant. Count user free-text messages
across owned runs under owner locking for daily quotas; failed provider turns count too.
Dataset definitions and lesson steps are versioned code/assets, not a configurable workflow schema.
Masterdata uses existing services; no business payload is typed merely for learning display.

## Migration and retention

Add purpose default, run/step tables, constraints and indexes for owner listing, tenant scope,
step pagination and request idempotency. Register tables in tenancy and lifecycle tests.
No production data backfill besides purpose. No data copy or automatic run deletion. Creation
caps retained data; future retention/archive export is a separate specified feature.
Migration review and PostgreSQL upgrade/downgrade proof precede release; rollback normally disables
feature entry, not isolation guards. Do not downgrade away purpose with retained sandbox data.
