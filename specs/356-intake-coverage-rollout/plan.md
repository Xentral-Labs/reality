# Implementation Plan: Intake decision coverage, demo and safe rollout

**Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)
**Language**: English
**Status**: Design prepared; implementation and runtime verification pending

## Summary

Use the writer inventory from 351 to finish classification and explicit service enforcement, then exercise transports as thin callers of the same boundary. Continuous demo uses the same preparation/apply as production; a configured bounded reviewer is required rather than inferred from source activation. Fixed initialization keeps its reviewed profile/transaction authority. Fence old binaries at cutover, retain raw sources and prepared proposals, and expose legacy unknown attribution without rewriting history.

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

- `docs/V0_CHECKLIST.md`
- `packages/reality-core/src/reality/services/company_setup.py`
- `packages/reality-core/src/reality/services/demo_data.py`
- `packages/reality-core/src/reality/services/intake.py`
- `packages/reality-core/src/reality/services/tenant_policy.py`
- `packages/reality-core/src/reality/web/api.py`
- `specs/351-decision-gated-intake/writer-coverage.md`
- `packages/reality-core/tests/test_intake_rollout_coverage.py`

- No new schema in this package; see data-model.md for reused storage and compatibility.

## Design

### Reality flow

Immutable source/artifact → non-authoritative prepared proposal → exact authorized
decision → canonical accepted evidence and explicit Reality effects → retained
receipt. The proposal is an interpretation stage, not accepted business evidence.

### Service and adapter flow

Use the writer inventory from 351 to finish classification and explicit service enforcement, then exercise transports as thin callers of the same boundary. Continuous demo uses the same preparation/apply as production; a configured bounded reviewer is required rather than inferred from source activation. Fixed initialization keeps its reviewed profile/transaction authority. Fence old binaries at cutover, retain raw sources and prepared proposals, and expose legacy unknown attribution without rewriting history.

### Data and migration impact

No additional tables beyond package 355's mandate. Pending jobs are transitioned via idempotent tenant-scoped application maintenance, not source mutation or fabricated decisions. Existing setup completion markers and source controls remain authoritative. Deploy additive mandate migration before new clients; reverse runtime automatic review only, not the admission boundary or retained approvals.

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
writes is not a safe rollback target. Spec 356 owns the final cross-path cutover.

## Review Risks

- Old workers running during cutover can violate the new invariant even when new clients are correct.
- Demo start permission must not become permanent blanket approval for arbitrary later effects.
- Global enforcement must preserve raw ingestion, tenant creation and audit maintenance without weakening business authority.

## Complexity Tracking

No constitutional exception is proposed. New agent authority is an explicit scoped
feature in spec 355, not an exception to existing finance/tenant rules. No new
external-I/O scheduler contract is proposed: provider inference stays client-side.

## Shared phase and locking contract

Follow spec 351's common lock hierarchy and immutable phase/outcome attempt
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

## Canonical master boundary slice

Enforce Party/Item/Location creation and updates independently of authentication
mode. The existing confirmed proposal executor owns the exact retained input,
current transaction and current named person/token authority. Freeze canonical
handler calls before invoking callbacks, consume each call once and refuse a root
commit before the receipt. Fixed initialization uses the same exact invocation
proof and never authorizes later arbitrary master changes. Ordinary company-partner
creation is bounded to the confirmed creation receipt and transaction.

REST form saves and CLI create/update submit existing catalog proposals and convey
actual confirmation; unconfirmed requests have no proposal or accepted effect.
Historical provenance and pinned migration fixtures explicitly represent retained
rows without manufacturing current decisions. This slice completes no unrelated
writer family; their semantic classification and enforcement remain required.

Qualification tasks T019–T022 cover direct/auth-disabled refusal, callback/root
attacks, transport parity, current token revocation and full committed-head checks.

## Canonical finance configuration slice

Reuse the existing atomic Finance command branch: delivery lock when needed,
finance lock, proposed row lock, execution and executed receipt in one transaction.
A private scope records only the actual confirmed retained command, current root,
principal/token and exact input. It must accept the existing proposed state and
must never force an executing claim. Freeze account calls before callbacks and
recheck current authority at canonical configuration writers. Fixed new-company defaults and the five authored initial preset account roles
remain narrowly classified initialization exceptions bound to the actual preset,
company/run/root and frozen single-use invocation; direct
arbitrary account changes and action tags refuse. Verify no-effect rollback,
callback duplication, altered arguments, current authority, stale configuration,
replay and transports before full CI qualification. Other finance/business writer
families retain their own pending enforcement work.

### Slice 27: normalized Document/DocumentLine admission

Use existing document/order/invoice/credit commands, with no new schema or invented
source facts. Bind the canonical normalized writer to the actual confirmed
application transaction and finite command family. Freeze its child invocation
before callbacks, consume once, and preserve the caller's original stated values.
For document_create, the executor owns the root commit for evidence plus receipt;
its writer flushes and refuses premature root commits. Existing order/invoice/credit
root ownership is a subsequent independently reviewed qualification, not claimed
by this slice. Route the direct Web manual-document form through
the existing proposal with the actual request principal and explicit confirmation.
Test direct/tag/unconfirmed refusal, callback changes/repeat/commit, positive
manual/source lineage and existing billing/refund/order stories. Port legitimate
fixtures through retained commands; historical fixtures remain historical.
Constitution check: PASS (lossless source, stated values, tenant scope, existing
shared tools, no fulfillment status or schema expansion).
