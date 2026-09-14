# Planned Executable Proof Map

**Status**: Planned tests, none claimed implemented or passing. Paths are relative to `packages/reality-core/tests/`. Each row inherits its independently authored acceptance fixture from [verification.md](verification.md). Tasks must assign concrete function names and test-first ordering.

| Requirement | Planned test file | Expected initial failure / proof target |
|---|---|---|
| FR-001 | `finance/test_recording.py` | Existing balanced-role services, no full external chart prerequisite, gross labels |
| FR-002 | `finance/test_recording.py` | Owner activation, source/type/revision scope, pause/revoke and no intake authority inheritance |
| FR-003 | `finance/test_recording.py` | Evidence survives posting error; durable handoff crash/retry proof |
| FR-004 | `finance/test_recording.py` | PostgreSQL replay/concurrency, lost response, changed version and cross-source ambiguity |
| FR-005 | `finance/test_recording.py` | Existing settlement/reversal regression plus remote outcome independence |
| FR-006 | `finance/test_components.py` | Source fidelity, absent versus zero, coding namespace and no inferred amounts |
| FR-007 | `finance/test_components.py` | Summary/line roles and no repeated document amount attribution |
| FR-008 | `finance/test_components.py` | 600/400 and partial assignment, over-allocation, mixed bases/currencies and immutable revision |
| FR-009 | `finance/test_components.py` | Target-specific references, no tax determination, local posting survives missing mapping |
| FR-010 | `finance/test_components.py` | Retire/rename and frozen package assignment/mapping history |
| FR-011 | `finance/test_handoff.py` | Independent readiness axes, reason counts and no Document status fields |
| FR-012 | `finance/test_handoff.py` | Exact package manifest/components/identities, neutral profile label and explicit omissions |
| FR-013 | `finance/test_handoff.py` | Stale preview, repeat preparation/download and no remote success inference |
| FR-014 | `finance/test_handoff.py` | Lossless receipt chain and target/item/version/outcome evidence |
| FR-015 | `finance/test_handoff.py` | Idempotent, partial, conflicting, unmatched and out-of-order receipts |
| FR-016 | `finance/test_handoff.py` | Correction/retry identity, unchanged prior packages, no blind resend or remote reversal |
| FR-017 | `finance/test_reads.py` | Filter-before-total/pagination, operational role balance, currencies and exact provenance |
| FR-018 | `finance/test_reads.py` | Assigned/unassigned/missing basis, no recognized expense or profit labels |
| FR-019 | `finance/test_reads.py` | Local/prepared/remote facts independent; compare only like-for-like evidence |
| FR-020 | `finance/test_web_contract.py` | V01–V13 route/state/keyboard/localization/visual matrix |
| FR-021 | `finance/test_authorization.py` | Shared tools, owner configuration, tenant mutation policy and unchanged Chat/MCP confirmation |
| FR-022 | `finance/test_initialization_reads.py` | Clean database initialization, service-generated fixtures and immutable new-model entry/allocation history |
| FR-023 | `finance/test_initialization_reads.py` | Source/local/remote date distinction, timezone boundaries and tied pagination |
| FR-024 | `finance/test_accounts.py` | Minimal setup, manual/imported references, unique codes and no number-derived role |
| FR-025 | `finance/test_accounts.py` | All shared posting paths, role/default resolution, tenant checks and concurrent block/revision race |
| FR-026 | `finance/test_accounts.py` | Immutable used role, audited rename, blocked exact reversal, replacement refusal and role-wide balances |
| FR-027 | `finance/test_accounts.py` | Optional per-target mapping revisions, frozen exports and unchanged gross basis |
| FR-028 | `finance/test_accounts.py` | Clean account initialization, required IDs, no legacy-string authority and currency-separated reads |
| FR-029 | `finance/test_mapping.py` | Eight-direction service/adapter matrix, explicit/default accounts and non-posting triggers |
| FR-030 | `finance/test_mapping.py` | Defined source/internal cases, target-independent source resolution, source/namespace/kind collisions, revision preservation and no country/rate inference |
| FR-031 | `finance/test_mapping.py` | Defined optional groups, no guessed classification and wrong-tenant/retired refusal |
| FR-032 | `finance/test_mapping.py` | Exact target resolution, group modes, overlap rejection and competing-path refusal |
| FR-033 | `finance/test_mapping.py` | Immutable revisions, owner activation, stale preview and unchanged prior package/local balances |
| FR-034 | `finance/test_mapping.py` | V01/V04/V05/V08 additions, shared resolver parity and read-only matrix |
| FR-035 | `finance/test_settlement.py` | Actual receipt 1,020, allocation 1,000, excess 20; strict legacy invoice action preserved |
| FR-036 | `finance/test_settlement.py` | Unaccepted skonto/withholding stays open; explanatory note has no financial/aging effect |
| FR-037 | `finance/test_settlement.py` | Stated adjustment 20 or 60, separate evidence/non-cash entries, no fake source or calculation |
| FR-038 | `finance/test_settlement.py` | Stale/duplicate/source-credit rejection; atomic combined action and independent cash recording |
| FR-039 | `finance/test_settlement.py` | Reuse/refund existing excess, no duplicate payment; tenant/party/currency and available-credit bounds |
| FR-040 | `finance/test_settlement.py` | PostgreSQL concurrent allocation/refund/adjustment and independent payment/adjustment/refund reversals |
| FR-041 | `finance/test_settlement.py` | Catalog/matrix/UI parity, 980 cash plus 20 adjustment wording and external missing-tax readiness |
| FR-042 | `finance/test_settlement.py` | Supplier cash/control signs, agreement authority, partial/full reduction, excess allocation/refund and PostgreSQL race/reversal parity |
| FR-043 | `finance/test_credits.py` | Both credit tabs, payment/credit-note origins counted once, same-party/side/currency bounds, no-open-invoice discoverability and V09 UI matrix |
| FR-044 | `finance/test_opening.py` | Four exact opening directions and no revenue/expense/cash effect |
| FR-045 | `finance/test_opening.py` | Source-stated residual, summary mode, separate directions/currencies and unknown aging |
| FR-046 | `finance/test_opening.py` | Bounded atomic import, owner/stale checks, re-upload, changed snapshot and coverage/backfill conflicts |
| FR-047 | `finance/test_opening.py` | Opening allocation/adjustment/refund parity, V09 origin identity and concurrent reversal/consumption |
| FR-048 | `finance/test_opening.py` | V10 shared state/visual/catalog proof and no accidental normal-business handoff/activity |
| FR-049 | `finance/test_money.py` | 100 capture / 3 stated fee / 97 payout-bank receipt; pending events, reserves and disputed funds distinct |
| FR-050 | `finance/test_money.py` | Capture/statement/bank economic identity, partial batch coverage, refund/fee duplication and unsupported FX |
| FR-051 | `finance/test_advances.py` | Both advance directions, partial orders/invoices, cancellation and PostgreSQL earmark-versus-consumption race |
| FR-052 | `finance/test_holds.py` | Hold-after-preview refusal across individual/run paths, explicit release and evidenced during-hold reconciliation |
| FR-053 | `finance/test_transfers.py` | Both control-side transfer directions, atomic paired allocations, unchanged role balance and reversal/blocked checks |
| FR-054 | `finance/test_trade.py` | Partial/consolidated order-goods-invoice-credit-settlement trace and source-stated unallocated charges |
| FR-055 | `finance/test_trade.py` | Linked/not-applicable/unknown, scoped coverage invalidation and migrated-history false-positive refusal |
| FR-056 | `finance/test_agent_contract.py` | Complete/paginated structured explanation, cutoff change/restart, exact provenance and no financial Fact writes |
| FR-057 | `finance/test_agent_contract.py` | Public capability parity, stale/permission refusal, authoritative result re-read and no invented external success |
| FR-058 | `finance/test_web_contract.py` | V11/V12/V13 and existing-screen shared read/UI/isolation/locale/visual proof |
| DR-001 | `finance/test_provenance.py` | Source/evidence/Reality and separate receipt provenance |
| DR-002 | `finance/test_schema.py` | Shortest-link schema review; no duplicated line ownership |
| DR-003 | `finance/test_tenant_isolation.py` | Isolation catalog and PostgreSQL cross-tenant/target refusal tests |
| DR-004 | `finance/test_immutability.py` | Immutable source/ledger/package/receipt history and read-only derived state |
| DR-005 | `finance/test_received_values.py` | Decimal balance, no source amount recomputation or silent split residual |
| DR-006 | `finance/test_adapter_jobs.py` | Tool/service/adapter parity, existing worker registry, no direct external-effect handler |
| DR-007 | `finance/test_migration_catalogs.py` | Reviewed clean-schema initialization/reseed, data/event/command/Inspector catalogs and existing regressions |

