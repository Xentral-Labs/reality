# Verification: Global Command Palette

## Setup — 2026-09-18

- Spec policy, local links and 32-identifier task coverage passed before implementation.
- Python 3.12.4 and Node 25.9.0 are installed; existing frontend dependencies and TypeScript compiler are present. CI targets Node 22; compatibility still requires build/tests.
- Local PostgreSQL 17.10 is reachable at the established disposable test server after sandbox network escalation. The initial sandboxed attempt was denied; the approved connection succeeded.
- Existing .gitignore, .dockerignore and frontend .prettierignore cover the project build/dependency outputs. No unrelated ignore edits needed.
- Browser environment and baseline full-suite verification remain pending. No application acceptance is marked complete.

## Test-first evidence

Pending.

- T003 red: new matching test collection failed with missing reality.domain.search. T004 green: 31 matching/validation tests passed.
- T005 red: new SQL/migration test collection failed with missing reality.db.search_sql. T006 green: 20 SQL-corpus and upgrade/downgrade/re-upgrade tests passed, preserving a preexisting tenant.

## Incremental implementation evidence

- Baseline frontend: `npm run test:contracts` — 275 passed before feature integration.
- Browser prerequisites: bundled Playwright at `~/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs`, installed Chromium 1234. Vite listens on 127.0.0.1:5225 after approved local-network escalation.
- Navigation target tests initially failed with missing `commandPaletteTargets.ts`; four target/catalog tests now pass. Shared TypeScript matching corpus: 19 passed.
- US1 browser test initially failed waiting for the new combobox; after integration, shortcut navigation, pointer action launch, modal precedence, input reset and Escape passed with zero business writes. This is partial US1 evidence, not all-story acceptance.
- Frontend TypeScript/Vite build passed for the initial US1 integration.
- Foundation after metadata fixture installation: 51 Python tests passed.
- Search service tests initially failed with missing module; API test initially returned 405. After integration, four service/API tests passed, covering complete pagination, cross-company exclusion, exact references, mismatched cursors, private reports/deletion, no autoflush and no API business writes.
- Remaining acceptance (including full authorization matrix, provider completeness, exact details, localization, recents/favorites, worklists, real-API browser and performance) is pending.

## Continuation verification — 2026-09-18

- Full Python suite: `cd packages/reality-core && ../../.venv/bin/python -m pytest -q -n 4 tests` produced **3,000 passed, 9 skipped, 3 failed** in 578.64 seconds. Two catalog equality assertions needed the newly specified search vocabulary; spec policy needed the new test-family mappings. After explicit vocabulary assertions and coverage entries, the targeted catalog, HTTP boundary, spec policy and benchmark checks passed: **71 tests**. This is not a claim that a subsequent complete run has passed.
- Frontend build passed; localization audit passed for **1,996 keys in all four languages** before the latest clear-history copy. Command-palette browser proof passed: shortcut, modal precedence, cancellation with zero business writes, exact off-list detail, reference-only favorite storage, required historical template date and company switch.
- Access proof: **4 passed** for cross-company linked parties, private report ownership/deletion, source versions/session-bound continuation and lesson restrictions.
- Query regressions now include nullable references and inverse ID/label ordering across pagination. Matching, service and migration checks after the final normalization refinement: **78 passed**. The Latin-1 normalization fast path is exhaustively compared with Python for characters 1–255, plus combined examples.

### Measured performance findings (not acceptance)

The guarded disposable dataset contains 100,000 searchable records across every mapped family and ten authenticated users. A second company supplies an exclusion fixture. No live company was seeded or reset. The manifest contains ephemeral session credentials and remains outside the repository with mode 0600.

Three-observation smoke runs exposed real bottlenecks and drove these corrections:

1. Equality predicates now use the indexed normalization expression directly; null handling wraps the predicate instead of changing the indexed field expression.
2. Shipment package matching uses tenant-scoped EXISTS without multiplying shipments.
3. Complete matching precedes materialized candidate ordering, preventing a top-N plan from traversing thousands of unrelated names in label order. Numeric constant preference expressions are omitted from ORDER BY, avoiding positional interpretation and incorrect branch truncation.
4. An equivalent frozen Latin-1 fast path avoids repeatedly scanning the full Unicode translation tables for common European names. The authoritative fallback and corpus semantics remain unchanged. This is the initial unreleased support migration, not an in-place modification of a deployed version.

