# Verification

## Independent master data — 2026-09-07

FR-013: six basic-field create/update entries reuse existing Party/Item/Location
tools, shared update snapshots and revisions. No migration or source-import worker
permission. Exact intent is checked at both tool and bulk-service entry; event
types remain family/action-bound. Back and selection never write; readable review
survives reload and keeps the actual tool name during uncertain execution.

Initial regression failed because party_create was not available in Playground.
Final targeted tests: six passed, including real foreign-tenant refusal, hidden
field preservation, rejection, repeat confirmation, stale preview and tampered
name/action/tool refusal. API plus master-data suite: 60 passed. Full backend suite
from packages/reality-core: 1373 passed, 7 skipped. The earlier root-directory run
had 11 migration configuration errors (missing Alembic script_location); corrected
working directory resolved all without changing migration code.

Web: 103 contracts, 1193 translation keys in four languages, formatting, production
build, Ruff, spec policy and whitespace checks pass. Isolated browser fixtures cover
all six entries, Back/no-write, selected IDs, nested-record review, reload and
confirmation; existing guided/finance/fulfillment flows also pass. Desktop/mobile
and light/dark screenshots reviewed. No connected signed-in browser was available;
browser fixtures do not claim real account end-to-end validation.

API/web images rebuilt locally. Final review preserves ordinary sandbox write denial,
existing shared services, private ownership, pending guards and source immutability.
No extension hooks configured. Source import simulation remains a follow-up increment.

## Execution status presentation — 2026-09-07

- FR-009: initial source regression failed because ExecutionStatus.tsx was absent.
  New read-only serialized polling stops on error/settlement/unmount, ignores late
  responses and never calls confirmation. Unknown is never inferred to be failure.
- 102 web contracts, four-language audit, formatting and production build passed.
  Existing guided browser journey passed; free-operation fixture covers automatic
  status observation, read failure/retry, proven discard, rejected settlement and
  same-sandbox continuation. Light/dark screenshots reviewed.
- UI-only: backend and schema unchanged, no tenant mutations. Browser fixtures used
  because the browser plugin reported no connected browser. Local web rebuilt.
- Review confirms polling only uses the existing scoped GET and explicit discard
  still calls the existing owner-confirmed rejection service. Spec policy passed.

## Shipment recovery verification — 2026-09-07

- FR-008 red proof: invalid shipment preparation/confirmation and legacy discard
  failed before implementation. The shared validator prevents overdelivery before
  execution is claimed; guided editors copy authoritative order/reservation quantities.
- Full PostgreSQL run: 1353 passed, 7 skipped, one catalog-count assertion failed
  after registering the new service (308 → 309). Both catalog counts were corrected;
  the isolated catalog assertion and all 66 catalog/isolation/spec-policy tests passed
  on rerun. Six shipment recovery tests passed, including
  refusal when action events or commitment movements exist and unknown execution.
- Web: 101 contracts passed, all four languages cover 1136/1136 strings, production
  build and formatting passed. Both isolated browser journeys passed, including
  normalized quantity reload and same-sandbox discard without replay. Browser tests
  use fixtures; no signed-in user browser was available.
- Local api/web rebuilt without database migration. API container is healthy and
  port 8080 serves index-oTtj_JbJ.js. The identified legacy step pgs_a372452d2b in
  pgr_402650baac was explicitly rejected through reject_step after its proof check.
  Stock remained 34, open order quantity remained 1, and shipment movements remained
  zero. No business operation was replayed; original proposal input is retained.
- Spec policy, Ruff and whitespace checks passed. Review retained owner checks,
  run serialization, decision attribution and blocking for unproven outcomes.

Run backend selected-work tests, full backend suite, web contracts/audit/build,
Spec policy and diff checks. Browser: free mode, sales A, purchase B, sales C,
reload, partial receipt B, reserve/ship A, final receipt B. C remains unchanged.
Verify explicit confirmation, archived/pending states, both themes and viewport
containment.

## Evidence — 2026-09-07

- Initial red: missing selected location response, missing shipment snapshot helper,
  and missing free-intent module; observed before implementation.