## Required cross-cutting proof

- Add `scenarios/test_operational_finance_trade.py` for the integrated customer/supplier story; share fixtures, not implementation-derived expected values.
- Extend existing ledger, credit-note, reversal, finance-payment-atomicity and payment-run tests. New tests must preserve existing strict invoice-action contracts.
- `finance/test_settlement.py`, `test_advances.py`, `test_holds.py`, `test_transfers.py` and `test_accounts.py` use real concurrent PostgreSQL sessions/barriers, not sequential simulations.
- `finance/test_recording.py` and `test_adapter_jobs.py` inject failures at evidence commit, effect commit and response delivery; test pause/revoke and worker transaction guards.
- `finance/test_migration_catalogs.py` covers empty-schema initialization, required account links, explicit disposable reseed and new-model history, every new table and public capability.
- `finance/test_web_contract.py` verifies shared API/tool read and refusal shapes; add `apps/web/scripts/finance-contract.test.mjs` for client bindings and run real browser acceptance separately.
- Existing adapter/security/tenant-isolation suites and the complete required suite remain mandatory. Passing only these new modules is insufficient.

## Opening delivery verification

The executable opening regression file covers four directions; actual payment,
credit allocation/refund and exact reversal; explicit residual versus original total;
known and unknown due dates; duplicate/snapshot/summary conflicts; foreign tenant,
owner and stale confirmation boundaries; injected mid-batch rollback; historical
original-document/cash coverage; HTTP/MCP preview parity and filtered register totals;
forged/repeated opening posting; concurrent legacy payment/import lock ordering; and
independent opening reversal after settlement. The existing additive account migration
test now upgrades populated 0048 history through 0050 and checks unchanged identities.

