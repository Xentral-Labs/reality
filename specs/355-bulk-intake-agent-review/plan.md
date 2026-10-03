# Implementation Plan: Bulk intake settlement and delegated agent review

**Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)
**Language**: English
**Status**: Design prepared; implementation and runtime verification pending

## Summary

Use a retained ChangeProposal for the immutable batch manifest and existing ScheduledJobRun identities for bounded continuation; manifest membership is non-authoritative until its exact review is confirmed. Child proposals own effects and receipts. One handler transaction can settle at most 25 units, using per-unit savepoints; successful units and run progress commit together at handler completion. External agents fetch full source/review via scoped MCP tools and submit an exact structured verdict; provider calls are client-side, outside database-only handlers. A dedicated minimal mandate model binds an existing MCP token and grant decision, scope and limits; no global agent approval switch is introduced.

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
- Larger raw item CSV: at most 5,000 rows/20 MiB via spec 353's separate packaging
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

- `apps/web/src/unified/DecisionsPage.tsx`
- `packages/reality-core/src/reality/benchmarks/intake.py`
- `packages/reality-core/src/reality/domain/intake_review.py`
- `packages/reality-core/src/reality/jobs/handlers/intake.py`
- `packages/reality-core/src/reality/mcp/catalog.py`
- `packages/reality-core/src/reality/services/intake_batches.py`
- `packages/reality-core/src/reality/services/intake_review.py`
- `packages/reality-core/src/reality/web/api.py`
- `packages/reality-core/tests/test_bulk_intake_review.py`

- Additive mandate migration in `packages/reality-core/migrations/versions/` plus metadata import in `db/core.py`; exact revision is allocated from Alembic head at implementation, never guessed.

## Design

### Reality flow

Immutable source/artifact → non-authoritative prepared proposal → exact authorized
decision → canonical accepted evidence and explicit Reality effects → retained
receipt. The proposal is an interpretation stage, not accepted business evidence.

### Service and adapter flow

Use a retained ChangeProposal for the immutable batch manifest and existing ScheduledJobRun identities for bounded continuation; manifest membership is non-authoritative until its exact review is confirmed. Child proposals own effects and receipts. One handler transaction can settle at most 25 units, using per-unit savepoints; successful units and run progress commit together at handler completion. External agents fetch full source/review via scoped MCP tools and submit an exact structured verdict; provider calls are client-side, outside database-only handlers. A dedicated minimal mandate model binds an existing MCP token and grant decision, scope and limits; no global agent approval switch is introduced.

### Data and migration impact

A new tenant-scoped IntakeReviewMandate is justified by repeated authority checks: opaque id, grant_decision_id, agent_token_id, scope/limits JSON, expires_at, revoked_at and revision. Composite FKs enforce same-tenant proposal/token links; grantor is derived from the grant decision rather than duplicated. Reviewer evidence and mandate version live in the exact child proposal review/receipt. Batch manifest, continuation identity and progress use existing proposal/run records. Review/effect amounts stay strings validated as Decimal; no authority is inferred from free text. Add additive migration and keep unknown old attribution unchanged.

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

- `packages/reality-core/tests/test_proposal_decision_policy.py`
- `packages/reality-core/tests/test_scheduled_jobs.py`
- `packages/reality-core/tests/test_scheduled_worker.py`
- `packages/reality-core/tests/test_decision_attribution.py`
- `packages/reality-core/tests/test_unified_item_csv_import.py`

## Rollout and Rollback

Deliver dependency contracts before activating this adapter. Keep raw capture
available while review waits. Stop/drain old commit-owning interpreter workers
before cutover; do not use a feature flag as a business-approval bypass. Retain all
historical sources/effects with honest legacy attribution. On interruption, leave
pending decisions inspectable. Rollback disables new automatic review but preserves
the admission boundary and receipts; code that restores direct interpretation
writes is not a safe rollback target. Spec 356 owns the final cross-path cutover.

## Review Risks

- A global delivery fingerprint can make later unrelated proposals stale after the first unit; validate relevant state and report stale children without auto-renewing approval.
- Bulk grant checks must not lower finance-owner or token permissions.
- A worker lease loss must roll back the current chunk, including any child effects and receipts.
- Provider quality/cost cannot be proved by deterministic fixture verdicts; report live-provider qualification separately.

## Complexity Tracking

No constitutional exception is proposed. New agent authority is an explicit scoped
feature in spec 355, not an exception to existing finance/tenant rules. No new
external-I/O scheduler contract is proposed: provider inference stays client-side.

