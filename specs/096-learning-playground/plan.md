# Implementation Plan: Learning Playground

**Branch**: `096-learning-playground` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)
**Language**: English. Status: approved; implementation in progress.

## Approved entry simplification

PR #135 readiness increment (owner approved): rebase on current main, preserving both
sets of domain commands and catalog discovery. Restore FR-003 fail-closed policy for
new upstream services and complete FR-013 translations without weakening audits.
Spec impact: restores existing requirements; no new scenario or schema expansion.
Constitution Check: PASS. Existing full suites and new denial regressions precede
completion; T064 records integration evidence. No critical design ambiguity remains.

Migration integration: both the existing local Playground revision and main's
commitment-revision branch descend from 0038. Preserve their immutable revision IDs
and join them with a no-op merge revision 0041. This adds no business schema; test
upgrade from either historical head and preservation of existing sandbox data.

FR-024 is adapter-only: new-sandbox action and bounded recent-run buttons replace the entry catalog. New setup uses the trading reference preset; retries retain their recorded preset. No API, domain or schema change. Constitution Check: PASS; confirmation, quotas and tenant boundaries remain shared. T063 tests direct navigation, cancel/confirm and legacy partial-delivery compatibility, then verifies contracts, build, isolated browser stories and spec gate. Rollback is a UI revert. Analysis: no unresolved clarification or critical finding.

## Summary

Add an authenticated learning workspace on the real Reality services, with a tenant per run.
Deliver the safe guided lesson first, then bounded chat and custom master data, restart and
public discovery. Full V1 includes all five stories; an internal guided milestone is not the
publicly complete product. Use existing proposals and verification, not a parallel executor.

## Technical Context

Python 3.12+, SQLAlchemy 2, PostgreSQL/Alembic, Pydantic v2, FastAPI, Typer, existing MCP and
React/Vite/Tailwind. Existing account cookies, membership, shared autocomplete, Inspector,
ChangeProposal and BusinessEvent machinery. Decimal quantities/amounts; UTC.
Tests: pytest against temporary PostgreSQL; Node UI contracts; actual desktop/mobile browser QA.
No new database, queue, provider SDK or frontend framework. Hosted AI uses existing managed
provider, an explicit outbound exception only for sandbox messages; no BYOK in a Playground.
V1 bounds and measurable targets are in spec.md. Research decisions: [research.md](research.md).

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Existing manual-order service creates lossless input and evidence; raw manual references need no invented source | PASS |
| Reality owns operational state | Existing inventory/commitment/exception reads; no document status flags | PASS |
| Proven schema only | Tenant purpose, run ownership/version and step receipt provenance have enumerated policy/retry/read uses in data-model.md | PASS |
| Tenant + shared service boundaries | All-entrypoint operation policy, tenant-derived run addressing, direct-service negative tests | PASS |
| Spec/test traceability | All 13 FR and 4 DR mapped to test-first tasks and acceptance stories | PASS |
| Explainable web behavior | Verified step references → existing Inspector → shortest evidence/source links | PASS |
| Received values not recomputed | Fixture/order values explicit and preserved; derived observations labelled as such | PASS |
| Smallest coherent design | One dataset, one lesson; common proposals; no universal simulator/replay engine | PASS |

Pre- and post-design checks PASS. Owner approval of the design/schema and explicit
permission to proceed despite unchecked reviewer items are recorded in quickstart.md.
Security and release checks remain mandatory; reviewer markers are unchanged.

## Repository Structure and Layer Changes

New paths below are intended implementation paths, not files created by this planning turn.

- Domain/storage: `src/reality/db/core.py`, `domain/playground.py`,
  `migrations/versions/<next_revision>_learning_playground.py` under packages/reality-core.
  Resolve migration number from current head at implementation time.
- Services: `src/reality/services/playground.py` (run/step/reads),
  `services/tenant_policy.py` (operation policy), `services/core.py` (allowed action correlation),
  `services/projections.py`, `services/exceptions.py`.
- Side-effect guards: `services/memberships.py`, `security/secrets.py`,
  `agent/settings.py`, `mcp/auth.py`, and the actual invitation delivery worker.