The real browser journey adds four opening rows for isolated new parties, checks no
business effect at preview, mobile overflow, pending review after reload, explicit owner
confirmation, receipt provenance, and subsequent actual payment through the same modal.
Complete backend, frontend/localization, migration, catalog, lint/spec, site and browser
gates precede live rollout. Live verification compares every existing LedgerEntry before
and after the additive migration and rebuilds all running financial writer services.

## Managed-reference delivery proof

`tests/finance/test_references.py` covers all three kinds; stable identity across
rename/block/reactivation; immutable before/after and reason/action/actor evidence;
no ledger effects; case/tenant uniqueness; wrong-kind/foreign/blocked resolution;
server paging/filtering; empty/invalid input; stale review; injected audit failure
rollback; HTTP/MCP parity; owner/member authority; CLI reads and proposal; concurrent
replay (one decision); competing changes (one accepted, one stale); populated 0050→0051
migration with exact existing posting equality and guarded downgrade.

The existing disposable business-journey browser adds create/review/no-effect/reload/
confirmation for each kind, rename/block/history/search, and narrow light/dark views.
No real company references are created by verification or deployment.

## Received-component attribution slice

Service regressions cover all four invoice/credit directions, document versus line
scope, stated net/tax/gross, absent versus zero values, exact/partial/cleared splits,
invalid source contracts, unsupported precision, tenant and reference-kind boundaries,
blocked references, stale evidence/configuration, immutable historical labels, owner
identity, retry after transactional failure, concurrent replay and competing reference
changes. API/MCP reads must equal shared service results. A populated 0051 database
must retain every ledger row after 0052; destructive downgrade with attribution history
must fail. The real browser records 600/400 attribution, reloads a pending review,
confirms, replaces it with a partial allocation, reads history and checks mobile layout.
All existing backend/frontend/localization/site gates and live preservation checks apply.

## Operational matrix slice

FR-025/029/034: compare all fourteen matrix directions with actual recorded invoice,
credit, payment, refund, accepted reduction and opening entries. Check missing/blocked
defaults and changed control defaults without rewriting original invoice settlement.
Verify tenant isolation, no initialized accounts/state on reads, and identical API/CLI/
MCP output. Restore actual canonical `credit_note` attribution (prior component scope).
Browser: read fourteen rows, block/reactivate cash through existing owner confirmation,
observe automatic matrix refresh, follow account configuration and inspect mobile.
Open an actual customer credit in Financial detail. Preserve full finance journeys.


Regression: open an actual canonical customer credit Financial detail at 390px using a normal click; fixed footer must not intercept the row action. Existing title-count and mobile/desktop page-introduction checks remain required.


## Source classification checks

