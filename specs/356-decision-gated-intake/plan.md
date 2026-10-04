# Implementation Plan: Decision-gated interpretation and admission

## Approved scope clarification (2026-10-04)

This rollout governs external sources, imports and agent-proposed business effects.
They require an exact retained proposal and an authorized confirmation before acceptance.
A direct action by an authenticated human is itself the decision and uses the existing
application authorization and audit trail; it does not require a second proposal or
confirmation cycle. Derived effects of one operation share its transaction and receipt.

The owner retained PRs #333–#346 and withdrew the later universal canonical-writer
rollout. Internal service calls and every manual UI/CLI operation are not additional
admission projects. Existing tenant, domain, Finance and Chat confirmation rules remain.
A static writer inventory is discovery material, not a mandate to guard every writer.
References below to governed writes mean external intake only; broader earlier planning
and universal-writer tasks are superseded by this clarification.

**Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)
**Language**: English
**Status**: Design prepared; implementation and runtime verification pending

## Summary

Use ChangeProposal.input as the non-authoritative typed prepared plan and retained review. Create no staging Document or operational status fields. A dedicated intake approval branch follows the existing finance executor's one-transaction pattern. Apply frozen effects through canonical no-commit services under locked source/proposal/reference state. The scope is internal and bound to session, transaction, tenant, proposal and operation/intent; executing_proposal supplies attribution only. Preparation and source persistence remain independently retryable.

## Technical Context

- Python 3.12+, SQLAlchemy 2, PostgreSQL, Pydantic v2, Decimal and UTC.
- Existing ChangeProposal, SourceRecord/SourceArtifact, ImportJob/outcome and
  application services; FastAPI/MCP/Typer remain adapters. React/Vite presentation
  is in scope only for stories that name frontend files.
- pytest with isolated real PostgreSQL; existing browser harness for changed flows.
- No parallel execution within a shared SQLAlchemy session; bounded independent
  work can use existing worker capacity under current authorization.
- Reviewed atomic package: at most 500 rows and the existing 2 MiB package profile;
  batch manifest: at most 500 independent proposals; continuation: at most 25 units.
- Larger raw item CSV: at most 5,000 rows/20 MiB via spec 358's separate packaging
  path. A coherent oversized order is review-required, never silently split.

## Constitution Check

| Principle | Concrete design evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Raw remains immutable; proposal precedes accepted evidence/effects; receipt cites shortest source links | PASS |
| Reality owns operational state | No provisional Document status or stored derived payment/stock authority | PASS |
| Proven schema only | Reuse proposal JSON; any mandate schema has repeated execution/expiry/revocation checks, documented in data-model.md | PASS |
| Tenant + shared services | Server-bound scope; composite links; adapters call common prepare/review/apply | PASS |
| Spec/test traceability | Every requirement maps to a story, exact planned test and ordered tasks | PASS |
| Explainable web | Review exposes exact meaning/effects and full source/receipt links; recovery reads only | PASS |
| Received values | Preserve stated values; never recalculate a source total or invent missing prices | PASS |
| Smallest coherent design | Existing proposal/jobs; no second workflow engine or business staging tables | PASS |

This is a design-level check, not evidence that the runtime has passed. Recheck
against the implemented diff and migration before marking tasks complete.

## Repository Structure and Layer Changes

- `packages/reality-core/src/reality/domain/intake.py`
- `packages/reality-core/src/reality/services/core.py`
- `packages/reality-core/src/reality/services/intake.py`
- `packages/reality-core/src/reality/tools/application.py`
- `packages/reality-core/tests/test_intake_admission.py`

- No new schema in this package; see data-model.md for reused storage and compatibility.

## Design

### Reality flow

Immutable source/artifact → non-authoritative prepared proposal → exact authorized
decision → canonical accepted evidence and explicit Reality effects → retained
receipt. The proposal is an interpretation stage, not accepted business evidence.

### Service and adapter flow

Use ChangeProposal.input as the non-authoritative typed prepared plan and retained review. Create no staging Document or operational status fields. A dedicated intake approval branch follows the existing finance executor's one-transaction pattern. Apply frozen effects through canonical no-commit services under locked source/proposal/reference state. The scope is internal and bound to session, transaction, tenant, proposal and operation/intent; executing_proposal supplies attribution only. Preparation and source persistence remain independently retryable.

### Data and migration impact

No new business table is required for this foundation. ImportJob.input carries proposal identity; existing status/classification strings distinguish prepared/awaiting decision from applied, and InterpretationRecordReference can reference the proposal using its existing opaque reference shape. ChangeProposal.input/output retain the plan/review and receipt. Add explicit typed validation in domain code. Historical outcome rows remain immutable. Scope guards must not turn source-record/audit writes into business-effect admission.

### Failure, security and tenant behavior

