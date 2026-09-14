# Verification results: first account-catalog slice

Date: 2026-09-09. Integration checkout: repository root. The active stack on port 8080 uses `.claude/worktrees/invoice-lines-research`; it was not migrated or replaced.

## Delivered scope

- [x] Three tenant-scoped account/default/coordination tables and required `LedgerEntry.account_id`, with composite tenant FK. No stored legacy account column.
- [x] Five existing operational roles, editable account codes/names, active/blocked state and deterministic role defaults. New-company reference setup does not create financial entries.
- [x] Shared account list/maintenance services, CLI/MCP discovery, typed proposals, owner confirmation, stale-preview refusal and atomic executed-result replay.
- [x] Existing invoice/payment/credit/refund services resolve account IDs; invoice-bound settlements retain their original control account after a default change.
- [x] Exact reversal preserves account ID, including blocked accounts. Ordinary blocked-account use fails.
- [x] Allocation checks concrete account/party/currency and available amount; concurrent consumers cannot spend the same credit twice. Supplier refund recording/allocation composes atomically.
- [x] Company settings panel and concrete code/name in the journal. Shared styling, localization and confirmation flow.
- [x] Data, command, event, tenant-isolation and spec coverage catalogs updated.

Broad task IDs remain open where they also require future operation/evidence/target schema or full-story acceptance. This checklist records the narrower authorized delivery without pretending those tasks are complete.

## Evidence

`packages/reality-core/tests/finance/test_accounts.py` covers explicit empty setup, required IDs, changed defaults, blocked-account reversal, invalid role/tenant references, credit reuse after refund, concurrent allocation with separate PostgreSQL sessions, proposal replay/staleness, owner authority, shared HTTP confirmation and clean schema migration. Existing payment atomicity, supplier credit, reversal, projection and migration regressions remain required.

The browser test is saved at `apps/web/scripts/finance-accounts-browser.mjs`. It uses synthetic HTTP responses and temporary component entrypoints removed on exit. Run against a separate Vite server with `PLAYWRIGHT_MODULE`, optional `PLAYWRIGHT_EXECUTABLE`, and `REALITY_BROWSER_URL`. It covers four languages (en/de/nl/es), two themes and three widths (390/1024/1440), checks document overflow and browser errors, and verifies that creating a proposal has no account effect before confirmation. Screenshots were visually inspected for German desktop dark mode and English mobile. This is Chromium proof; Safari and integration into the active unified shell are not claimed.

Completed checks:

- `make lint`: PASS.
- `make spec-check`: PASS.
- `git diff --check`: PASS.
- Web TypeScript/Vite build, format check and four-language localization audit: PASS; 102 frontend contract tests passed.
- Saved Chromium acceptance script: 24 locale/theme/viewport cases passed, including create → preview → confirm.
- `make site-build`: PASS (format, tests, localization audit and production build).
- Final focused finance/journal/reversal/projection run: 107 passed, with one old practice fixture failure subsequently corrected through the shared reference bootstrap.
- Corrected migration, PostgreSQL integration, practice, source and tenant-lifecycle regression run: 81 passed, 1 skipped. Test cleanup now removes new reference records before the disposable tenant; empty downgrade restores the prior account index. Production foreign-key protections remain unchanged.

- Full backend suite, run from `packages/reality-core` using `../../.venv/bin/pytest -q --tb=short`: **1,562 passed, 9 skipped**, exit 0, 325.39 seconds. This final run includes the corrected fixtures, migration round-trip, concrete journal fields and all existing regressions.

Final self-review: the diff matches the bounded account-catalog delivery and preserves unrelated work. New monetary history retains required IDs and explicit reversal; no old-string backfill, automatic reset, financial statements, tax engine or external effect was introduced. Full-feature acceptance and integration into the active unified shell remain open.

## Remaining scope

Cost centers and assignments, source-stated financial components, transaction/case/coding-group mappings, accepted skonto/withholding adjustments, the new customer/supplier available-credit view, opening imports, PSP/advance/hold/transfer semantics, translation-triggered financial recording, economic-effect identity, handoff packages and external receipts remain unimplemented under the full specification. Existing operational report filters still aggregate by technical role; this slice adds concrete account identity/display to journal entries, not a new account-statement product.

No live database reset, vendor connection, accounting statement or tax inference was performed. Adopting the new schema on disposable local data requires explicitly selecting that environment; populated ledgers fail the migration before schema changes.

## Active worktree integration — 2026-09-09

The owner approved integration and fresh local test data after the root slice. The active checkout retains the newer unified shell, lot expiry, delivery locks and read-performance changes. Only finance deltas were transferred; its migration is `0048_finance_accounts`, based on `0047_merge_demo_lot_expiry`.

Completed integration proof:

- Account regression tests initially failed collection because the active checkout lacked the finance service. After transfer they pass.
- `tests/finance/test_active_stack_stories.py` covers source-backed customer and supplier invoices, partial/full payment, payment reversal, credit, partial refund and remaining-credit allocation. Both pass; each side ends with one open amount of EUR 38.
- Owner-confirmed account maintenance also succeeds in an active practice company. The practice allowlist admits this bounded operation; temporary and archived restrictions remain.
- Invoice execution evidence now verifies the required `account_id` carried by `ledger.posted`. Targeted multi-position/rebilling/account tests: 36 passed.
- The real-browser business journey uses an isolated PostgreSQL database and actual API services, with no mocked business responses. Order, reservation, partial shipment, invoice, payment, credit, partial refund and refund reversal all verify after confirmation and reload. Its heading selector was updated to the current shell's accessible heading location; application behavior was not changed for this test.
- The account component's synthetic browser matrix passes 24 locale/theme/viewport cases. Unified company settings use existing `br-*` controls/theme tokens. Journal rows expose account code/name and ID. Members cannot propose changes from the form.
- Full web gate passes: format, 61 contract tests, four-language translation audit and production build. Layout constants in ActivityDrawer avoid false translation detection without changing presentation. An existing browser script was formatted without behavior changes.

Prepared local data: one existing user and login records copied into an explicitly named new database, two freshly created companies (Reality Handel and Northstar Demo), 11 account references and 82 ledger entries before browser acceptance. Company/demo creation and all monetary evidence use shared application services. The demo source is not started automatically. The previous local database remains recoverable and a private PostgreSQL archive was created before cutover. No database or object-storage volume is deleted.

Final results:

- Complete active-checkout backend suite: `pytest -q -n 4 --dist loadfile --tb=short`, **1,984 passed, 9 skipped**, 182.10 seconds. Each worker owns an independent PostgreSQL test database. The final legacy MCP fixture uses the supported cash role instead of an arbitrary bank string.
- Real isolated browser journey: **1 passed**, 38.32 seconds, with all eight actions verified from persisted evidence after reload.
- Local rollout on port 8080: **PASS**. The live browser created `BANK-LOCAL` through proposal → explicit confirmation, verified no pre-confirmation mutation, and read journal account identities and EUR 38 remaining on each customer/supplier side. Reality Handel has six accounts and 32 journal entries after this check. No browser errors occurred. Desktop/mobile panel and journal screenshots were inspected; mobile account actions remain inside a horizontally scrollable table.
- API, MCP, web, invitation worker, scheduler and worker are running with zero restarts; active database revision is `0048_finance_accounts`.
- `make lint`, `make spec-check`, `git diff --check`, `make site-build` and the full web gate pass. No application code was changed to bypass the invoice evidence assertions.

Cutover retained the previous database as `reality_pre_finance_20260909`; the prepared `reality_finance_local_20260909` was renamed to the configured original database name. Root `.env` and PostgreSQL/object-storage volumes were not changed. Existing owner/login records were preserved. A private archive is `/private/tmp/reality-before-finance-20260909.dump`; previous runtime image IDs are in `/private/tmp/reality-finance-previous-images.txt`. Do not apply the root checkout's 0047 account migration to this combined history.