- Lessons: `src/reality/playground/catalog.py`; explicit versioned data and step definitions.
  Existing `demo/normal_month.py` remains unchanged and separately tested.
- Tools/AI: `tools/application.py`, `mcp/catalog.py`, `agent/mcp_chat.py`.
- Adapters: `web/app.py`, `web/auth.py`, `web/api.py`, `web/read_models.py`,
  `cli/app.py`, `mcp/server.py`; typed HTTP surface may live in `web/playground.py`.
- Product: `apps/web/src/playground/PlaygroundPage.tsx`, `StepReceipt.tsx`,
  `ScenarioControls.tsx`, plus existing App.tsx, api.ts, localization.tsx and shared components.
- Public: `provider-site/src/LandingPage.tsx`, site-routing.ts, localization.tsx;
  additive Playground link, no landing redesign. Public labelled preview lives in
  `apps/docs/content/getting-started/playground.md` and its `de/` edition.
- Durable contracts updated during implementation: docs/WEB_SPEC.md, WEB_UX_MATRIX.md,
  DATA_MODEL.md, TEST_STRATEGY.md and a new docs/features/learning-playground.md.

## Design

### Run lifecycle and admission

Use immutable Tenant.purpose=business|playground, defaulting existing tenants to business.
A PlaygroundRun binds exactly one new tenant to its owner and lesson/preset version.
Never convert a business tenant or old demo. Atomic empty tenant+membership+run creation
precedes deterministic sample setup; initialization progress/failure is visible and excluded
from the user's lesson recorder. Stable versioned seed references prevent duplicate seeding.
Start again prepares a new run first; after success the previous run is archived. One active
run per user; concurrent starts/restarts serialized. Run history is not deleted.

Initial setup uses the existing services' `_commit=False` paths for all eight reference
records. An owner-row lock is reacquired after the durable metadata commit and held through
the entire seed/savepoint/ready transaction. There are no per-reference commits to reconcile:
progress is empty until the complete opaque-ID reference map commits. A temporary session-
and transaction-bound capability rejects internal commits, wrong-session/tenant targets,
all business-only operations and every non-seed mutation. Failure rolls back the complete
preset before recording the safe failure status. This lock strategy applies to initial setup
only; lesson actions still require the pinned-connection strategy described below.

Verified pending-production users get a narrow admission lane: run management and read-only
inspection of their own sandbox, plus supported proposal/confirmation/chat APIs only.
Existing production endpoints stay blocked. Disabled/rejected/unverified users stay denied.
Require real user identity even when local auth is disabled. Account status is rechecked.

### Authoritative operation policy

Central policy uses tenant purpose, run ownership/state and named operation, independent of UI,
prompt, role and transport. Every shared mutating entrypoint and sensitive outbound boundary
participates. Default deny unknown operations in Playground. A registry coverage test enumerates
HTTP/tool/CLI/MCP mutation routes so a newly added operation cannot accidentally become allowed.
Normal company behavior is unchanged. Policy also runs on proposal creation and confirmation.
No sandbox tokens, invitations, secret resolution, custom provider endpoints or connector setup.
Run tenant is server-resolved; never accept an arbitrary target tenant from a prompt.

Archived runs allow only reads and derived-cache maintenance necessary for those reads; no
new proposals, chat messages, membership changes or domain mutations. Production and other
users' record IDs fail scoped lookups. Normal Inspector/Views expose only approved read families;
configuration, global administration and secret registries are not part of sandbox inspection.
No global administrator override of the sandbox business-operation restrictions.

### Scenario/action engine

Versioned lesson metadata maps to existing tools; buttons and chat use the same allowlist:
party_create, item_create, location_create, order_create restricted to sales,
movement_create restricted to opening_stock and shipment, reserve, reservation_release.
Read allowlist includes run-local references, facts, commitments, inventory, exceptions,
proposal status and allowed record inspection. Cross-reference exact catalog names during T002.

A free-text sequence is a draft, not authorisation. Resolve existing IDs; render ambiguous
choices using shared autocomplete. Dependent actions wait for the preceding verified record.
Create one normal ChangeProposal per step and confirm it explicitly. Do not send the model
confirmation/execute tools. Fixture prices, amounts, dates and defaults are visible input,
never recomputed source totals. Source-update/purchase/payment requests explain V1 limits.

