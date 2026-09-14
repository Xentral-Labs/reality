# Validation and Review

## Preview

Start the existing local Vite preview with `VITE_UNIFIED_APP=1` on5177 and proxy
API8007. Open `/app/facts?tenant=ten_7bcf46fd38`. The dedicated local company
is **Northstar · Local sample preview**, using database `reality_unified_preview_107`.
The fixture uses canonical `store_source_record` and `observe_fact`, guarded by
database name and tenant identity. Its two synthetic shipping-priority observations
refer to the same commitment and retain separate sources/timestamps.

## Behavior review

- The register reads recorded observations, not an inferred current winner.
- SQL filters and count precede stable timestamp/ID paging; source/rule joins are
  tenant-scoped metadata projections. No source payload or rule mapping is selected.
- Source navigation uses the exact source record. Related observations clears the
  source filter and selects exact subject type and opaque ID.
- The shared Inspector follows existing subject/source links. Historical unsupported
  subjects remain plain identities; missing source is not called manual input.
- Raw predicates/values remain escaped and untranslated in register and Inspector.
- No schema, write service, new predicate or legacy-retirement change was introduced.

## Verification evidence

Backend and route regression tests were run red before implementation. The browser
harness was developed alongside the UI; its first failure exposed an incorrectly
object-shaped fixture payload, corrected to the existing string contract. Visual
review then caught an unstyled input class, corrected to shared `br-control` styling.

Commands use the existing package environments:

- `cd packages/reality-core && PYTHONPATH=src ../../.venv/bin/pytest -q`
- `cd apps/web && npm run format:check && npm run test:contracts && npm run i18n:audit && npm run build`
- All unified browser scripts: foundation/delivery, workspaces, operations, finance,
  sources, settings, orders and the new `npm run test:facts-browser`.
- `cd apps/docs && npm run format:check && npm run test && npm run build`
- `make lint && make spec-check && git diff --check`

The Facts browser covers exact subject/source filters, page navigation, company
reset, foreign Inspector rejection, keyboard focus return, reload, empty/retry,
original-value preservation in every language and16 language/theme/viewport images.
Screenshots: `/private/tmp/reality-114-browser/`. Desktop light and German mobile
dark were visually inspected, including the corrected input controls.

The authenticated browser journey passes: Data & sources selects one exact source;
Facts shows its observation; Related observations shows both sample values; the
Inspector opens the actual commitment and original payload; source selection
survives reload. Navigation produces no business writes. Evidence is recorded in
`/private/tmp/reality-114-live.log`; screenshots include `live-related.png` and
`live-original.png`.

Final gate results are recorded below. Owner visual acceptance,
activation and legacy/Playground retirement remain separate from this increment.


## Final results — 2026-09-07

- Backend: **1499 passed, 7 skipped**,349.66 seconds. The seven skips are the existing
  retired server-rendered UI tests; no newly skipped tests. Focused Facts/master-data
  API validation:45 passed.
- Frontend: **129 contracts passed**; four-language audit **1531/1531** per language;
  formatting and production build pass. The existing bundle-size advisory remains.
- All unified browser gates pass: foundation/delivery, workspaces, operations,
  finance, sources, settings, orders and Facts. Facts includes16 screenshots and
  original-value Inspector checks in all four languages.
- Authenticated synthetic preview passes with an explicit200 subject response,
  original-source inspection and no business writes during navigation.
- Docs:45 tests, formatting and build pass. Ruff, spec policy and diff checks pass.

Logs use `/private/tmp/reality-114-` with suffixes `backend.log`, `contracts.log`,
`i18n.log`, `web-format-final.log`, `build.log`, `browser-final.log`, `live.log`,
`foundation.log`, `workspaces.log`, `operations.log`, `finance.log`, `sources.log`,
`settings.log`, `orders.log`, `docs-test.log`, `docs-format.log`, `docs-build.log`
and `policy-final.log`.

Final self-review found no unresolved requirement or Constitution conflict. The
complete verified increment is implemented; owner rollout acceptance remains open.