The old database remains a recovery artifact, not a second active source. Recovery requires stopping application writers, restoring its configured name and the recorded prior images together. No automatic downgrade of populated finance history is supported. The temporary browser test session is revoked after verification; preexisting user sessions remain intact.

## Available-credit register verification — 2026-09-10

Delivered C001–C004 in the active unified checkout and deployed API/web to local
port 8080. Customer/supplier balance filters expose active payment and credit-note
origins with original/used/available amounts, currency totals and evidence links.
No migration or data reset was required. Adjustment acceptance, guided overpayment
recording and payment-credit refund actions remain unimplemented roadmap work.

- Test-first proof: new service import failed before implementation. Four symmetric
  service/HTTP cases now cover payment allocation, refund consumption, reversal,
  source provenance, blocked-account visibility, tenant isolation and pagination.
- Full backend suite: **1,988 passed, 9 skipped**, 211.42 seconds;
  `/private/tmp/finance-credits-suite.log`.
- `make web-build`: 61 contract tests, all four localization audits, TypeScript and
  production build passed; `/private/tmp/finance-credits-web.log`.
- `make site-build`, `make lint`, `make spec-check`, `git diff --check`: passed.
- Real browser journey: **1 passed**, 51.37 seconds. Eight reviewed business actions
  retain their receipts; additional customer/supplier available-credit checks use
  real API/database data at 1440px and 390px with no page overflow or browser errors.
  Artifacts: `/private/tmp/finance-credit-journey`; runner log:
  `/private/tmp/finance-credit-browser.log`. Desktop and mobile screenshots inspected.
- Local rollout: API healthy, web HTTP 200 and expected new asset served on 8080;
  other local services remain running. Logs: `/private/tmp/finance-credits-build.log`,
  `/private/tmp/finance-credits-rollout.log`.

Review: no stored derived balance, no new schema/monetary authority, no transport
business rules, no new mutation/confirmation bypass, and original credit-note-only
filter remains compatible. The read service currently scans tenant allocations,
matching existing settlement reads; no large-tenant performance claim is made.

## Separate accepted reductions — verified and deployed 2026-09-10

A001–A004 are complete in the active unified checkout. Customer and supplier invoice
actions retain the stated accepted amount, reason, supplier agreement, original
source/effect reference and authenticated confirming actor as immutable internal
evidence. One balanced noncash group and its allocation commit with the executed
proposal receipt. Reopening/reload preserves the same proposal identity. Reversal
remains independent of payment; blocked historical counterpart accounts are allowed
for exact inverses. Existing source credit evidence must be reused. Source-effect
identity spans source versions, preventing changed payloads from repeating a reduction.

Evidence:

- Initial failing proof: missing settlement service. Additional regression
  `test_new_source_version_cannot_repeat_accepted_effect` observed failing before
  stable source-stream/effect identity was implemented.
- Focused finance suite: **18 passed**, covering symmetry, invalid input, agreement,
  stale/replayed/concurrent confirmation, rollback, source deduplication, existing
  credit reuse, tenant boundary, additive migration and blocked-account inverse.
  `/private/tmp/adjustment-final-focused.log`.
- Final complete PostgreSQL suite: **2,019 passed, 9 skipped**, 326.06 seconds.
  `/private/tmp/adjustment-suite-verified.log`. The preceding run exceeded the
  existing 60-second bulk-import timing assertion during concurrent image builds;
  the limit was not relaxed, and the final run passed without concurrent builds.
- Frontend: **68 contract tests**, four localization audits, TypeScript/Vite build
  passed; `/private/tmp/adjustment-web-final.log`. Site build, lint, spec policy and
  diff whitespace checks passed.
- Real browser: **1 passed**, 170.86 seconds. Existing eight-action trading journey
  plus both reductions, no effects before confirmation, preserved proposal after
  reload, zero cash change, remaining invoice zero and persisted confirming user.
  Desktop/mobile and light/dark mobile review screenshots were captured; desktop
  and dark mobile reviewed. Artifacts `/private/tmp/adjustment-journey-final`;
  runner `/private/tmp/adjustment-browser-final.log`.
- Additive local migration `0049_settlement_reduction_roles` applied successfully.
  API, Web and MCP images updated; Web HTTP 200 and expected bundle verified.
  All 82 LedgerEntry rows retain an identical SHA-256 fingerprint. Customer and
  supplier live invoice contexts remain EUR 38 each; no actual invoice reduction
  was applied during rollout. `/private/tmp/adjustment-live-proof.json`.
- Private pre-migration backup: `/private/tmp/reality-before-adjustments-20260910.dump`,
  mode 0600. Migration/rollout logs: `/private/tmp/adjustment-migration.log`,
  `/private/tmp/adjustment-rollout.log`.

The two reduction defaults are intentionally not silently created in live companies.
The existing owner-confirmed initialization action can now add missing permitted
roles while preserving existing defaults. Both live contexts correctly report
missing counterparts until the owner completes this setup.

Integration review included the concurrently introduced spec-158 action directory:
classify the finance services, complete missing existing read classifications,
maintain catalog input/verification references, and adapt browser selectors to the
current action menu. Small lint/localization fixes preserve its behavior. No spec-158
completion markers were changed. Combined payment/adjustment editing, automated
financial recording, cross-source matching, guided payment-credit refunds, cost
centers and external accounting handoff remain roadmap work.


## Guided settlement verification (2026-09-10)

- 25 focused symmetric finance tests passed: `/private/tmp/settlement-focused-final.log`.
  Includes explicit optional reduction, overpayment, credit-note/payment reuse and refund,
  independent reversal, concurrency, rollback, tenant/owner boundaries, repeated source
  versions, amount range and timezone validation. Meaningful failing proofs were captured
  in `/private/tmp/settlement-red.log` and `/private/tmp/settlement-boundary-red.log`.
- Catalog/action-discovery integration: 44 tests passed, `/private/tmp/settlement-catalog.log`.
- Real browser: 1 passed in 54.12 seconds, `/private/tmp/settlement-browser-final.log`.
  Both sides execute all new modes with no effects before confirmation, pending-review
  recovery after reload, original evidence and authenticated confirming actor. Light/dark
  390px screenshots inspected in `/private/tmp/settlement-journey-final`; no dialog overflow.
- Final suite, web build and local rollout completed; see the final evidence below.
- Private backup before local rollout: `/private/tmp/reality-before-guided-settlement-20260910.dump`
  (0600). Existing ledger fingerprint: 82 rows, SHA-256
  `65cacd7cc314d05dafdbcf620a2213913dead6847266626b7d2d0a866ec34442`.
  Migration remains `0049_settlement_reduction_roles`; no schema or data reset.


Final-gate follow-up: the first complete run reported 2043 passed/9 skipped and
three failures (`/private/tmp/settlement-suite.log`). Two required an object root
for every public tool schema; the settlement adapter now exposes that envelope
while retaining discriminated mode validation. The existing 10,000-source replay
timing proof took 61.88 seconds against its unchanged 60-second limit. The final
complete run uses three workers after image builds finish. Focused finance, MCP,
agent parity and catalog verification then passed 78 tests with 2 expected skips
(`/private/tmp/settlement-tools-final.log`). Web verification passed 73 tests,
all four localization audits and TypeScript/Vite (`/private/tmp/settlement-web-final.log`).
Three concurrently introduced guided-rule UI files received formatting-only changes
to satisfy the shared frontend format gate; their business behavior was preserved.
API/Web/MCP image builds passed (`/private/tmp/settlement-images.log`). No rollout
or P004 completion is implied until the final suite and live read-only proof pass.


### Final complete and live verification