### Step execution, retries and causal evidence

Reuse approve_and_execute_proposal and proposal_execution_status. Existing proposed→executing
CAS prevents duplicate confirmation; uncertain execution is not automatically retried.
Serialize sandbox mutations using a PostgreSQL advisory lock on a dedicated pinned connection
bound to the step Session; keep that connection across existing service commits and release
in finally. All allowed mutation paths must participate, including direct service access.
Lock contention returns busy, not a queued duplicate action.

The internal lock primitive owns a dedicated, pool-detached connection and permanently closed
operation Session. It retains the physical driver reference for explicit final cleanup even
after SQLAlchemy invalidation. A lost connection cannot reconnect inside the operation. Ownership
is checked before and after acquisition; acquiring the lock grants no core/proposal capability.
The initial implementation is tested independently and is not yet wired to a lesson adapter.

Opening stock now has an internal decision slice: preview revision hashes resolved arguments
and relevant reference/stock state, and confirm rechecks it under the pinned lock. Before-state
and requested intent commit before the ordinary executor claims the proposal. The scoped
decision permits only that proposal and one exact opening Movement plus its correlated event;
quantity, timestamp, identity substitution and duplicate handler calls are denied. Normal generic
confirmation remains denied. Rejection reuses the existing lifecycle and human attribution.
Shared proposal_execution_status verifies a unique correlated opening event and its exact
Movement; it does not settle an interrupted executing proposal. An executed proposal's write-once
observation may be retried independently. Pending execution/observation blocks new mutations,
while owner reads (including archived history) remain available. No decision adapter exists yet.

The first internal preparation slice supports opening_stock through movement_create only.
A transaction-bound, exact-intent capability permits the common proposal factory's new
`_commit=False` path; proposal and step commit atomically. It grants no executor, core mutation
or egress permission. The proposal preview retains normalized requested intent separately
from resolved defaults. The future execution claim must copy that request identity into
before-observation metadata before the ordinary executor replaces proposal.output; missing
identity fails closed on replay. Input quantity precision follows Movement's Numeric(18,4).
Run-local reference names and units are preview labels, not independent business state.

A PlaygroundStep binds one proposal and idempotency key, with a bounded pre-action read receipt.
Take the before measurements immediately before execution, not from an old preview. A targeted
state/version fingerprint protects approval: changed intent-relevant state requires fresh preview.
Record immutable-intent and before-observation metadata durably before calling the existing executor.

Thread proposal action_id through every V1 handler into its service. Co-commit correlated
BusinessEvents with affected records. Add missing reservation-consumed, active-remainder-created
and commitment-fulfilled events without altering business quantities/lifecycle behavior.
Use returned IDs and correlated events plus re-reads to identify actual effects, never merely a
tenant sequence interval, creation timestamp or model assertion. Include no-allocation success.
Preserve old tool outputs compatibly and reuse the existing execution receipt/status schema.

After domain commit, verify expected record links and fetch authoritative current reads. Store
a write-once explanatory observation for that step with evaluated_at and event watermark.
If projection/verification fails, report execution separately from unavailable verification;
never mark it failed-and-retry solely because a read failed. A crash after domain commit is
reconciled only from exact correlated evidence. Incomplete attribution remains unknown and
blocks new mutations. Multi-step requests are not globally atomic: earlier effects remain.
Reads and status polling stay available during recovery.

### Current position and UX

Three coordinated regions: Try (lesson + chat), What happened (step receipts),
What is true now (stock, obligations, active Reservations, Facts, Exceptions).
At narrow widths use labelled tabs/stacking, preserve confirmation focus and selected step.
Technical IDs/raw JSON collapsed; stored record types visually distinct from derived amounts.
Each receipt explains explicit writes, automatic changes and relevant unchanged values.
Current state always comes from shared readers; historical receipt snapshots are labelled and
never used for mutation validation. Exceptions compared by stable subject/type identity with
their normal reasons; do not invent an exception-clear event or empty-state proof of completeness.
Reuse projection checkpoint/freshness handling. List events by step action references/cursors,
not the current activity API's rolling 24-hour default.

