# Verification

## Passed
- `make lint` and `make spec-check`.
- `make web-build`: formatting, TypeScript/Vite build and four-language audit
  (1,843/1,843 strings in each language). Final `npm run test:i18n`: 167 passed.
- `make docs-build`: four generator tests, 67 documentation tests, formatting and
  VitePress build. `make docs-catalog-check`: generated vocabulary remains current.
- Chromium `apps/web/scripts/storyline-browser.mjs`: existing library/scripted flow,
  proposal confirmation, restart, autoplay and pause, plus Free Play draft handoff,
  no automatic writes, exactly one explicit send, lazy reply evidence and reload
  without resending. 32 layouts cover en/de/nl/es, light/dark and 390/1440px.
- Visually inspected Free Play German desktop dark and mobile light screenshots.
  Evidence is readable, the composer remains usable and no horizontal overflow occurs.
- `git diff --check`.

## Full backend suite
`PYTEST_ADDOPTS="-n 4 --dist worksteal --durations=15" make test`: **2,518 passed,
9 skipped, 1 warning**, in 375.67s. This includes all five new chat evidence tests.
The warning is the existing transaction-cleanup warning in
`test_storyline_library_api.py::test_a_chapter_is_prepared_confirmed_and_explained_over_http`.

## Test boundaries
Browser tests use deterministic HTTP fixtures. Backend tests replace only the LLM
provider transport, invoking real application tools and PostgreSQL. They do not call
an external model or mutate a live company. Production needs its existing configured
chat provider and allowance; this change introduces neither credentials nor a provider.

The first endpoint proof failed with 404 before implementation. The focused suite
then exposed a missing test import, which was corrected. An existing browser pause
assertion was moved before chapter navigation so it observes the pause control before
that navigation changes the selected chapter; the complete browser run then passed.
Temporary source-shape checks were replaced by behavioral browser assertions.

Builds report existing bundle-size notices. No schema migration or deployment is
included. Review conclusions are in analysis.md.

## Focus correction (FR-006)
The browser regression first failed waiting for input focus after a failed Enter
send. The shared input now remains read-only while busy, and ChatPage restores
focus after an explicit send settles, including session remounts. Deliberate focus
on another control is preserved. Both `unified-chat-composer-browser.mjs` and the
complete `storyline-browser.mjs` passed on the final code. `make web-build` (167
tests, locale audit, TypeScript/build), spec policy and diff checks passed.
No backend behavior changed, so the recorded full backend result remains applicable.
The built frontend was copied to the local 8080 preview; the served asset hash and
health endpoint were verified. No production deployment.