- Complete backend suite: **2046 passed, 9 skipped**, 203.02 seconds, three workers;
  `/private/tmp/settlement-suite-final.log`. The unchanged 60-second replay check passes.
  All public tool schemas and the final typed settlement validation are included.
- Frontend: **73 tests passed**, four complete localization audits and TypeScript/Vite
  passed; `/private/tmp/settlement-web-final.log`. Site build, lint, spec policy and
  whitespace checks passed. No test threshold was loosened.
- Real browser: eight new confirmed lifecycle cases across both customer and supplier,
  plus the existing trading journey and separately accepted reductions. Review/reload,
  mobile light/dark layout and evidence/confirming actor were verified against real
  isolated PostgreSQL, API and browser processes; no financial live records were created.
- Built and deployed local API/Web/MCP. Web returns HTTP 200 with image bundle
  `index-CZLg11j-.js`; API/MCP/database are healthy, all other existing services run.
  `/private/tmp/settlement-images.log`, `/private/tmp/settlement-rollout.log`,
  `/private/tmp/settlement-runtime-proof.json`.
- All **82 existing LedgerEntries are unchanged** under the same SHA-256 fingerprint.
  Migration remains `0049_settlement_reduction_roles`. Customer and supplier live
  contexts each retain EUR 38 open; actual-cash previews use incoming/outgoing
  directions respectively. `/private/tmp/settlement-live-proof.json`.
- Reduction defaults in the live company remain explicitly unconfigured. The owner
  can initialize the missing counterparts through existing account settings. Ordinary
  actual payment and existing-credit use do not require those reduction defaults.

P001–P004 are complete. No new tables, derived monetary Facts, bank transfers, opening
balances, cost centers or accounting handoff were introduced by this slice.

## Opening-position verification (2026-09-10)

The bounded manual opening slice records four directions with stable snapshot/item
coverage, existing tenant parties and neutral operational accounts. It reuses actual
payment, credit allocation/refund, accepted reduction and exact reversal. Scope and
item metadata have no duplicate balance. Due dates remain explicitly unknown when
absent. Summary origin remains visible in the review and both registers. Historical
normal posting is refused where it would overlap opening evidence.

The initial real-browser run exposed a test navigation omission: the new action uses
the existing More actions menu. Corrected browser navigation passed against a real
isolated database, API and browser (76.99 seconds), including mobile overflow, four
items, preview with no financial effects, reload, owner confirmation and subsequent
payment. Final proof is refreshed after the summary-label refinement.

The complete regression run caught legacy customer refund proof regressions when no
actual timestamp was supplied. Default occurrence is now captured once for both sides
and the ledger event, after coverage validation. The unchanged historical-proof checks
and all opening regressions pass together: 60 passed, 10.24 seconds. No assertion or
performance threshold was weakened. Logs: `/private/tmp/opening-regressions-fixed.log`.

Pre-rollout backup is `/private/tmp/reality-before-opening-positions-20260910.dump`
(mode 0600, 309582 bytes). All 82 pre-existing LedgerEntries fingerprint to
`65cacd7cc314d05dafdbcf620a2213913dead6847266626b7d2d0a866ec34442` on migration 0049.
Final full-suite, browser and runtime results are recorded below only after they pass.

Final backend gate: **2073 passed, 9 skipped**, 195.74 seconds with three workers.
`/private/tmp/opening-suite-final.log` includes the complete opening suite, shared
refund proof, schema/migration, catalog, tenant and performance gates. All unchanged
performance limits passed. The opening-specific file includes 25 cases; existing
customer-refund and trading regression files pass with it (60 combined tests).


### Final opening slice delivery

- Backend: **2073 passed, 9 skipped**, final complete suite above.
- Frontend: **74 tests passed**, all four language audits complete, TypeScript/Vite
  passed: `/private/tmp/opening-web-verified.log`. Site build, lint, spec policy and
  whitespace checks passed. Existing bundle-size notices are unchanged build notices.
- Final real browser: **1 passed in 58.06 seconds**; complete trading journey, four
  opening directions, preserved party selections across a new search, mobile layout,
  no-effect review, reload, explicit owner confirmation, source provenance and later
  actual payment. `/private/tmp/opening-browser-verified.log` and
  `/private/tmp/opening-journey-verified/`.
- Built matching API/Web/MCP/migration/scheduler/worker/invitation-worker images, then
  stopped writers, applied additive **0050_opening_subledger**, and restarted the
  matching services. No database reset or historical conversion.
  `/private/tmp/opening-images.log`, `/private/tmp/opening-rollout.log`.
- **All 82 historical LedgerEntries remain byte-equivalent under the same canonical
  fingerprint.** `/private/tmp/opening-ledger-after.json`. Both original live customer
  and supplier claims remain **EUR 38**. No live opening import/payment was created.
- Local Web returns HTTP 200 and serves `index-C24lQvGK.js`, with the opening UI in
  `UnifiedApp-CgFGE273.js`. API/MCP/database are healthy; all existing services run.
  All five Python writer services carry the same opening-service source fingerprint.
  `/private/tmp/opening-runtime-proof.json`.
- The live opening counterpart remains **unconfigured intentionally**. The owner can
  initialize missing permitted accounts or select an active neutral opening default
  in company account settings before the first import. Existing defaults are preserved.

O001–O004 are complete. The operational slice is manually entered in bounded batches;
file upload and guided historical coverage reconciliation remain future work alongside
cost centers, case mapping and external-accounting handoff.

## Managed-reference catalog verification — 2026-09-10

The bounded R001–R004 slice adds defined cost centers, case codes and coding groups,
with stable code/kind/identity, editable names/state, owner-confirmed previews and
immutable reasoned before/after history. List, search, state filtering, paging,
active-kind resolution, and API/CLI/MCP tools share one service. Company settings
uses the existing controls and supports restoring a pending review after reload.
No financial components, allocations, posting-case matrix or external handoff are
claimed complete by this catalog slice.

- Final full backend: **2088 passed, 9 skipped**, 300.01 seconds, three workers:
  `/private/tmp/references-suite-final.log`. All original performance thresholds pass.
  The initial full run found only the stale event count and migration-head assertions;
  they were updated to the added event and schema revision, retaining their financial
  preservation assertions. Final focused reference/adjustment/HTTP regressions:
  **37 passed**, 24.18 seconds: `/private/tmp/references-regressions-final.log`.
- Reference-specific tests include all kinds, blocking/reactivation, immutable
  snapshots/actor/action/reason, foreign/wrong-kind refusal, members versus owners,
  stale/replayed proposals, rollback on audit failure, competing changes, concurrent
  same-proposal execution, CLI/API/MCP parity, paging and populated migration proof.
- Final combined frontend build: **76 tests passed**, complete EN/DE/NL/ES audits,
  TypeScript and Vite pass: `/private/tmp/references-web-integrated.log`. Site build
  passes: `/private/tmp/references-site.log`. Ruff and spec policy pass:
  `/private/tmp/references-lint-integrated.log`, `/private/tmp/references-spec-integrated.log`.
- Real finance/reference browser proof before current-UI integration: **1 passed**,
  92.00 seconds: `/private/tmp/references-browser-final.log`. Actual-source four-way
  opening and settlement stories remain included. Final combined UI proof follows.
- Runtime review found the newer Main/spec160 frontend. Its Sales/Purchasing
  navigation, one main heading, page counts, page-local tabs and Inspector changes
  are preserved in the integration checkout; original source worktree is untouched.
  Source snapshot: `/private/tmp/references-current-ui-manifest.json`; prior files:
  `/private/tmp/references-ui-before-main-integration/`. The supplier-balance
  discovery regression remains covered. No older global heading/Facts shortcut is
  reintroduced by the finance delivery.