### AI budgets, quotas and fallback

Dedicated managed-provider context contains sandbox data only; do not inherit production chats,
keys, URLs or tools. Default quotas from spec are checked under user-level DB locking.
Persist a free-text ChatMessage before provider invocation; count user turns across this user's
PlaygroundRuns for daily chat quota (buttons do not create model turns). Failed calls count.
One in-flight model call per user, bounded existing tool loop and request timeout.
Provider unavailable/limited: guided forms/buttons and all reads continue; show clear state.
Run and applied-step quotas count retained runs and executed proposals respectively; executing
work reserves capacity so concurrency cannot exceed the limit. No automatic cleanup/deletion.

### Data and migration impact

See data-model.md: Tenant purpose plus PlaygroundRun and PlaygroundStep. No extra fields on
operational records, no mirror Fact/state table and no independent execution-status authority.
Tenant registry/membership, archive visibility and tenant-scoped table catalog tests expand.
Additive migration defaults every existing tenant to business; never infer a demo from its name.
Review schema and whole migration chain against actual main before creating a numbered revision.

## Test Strategy and Traceability

tasks.md maps every FR/DR to failing tests and implementation. Specific suites:
test_playground_security.py, test_playground_runs.py, test_playground_steps.py,
test_playground_reads.py, test_playground_chat.py, test_playground_api.py,
scenarios/test_learning_playground.py and existing proposal/movement/masterdata/migration tests.
Frontend: new playground-contract.test.mjs included in normal gates, full i18n and build.
Adversarial tests exercise generic endpoints and CLI/MCP, not only new playground routes.
Real browser acceptance includes fresh verification/pending admission, step confirmation,
ambiguous combobox, reload/restart, archived Inspector and 390/1280 px layouts.
Measured local PostgreSQL profile and five-person learning check are in quickstart.md.

## Rollout and Rollback

Feature flag REALITY_PLAYGROUND_ENABLED defaults off. Migration and policy land before any
public link. Internal complete guided slice first; chat/archives/accessibility and full negative
tests before public activation. Managed provider readiness and quotas are deployment checks.
Roll back by disabling entry and writes while retaining guarded read-only history; do not remove
purpose guards or deploy an older API that ignores purpose while sandbox data exists.
DB downgrade only on a disposable prelaunch database with no runs, otherwise forward-fix.
Public links never promise immediate production approval or live vendor integration.

## Review Risks

Missing service policy coverage; uncorrelated automatic events; internal commits and crash
windows; narrow pending-admission bypass accidentally broadening access; provider data leakage;
stale projection reads presented as current truth. These are acceptance gates, not future cleanup.

## Complexity Tracking

### Supplier finance and customer returns (FR-022–023)

First harden existing post_supplier_payment/record_supplier_payment and
post_customer_refund/record_customer_refund with savepoints, optional caller-owned
commit, currency preservation and trusted action-ID propagation. Test durable
rollback and ordinary tool attribution before changing Playground permissions.
Then compose supplier invoice evidence through the shared service layer, followed
by narrowly typed Playground adapters. Physical returns reuse movement_create;
credit and refund remain separate commands with exact evidence links and amounts.
No new schema or alternate financial engine. Constitution Check: PASS. Analysis:
no critical conflict; atomicity is a prerequisite to enabling the new cockpit steps.
Rollback disables new controls; previously recorded Reality remains untouched.

Implementation review: supplier invoice and return credit share the private atomic
order-evidence composer in core.py. Credit lines use billed_document_line_id to the
sales order; eligibility is the shared uncredited_return_quantity reader. A returned
Movement retains its original Commitment and does not alter delivery fulfillment.
The return observation distinguishes returnable_quantity from open_quantity so the
original fulfilled promise never appears reopened. The cockpit selects a recorded
shipment, then uses the confirmed return's order-line reference for credit and the
confirmed credit's document reference for refund. Supplier/return steps use existing
run metadata; no schema change. New exact models reject unreviewed source overrides.

### Embedded operation chooser (FR-021)

