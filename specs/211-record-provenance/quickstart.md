# Validation

Use the local PostgreSQL test setup from `docs/TEST_STRATEGY.md`. Run `cd packages/reality-core && ../../.venv/bin/pytest tests/test_provenance.py tests/test_source_system_addressing_migration.py`, then repository `make test lint spec-check web-build docs-catalog-check`.

Run the provenance Playwright script against local Vite with `PLAYWRIGHT_MODULE` and `PLAYWRIGHT_EXECUTABLE` configured. In a worktree, symlink `.venv` and `apps/web/node_modules` from the main checkout first, or the suites silently test the wrong source.

Manual pass, in a demo company and in a company with imported records: open orders, deliveries, invoices, items and parties; confirm every row states an origin and that manually created records say so. Activate an origin and confirm identity, bounded payload, interpretation outcome and produced records. Configure a base address on one installed source system, confirm the link appears only for supported source types, that its host is visible before activation, and that a non-https address is rejected with a stated reason. Clear the address and confirm origin survives without a link. Repeat at 390px and in all four languages, and confirm no request issued by the browser writes.