- Private pre-rollout backup: `/private/tmp/reality-before-finance-references-20260910.dump`,
  mode 0600, 318469 bytes. All 82 existing ledger rows have canonical fingerprint
  `65cacd7cc314d05dafdbcf620a2213913dead6847266626b7d2d0a866ec34442` on schema 0050.
  `/private/tmp/references-ledger-before.json`. No live reference was created by tests.

### Final managed-reference delivery

- Combined actual browser journey: **1 passed in 138.77 seconds**, including all
  earlier financial stories and new reference settings. Additional matrix passes
  for **18 main register counts**, zero/filter/tab/navigation/nested-count behavior,
  **44 desktop/mobile page layouts** and three translated views with unavailable
  reads. `/private/tmp/references-browser-integrated.log`,
  `/private/tmp/references-journey-integrated/`. Screenshots of the reference history,
  mobile light/dark controls and page chrome were inspected.
- Matching API/Web/MCP/migration/scheduler/worker/invitation-worker images were built;
  writers were stopped before additive **0051_finance_references**, then restarted.
  `/private/tmp/references-images.log`, `/private/tmp/references-rollout.log`.
- Live preservation proof: **all 82 prior LedgerEntries unchanged**, identical
  canonical fingerprint to the pre-rollout snapshot. Both original customer/supplier
  claims remain **EUR 38**. `/private/tmp/references-ledger-after.json`.
- Local Web returns HTTP 200 and serves `index-eql-Rz96.js`, with the integrated
  reference UI in `UnifiedApp-CXqWKZ0g.js`. API/MCP/database are healthy and every
  existing service runs. All five Python writer services carry reference service
  fingerprint `8f6394c62a15ac743db1dc668b6e7baa78f725bf37af98a05c038317d02192da`.
  `/private/tmp/references-runtime-proof.json`.
- No live reference or financial evidence was created by the tests/rollout. Owners
  explicitly define their own catalog in Companies → Finance references. Existing
  opening/reduction defaults are unchanged. The latest Main/spec160 layout, separate
  Sales/Purchasing navigation and removal of the duplicate Workspace Facts shortcut
  are retained alongside all delivered finance dialogs.

R001–R004 are complete. The next bounded work is evidence-backed component attribution
and cost-center assignment/splitting; automatic source-case mapping, posting-case
matrix and external accounting handoff remain unfinished. Broad checklist/US2/US6
markers are not changed by this delivery.


## Received-component attribution delivery — 2026-09-10

D001–D004 deliver customer/supplier invoice and credit-note financial detail,
received net/tax/gross/other basis where explicitly supplied, defined case/group
selection, exact or partial cost-center shares, clearing by a new revision,
owner confirmation, pending-review recovery and immutable history. Documents with
lines use individual line owners; the document summary is never added again.
Three tenant-scoped tables are added by `0052_component_assignments`. Shared
API/CLI/MCP tools use the same preview/approval services. No monetary Fact, posting,
tax calculation, automatic source interpretation or external handoff is added.

Verification and review:

- Full PostgreSQL backend suite: **2108 passed, 9 skipped**, 477.06 seconds,
  three workers: `/private/tmp/components-suite.log`. All original thresholds pass.
  Initial implementation red: `/private/tmp/components-red.log`; initial component
  plus application-catalog proof: 40 passed. Supplemental CLI/database boundaries:
  2 passed, `/private/tmp/components-boundaries.log`.
- Regressions cover four directions, line ownership and summary refusal, zero versus
  unknown, stated-value fidelity, 600/400 and partial/cleared splits, source conflicts,
  tenant/kind database constraints, blocked references, owner attribution, stale
  evidence/configuration, historical labels, rollback, concurrent replay and competing
  reference changes. Populated 0051→0052 preserves postings and guarded downgrade
  refuses to destroy component history. Finance writes consistently lock tenant then
  finance state, preventing the former inverse configuration/attribution lock order.
- Frontend: **76 tests passed**, complete EN/DE/NL/ES coverage, formatting, TypeScript
  and Vite: `/private/tmp/components-web-final.log`. Site build passes:
  `/private/tmp/components-site.log`. Ruff, spec policy and whitespace checks pass:
  `/private/tmp/components-lint-all.log`, `/private/tmp/components-spec.log`,
  `/private/tmp/components-diff.log`.
- The first browser run found overlapping row actions. Open-item action width now
  accommodates all five buttons, and real clicks pass without forced interaction.
  Screenshot review then found an unconditional read-error placeholder; it is now
  rendered only for missing data or an actual error. The browser explicitly rejects
  false alerts on a successfully loaded attribution preview.
- Final actual-API/PostgreSQL browser journey: **1 passed**, 166.87 seconds:
  `/private/tmp/components-browser-verified.log`; artifacts and visual review:
  `/private/tmp/components-journey-verified/`. It records 1000 net / 190 tax / 1190 gross,
  assigns 600/400 without posting effects, reloads and confirms, replaces with a
  partial revision, inspects history and source, and checks mobile layout. Existing
  delivery/payment/credit/refund/reversal/opening/reference stories remain green.
- Combined current-Main/spec160 proof: **1 passed**, 238.58 seconds:
  `/private/tmp/components-browser-final.log`. The 18-register title-count matrix,
  44 desktop/mobile page layouts and three translated page views pass. The later
  dialog-only placeholder fix was rechecked by the final business journey above;
  it does not change page headings or navigation.
- Final self-review: source and internal authority remain separate; shared services,
  tenant and reference-kind checks, confirmed atomic receipts and original evidence
  links are preserved. No unresolved critical finding remains for this slice.

Local rollout and preservation:

- Private backup (0600): `/private/tmp/reality-before-finance-components-20260910.dump`,
  321730 bytes. Root `.env`, volumes and recovery database are preserved.
- Matching API/web/MCP/migration/background images were built from the integrated
  checkout. All five Python writers were stopped before the additive 0052 migration
  and restarted afterward. Evidence: `/private/tmp/components-images.log` and
  `/private/tmp/components-rollout.log`.
- All **82** historical ledger rows retain SHA-256
  `65cacd7cc314d05dafdbcf620a2213913dead6847266626b7d2d0a866ec34442`.
  Original customer/supplier claims remain **EUR 38 each**. Reads of both original
  invoices return stated gross 50 with unknown net/tax/base, without normalizing new
  components. No live references, assignments or account defaults were prefilled.
- Schema head: `0052_component_assignments`. Web HTTP 200 serves
  `index-a4Tjpiff.js` and `UnifiedApp-Cg5vjUVZ.js`. API, MCP and DB are healthy; all
  services run, and all five writers match the verified component service hash.
  `/private/tmp/components-runtime-proof.json` and
  `/private/tmp/components-ledger-{before,after}.json` record the checks.

Remaining roadmap work includes source classification mapping, posting-case/account
resolution, global cost reporting and external accounting handoff. This bounded
slice does not complete the broad US2/US6 phases or reviewer-owned checklists.


## Operational matrix verification — 2026-09-10

Delivered a tenant-scoped, read-only description of 14 fixed operational transactions with current default accounts, debit/credit sides, stated amount basis and original-control-account policies. Missing and blocked defaults remain explicit. No schema, posting engine, automatic tax determination or source/case/target-account mapping was introduced. Actual canonical customer credits (`credit_note`) now support received-component detail and attribution.

Regression-first coverage compares the matrix to real invoice, credit, payment, refund, accepted-reduction and opening entries; checks tenant scope, no-write reads, original-account settlement and HTTP/CLI/MCP parity. Initial missing-service and canonical-credit failures were observed before implementation.

