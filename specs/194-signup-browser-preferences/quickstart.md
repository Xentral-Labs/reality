# Validation

Use the repository virtual environment and the disposable PostgreSQL test database.
Focused proof: `packages/reality-core/tests/test_user_access.py`,
`apps/web/scripts/signup-preferences.test.mjs` and
`apps/web/scripts/signup-preferences-browser.mjs`.

The browser proof needs a Vite server for this worktree and a Playwright installation,
neither of which is a repository dependency:

```bash
cd apps/web && npx vite --config vite.config.ts --port 5191 --strictPort --host 127.0.0.1
PLAYWRIGHT_MODULE=<playwright>/index.mjs UNIFIED_APP_URL=http://127.0.0.1:5191 \
  npm run test:signup-preferences-browser
```

## Evidence

- Initial regression proof: the five new backend expectations failed against the old
  implementation (stored `en`/`en-GB`/`UTC`, no `SUPPORTED_LOCALES`), and
  `signup-preferences.test.mjs` failed with no module, before implementation.
- `tests/test_user_access.py`: 16 passed.
- Related account suites (`test_user_access`, `test_access_admission`,
  `test_platform_admin_overview`, `test_application_catalog`, `test_spec_policy`): 97 passed.
- `make lint`: passed.
- `make spec-check`: passed.
- `apps/web` contract tests (`npm run test:contracts`): 167 passed, including the six new
  signup-preference expectations.
- `npm run format:check`: passed. `npm run test:i18n`: passed. `npm run i18n:audit`: all four
  languages 1835/1835 covered, no missing or invalid strings. `npm run build`: passed with the
  existing bundle-size warning.
- `npm run test:signup-preferences-browser`: PASS. A real Chromium context in `America/Denver`
  registering from `/signup?lang=de` sent
  `{"email":…,"accepted_terms":true,"playground":true,"language":"de","timezone":"America/Denver"}`;
  a Dutch browser without a language choice sent `nl` with `Europe/Amsterdam`; a French browser
  sent `Asia/Tokyo` and no language. No request carried a locale.
- Full backend suite (`make test`, serial, disposable PostgreSQL): 2497 passed, 9 skipped,
  one pre-existing SQLAlchemy warning, in 571 s. Re-run after the final refactor of the
  shared time-zone check, with the same result as the run before it.
- No account, deployment or remote service was changed by these runs.

## Environment notes

Two traps cost time here and are worth recording:

- A second worktree's Vite server already held `127.0.0.1:5177` while the new server bound
  `[::]:5177`, so the browser silently loaded the other checkout's bundle. Use a free port and
  bind `127.0.0.1` explicitly.
- `apps/web/node_modules` in the main checkout contains a `node_modules -> …/apps/web/node_modules`
  self-symlink. Copied into a worktree it resolves to the main checkout and loads a second React,
  which fails as "Invalid hook call". Delete it in the copy.