## Performance qualification

Controlled workloads: ten 500-item packages (5,000 new items) and 500 orders with
five lines each. Declare host CPU/memory, PostgreSQL version/topology and baseline
commit before measuring; run three repetitions after one warm-up. Compare with
repeated single-unit execution through the same new approval services, not an
unsafe legacy direct-writer path. Report prepare/review/apply elapsed time and query
counts, total duration, peak RSS and all success/failure counts.

Budgets: median bulk apply time per record and queries per record ≤1.5× the
single-unit baseline; incremental peak RSS ≤256 MiB for the controlled workloads;
default database-only run target ≤30 seconds, with hard registration bound ≤120
seconds, and configuration/result payloads within the existing registry's limits.
Reduce continuation units below 25 if needed; never split an atomic package or
commit mid-handler to meet a timeout. Oversized atomic work refuses safely.
Agent verdict fixtures prove pipeline correctness, not independent model quality.
Separate live-agent qualification reports model/version, complete-source coverage,
latency, cost and adversarial/malformed-source outcomes without a universal price
or wall-time promise. All reported metrics must come from actual runs.

## Shared phase and locking contract

Follow spec 351's common lock hierarchy and immutable phase/outcome attempt
allocation; do not acquire business/finance locks after proposal/source locks.
Replay never appends a new phase outcome or re-invokes interpretation.

## Reviewed implementation details

Parent authorization, original-reviewer handoff, chunk transaction ownership,
source/child freshness, stop semantics and small queue payloads are normative in
contracts/intake.md. Mandate scope, source-stated exposure and serialized daily
quota checks are defined in data-model.md. Implement these before enabling any
asynchronous approval; storing a queued batch reference alone does not prove that
the original reviewer is still authorized.

Add `packages/reality-core/src/reality/db/intake_review.py` for the minimal mandate
model, import it from db/core.py, and add only the justified tenant/source/token/
grant-decision relations and expiry/revocation/revision constraints. Resolve each
source/capability scope against current tenant records. Extend
services/decision_attribution.py so token identity remains the decider and mandate/
parent authorization are inspectable context, never the issuer as personal approver.

MCP agent clients perform provider I/O outside Reality's database-only job handler.
Reality supplies scoped source/review-fetch and structured verdict submission, not
a new provider-running daemon. Until an external reviewer is connected and given
an explicit mandate, prepared intake remains available for human decisions.

## Mandate implementation details

Migration 0141 adds only the current tenant-scoped mandate linked to an actual
owner decision and named token. Grant/revoke service writes require an exact
server-established owner-confirmation scope, with transaction and argument binding
and an inner-commit guard. An auth-disabled environment grants no mandate authority.
A token must belong to the real granting owner; issuer membership and account
status, current token permissions, expiry/revocation, source/capability activity,
profile/effect scope and finite quotas are checked again before execution.

Agent decisions record the actual token and mandate revision; the issuer supplies
current owner authority but is never presented as having personally decided.
Commercial exposure uses one explicitly received unit amount, without FX or line
recalculation. Missing or multiple unaggregated monetary statements require a
human decision. Daily limits derive from retained completed decision receipts while
the mandate row is locked. Retry of an executed exact verdict consumes no quota.

Original source content is read through bounded 64 KiB source/original/artifact byte
pages, at most 20 MiB per stream. Clients reassemble complete bytes and assess
externally; provider calls never occur in database-only continuation handlers.
Review evidence freezes every byte-range and original row/line reference, required
server validation checks and structured approve/reject/uncertain verdict. Evidence
proves binding and current scope, not independent human review or model cognition.

### Delegated fixed-batch execution

External agents submit one bounded, complete set of per-unit structured verdicts
for an exact manifest digest/revision. All entries must name the same current
mandate revision and actual authenticated token. Parent authority retains those
exact verdicts and a content digest; queues still carry only opaque run identities.
Uncertain/contradicted entries prevent unattended acceptance and remain reviewable.
A private transaction-bound batch-child scope authorizes a worker to revalidate a
retained verdict, never to infer a new verdict or authenticate caller-supplied
actor fields. The worker rechecks current mandate/token/issuer/source scope,
exact child evidence, current state and global UTC-day quota before each unit.
Accepted child receipts retain token attribution and mandate revision; rejected
children have no business effects. Known refusals retain review-required results;
unknown infrastructure errors roll back the whole provisional chunk.
