# Quickstart Verification: Physical Shipments and Tracking

Use the repository PostgreSQL test environment and a disposable migrated database.

1. Prove forward/backward migration and no historical Shipment backfill.
2. Prove all four purpose/direction combinations, invalid combinations, effective contents,
   event supersession and tenant isolation.
3. Prove notice/event has zero stock effect; dispatch/receive changes stock and fulfillment once;
   stale, replay, concurrency and lost response remain atomic.
4. Compare API, CLI and MCP list/explain results and errors.
5. Run the Web journey across supported widths/themes/locales, distinguishing open Commitments from
   real Shipments and tracing Package contents/tracking.
6. Run measured PostgreSQL query-plan/performance proof.

Required gates:

```bash
make spec-check
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

Focused migration, backend, adapter, contract and browser commands are recorded in `tasks.md`.

## Verification evidence — 2026-09-11

- `make spec-check`: PASS.
- `make lint`: PASS.
- `git diff --check`: PASS.
- Shipment, application catalog, inventory, fulfillment and return regression selection:
  **101 passed**.
- `tests/test_migrations.py` from `packages/reality-core`: **13 passed**, including the
  disposable Alembic forward/backward proof.
- `npm run test:contracts`: **123 passed**.
- `npm run i18n:audit`: PASS for en/de/nl/es, **1544/1544** keys covered per language.
- `npm run format:check`: PASS.
- `npm run build`: PASS; Vite reports only the pre-existing large-chunk advisory.
- Stateful Chromium Shipment journey: PASS for register/detail, all five discovered forms,
  confirmed execution, local error handling, Escape-key close/focus flow, 1440 px and 390 px
  layouts, en/de/nl/es, and explicit light/dark preferences.
- Representative PostgreSQL register budget: **80 Shipments**, page size **50**, at most **6 SQL
  statements** including count and batch-loaded Package/Movement/Event/Commitment detail; PASS.
- Focused final Shipment domain/read/story/action/API/CLI/MCP/return and catalog suites were run
  after the complete suite so the final lossless-source/discrepancy assertion is included.
- Final Shipment, migration, return, adapter and Movement-correction risk matrix: **83 passed**;
  the subsequent stale/replay hardening selection: **46 passed**.
- Final complete PostgreSQL backend suite on the unchanged end state: **2,285 passed, 9 skipped**
  in 519.56 seconds.
- Final Shipment acceptance selection after documentation-only checklist updates: **51 passed**.
- Final `make spec-check`, `make lint`, `git diff --check`, frontend contracts, localization,
  formatting and production build: PASS. The final Chromium matrix also passed after the
  quantity/discrepancy presentation change.
