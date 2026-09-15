# Verification

Use the running local PostgreSQL stack and repository .venv. Execute pytest for scheduled startup and demo startup first, then complete `make test`, `make lint`, `make spec-check`, `make web-build`, and `make docs-catalog-check`. Browser acceptance: start web Vite on 5177 and run `node apps/web/scripts/live-simulation-header-browser.mjs` with PLAYWRIGHT_MODULE set to the installed module.

Expected: first three newly started deliveries at 0/12/24 seconds each import one order; fourth returns to normal stochastic cadence. Replay, retry, pause/resume, rate edit, downtime and tenant isolation remain safe. Header only shows a fresh running status and routes to current-company Demo Data; check mobile and reduced motion.

## Verification evidence — 2026-09-15

- Red proof: startup service tests failed because initial_offsets_seconds was unsupported; browser test failed because the indicator did not exist.
- Initial focused backend acceptance: 14 passed (includes initial intake, replays, pause/resume, capacity and frozen retry metadata).
- Frontend contracts: 191 passed. Build and en/de/nl/es localization audits passed.
- Header browser acceptance passed: normal/derived-error states, failed and stalled reads, hidden tabs, company-switch late response, keyboard link, 1440/1280/1024/768/390 widths and reduced motion. Screenshots inspected in /tmp/reality-live-simulation (desktop, dark, mobile).
- Ruff and spec policy passed. Catalog regeneration leaves no generated-page diff.
- Final scheduling preview/control/recovery regression: 33 passed.
- Local scheduler and worker rebuilt; API, scheduler and worker health endpoints returned HTTP 200. Worker signature confirms the new initial-offset implementation.
- Full PostgreSQL suite: 2,605 passed, 9 skipped, 1 existing transaction warning in 891.27 seconds. Final preview/resume adjustments were additionally verified with the 33-test scheduling/control/recovery run.
- Final frontend build and final header browser rerun passed. Temporary browser test server was stopped; the normal app remains running on port 8080.
- macOS make is blocked by the host's unaccepted Xcode license. Equivalent commands from Makefile ran directly; no license acceptance or host configuration change was performed.
