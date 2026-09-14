# Implementation Plan: Analytics and Master Data

## Technical Context
Python/SQLAlchemy/PostgreSQL services and existing React/TypeScript/Tailwind frontend. No new dependency or schema. Work remains in `/private/tmp/reality-139` with the uncommitted foundation preserved. Frontend rollout uses the same opt-in flag.

## Constitution Check

| Principle | Result | Evidence |
| --- | --- | --- |
| Source → Evidence → Reality | PASS | Contributor and master detail links retain existing opaque identities and source pointers |
| Operational authority | PASS | Shared fulfillment expressions; no document status or historical backlog authority |
| Proven schema | PASS | No schema change; existing ChangeProposal stores durable intent |
| Tenant/service boundary | PASS | Scoped services and existing tool executor; ordinary-company gate |
| Specification and evidence | PASS | Owner continuation recorded; tests precede implementation |
| Explainability | PASS | Defined metrics, bounded contributors, existing Inspector |
| Simplicity/storage | PASS | PostgreSQL aggregates, bounded reads, existing batch tools |
| Received values | PASS | Count records, never derive source prices/revenue; preserve untouched fields |

## Architecture and Files

1. `services/company_insights.py`: shared SQL current-position counts and date-bucketed activity; use `delivery_reads.fulfillment_expressions/effective_value`. Count customer commitments by created_at; count positive shipment movements excluding originals/compensations named by MovementCorrection. Return fixed period buckets and scoped paginated contributors. No browser business arithmetic.
2. `services/reference_workspace.py`: bounded Party-role/Item/Location search; detail through existing update snapshots, opaque ID/revision and source link. Prepare whitelisted basic create/update records through canonical `create_change_proposal` with deterministic request-derived proposal ID under the tenant guard. Compare client edit revision before creating the canonical proposal. Preserve mandatory unchanged fields such as roles and location parent.
3. `services/business_locks.py` / `tools/application.py`: include batch reference updates in the shared guard, and recheck revision before invoking a claimed update handler. Restore proposed only on pre-handler refusal. Existing proposal CAS and receipts remain authority; no generic mutation gateway is added.
4. `web/api.py`: thin typed Analytics, contributors, master register/detail/prepare/proposal adapters. Confirmation requires explicit confirmed=true and uses existing canonical execution. Require ordinary company and current principal. Unknown results return persisted status and never call the handler as recovery.
5. `apps/web/src/unified/AnalyticsPage.tsx`, `MasterDataPage.tsx`, `MasterDataCard.tsx`: new presentation with accessible inline SVG chart plus table/record alternatives; native review dialog. Reuse existing Inspector and loading patterns. `api.ts`, `routing.ts`, `Shell.tsx`, `HomePage.tsx`, `DeliveryCase.tsx`, `DecisionsPage.tsx`, `ChatPage.tsx` connect the destinations. No legacy CSS import.

## Data and Transactions
See data-model.md and contracts/workspaces.md. The same current metric function serves Home preview and Analytics. SQL aggregates do not use bounded samples. All windows are explicit UTC and bounded to 7/30/90 days. Contributor paging is capped at 100.

Reference preparation stores only canonical records and expected revisions; request identity derives a stable proposal ID. Replay compares tool and intent excluding server-added revision fields. For ordinary reference updates, claim first, then tenant guard and exact revision check before handler; all batch/direct writers share that guard. A successful response can be recovered by GET proposal. Executing with no conclusive receipt remains unresolved and cannot authorize another execution.

## Verification and Rollback
Tests: `test_company_insights.py`, `test_reference_workspace.py`, `test_unified_workspace_api.py`; extend frontend contracts and add `scripts/unified-workspaces-browser.mjs`. Existing core update/proposal/practice suites remain required. Run full PostgreSQL suite, lint/spec policy, web build/i18n/contracts, browser matrix and docs build. Baseline: Spec 139 final 1470 passed, 7 pre-existing retired UI skips, 122 frontend contracts.

Disable only the frontend opt-in flag to return to existing presentation. Keep canonical services and compatible persisted proposals. No deployment or removal is part of this plan. Review owner-visible results after technical checks.

## Complexity Tracking
No exception. Reject new analytics storage, historical snapshots, a second reference write engine and a generic command endpoint: none is needed for this scope.