- Full PostgreSQL backend suite: 1349 passed, 7 skipped (159.36s).
- Targeted final backend suite: 3 passed. Ruff: PASS.
- Web contract suite: 98 passed. Four-language audit and production build: PASS.
- Formatting, spec coverage policy, diff whitespace: PASS.
- Isolated browser story: three independently created orders; pending reload;
  purchase partial receipt; earlier sales reservation and shipment at that order's
  item/location; purchase remainder; unrelated sales unchanged; rejection and
  archived restrictions; four languages, both themes and desktop/mobile controls.
- Existing guided browser journey: PASS, including confirmation, reload, inspectors,
  both themes and viewport containment.
- Browser fixtures do not mutate a real tenant. The separate PostgreSQL mixed story
  verifies actual shared Reality executions and resulting balances.
- Review corrected a stale-row/filter transition and retained owner-scoped services,
  no policy bypass, no migration and no alternative business balances.
- Build reports the existing large-bundle warning; no build failure.

## Usage

## Register separation verification — 2026-09-07

- FR-007: central Open deliveries and Open items; right pane contains exceptions only.
- Red before implementation: duplicate-side-list contract and outstanding partial
  invoice API regression. Both green after the shared filter and UI changes.
- Backend suite: 1349 passed, 7 skipped; additional finance paging/direction test
  plus partial/paid regression: 2 passed. Ruff passed.
- Web: 100 contracts, four-language audit, build, formatting and spec policy passed.
- Both isolated browser stories passed. New coverage: partial item visible,
  settled toggle, customer/supplier tabs, query/empty state, error/retry and document
  inspection. Desktop light/dark and mobile screenshots reviewed. No user tenant
  mutations in browser fixtures. Existing mobile horizontal cockpit navigation retained.
- Local api/web rebuilt; database untouched, no migration required.
- Review: no duplicate financial calculation, status filters run before paging and
  totals; old exact-status filters remain compatible. No extension hooks configured.

In a sandbox use the Individual operations group to create only a customer or supplier order.
Then open the central Open deliveries tab, select customer or supplier work and prepare a
reservation/shipment/receipt. Confirm each review. Guided examples remain available.
Bulk/picking and Shopify sample imports are deliberately not included yet.

Grouped chooser refinement: 99 web contracts pass, four-language audit/build/format
and spec policy pass. Both isolated browser journeys pass, including direct entry,
cancellation, review reload, settlement return, archived protection and guided
continuation. Visual inspection confirms both groups fit at 1280×800. Only web was
rebuilt locally; port 8080 serves index-CnTrCxLw.js. No backend/schema change.
# Independent fulfillment entries — 2026-09-07

FR-012: Release regression first failed because the tool was unavailable, then
passed through the shared tool. Tests cover no mutation on review/reject, missing
target, exact authority IDs, stale confirmation, one release event on repeat and
unchanged physical stock/open obligation. 135 Playground/API tests and 429
security/reservation tests pass; final two release tests also pass. Frontend: 103
contracts, four-language audit (1190 keys), build/format and browser selection,
Back, reviewed release, reload and four business-area groups pass. Grouped cockpit
screenshot reviewed. No schema changes or generic sandbox write permissions.
Final event-type restriction verified by 424 security/release tests; API and web
containers rebuilt and restarted locally.

Independent finance refinement: customer/supplier invoice and payment entries use
existing evidence/open-item reads and reviewed Playground finance tools. 96 scoped
backend/API tests and 103 frontend contracts pass. Browser verifies all four tool
names, exact selected line/invoice IDs, editable amount, read-only selection, reload
before confirmation and return to chooser. Build, format, Ruff, spec and i18n
(1186 keys in four languages) pass. No migration. Reservation release/grouping T017
remains open.

Reservation, shipment and receipt shortcuts reuse OpenWork and FreeOperations.
Browser verifies correct destination and Back without writes, then the existing
reviewed business stories. All 103 web contracts, build, localization (1181 keys),
format and spec checks pass. Local web container rebuilt/restarted. Independent
finance and release entry paths remain explicitly tracked in T015–T017.
## Progressive disclosure verification

FR-014: 104 web contracts pass; production build, formatting, four-language audit
(1194 keys) and spec policy pass. The isolated workspace browser journey verifies
six initially visible actions, twenty after keyboard expansion, no toggle writes,
compact reset after returning, and all finance, release and master-data entries.
The grouped-operations screenshot was visually reviewed at 1280 × 800. Local web
container rebuilt; no API/domain/schema change. Tests use fixtures, not live data.
