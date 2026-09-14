# Validation

Use PostgreSQL and the existing test environment. Run `make lint`, `make spec-check`, `make web-build`, `make site-build` and `make docs-build`.

Run the timed replay benchmark without competing test workers, then all remaining backend tests. Together these commands cover the complete suite; the benchmark keeps its existing 60-second assertion:

```sh
cd packages/reality-core
../../.venv/bin/pytest tests/test_postgresql_integration.py::test_reality_gap_replay_resumes_ten_thousand_sources_without_duplicates -q
../../.venv/bin/pytest -n 4 -k 'not test_reality_gap_replay_resumes_ten_thousand_sources_without_duplicates'
```

For manual review, use an ordinary signup with open admission and Playground enabled, verify email, and observe a private populated demo Home. Retry a simulated failed setup and confirm the same company; pause Demo Data then replay and confirm it stays paused. Inspect all three starter results and their source links. The GitHub invitation must not appear on click/loading/error; dismiss and reload. Confirm English/German/Dutch/Spanish and narrow-screen keyboard access.

Use fake providers for allowance tests; never spend production AI quota for verification. Twenty dispatched questions across sessions share a UTC-day account allowance, question 21 never reaches the provider, reset restores access. Exhaustion retains the draft and operational navigation. Explicit disabled/manual policies and invitation destinations remain effective.

## Browser acceptance command

Start the app preview locally. Set `UNIFIED_APP_URL` to that preview and `PLAYWRIGHT_MODULE` / `PLAYWRIGHT_EXECUTABLE` to the installed test browser, then run `npm run test:free-playground-browser` from `apps/web`. The fixtures perform no external writes, use no paid provider and do not create real accounts. PostgreSQL tests separately establish actual service effects.

The test covers failed creation/retry, root reload with an existing partially initialized company, archive non-recreation, empty/uninitialized/error observations, GitHub dismissal, operational task routes, retained draft after quota rejection and all four actual mobile locales. Screenshots are written to `/private/tmp/reality-190-browser` during local acceptance.

## Verified result (2026-09-14)

2473 backend tests passed across the isolated benchmark and complete parallel remainder; 9 existing skips. The new keyboard/mobile/recovery/quota browser journey and all 16 existing manual setup combinations passed. Web: 155 contracts and 1819 localized strings; site: 63 contracts and 480 localized strings; docs: 67 Node contracts plus Python checks. Production builds, catalog generation, lint, spec policy and diff checks passed. No Railway deployment was performed.