Use one shared card renderer in the left action slot for empty/completed states.
Opening-stock completion returns to that chooser; sale starts at order, purchase
at supplier order. Draft selection is presentation state only. Existing commands,
pending-action guards, run IDs and shared reads are unchanged. Hide unrelated
progress while choosing and show a single stock step for that standalone operation.
Tests: entry/no-write/cancel, stock→chooser→sale, completion→same chooser→purchase,
reload and pending review regression. Constitution PASS, no schema/API changes;
analysis found no critical conflict. FR-021 supersedes the automatic first lesson
and isolated completion buttons. Rollback is presentation-only.

### Purchase/receipt continuation (FR-020)

Reuse the existing purchase order and receipt commands, proposal executor and
shared stock/fulfilment readers. Extend the typed Playground order direction and
add a receipt input requiring a supplier commitment, item and destination. No
schema or new domain rules. Receipt review fingerprints current open quantity,
commitment identity and physical stock; confirmation rechecks them. Exact-intent
policy admits only the reviewed receipt, including action attribution and allowed
co-committed fulfilment events. Its write-once receipt uses the correlated Movement
and shared remaining-quantity read. Reject invalid receipt links/quantities before
claiming execution. UI adds purchase/receipt states and a same-run operation option;
partial receipt continues against its saved commitment, full receipt opens choices.
Current-operation segmentation recognizes purchase boundaries. Inactive scenarios
stay inactive; this does not advertise a complete P2P financial lesson.
Constitution PASS; analysis: no critical findings. Tests first: real PostgreSQL
purchase/partial/final receipt/replay plus negative identity/tenant/quantity cases;
UI reload, exact destination/commitment, and sales→purchase→sales continuation.
Rollback hides purchase controls while preserving readable history and purpose guards.

### Continuing sandbox increment (FR-019)

Owner approved continuing in the same sandbox. Reuse existing step preparation and
confirmation; no new schema, permissions or business calculations. A pure UI helper
selects the latest order segment from ordered persisted steps (including an immediately
preceding opening-stock step). Both the controller and progress inspector use it.
An unsubmitted continuation draft is local presentation state; reload discards that
draft, while persisted proposals resume normally. Invoice/payment lookups use the
current segment only. New orders receive distinct display numbers, never identities.
Tests precede implementation: segment boundaries and isolation, UI contracts and a
two-operation browser fixture with distinct evidence IDs. Existing service story
tests verify shared mutation behavior. Constitution PASS; analysis: no critical
conflicts, FR-019 supersedes the single-use presentation, not the safety quota.
Purchasing/returns remain separately tracked in T044. Rollback hides continuation
controls without rewriting saved steps or domain records.

### Invoice/payment cockpit increment (FR-018)

Owner approved the next invoice/payment implementation. Add record_sales_invoice in
services/core.py composing existing source, manual document-line and ledger helpers in
one transaction; expose sales_invoice_record through the common proposal/MCP registry.
Use an existing order-line FK, explicit quantity/total and UTC time; no new schema.
Extend typed Playground inputs and exact owner/decision policy narrowly for this command
and customer_payment_post. Financial previews fingerprint linked evidence/open amounts;
receipts use action-correlated events and tenant-scoped shared financial reads. Keep
generic sandbox writes and outbound activity denied. UI adds two action states to the
trading cockpit, leaves partial delivery at four, and uses existing open-item rendering.
Tests first: stated amounts, rollback, tenant/action identity, preview-only, confirmation
replay, settlement, receipts and refreshed UI. Constitution PASS. Analysis: no critical
conflict; combined payment/allocation is explicitly labelled, not a separate simulator.
Rollback hides new controls and disables entry; keep financial history and purpose guards.

### Shared finance prerequisite (FR-017)