Latest ten-worker service smoke had no failures in its three warm observations per case. Warm p95 ranged from about 0.26 seconds for private reports to 1.81 seconds for invoice/payment providers; item prefix/typo measured about 0.26/0.40 seconds and tracking about 0.79 seconds. **These are insufficient observations and some already exceed the browser budget before network/debounce. SC-003 remains unpassed.** Raw local evidence: `/private/tmp/reality-235-service-smoke.json`; query plans: `/private/tmp/reality-235-plan.log`.

The first real-browser smoke could not complete initialization because the default API connection pool exhausted under ten browsers. That run is failed setup evidence, not discarded successful samples. A separate benchmark configuration of pool size 40 plus overflow 10 is being checked. The harness now counts session-setup failures as samples. Cold browser contexts are explicitly distinguished from cold database/OS caches; controlled cold-database acceptance remains pending.

### HTTP concurrency and latest UI checks

- Authentication work now runs in the existing threadpool instead of blocking the async middleware event loop. The explicit delayed-authorization event-loop regression and HTTP boundary checks passed (**13 tests**); user access, admission and invitations passed (**42 tests**). Authorization rules and production pool defaults remain unchanged.
- This correction is **not sufficient to pass the ten-browser workload**: repeated runs still exhausted the API connection pool. The latest harness retained all 26 smoke samples and reported `budgets_pass: false`. Task-owned benchmark API processes were stopped, releasing their idle transactions. Further HTTP lifecycle/concurrency analysis remains required before SC-003 acceptance; do not hide the failure by raising production pool defaults.
- Analytics workspace state now survives internal navigation; route-backed report, template and proposal targets are mutually exclusive. A test-harness hook adapter was updated to reflect the real component hooks; all five analysis-state tests passed afterward. Shipment direction survives route serialization.
- Separate Clear history preserves favorites. Localization/build checks prior to final formatting passed for **1,997 keys** in English, German, Dutch and Spanish.
- Browser tests passed again after adding a delayed-old-query case: old results cannot replace the current exact item. Existing off-page opening, template dates, pin privacy and company-switch checks still pass.
- Spec policy currently also reports newly added, concurrent spec234 costing test families that are not mapped by their owner yet. Those unrelated artifacts are preserved. Spec235's new feature contract and test families are explicitly mapped.

### Final checks for this continuation

- `pytest -q tests/test_global_search_*.py`: **87 passed in 8.82 seconds**. This includes matching, access, service, read-only adapter, overdue worklists, migration round-trip and the 100,000-item probe.
- `npm run test:contracts`: **305 passed**, zero failures.
- `npm run build`: passed (existing large-bundle warning remains).
- `npm run i18n:audit`: all four languages passed, **1,997/1,997 keys** each.
- Ruff passed for the touched search/domain/service/API/catalog/test/benchmark paths; `git diff --check` passed.
- The earlier materialization refinement was narrowed: direct label families use their ordered access path, while joined evidence retains complete predicate materialization. Materializing every one of 100,000 broad item matches exceeded the timeout and was corrected. The final single-user probe measured exact SKU **0.058s**, prefix **0.027s**, typo **0.036s**. These remain risk-probe observations, not SC-003 acceptance.
- A combined intermediate run had 131 passes and two failures: the broad-item materialization regression (now fixed, covered by the 87-test pass) and a source-code line cache mismatch while the shared core file changed concurrently. The isolated source-code test passed in the next run; no unrelated source lookup behavior was modified.
- Overall release status remains **in progress**: ten-user HTTP workload fails, full final suite and remaining story/browser acceptance are pending. Spec policy currently names only concurrent costing test families missing from their coverage mapping. No deployment, commit, merge or business-data reset was performed.

## Port 8080 missing-migration repair — 2026-09-18

User reported every provider unavailable for existing records, including Amber
Coast Retail. The running local database reported revision 0062 and no
`reality_search_tier_v1(text,text[],text[])` function. The API code was already live.
Executed the existing reviewed migration with
`docker compose exec -T api alembic upgrade 0063_global_search_support`; it succeeded.
No application restart, business-data reset or automatic startup migration was used.

