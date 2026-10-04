# Implementation Plan: Intake decision coverage, demo and safe rollout

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

Use the writer inventory from 356 to finish classification and explicit service enforcement, then exercise transports as thin callers of the same boundary. Continuous demo uses the same preparation/apply as production; a configured bounded reviewer is required rather than inferred from source activation. Fixed initialization keeps its reviewed profile/transaction authority. Fence old binaries at cutover, retain raw sources and prepared proposals, and expose legacy unknown attribution without rewriting history.

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

- `docs/V0_CHECKLIST.md`
- `packages/reality-core/src/reality/services/company_setup.py`
- `packages/reality-core/src/reality/services/demo_data.py`
- `packages/reality-core/src/reality/services/intake.py`
- `packages/reality-core/src/reality/services/tenant_policy.py`
- `packages/reality-core/src/reality/web/api.py`
- `specs/356-decision-gated-intake/writer-coverage.md`
- `packages/reality-core/tests/test_intake_rollout_coverage.py`

- No new schema in this package; see data-model.md for reused storage and compatibility.

## Design

### Reality flow

Immutable source/artifact → non-authoritative prepared proposal → exact authorized
decision → canonical accepted evidence and explicit Reality effects → retained
receipt. The proposal is an interpretation stage, not accepted business evidence.

### Service and adapter flow

Use the writer inventory from 356 to finish classification and explicit service enforcement, then exercise transports as thin callers of the same boundary. Continuous demo uses the same preparation/apply as production; a configured bounded reviewer is required rather than inferred from source activation. Fixed initialization keeps its reviewed profile/transaction authority. Fence old binaries at cutover, retain raw sources and prepared proposals, and expose legacy unknown attribution without rewriting history.

### Data and migration impact

No additional tables beyond package 360's mandate. Pending jobs are transitioned via idempotent tenant-scoped application maintenance, not source mutation or fabricated decisions. Existing setup completion markers and source controls remain authoritative. Deploy additive mandate migration before new clients; reverse runtime automatic review only, not the admission boundary or retained approvals.

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

- `packages/reality-core/tests/test_demo_data_intake.py`
- `packages/reality-core/tests/test_demo_data_security.py`
- `packages/reality-core/tests/test_demo_data_startup.py`
- `packages/reality-core/tests/test_demo_data_api.py`
- `packages/reality-core/tests/test_demo_entrypoint_parity.py`
- `packages/reality-core/tests/test_decision_trail_details.py`

## Rollout and Rollback

Deliver dependency contracts before activating this adapter. Keep raw capture
available while review waits. Stop/drain old commit-owning interpreter workers
before cutover; do not use a feature flag as a business-approval bypass. Retain all
historical sources/effects with honest legacy attribution. On interruption, leave
pending decisions inspectable. Rollback disables new automatic review but preserves
the admission boundary and receipts; code that restores direct interpretation
writes is not a safe rollback target. Spec 361 owns the final cross-path cutover.

## Review Risks

- Old workers running during cutover can violate the new invariant even when new clients are correct.
- Demo start permission must not become permanent blanket approval for arbitrary later effects.
- Global enforcement must preserve raw ingestion, tenant creation and audit maintenance without weakening business authority.

## Complexity Tracking

No constitutional exception is proposed. New agent authority is an explicit scoped
feature in spec 360, not an exception to existing finance/tenant rules. No new
external-I/O scheduler contract is proposed: provider inference stays client-side.

## Shared phase and locking contract

Follow spec 356's common lock hierarchy and immutable phase/outcome attempt
allocation; do not acquire business/finance locks after proposal/source locks.
Replay never appends a new phase outcome or re-invokes interpretation.

### Fixed compact and month setup compatibility

Legacy compact/month seeds become actual confirmed fixed-definition proposals,
with retained profile version and frozen day. A private session/transaction-bound
application execution scope authorizes their authored definitions only. Their
Shopify-shaped examples use the shared pure planner and exact scoped effect
dispatch; no retired interpreter or derived line total is reused. Setup effects
and its receipt commit together. Raw-only source scopes cannot enter this setup
scope. Configuration-only empty-database bootstrap creates no business demo data.

## Independent defect retained from closed PR #352

FR-006 and spec 146 require Demo Data controls and shared worker transactions to
remain correct. Production/settlement workers and Pause currently acquire the two
schedules in opposite orders. Retain only the stable schedule/run/connection lock
ordering correction, with the genuine two-connection regression in
`tests/test_demo_schedule_lock_order.py`. It adds no decision layer, schema or
canonical-writer gate. Existing cancellation/revision/replay rules remain intact.

Plan Constitution Check: PASS; this restores existing source-control behavior.
Proof order: observe the real lock inversion before the fix; apply the two service
changes; verify the regression and existing scheduler/demo/import families.