- Full backend: **2119 passed, 9 skipped**, 204.38s (`/private/tmp/matrix-suite.log`).
- Frontend: **76 passed**, four full 1359/1359 locale audits, formatting, TypeScript and production build (`/private/tmp/matrix-web-final.log`). Site build passed (`/private/tmp/matrix-site.log`).
- Ruff, specification policy and whitespace checks passed.
- Final real business browser: **passed, 148.42s** (`/private/tmp/matrix-browser-mobile-final.log`), including matrix no-effect reads, 14 rows, confirmed block/reactivate refresh, reference retry after stale shared revision, canonical credit detail at 390px, and existing component/settlement/opening flows. Companion checks cover 18 title-count scenarios, 44 desktop/mobile layouts and 3 translated layouts. Artifacts: `/private/tmp/matrix-journey-mobile-final/`; desktop/mobile matrix screenshots visually inspected.

Browser failures were resolved without forced clicks: reference retry waits for the fresh response before refilling; shared register measurement now respects the existing in-flow footer below 640px, restoring mobile row access. No backend re-run was needed after the final UI-only correction; frontend and full browser gates were repeated.


Local rollout completed without schema change (`0052_component_assignments`). A private pre-rollout PostgreSQL backup is held at `/private/tmp/reality-before-finance-matrix-20260910.dump` (0600). All 82 ledger entries retained SHA-256 `65cacd7cc314d05dafdbcf620a2213913dead6847266626b7d2d0a866ec34442`; exact hashes/counts also match for all seven account, allocation, reference and component tables. Customer/supplier sample residuals remain 38 against received gross 50. All five writers have matching matrix-service hash `34bca074ac6bdf05343790c21c577b3494f4496144c0aa89cbdf9a29caff418b`. Live canonical customer-credit detail and the 14-operation shared read succeed. Web returns HTTP 200 and serves `index-CsaidZVs.js` / `UnifiedApp-Bh9gS_AF.js`. Runtime evidence: `/private/tmp/matrix-runtime-proof.json`; preservation evidence: `/private/tmp/matrix-ledger-before.json` and `/private/tmp/matrix-ledger-after.json`. API/MCP/database are healthy; all required writers are running.

## Source classification mapping verification (2026-09-10)

Regression-first source mapping tests observed the missing service before implementation.
The final focused suite passes all 16 cases, including exact source/namespace/kind/code
scope, independent choice searches, no-effect preview/read, immutable decision history,
blocked and conflicting resolution, tenant/owner boundaries, stale/replay/concurrency,
HTTP/CLI/MCP parity, event rollback and additive migration/downgrade preservation
(`/private/tmp/source-mapping-focused-final.log`, 20.14s).

The first complete backend run reported 2147 passed, 9 skipped and two failed existing
expectations: the old migration head and the old event-catalog count. Both expectations
were updated to the additive schema and registered event; final full-suite evidence
follows below. No production behavior was changed to accommodate these assertions.

Frontend gate passes all 84 tests, formatting, four 1386/1386 locale audits, TypeScript
and production build (`/private/tmp/source-mapping-web-verified.log`). Site gate also
passes (`/private/tmp/source-mapping-site.log`). The integrated main UI passes 18 title
count scenarios, 44 desktop/mobile page layouts and three translated layouts against
production assets (`/private/tmp/source-mapping-chrome.log`). Ruff, spec policy and
whitespace checks pass. No extension hook file is present.

The complete real business journey passed in 151.81s
(`/private/tmp/source-mapping-browser-v2.log`): source mapping review/reload/confirmation,
block/reactivate, three preserved revisions, component resolution and linked history,
plus all existing opening, reference, attribution, payment, credit and refund flows.
An earlier selector failure prompted explicit accessible names on the form selects.
Visual review found that the mobile screenshot still showed the open chat overlay;
the final screenshot pass explicitly closes chat before inspecting the mapping history.

## Finance Settings workspace verification (2026-09-10)

The two initial route/destination regressions failed before implementation
(`/private/tmp/finance-settings-red.log`). They now pass alongside page introduction
checks. The settings view has its own bookmarkable Finance tab and introduction;
the operational register is unmounted there, and both owner management action links
use its shared destination. Financial editor components were removed from CompanySettings.

Full frontend gate: 86 passed, 0 failed; four 1388/1388 locale audits, formatting,
TypeScript and production build passed (`/private/tmp/finance-settings-web.log`).
The synthetic production-browser acceptance passed owner/member controls, tenant switch
and draft reset, zero unrelated register reads, zero mutations, and responsive light/dark
layouts (`/private/tmp/finance-settings-browser.log`). Screenshots in
`/private/tmp/finance-settings-workspace/` were visually inspected on mobile and desktop.
No financial service/schema behavior changed in this placement slice; shared discovery
changes are presentation destinations only. The complete source-classification backend
run remains the financial regression gate, supplemented by final catalog/boundary checks.

Final complete backend gate: **2150 passed, 9 skipped**, 725.72s
(`/private/tmp/source-mapping-suite-final.log`). The final source-mapping browser pass
with visible mobile history also passed, 216.05s
(`/private/tmp/source-mapping-browser-final.log`, artifacts
`/private/tmp/source-mapping-journey-final/`). The Settings placement is included in
the subsequent end-to-end and local runtime evidence below.

Final placement acceptance: the real complete business journey passed in **237.46s**
(`/private/tmp/finance-settings-journey.log`; artifacts
`/private/tmp/finance-settings-journey/`). It explicitly verifies the canonical Finance
Settings destination, reload retention, no duplicate Company editors and no unrelated
register reads, then executes the existing matrix/reference/source-mapping and full
financial workflows. Final catalog/HTTP checks: **52 passed**, 98.44s
(`/private/tmp/finance-settings-catalog.log`). Shared page-chrome checks pass 18 main
register scenarios plus Finance Settings count cleanup, 46 desktop/mobile layouts and
three translated layouts (`/private/tmp/finance-settings-chrome.log`).


## Source classifications and Finance Settings local rollout (2026-09-10)

Port 8080 serves `index-CIip2Hok.js` / `UnifiedApp-Aculpxe8.js` from the active
`.claude/worktrees/invoice-lines-research` checkout. Finance → Settings is the canonical
home for operational accounts/matrix, managed references and source-code mappings;
Company settings retains company/access administration. Explicit source mappings have
reviewed revision history and separate read-time component resolution.

Schema head is `0053_source_classification`. Root `.env`, compose project `reality`,
background roles and existing volumes are preserved. All five writers run matching
verified source-mapping code (`3735b8ffa0dc9a31e864d63b06c41a87d9663e4a9f709ebb4a780a99b6134277`).
API/MCP/database are healthy; web/site/docs return HTTP 200. All 82 ledger rows retain
SHA-256 `65cacd7cc314d05dafdbcf620a2213913dead6847266626b7d2d0a866ec34442`;
seven existing finance table snapshots also match exactly. Customer/supplier residuals
remain 38 against received gross 50. No live mappings or references were prefilled.

Private backup: `/private/tmp/reality-before-finance-source-classification-20260910.dump`
(0600). Preservation/runtime evidence: `/private/tmp/source-classification-ledger-before.json`,
`/private/tmp/source-classification-ledger-after.json`, and
`/private/tmp/source-classification-runtime-proof.json`. Full backend: 2150 passed,
9 skipped; frontend: 86 passed; final real journey and owner/member/mobile checks pass.
The previously integrated main base remains `c8a9682`; runtime proof separately records
the observed origin/main tip, which may advance during parallel work.

## Finance settings area navigation (2026-09-10)

The initial area URL regression failed before implementation
(`/private/tmp/finance-areas-red.log`). The frontend gate passes 87 tests, formatting,
TypeScript and production build (`/private/tmp/finance-areas-web-verified.log`). Final
area-specific copy was rebuilt and all four locale audits pass 1395/1395 labels.
Catalog/HTTP verification: 52 passed in 19.97s (`/private/tmp/finance-areas-backend.log`).
No financial service/schema changed, so the previously passed full backend suite remains
the financial baseline; the changed discovery validator/destination has focused coverage.