Native Chrome verification on port 8080, company `ten_13f2feb06c`: searching Amber
returned the customer, four order previews and four finance previews, with Show all
for additional matches and no provider errors. Selecting order
`DEMO-072B837706E7-3` opened its exact Sales detail, including Amber Coast Retail,
Summit Bottle, held amounts and delivery progress, independently of the register's
first page.

A read-only shared-service audit under the company's active owner checked 121
queries, all found: 48 partner name/ID checks, 32 item name/ID checks, four location
name/ID checks, three each for customer/supplier orders and invoices, one customer
credit, and three each for source records, commitments, reservations, movements,
payments, other ledger entries, generic documents and owned private reports. Maximum
observed service query duration was 1,146 ms. Shipment, Fact and supplier-credit
populations were absent in this company and are not claimed as live-data proofs.
This repairs local installation readiness; earlier sustained-load gates remain open.

Spec impact: none. This installs the already-specified and tested migration and
clarifies the existing local setup procedure; no new behavior or business schema
was introduced during this repair.

### Visual refinement — 2026-09-18

- Added rendering tests before implementation (initial missing-component failure),
  then verified aggregated loading, collapsed provider failures with independent
  retries, and mixed pending/failure states: 3/3 pass.
- Full frontend contracts: 308/308 pass. Production build passes (existing bundle
  size advisory remains). Localization audit: 2001/2001 covered in all four languages.
- Native Chrome on the actual port 8080 application, company `ten_13f2feb06c`:
  typed `Amber` and observed the in-flight state with one spinner/status line;
  observed settled results including Amber Coast Retail, four orders and finance
  entries. The header, filters and footer stay in the same positions between the
  empty pending state and populated results. Rows align icon, label, contextual
  metadata, destination and pin controls consistently.
- Narrow-screen CSS is implemented but its live visual verification remains open:
  the native browser capture became unavailable when attempting the responsive
  preview (empty accessibility tree and no screenshot, including after reconnect).
  No narrow-view acceptance is claimed. Error disclosure is covered by rendering
  tests; no live provider outage was induced in the user's running company.
- This presentation-only refinement does not close the previously recorded load,
  performance, broader browser coverage or full-feature release gates.

### Exact destination layout audit — 2026-09-18

Root cause: off-page orders/master details reused `register-surface`, whose direct
child rules reset the Close button's horizontal padding and corner radii. Replaced
that wrapper with shared SelectedRecordPreview. Both off-page and table previews
now use content-width columns, compact flat sections and start alignment. Existing
readers, business links, actions and exact routing remain intact. Order and master
previews reveal loaded selected content (not only its loading placeholder), without
scrolling again on ordinary background refresh.

Regression proof: new wrapper/integration tests initially failed before implementation;
final frontend suite **312/312 passed**. The destination matrix contract covers 19
record-family/role cases and opaque identity round trips. Build and four-language
localization audit pass (2001 keys; existing bundle-size advisory remains).

Native Chrome live audit on port 8080, tenant `ten_13f2feb06c`, selecting Command K
results and inspecting rendered content:

| Family | Live example | Result |
|---|---|---|
| Customer | Amber Coast Retail | Correct inline master preview, aligned fields/actions |
| Supplier | Alpine Components | Correct inline master preview |
| Item | Summit Bottle / P01 | Correct preview; selected detail revealed |
| Location | Rotterdam Warehouse | Correct hierarchy preview |
| Customer order | DEMO-072B837706E7-3 | Exact off-page order, repaired close control and detail layout |
| Supplier order | PO-001 | Correct inline preview, loaded content/actions visible |
| Customer invoice | INV-7C14266504E2-2 | Exact document Inspector, readable scrolling layout |
| Supplier invoice | SINV-S04 | Exact document Inspector |
| Customer credit | CR-001 | Exact credit Inspector |
| Payment | PAY-1D778E99D481-1 | Payment Inspector targets led_66011298a5 |
| General document | doc_00c9c1c38e | Payment evidence document, distinct from payment target |
| Commitment | com_008227460d | Inspector context and trace links present |
| Reservation | res_7fb480dd91 | Quantity and shortest links fit |
| Movement | mov_00ea82aa45 | Movement and correction links fit |
| Ledger entry | led_0071e80edb | Financial Inspector and allocation details fit |
| Source record | src_001b2bc3cb | Long external reference wraps; source links readable |

