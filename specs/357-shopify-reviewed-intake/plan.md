# Implementation Plan: Reviewed Shopify orders, changes and refunds

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

Register a Shopify planning adapter producing the shared frozen plan. First-order plans carry one coherent order; later-version plans reuse classify_order_version with explicit read-only snapshots and supported effect operations. Refund plans carry their independent raw source and proposed evidence/announcements. No mutating interpreter runs during review. Approved apply is transaction-bound and attributes every resulting business event to the deciding proposal.

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

- `packages/reality-core/src/reality/services/core.py`
- `packages/reality-core/src/reality/services/shop_order_changes.py`
- `packages/reality-core/src/reality/services/shop_refunds.py`
- `packages/reality-core/src/reality/services/shopify_intake.py`
- `packages/reality-core/tests/test_shopify_intake_admission.py`

- No new schema in this package; see data-model.md for reused storage and compatibility.

## Design

### Reality flow

Immutable source/artifact → non-authoritative prepared proposal → exact authorized
decision → canonical accepted evidence and explicit Reality effects → retained
receipt. The proposal is an interpretation stage, not accepted business evidence.

### Service and adapter flow

Register a Shopify planning adapter producing the shared frozen plan. First-order plans carry one coherent order; later-version plans reuse classify_order_version with explicit read-only snapshots and supported effect operations. Refund plans carry their independent raw source and proposed evidence/announcements. No mutating interpreter runs during review. Approved apply is transaction-bound and attributes every resulting business event to the deciding proposal.

### Data and migration impact

Reuse SourceRecord/SourceStream, Document/DocumentLine, Commitment, refund evidence and existing proposal/outcome tables. This package requires no new tables. SourceStream remains the newest accepted source delivery pointer under its existing ingestion contract; it is not a declaration that the business interpretation has been approved. Pending effects exist only in proposal JSON.

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

- `packages/reality-core/tests/test_shopify_and_explain.py`
- `packages/reality-core/tests/test_shopify_update_guard.py`
- `packages/reality-core/tests/test_shop_order_changes.py`
- `packages/reality-core/tests/test_shop_refunds.py`

## Rollout and Rollback

Deliver dependency contracts before activating this adapter. Keep raw capture
available while review waits. Stop/drain old commit-owning interpreter workers
before cutover; do not use a feature flag as a business-approval bypass. Retain all
historical sources/effects with honest legacy attribution. On interruption, leave
pending decisions inspectable. Rollback disables new automatic review but preserves
the admission boundary and receipts; code that restores direct interpretation
writes is not a safe rollback target. Spec 361 owns the final cross-path cutover.

## Review Risks

- SourceStream acceptance and accepted business interpretation are different states.
- Approval must not bypass reservation-choice or cancellation-after-shipment guards.
- Order/refund processing must not imply money moved when only the source stated a refund.

## Complexity Tracking

No constitutional exception is proposed. New agent authority is an explicit scoped
feature in spec 360, not an exception to existing finance/tenant rules. No new
external-I/O scheduler contract is proposed: provider inference stays client-side.

## Shared phase and locking contract

Follow spec 356's common lock hierarchy and immutable phase/outcome attempt
allocation; do not acquire business/finance locks after proposal/source locks.
Replay never appends a new phase outcome or re-invokes interpretation.

## Implementation finding: preserve unstated amounts

The old Shopify adapter stores computed line amounts. To satisfy FR-002/FR-003 and
DR-001, preserve absence with nullable existing DocumentLine.gross_amount and
physical Commitment.amount columns. See data-model.md for the repeated read/billing
use case, canonical source-only entrypoint, historical compatibility and refusal
on unsafe rollback. This replaces the earlier no-schema-change assumption with a
small nullability change; no staging table or new business field is introduced.