The complete real business journey passed in 76.81s
(`/private/tmp/finance-areas-journey.log`). It confirms actual account/matrix, all three
reference kinds, source mappings and financial operations from the selected area;
a prepared cost-center review survives switching to classifications and back, then
reload and confirmation. The synthetic browser also verifies legacy pending-review
recovery, owner/member permissions, tenant reset, fixed cost-center kind, restricted
classification choices, URL restoration and mobile area selection. A mobile accessible
name failure was corrected by explicitly labeling the select. Native form color-scheme
was aligned with each synthetic screenshot theme; no production theme rule changed.

Final area browser checks pass (`/private/tmp/finance-areas-browser-stable.log`),
including legacy review recovery and real area switching. Desktop/mobile screenshots
were visually reviewed in `/private/tmp/finance-areas-screens-stable/`; screenshots
await CSS transitions so native controls are captured in the selected theme. Shared
chrome checks pass 18 register scenarios, 46 desktop/mobile layouts and 3 translations
(`/private/tmp/finance-areas-chrome.log`). Final copy build assets are
`index-BR_DMDDu.js` / `UnifiedApp-ClEzbYCr.js`.


## Finance settings area menu rollout (2026-09-10)

Finance Settings now uses a vertical four-area menu and one visible editor, with a
mobile area select. Cost centers is separate from case codes/coding groups. Area
bookmarks and pending-review recovery are verified. Local web serves `index-BR_DMDDu.js`
and `UnifiedApp-ClEzbYCr.js`; all five writers include the updated shared navigation
metadata. Schema remains `0053_source_classification`, without migration or reset.
All 82 ledger rows and all eight finance table snapshots, including source mapping
history, match the pre-rollout fingerprints. API/MCP/database are healthy; web/site/docs
return HTTP 200. Runtime proof: `/private/tmp/finance-areas-runtime-proof.json`.
Preservation: `/private/tmp/finance-areas-ledger-before.json` and
`/private/tmp/finance-areas-ledger-after.json`. Private backup (0600):
`/private/tmp/reality-before-finance-finance-areas-20260910.dump`.

Validation: 87 frontend tests; 52 catalog/HTTP tests; full real finance journey (76.81s),
owner/member/tenant/recovery/mobile browser checks; 18 title-count scenarios and 46
responsive page layouts. Four final locale audits cover 1395/1395 labels. N001–N003
are complete; broader external accounting roadmap and reviewer-owned checklists remain
unchanged.

## Compact Finance settings actions

The initial browser regression reproduced a 64px-high account submit button before
implementation (`/private/tmp/finance-buttons-red.log`). Scoped styles and explicit
form footers now keep desktop form actions at normal height below every field and row
actions compact. Account secondary actions use an unclipped native popover; Default
is a status badge. Cost-center review has an area-specific label.

Frontend gate: 87 passed, formatting, TypeScript and production build; all four locale
audits cover 1396/1396 labels (`/private/tmp/finance-buttons-web.log`). The complete
real financial journey passed in 72.18s (`/private/tmp/finance-buttons-journey.log`),
including reviewed block/activate actions through the popover, reference/source changes
and existing financial flows. No financial service, API, database or permission changed;
prior backend verification remains applicable to this presentation-only slice.

Synthetic browser checks cover measured footer/row dimensions in all four settings
areas, default/non-default actions, Escape and outside dismissal, menu viewport bounds,
member restrictions, review recovery and responsive themes. A broad BANK text selector
matched both rows' Cash and bank role; the fixture now selects the exact code cell.


## Compact Finance buttons local rollout (2026-09-10)

Web-only update: `index-Ch2Dji5A.js` / `UnifiedApp-BaylGfEp.js`, stylesheet
`index-DAGOidoP.css`. Form actions have an independent footer and content-sized buttons;
account secondary actions are in a native top-layer popover and Default is a badge.
The deployed assets were checked over HTTP 200 (`/private/tmp/finance-buttons-live.json`).
No backend container, schema, account or financial record was changed by this rollout.
Verification: 87 frontend tests, four 1396/1396 locale audits, real financial journey
72.18s, measured button/footer/menu browser checks and desktop/mobile visual review.
Screenshots: `/private/tmp/finance-buttons-screens-final/`.

Final shared chrome verification passes 18 title-count scenarios, 46 desktop/mobile page layouts and 3 translations (`/private/tmp/finance-buttons-chrome.log`). B001–B003 are verified and deployed.

## Finance-specific external target mappings (2026-09-10)

The approved three-table slice adds accounting targets, allowed external account/tax
references and immutable exact mapping revisions. Shared application tools enforce
owner confirmation, tenant boundaries, stale revision refusal and replay. Document
preview keeps received amounts, source classification, internal assignment and target
resolution separately explainable; gross operational account legs remain separate.
A confirmed assignment from an earlier evidence version produces `stale_assignment`.
No export, remote posting or profile engine is delivered.

Initial seven feature failures were observed before implementation
(`/private/tmp/target-mappings-red.log`). The final stale-evidence regression also
failed before its fix (`/private/tmp/target-stale-red.log`). The complete backend
suite passed with 2180 passed and 9 skipped in 320.66s
(`/private/tmp/target-full-final.log`). After the final stale-evidence correction,
65 affected Finance, action-discovery and application-catalog checks passed in
19.15s (`/private/tmp/target-verified.log`); the complete suite preceded that correction.
Frontend verification passes 87 tests, four 1423/1423 locale audits, formatting,
TypeScript and production build (`/private/tmp/target-web-verified.log`). Ruff and
spec policy pass (`/private/tmp/target-gates.log`); `git diff --check` is clean.

The real browser journey previously passed in 117.97s, including confirmation
recovery after reload, mapping history, received evidence preview, unchanged financial
record counts and visible Finance settings at 390/1024/1440 in light/dark themes
(`/private/tmp/target-journey-final/`). Final post-correction rerun is recorded below.

Final post-correction real browser journey: 1 passed in 83.81s
(`/private/tmp/target-browser-verified.log`, screenshots and request evidence in
`/private/tmp/target-journey-verified/`). The final mobile Finance view was visually
inspected. TM002–TM006 are verified; the separate local rollout follows below.


## Finance external target mappings local rollout (2026-09-10)

Active runtime: `.claude/worktrees/invoice-lines-research`, branch
`150-shared-read-states`, observed HEAD `6235db2117c0bc385559f92d0d8cdaf2618f6a49`
plus the verified working changes. Compose project `reality` uses root `.env`.
API, MCP, invitation worker, scheduler, worker and web were rebuilt and restarted;
the migration service exits successfully. All five writers load the same verified
`target_mappings.py` hash. API/MCP/scheduler/worker health checks and web return 200.

Schema is `0054_target_mappings`: three Finance-only target/catalog/mapping tables.
The migration preserves all 76 existing table snapshots exactly, including 82 ledger
rows (fingerprint `ab2c2acac24d5637d62a9b23b875b7a6`). No live target, external
reference or rule was prefilled. Backup (0600):
`/private/tmp/finance-target-rollout/verified-before.dump`. Preservation and runtime
proof: `/private/tmp/finance-target-rollout/preservation.json` and `runtime.json`.
The initial migration attempt used a metadata-only environment URL and failed before
connecting; the corrected rollout used the existing Compose database configuration.

Web assets: `index-DQYHRfBL.js`, `UnifiedApp-BhaB5rNd.js`, `index-DAGOidoP.css`;
served bytes match the verified build. Navigate Finance → Settings → Accounts &
account mapping → External accounting for targets, allowed accounts/tax codes and
reviewed rules. Financial detail includes a received-evidence target preview.