Validate current permission and exact digest under the relevant locks. Known
no-effect failure rolls back its coherent unit. An unknown outcome is reconciled
against its retained proposal/run/receipt before redispatch. No token, queue receipt
or source text authorizes broader effects. Never substitute a fallback tenant.

### Bulk atomicity and freshness

An atomic package is one decision. A manifest groups independent child decisions.
The unit's reviewed source/mapping remains frozen; current relevant state is checked
at apply. Do not refresh review during confirmation or accept a new digest merely
because an earlier sibling completed. Stale children require an explicitly renewed
review and a new matching manifest selection; already completed children replay.

## Test Strategy and Traceability

The spec traceability table names every planned test and implementation task.
Tests are written and observed failing before their implementation where practical.
Shared negative matrix covers foreign tenants, direct service/interpreter calls,
forged action IDs, changed intent/state/permission and scope reuse across sessions
or transactions. PostgreSQL tests inject failure before commit and replay after
commit, and coordinate two competing approvers rather than mocking lock behavior.

Existing regression suites to update without weakening refusal assertions:

- `packages/reality-core/tests/test_source_ingestion.py`
- `packages/reality-core/tests/test_unified_item_csv_import.py`
- `packages/reality-core/tests/test_proposal_decision_policy.py`
- `packages/reality-core/tests/test_decision_attribution.py`

## Rollout and Rollback

Deliver dependency contracts before activating this adapter. Keep raw capture
available while review waits. Stop/drain old commit-owning interpreter workers
before cutover; do not use a feature flag as a business-approval bypass. Retain all
historical sources/effects with honest legacy attribution. On interruption, leave
pending decisions inspectable. Rollback disables new automatic review but preserves
the admission boundary and receipts; code that restores direct interpretation
writes is not a safe rollback target. Spec 361 owns the final cross-path cutover.

## Review Risks

- Existing generic proposal execution commits its claim before the handler; this branch must not inherit that transaction model.
- Many core functions commit internally; every called effect path needs a tested no-commit entrypoint.
- Business mutations must not accidentally accept source strings or arbitrary action_id values as authority.

## Complexity Tracking

No constitutional exception is proposed. New agent authority is an explicit scoped
feature in spec 360, not an exception to existing finance/tenant rules. No new
external-I/O scheduler contract is proposed: provider inference stays client-side.

## Common lock hierarchy

For new intake application and grant/batch controls, acquire locks in this order:

1. Existing Tenant row `FOR UPDATE` via `lock_delivery_state`. This is also the
   event-sequence serialization row; it is not an advisory lock.
2. Shared finance lock when any proposed effect is financial.
3. Mandate rows, then parent batch row, then child proposal rows, each ordered by
   opaque ID when more than one is needed.
4. Source-identity advisory locks ordered by their computed signed-bigint hash
   key, matching `_store_source_records`, then SourceStream rows in deterministic
   source-identity order. Acquire the complete needed key set before row locks.
5. ImportJob rows ordered by opaque ID.
6. Affected business/reference rows in deterministic record-type/ID order.
7. Event emission reuses the Tenant row lock already held from step 1; it does
   not introduce another lock resource late in the transaction.

Event-emitting raw admission must be changed to Tenant-row → sorted source-key →
SourceStream → ImportJob order. Current raw admission may lock a source before
event emission locks Tenant; keeping that order would deadlock with approved
intake that holds Tenant while waiting for the same source. Taking the Tenant
serialization lock grants no business approval and does not block raw admission
on a Decision. Raw intake never requests finance/proposal locks after source locks.
Shopify child-refund source registration uses the same Tenant-first prefix. The
finance proposal executor already acquires business → finance → proposal; new
intake must not lock its proposal first and then request business/finance locks.
Review renewal, grant revocation and batch stop follow the same applicable prefix.
Preflight authorization reads are not permission-granting lock shortcuts.
Validate this hierarchy against all actual callees during T001 and add competing
intake-versus-finance, order-change-versus-refund and raw-arrival-versus-approval
PostgreSQL tests. Any discovered reverse acquisition must be repaired before
implementation completion, not masked with broad retries.

Immutable outcome allocation follows data-model.md. Preparation/approval replay
must neither mutate earlier outcomes nor collide on their unique attempt number.

## Explicit review recovery

Prepare uses a business savepoint. Known domain/Pydantic failures roll back provisional
proposal preparation, retain a safe phase-labelled outcome against the existing raw
source/job, and propagate the refusal. Unknown infrastructure failures propagate.
Renewal names the current prior proposal and a bounded request ID. Technical renewal
identity/history is retained on the job; only stable interpretation configuration
is included in the new plan. Completed receipts refuse new renewal. Replaying a
known renewal request returns its retained proposal even after completion.
Old plans remain unchanged and old pending reviews read as stale. Shared tools/MCP
expose renewal as preparation, not approval, under existing proposal permissions.