Inspection found no ordinary invoice-recording proposal tool and found intermediate
commits in post_customer_payment → record_customer_payment → create_document /
post_ledger → allocate_settlement. Do not open broad sandbox permissions to work
around that. First add composable `_commit` options (default true) and optional
action_id propagation to those shared financial helpers and post_sales_invoice.
post_customer_payment composes its children without commits in a savepoint and
commits the complete result once; exceptions roll back the entire payment.
The ordinary customer_payment_post handler forwards the executor's trusted action
ID. No schema, new financial calculation or alternate simulator engine.
Tests precede implementation: independent-connection rollback proof, exact event
attribution and ordinary tool confirmation. Run financial, Playground/isolation,
tool/catalog and complete backend suites from packages/reality-core.
Constitution PASS. Analysis: no critical conflict; FR-017 is a prerequisite within
the approved O2C goal, not activation of the unfinished lesson. Existing UI unchanged.

### Scenario library increment (FR-014–016)

Reuse the existing preset/version and lesson/version fields. Add one partial-delivery
preset sharing the synthetic references; retain `trading` for legacy and delivery
basics. The catalog supplies supported versions; the browser supplies localized
learning descriptions and labels the six-step O2C goal as delivery-only for now.
No schema, new command, new permission or financial calculation. Partial delivery
uses an editable five-piece shipment suggestion and the existing shared obligations
view. It is an exercise ending at the open remainder, not a complete two-delivery flow.
Restart optionally selects a supported preset, validated before archiving. Entry,
header and completion open the same library; confirmation remains a separate step.
Tests first: supported preset persistence/rejection, restart preservation, browser
library/cancel/confirmation/refresh, existing action lifecycle and layout regression.
Constitution PASS. Analysis: no critical findings; unavailable workflows explicitly
remain follow-up work. Owner approved the scenario direction with “ja perfekt” / “jau bau”.

### Cockpit revision implementation gate

Public discovery implementation: account-first landing CTA through configured APP_URL
(Spec 022 FR-027 supersedes the secondary Playground hero CTA), localized copy,
Docs hero action plus reusable configured-origin PlaygroundLink in
EN/DE first-journey and inventory lesson. Preserve existing narrative and timed paths.
No new auth/commands; normal account gate handles entry. Tests: site and Docs contract
suites, builds, rendered destination checks. Local preview only; no public deployment.

Account-menu entry: plain same-origin anchor, new tab with noopener/noreferrer,
existing AuthGate/session and no company mutation. Verify menu-link contract and
frontend build. No domain or API changes; Constitution PASS.

Legacy removal gate: user-approved after backup branch was pushed at d3a9b29.
Remove duplicate rendering/helpers/styles and the unused header adapter, update
contracts to the sole cockpit, keep command handlers and sandbox boundaries unchanged.
Verify build, frontend contracts and isolated full-story browser checks in both themes.
Rollback is the remote backup branch; no database/schema work. Constitution PASS.

Approved scope: presentation replacement plus freshness/context corrections only.
Constitution: PASS — same services, IDs, tenant scope, confirmation and read models;
no schema or alternative domain logic. Build a separate PlaygroundWorkspace and use
the existing PlaygroundPage handlers through an action slot. Retain legacy rendering
behind a reversible layout switch. Tests cover the integrated action lifecycle,
in-workspace navigation and viewport containment. Analysis: no critical conflict;
the new layout supersedes the old stacked presentation, not the command contract.

Revision verification: TypeScript/Vite build, 90 frontend contracts and spec policy
pass. Isolated browser fixtures prove setup confirmation, four action confirmations,
nondefault reference context after reload, partial shipment, tabs, inspectors,
1280x800 containment and legacy roundtrip. This is UI acceptance, not live backend
end-to-end proof. Full multilingual audit remains red (including legacy Playground
copy and untranslated Dutch/Spanish cockpit copy); no complete release claim.

Appearance regression: replace cockpit light-only literals with the shared semantic
tokens; preserve the intentionally dark brand header and paired solid-button colors.
The isolated browser check switches both themes and asserts actual computed table,
item, amount and panel colors against their theme tokens, with screenshots. This
restores FR-013 presentation consistency without changing commands or domain state.

Owner-requested local testing configuration: 1,000 runs per day and 2,000 retained
runs in ignored .env; production defaults and enforcement remain unchanged. No
existing run is deleted. Timeline subtitles resolve only payload/reference data.

| Constitution exception | Why needed | Alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

New orchestration metadata is justified in data-model.md; it does not replace domain records.