Verification: full backend 2180 passed/9 skipped, followed by 65 affected checks
after the final stale-evidence correction; frontend 87 passed, four 1423/1423 locale
audits, TypeScript/build, Ruff and spec policy. Final real browser journey passes
in 83.81s, including reload recovery, history, evidence resolution and visible
390/1024/1440 light/dark settings. TM001–TM007 are complete. Export packages,
remote posting and external delivery receipts remain subsequent work.

## Finance settings native dialogs (2026-09-10)

FR-059 reuses the native modal pattern from Company settings and invoice entry.
All nine configuration editors now require an explicit named create/edit action;
no permanent form sits below the list. Immutable history uses its own dialog.
Existing commands and confirmation payloads remain authoritative. Closing a pending
review preserves it; account reviews now also recover through tenant-scoped session
storage. Dialogs show errors, prevent busy dismissal, restore focus and provide
contextual field guidance. External immutable codes remain visible during editing.

The initial browser test observed the old permanent-form failure
(`/private/tmp/finance-dialog-red.log`). The new all-editor suite passes creation,
account prefill, no-write cancellation, focus return, visible errors, member controls
and review recovery (`/private/tmp/finance-dialog-browser-reviewed.log`). Screenshots
after completed theme transitions are in `/private/tmp/finance-dialog-screens-reviewed/`;
cost-center desktop/light and rule mobile/dark layouts were visually inspected.
Existing row/popover sizing, menu dismissal, area navigation, legacy recovery and
permissions checks pass (`/private/tmp/finance-dialog-compat.log`).

Frontend gate: 91 passed, four 1456/1456 locale audits, formatting, TypeScript and
production build (`/private/tmp/finance-dialog-web-complete.log`). Ruff/spec policy
and diff whitespace checks pass. Backend behavior/schema is unchanged; the previous
complete backend proof applies. Final real journey and local rollout follow below.

Final real financial journey: 1 passed in 135.33s
(`/private/tmp/finance-dialog-journey6.log`, artifacts in
`/private/tmp/finance-dialog-journey6/`). This includes actual account state changes,
all three internal reference kinds, source mapping changes, external target/account
creation, exact rules, immutable history, recovered confirmations and source-backed
target preview, with unchanged financial counts during configuration.
Earlier runs identified duplicate history titles and tests still assuming inline
controls; those were corrected. Full-navigation fixture reads now settle before
operational interactions, and tests await completed confirmation rather than an
already-visible background create button. All existing financial assertions remain.
Final frontend verification remains green: 91 tests, four 1456/1456 locale audits,
formatting, TypeScript and build (`/private/tmp/finance-dialog-web-final-verified.log`).


## Finance settings native-dialog rollout (2026-09-10)

The active invoice-lines-research worktree serves the verified Finance settings UX
on local port 8080. All nine configuration editors use explicit create/edit actions
and native dialogs matching Company settings and invoice entry. History is separate;
prepared changes remain recoverable. No permanent create form remains below a list.

Web assets: `UnifiedApp-CHGu7W1N.js`, `index-DL-0DnEx.css`, `index-DdI1lPWC.js`.
Served bytes match the verified production build; HTTP 200. Only web was rebuilt and
restarted. API, MCP, invitation worker, scheduler, worker and database container IDs
remain unchanged. Schema stays `0054_target_mappings`; no migration or database reset.
Runtime proof: `/private/tmp/finance-dialog-runtime-proof.json`.

Verification: 91 frontend tests, four 1456/1456 locale audits, TypeScript/build,
formatting, lint/spec policy; all-editor browser checks and existing area/menu/
permission/recovery checks pass. The complete real financial journey passes in
135.33s (`/private/tmp/finance-dialog-journey6.log`). Final screenshots are in
`/private/tmp/finance-dialog-screens-reviewed/` and `/private/tmp/finance-dialog-journey6/`.
Spec148 UX001–UX003 are complete; broader accounting handoff work remains separate.

Post-rollout browser verification against localhost:8080 passes all named editors, cancellation/focus, visible errors, member permissions and restored reviews using isolated request fixtures (`/private/tmp/finance-dialog-live-browser.log`; screenshots `/private/tmp/finance-dialog-live-screens/`).


## Operational account setup clarity rollout (2026-09-10)

FR-060 is verified and available at localhost:8080. Operational accounts now has
an Add account toolbar action and an explanation of role defaults versus external
ledger numbers. View account usage opens Accounts for business transactions;
Change default opens a role-scoped active-account picker and the existing confirmed
command review. The dialog explains the shared-role effect and preservation of
existing postings. AC001–AC003 are complete; no schema or business-rule changes.

Verification: 95 frontend tests, four 1466/1466 locale audits, formatting,
TypeScript and production build passed (`/private/tmp/account-usage-web-verified.log`).
Focused all-editor, default-selection, cancellation, permission, recovery and
responsive/theme checks passed (`/private/tmp/account-usage-browser-final.log`).
The real financial journey passed in 82.63s, including a confirmed role-default
change with unchanged historical financial counts
(`/private/tmp/account-usage-journey-final.log`). Accessible labels for the Account
and Role selectors were corrected after initial browser failures.
Post-rollout compatibility checks passed against localhost:8080, covering compact
controls, menus, area navigation, recovery, permissions and responsive themes
(`/private/tmp/account-usage-compat.log`).

The web image uses the frozen, tested production build at
`/private/tmp/account-usage-frozen-final`, avoiding development HMR from concurrent
source edits. Served assets match the tested bytes: `UnifiedApp-D9V9U6Xk.js`,
`index-BSDcBHsg.js`, `index-ChcM3b0Q.css`. HTTP 200; API, MCP, invitation worker,
scheduler, worker and database container IDs remain unchanged. Schema remains
`0054_target_mappings`. Runtime proof: `/private/tmp/account-usage-runtime-proof.json`.
Concurrent source edits were preserved; a future normal build uses current sources.


## External accounting list entry — FR-061 (2026-09-10)

The new regression failed against the previous deployed permanent target picker
(`/private/tmp/external-settings-red.log`, expected zero target selects, received one).
TargetMappings now starts with a target list and Open account setup navigation.
It reuses existing create/edit/review dialogs and target-scoped service calls;
empty lists have contextual guidance instead of redundant filters and pagination.
Selected target identity remains the existing opaque ID; the stored label is only
presentation context. No business rules, schema or financial posting changes.

Focused browser checks passed (`/private/tmp/external-settings-browser.log`): empty
first entry has no input/select or pagination, explicit target creation opens a
dialog, target-row entry/back navigation works, and all existing editor, no-write
cancellation, error, permission, recovery and responsive/theme assertions remain.
Empty-list desktop and create-dialog mobile screenshots were visually reviewed
in `/private/tmp/external-settings-screens/`.
Frontend gate passed: 95 tests, four 1480/1480 locale audits, formatting,
TypeScript and production build (`/private/tmp/external-settings-web.log`).
Lint, spec policy and whitespace checks pass. Real journey and rollout evidence
are recorded below when complete.


## External accounting list/dialog rollout (2026-09-10)

FR-061 is deployed at localhost:8080 from the tested frozen production build
`/private/tmp/external-settings-frozen`. The target list replaces the permanent
search/select block. Open account setup enters a target's accounts, tax codes and
rules; Back to accounting targets returns to the list. Create/edit remains in native
dialogs, and unused empty-list search/pagination controls are omitted.

Verification: 95 frontend tests, four 1480/1480 locale audits, formatting,
TypeScript/build, lint/spec policy and focused responsive/dialog browser checks pass.
The real financial journey passed in 80.73s, including actual target creation,
allowed accounts, confirmed exact rules, immutable history, component preview and
unchanged configuration-time financial counts (`/private/tmp/external-settings-journey.log`).