No shipment, additional Fact or supplier-credit fixture exists in this company;
only their route contracts are verified here. This is a record-destination layout
audit, not a new live audit of every report/form/help destination.

Responsive native-browser device preview at **390px**: exact off-page customer order,
inline Summit Bottle master detail, full document Inspector and populated Amber
palette all fit the viewport. Sections stack; action buttons wrap; long document
references wrap. Device mode was disabled and developer tools closed afterward.
This completes the previously pending narrow visual check in T058.

During live development, hot module replacement briefly left TablePreview component
identity stale inside RegisterTable, producing apparent secondary action rows.
A full browser reload restored the normal rendering. Final desktop/mobile checks
used freshly loaded modules. One earlier supplier search exposed a transient partial
provider failure; retrying the search returned all four results. The existing broader
search reliability/load qualification remains open and is not certified by this audit.

Final repository policy gate: `python3 scripts/check_spec_policy.py` passed. Invoked
the Makefile target's Python command directly because local Apple `make` requires
an unaccepted Xcode license; no license or system setting was changed. Scoped
`git diff --check` passed. No commits or unrelated working-tree resets were made.

### Palette app-style alignment — 2026-09-18

Kept palette dimensions, row spacing, focus targets and behavior. Removed icon
frames, matched sidebar 16px/1.5-stroke Lucide treatment, selected page glyphs by
canonical destination, and distinguished item/location record icons. Matched the
app's neutral active-tab underline, regular row-label weight, surface and 12px
modal radius; navigation uses the shared horizontal-arrow convention.

Native Chrome on port 8080: opened the fresh palette and visually compared Inbox,
Purchasing, item and finance-worklist symbols with the surrounding sidebar. Neutral
tabs, unframed glyphs and layout align; existing preview/result structure remains.
Frontend contracts: 312/312 pass. Build, four-language audit (2001 keys), spec policy
and scoped whitespace checks pass. Existing feature-wide release gates remain open.

### PR integration on current main — 2026-09-18

Prepared in an isolated worktree on main `358ca967`; unrelated receipt-costing and
unmerged chat styling changes were excluded. Current main contains document-date
and requested-analysis migrations, so the unmerged search migration is now
`0066_global_search_support`, following `0065_requested_analysis`. The earlier
local-demo `0063_global_search_support` run above is historical evidence from the
pre-integration checkout, not the upgrade command for this PR. That experimental
local database's revision history needs reconciliation before switching it to this
branch; no existing local database was stamped or migrated during PR preparation.
The missing-date worklist fixture now uses SQL NULL, matching current main's Date
column. Production search logic and the SQL support definitions are unchanged.

The integration also assigns this feature number 237 because current main already
uses 235 for derivations in SQL. Historical benchmark seeds and artifact names
remain unchanged for reproducibility. Fresh integrated frontend checks: 312 contract
tests, production build, i18n tests and all four 2000-key language audits pass.

Final integrated focused backend regression run: 133 passed in 52.23 seconds,
including search matching, migration upgrade/downgrade, service authorization, HTTP,
worklists, benchmark contracts and application catalog checks. The full serial
PostgreSQL suite is still running; no complete passing result is claimed.

### PR 98 frontend CI environment correction

The first frontend CI run failed because the command-palette target contract imports
the executable catalog fixture, which requires `.venv/bin/python` and reality-core.
The frontend job previously installed only Node dependencies; local checks had an
existing Python environment. The job now provisions Python 3.12 and installs the
shared core into that expected virtual environment before running contracts.
Spec impact: none; this supplies test dependencies without changing product behavior
or replacing executable catalog coverage with a manually duplicated fixture.
All seven target contract tests pass locally; hosted CI remains the clean-environment
verification of the workflow correction.

### Record-filter clarity — 2026-09-19

The Records filter now uses an inset, wrapping row with an intrinsic-width select,
"Search in" label and a description associated through aria-describedby. An empty
query with no shortcuts prompts a name/number search rather than claiming no matches.
312 frontend contracts, production build and all four 2003-key localization audits
pass in the isolated checkout. Changes also applied to the active local frontend.
Browser visual acceptance remains pending; T062 is not marked complete.
PR 98 is already merged, so this refinement has not been pushed to that branch.
