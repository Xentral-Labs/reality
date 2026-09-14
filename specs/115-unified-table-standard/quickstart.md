# Validation and Review

## Local preview

The isolated preview remains at `http://127.0.0.1:5177`, with API8007 and the existing
`reality_unified_preview_107` database. Open `/app/orders-deliveries` or `/app/facts`
with the selected sample company. No business fixtures were added for this feature.
`/private/tmp/reality-115-live.mjs` authenticates the existing preview account and
reads16 register variants. It checks actual SQL sort responses,25-row page selection,
44px rendered rows and column widths bounded to320px; no business write request occurs.
Screenshots are under `/private/tmp/reality-115-browser/`.

## Scope review

Shared `RegisterTable` decorates semantic table content; existing renderers retain
canonical amounts, units, statuses and exact detail/action handlers. Delivery rows
split party, item and location into separate columns. Master-data columns vary by
family. Facts retains its exact predicate, original value, subject, observation time,
source/rule metadata and Inspector links. Contextual Home/Analytics/Chat remain intact.

Layout settings contain only density, hidden column indexes and bounded widths.
Storage keys include schema version, authenticated user and register variant. Changing
a register's column order in a future release requires versioning its layout identity.
Corrupt values are validated; blocked storage falls back to in-memory defaults.
Key and action columns stay visible. Text columns do not stretch into spare space;
a blank spacer keeps actions at the right edge. Action cells use4px horizontal
padding to fit up to three24px labeled controls inside80px.

Sorting uses explicit SQL-expression allowlists before pagination. Hydrated labels
and post-page derived fields do not advertise sorting. Projection money is cast to
Numeric; no new operational derivation, source authority or business schema is added.
Default order and1–100 API page-size compatibility remain for older callers.

## Executable evidence

- `test_unified_table_queries.py`: unknown sort rejection across11 route families;
  global descending master-data order over28 records/two pages;25/50/100 sizes;
  numeric3/20/100 order for financial projections and canonical available stock;
  totals remain123 regardless of page size.
- `unified-table-contract.test.mjs`: invalid/corrupt preference validation, protected
  key/actions, bounded widths, user/register separation and safe URL roundtrip/reset.
- `unified-tables-browser.mjs`: actual44/36px rows and44px header, column visibility,
  density/resize persistence, keyboard resizing, server query parameters, row click
  and Enter, sticky positions and24 locale/theme/viewport combinations.
- Existing unified workspace/operations/orders/finance/sources/facts/foundation/settings
  browser suites cover the retained detail, original-value and confirmed-action flows.
- Authenticated real-API proof covers16 variants at1920px. Live delivery and narrow
  finance screenshots were visually reviewed; new Facts matrix includes390/1440/1920px.

The initial backend and preference tests were run red. The first full backend run
had1511 passing tests and a failed specification-metadata gate; the missing English
and traceability declarations were fixed and the complete suite rerun. Browser
verification caught scroll overflow, a clipped third action and overwritten explicit
Inspector labels. Those were fixed in the shared component and affected journeys rerun.

## Required commands

- `cd packages/reality-core && PYTHONPATH=src ../../.venv/bin/pytest -q`
- `cd apps/web && npm run format:check && npm run test:contracts && npm run i18n:audit && npm run build`
- All `test:*browser` unified scripts, including new `test:tables-browser`.
- `cd apps/docs && npm run format:check && npm run test && npm run build`
- `make lint && make spec-check && git diff --check`

Final results are recorded below. Local implementation
verification does not mark the separate rollout or legacy/Playground retirement done.


## Final results — 2026-09-07

- Complete PostgreSQL backend: **1512 passed, 7 existing skips**,348.95 seconds.
  The seven skips remain the retired server-rendered UI tests.
- Web: **131 contracts passed**, formatting and production build pass.
  Locale audit: **1539/1539** in en/de/nl/es. The existing bundle-size advisory remains.
- All unified browser gates pass: foundation/delivery, workspaces, operations,
  orders, finance, sources, facts, settings and the new table matrix. Final Finance
  proof includes numeric alignment and a dedicated reversal-status column.
- Real-API proof passes for16 variants; the final6 order/finance variants were
  rechecked after the last column refinements. No business writes occurred.
- Docs: **45 tests passed**, formatting and build pass.
- Ruff, specification policy and diff checks pass. No schema migration or dependency
  installation is required. The existing feature flag remains the rollback boundary.

Logs are under `/private/tmp/reality-115-`: `backend-final.log`, `contracts-final.log`,
`web-format-final.log`, `i18n-final.log`, `build-final.log`, `tables-final.log`,
`live.log`, `live-final.log`, `orders-final.log`, `finance-final.log`, `workspaces.log`,
`operations.log`, `sources.log`, `facts.log`, `foundation.log`, `settings.log`,
`docs-test.log`, `docs-format.log`, `docs-build.log` and `policy-final.log`.

All feature tasks are complete. Global rollout and legacy/Playground retirement
remain separate decisions; this increment introduces no retirement or activation.