Served bytes match the tested build: `UnifiedApp-BkMOb9Cg.js`, `index-CU9j8hEn.js`,
`index-CcgPXTUH.css`. HTTP 200. Only the web container was replaced; API, MCP,
invitation worker, scheduler, worker and database container IDs remain unchanged.
Schema stays `0054_target_mappings`. Proof: `/private/tmp/external-settings-runtime-proof.json`.
Concurrent source work is preserved; the local image uses the frozen tested assets.
EA001–EA003 are complete. No external transmission or new accounting behavior added.


## Consistent Finance settings layout — FR-062 (2026-09-10)

Meaningful red: the previous deployed page had no shared toolbar
(`/private/tmp/finance-layout-red.log`). SettingsToolbar now places contextual
controls left and named create actions right, preserving alignment when wrapped.
All four settings implementations share it. Heading/help typography, filter widths,
empty-state cards and conditional pagination are aligned; existing native dialogs
and footer action order are retained. Empty reference/source lists hide unused
filters; active filters stay available when no results match.

Focused browser checks pass (`/private/tmp/finance-layout-final-browser.log`), including
cross-area toolbar geometry and mobile list views with chat closed. Mobile case-code
list screenshot was visually reviewed. Initial overall checks caught transient
unrelated FlightRecorder changes; those files were left untouched. The later complete
frontend gate passed: 96 tests, four 1481/1481 locale audits, formatting,
TypeScript/build (`/private/tmp/finance-layout-web-green.log`). Final release checks
and rollout evidence follow below. No schema or finance service changes.


## Finance settings alignment rollout (2026-09-10)

FR-062 is available at localhost:8080. A shared SettingsToolbar aligns contextual
controls left and named create actions right in operational accounts, cost centers,
classifications, source mappings and external accounting. Existing compact buttons,
card/help spacing, filter widths, empty-state cards and conditional pagination are
consistent; existing native dialog footers and finance service behavior remain.

Final frontend gate: 96 tests, four 1481/1481 locale audits, formatting and
TypeScript/build pass (`/private/tmp/finance-layout-web-green.log`). Final release
browser checks pass, including desktop/mobile toolbar geometry, all settings editors,
no-write cancellation, permissions, errors and recovered reviews
(`/private/tmp/finance-layout-release-browser.log`). The real financial journey passes
in 92.17s (`/private/tmp/finance-layout-journey.log`), using the frozen Finance changes
before the unrelated parallel FlightRecorder work finished. The final shared release
build was separately browser-checked; no Finance source changed between these builds.
Lint, spec policy and whitespace checks pass.

The local web image serves the verified release assets from
`/private/tmp/finance-layout-release`: `UnifiedApp-Ce4_nFGQ.js`, `index-B539j8WZ.css`,
`index-CSJpyBXr.js`. Served bytes match, HTTP 200; backend and database container IDs
remain unchanged and schema stays `0054_target_mappings`. Proof:
`/private/tmp/finance-layout-runtime-proof.json`. No source edits from concurrent work
were discarded. FL001–FL003 complete; broader roadmap markers are unchanged.


## Empty catalogs versus filtered no-results — FR-063 (2026-09-10)

Red observed against the old deployed UI: Reset filters was missing after searching
for a nonexistent target (`/private/tmp/finance-empty-red.log`). Shared
SettingsEmptyState now distinguishes empty catalogs from filtered no-results and
provides a reset action. Reference kind switches clear query/status/paging; unfiltered
reads update catalog presence instead of permanently retaining a previous positive
count. Target filters remain mounted during reset/loading. Empty operational account
catalogs omit table headers, and empty source lists omit the refresh action.

Focused browser passes (`/private/tmp/finance-empty-final-browser.log`): empty reference
and source lists have no input/table/pagination; target query reset restores results;
reference query reset restores rows; switching from a blocked-status filter to an
empty coding-group catalog clears filters while preserving type navigation. The empty
account catalog has no table/input/select and retains its enabled create action.
All previous dialog, permission, recovery, cancellation and responsive checks remain.
Frontend: 98 tests, four 1482/1482 locale audits, formatting, TypeScript and production
build pass (`/private/tmp/finance-empty-web.log`). Lint/spec policy and diff whitespace
checks pass. No service or schema changes; full finance journey and rollout below.


## Finance empty-state rollout (2026-09-10)

FR-063 is deployed at localhost:8080. Empty settings catalogs show a placeholder
and permitted create actions without list filters/table headers/pagination. Area
navigation remains available; filtered no-results keeps filters and Reset filters.
Reference kind switches clear previous query/status/paging. FE001–FE003 complete.

Verification: 98 frontend tests, four 1482/1482 locale audits, formatting,
TypeScript/build and lint/spec policy pass. Focused browser empty/reset/kind-switch/
empty-account and existing dialog checks pass (`/private/tmp/finance-empty-final-browser.log`).
The complete real finance journey passes in 81.97s (`/private/tmp/finance-empty-journey.log`).
Both browser suites use the frozen release at `/private/tmp/finance-empty-release`.

Served assets match the verified release bytes: `UnifiedApp-Dd663VvV.js`,
`index-Dip0vLtJ.js`, `index-ckKgtbpD.css`. HTTP 200. Only web was replaced;
backend/database container IDs are unchanged, schema remains `0054_target_mappings`.
Proof: `/private/tmp/finance-empty-runtime-proof.json`. No source edits from parallel
work were discarded; no schema, service or financial posting change.


## Isolated Finance-only PR verification (2026-09-10)

Branch `feat/operational-finance-settings` in `/private/tmp/reality-finance-pr` is
rebased on main `a39d277`. The diff excludes unmerged FlightRecorder, ObjectGraph,
recorder/constellation layout, related tests/styles/translations, AGENTS and local
stack deployment notes. The original combined worktree is unchanged.
Main's PageActionBar and inline Inspector previews are retained; Finance actions are
integrated into their existing menus and expanded rows. Browser tests follow these
visible controls. UI requirement IDs are corrected to FR-059–063, retaining the
original settlement definitions at FR-035–039.

Spec Kit analysis: 70 unique requirement definitions, 196 tasks at analysis time,
100% requirement-to-task reference coverage, zero duplicate definitions, no unresolved
clarification or critical finding for the delivered slices. The broad roadmap remains
open. This does not claim full implementation of every planned Finance requirement.

Final isolated verification:
- PostgreSQL suite: 2182 passed, 9 skipped in 486.03s, including migration checks
  (`/private/tmp/finance-pr-backend.log`).
- Frontend: 95 passed; four 1471/1471 locale audits; formatting, TypeScript/build
  (`/private/tmp/finance-pr-web.log`). Recorder-only tests/translations are excluded.
- Real finance journey: passed in 96.41s (`/private/tmp/finance-pr-journey3.log`),
  preserving all monetary, evidence, confirmation, history and recovery assertions.
- Settings browser: passed (`/private/tmp/finance-pr-settings.log`).
- Action directory/context browser: passed, zero business writes
  (`/private/tmp/finance-pr-actions-final.log`).
- Ruff, spec policy against origin/main and whitespace checks passed.

Initial integration browser attempts exposed obsolete detail labels and a duplicated
menu toggle in the test navigation; final tests use main's actual disclosure/full
explanation and shared menu controls. The mobile global menu is explicitly opened.
No product behavior was reverted to satisfy the old selectors.

Migration 0048 refuses populated legacy ledgers; it performs no automatic data reset
and is not a production backfill. The approved clean local cutover remains the scope.
Publication was rejected by automatic approval review because explicit destination
approval for Xentral-Labs/reality was requested. After the user explicitly approved
that destination, branch `feat/operational-finance-settings` was pushed and
[PR #187](https://github.com/Xentral-Labs/reality/pull/187) was created against `main`.
No merge or deployment was performed.

Spec impact: none for this publication record; it documents delivery of the verified
Finance slice without changing product behavior.
