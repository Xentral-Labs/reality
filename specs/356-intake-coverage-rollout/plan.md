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

## Atomic manual order implementation slice

First qualify valid changed/repeated/early-commit and post-write failure callbacks.
Freeze the existing canonical create_manual_order entry, recheck its actual
retained order_create confirmation, and make the existing command executor own
the root commit. Add a private commit option for nested orchestration; public
proposal fields cannot set it. Preserve real delivery review tokens, source
values, existing locks, credit-hold rules and receipt shapes. Test both directions,
then the affected order/catalog/credit/profile/transport scenarios and full CI.
Constitution: PASS; no schema, new command, fabricated source or authority.

## Atomic invoice implementation slice

Observe valid changed/repeated/early-commit/post-write failure callbacks for the
three existing invoice commands first. Freeze each existing canonical parent
writer, require its real retained confirmation, and pass a private commit option
through its existing single/multi-position recorder. The application executor
owns the root commit. Preserve previews, locking, down-payment offsets, stated
amounts and receipt shape. Fixed setup remains tied to actual authored intent.
Constitution: PASS; no schema, tool or invented source/approval. Qualify both
order-linked directions and free supplier invoices, then affected full CI.
## Interactive MCP authority implementation slice

Issue a real authorization interaction, consent grant and PKCE credential in
tests, resolve its actual principal, dispatch explicit approval, then change
credential/grant authority in the canonical callback. Observe valid refusal
proofs first. Capture the real request principal in existing application/Finance
scopes and reread the exact credential/grant rows under settlement locks without
calling the resolver that commits. Preserve current person/Owner and manual token
checks. Constitution: PASS; no schema, fake actor, manufactured grant or consent.
## Live source control lock-order regression plan

Constitution Check: PASS. CI's real company-setup browser captured PostgreSQL's
production/settlement schedule cycle during Pause. Lock both retained schedule
rows in opaque-ID order, then unfinished runs, then the connection. Demo worker
claim execution enters the same schedule boundary before its own run lock;
other registered job families keep their existing execution path. Preserve
ownership, claim validation, cancellation refusal and request replay. Qualify
shared job/demo regressions and the actual company-setup browser before CI.
## Atomic customer credit implementation

Constitution Check: PASS. No schema changes or derived authority. Reuse the actual
retained application decision and current principal; freeze sales-credit parent,
credit posting, ledger and explicit allocation through the existing invocation
mechanism. Carry _commit=False into both actual recorders and deny root commits
until receipt settlement. Test valid callbacks before implementation, then the
modern/legacy credit, invoice, settlement and source attribution regressions.
## Fixed new-company reference exception plan

Constitution Check: PASS. No schema expansion or fabricated decision. A private
initializer takes the actual transient Tenant, binds its insert and fixed account
bootstrap to one session/root transaction and consumes initialization once.
The low-level bootstrap refuses calls outside that narrow scope. Reuse it in the
three actual company creation paths; preserve historical migration helpers.
Test existing-company refusal, repeat/identity/commit/failure callbacks first,
then ordinary/lesson/setup and migration compatibility before full CI.
## Confirmed commercial master data plan

Constitution Check: PASS. No schema expansion. Extend the finite canonical
operation/tool mapping for the ten existing commercial master commands; reuse
current principal checks, frozen invocation nonces and root commit denial. Carry
private _commit=False through canonical services and exact application callbacks.
Reject caller private execution fields. Route REST and CLI through actual retained
proposals, preserving response records and explicit human confirmation. Fixed
profile/lesson callers freeze their authored input under existing setup authority.
Test direct/confirmation/callback/refusal/rollback first, then positive stated
values, replay, source attribution, setup, adapters and full committed-head CI.

## Current fixed application authority plan

Constitution Check: PASS. Factor the existing current confirming person/manual
token/interactive MCP check into one private helper shared by ordinary canonical
and fixed application decisions. Call it from the actual fixed-definition
validator with current retained proposal state. Preserve fixed fingerprints,
scope/root locks and separately bound initializer semantics. Prove actual OAuth
revocation/expiry/permission and actual membership changes after dispatch before
the first canonical fixed-profile write; qualify real positive confirmation,
source values and receipt replay. No schema or invented identity is required.
## Master-data lifecycle plan

Constitution Check: PASS. Reuse the finite existing lifecycle tool and canonical setter. Freeze the supported model identity, record, supplied active flag and action ID; retain a private current-record hash at preparation and recheck before effects. The canonical service accepts the existing type or corresponding finite model string and normalizes both to the same frozen identity. Replace internal commit with application-owned root settlement. REST/CLI explicit confirmation returns the existing record shape. Tests precede implementation; compare full row/event state for update rollback, qualify current references and adapters, then require full committed-head CI. No schema expansion or new authority store.

Qualify the real existing party_merge caller of lifecycle in the same boundary: freeze its canonical parent and exact nested duplicate deactivation, carry private no-commit to both, and let its retained reviewed proposal own root settlement. Existing merge eligibility/current review remains authoritative; tests precede this necessary caller integration.

Keep fixed application canonical admission literal: the two authored current definitions directly create party/item/location only, while separately bound exact source-intake and company/lesson scopes retain their existing checks. New canonical map entries cannot automatically broaden an earlier fixed confirmation. Test actual borrowed frozen lifecycle/merge invocations against a preserved runtime snapshot first.

## Manual document corrections plan

Constitution Check: PASS. Reuse the two existing command meanings and canonical correction functions. Retain private hashes of the actual document/line snapshot and referenced partner/item/payment-term meaning before review; reject caller private fields and recheck current state under existing delivery/root locks. Freeze exact canonical invocation and carry private no-commit through correction functions; settle evidence/events with the actual retained receipt. Keep domain line revisions and downstream restrictions. REST flags require explicit actual request confirmation; SDK callers supply it explicitly. Prove meaningful direct/unconfirmed/callback rollback first, then current references, exact stated values, person/replay, adapters and complete committed-head CI. No schema or fabricated historical approval.