First failing tests cover exact scope and same-kind reference validation, tenant isolation, no-effect reads/proposals, confirmation/replay/stale revision, replacement/history, blocked source/reference/mapping, malformed/missing source codes, no document-to-line inheritance and explicit internal conflict. Add HTTP/CLI/MCP parity and owner guards, concurrent same-scope activation and additive migration checks. Browser: create/reload/confirm, inspect history, block/reactivate and view resolution on source-backed invoice detail on desktop/mobile. Required full gates stay unchanged.

Finance Settings placement: first assert URL parse/serialize and page introduction
for finance_view=settings and shared action destinations. Then run existing real
account/matrix/reference/source-mapping journeys from Finance Settings, assert Company
settings no longer contains editors, reload retains the tab, and settings navigation
issues no open-item/payment/journal read. Verify mobile access and existing owner-only
confirmation/member read behavior. Full frontend and catalog/backend boundary gates
plus local image/source parity and finance snapshot preservation are required.

Area navigation checks: URL round trip and invalid-area fallback, only selected editor
mounted and directly visible, cost-center kind fixed and classifications restricted,
owner/member and tenant reset, desktop/mobile selection, reload, existing reviewed
matrix/reference/mapping workflows. Run frontend gate, catalog/boundary tests and
complete real browser journey; compare live financial snapshots after web rollout.

Compact action proof: measure form buttons and verify submit starts below every field;
check account row Edit/More actions dimensions, default badge and hidden secondary
operations, Escape/outside dismissal, member restrictions, desktop/mobile rendering.
The full existing real finance journey must still review/confirm account block/activate,
reference and source changes. Full frontend gate and shared header checks apply.

## External target mapping slice (TM001–TM007)

Use the eleven numbered independent proof groups in
[target-mappings.md](target-mappings.md#planned-acceptance-proof). Backend tests belong
in `tests/finance/test_target_mappings.py`, with migration/catalog regression updates
where required. Observe meaningful failing tests before implementation. Browser
coverage extends the settings and real business journey scripts for setup, member
read access, all four invoice/credit kinds, preview provenance and unchanged balances.
Run `make spec-check`, `make lint`, `make test`, `make web-build`, localization audits
and applicable real/synthetic browser checks. Record results rather than extrapolating
from the delivered source-mapping or compact-button suites.

FR-059: browser checks prove list-only initial state, named create action for every
settings entity, prefilled editing, cancel/Escape without mutation, modal focus and
visible errors, pending review recovery, read-only member behavior and narrow/dark
layouts. Extend the real financial journey to enter through create/edit actions and
confirm actual account/reference/source/target changes through existing services.
Run frontend formatting/contracts/localization/TypeScript/build plus lint/spec policy.
No backend behavior change: existing complete backend proof remains applicable.

FR-060: browser proves no matrix accordion, named usage dialog, role-specific active choices, shared-role warning, confirmed default proposal, no mutation on cancel and no member change action. Adapt the real matrix/account-state journey to close/reopen native dialogs. Frontend contracts/locales/build plus lint/spec policy; existing backend tests cover unchanged service behavior.

When concurrent UI work triggers HMR, JOURNEY_PREVIEW_DIR can select an immutable production build for the same isolated browser journey; existing API proxy and all assertions remain enabled.

FR-061: extend finance-settings-dialog-browser.mjs to assert absence of a permanent Accounting target picker, navigate via target row, preserve create/edit dialogs and return navigation. Verify empty target list omits search/pagination and has explanatory copy. Keep the real confirmed target/reference/rule journey and existing financial assertions. Run make web-build, lint, spec-check and browser checks; inspect responsive screenshots and verify local served assets.


FR-062 verification: finance-settings-dialog-browser.mjs asserts one shared toolbar
per list and the create action's right edge. Reference/source list geometry is
checked at 390px and 1440px; native create/edit/review checks cover all existing
editors. Screenshots hide chat before checking visible mobile settings. Initial
empty lists omit filter fields and redundant pagination; filtered empty results
retain controls. Existing real finance journey proves reference filtering, changes,
source mapping, target setup and no financial effects from configuration.
Frontend gate includes all contract tests, four locale audits, formatting and
TypeScript/build; lint/spec policy and local asset preservation are required.

FR-063: browser checks empty areas have no list filters/table headers/pagination, populated target search gives no-results with retained search and Reset filters restores entries. Verify kind switches clear filters, existing confirmed journey and all frontend gates.
