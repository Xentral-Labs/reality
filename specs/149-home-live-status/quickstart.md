# Verify Home activity and readiness

From the active worktree:

```sh
make lint spec-check
cd packages/reality-core
../../.venv/bin/pytest -q
```

From `apps/web`, run `npm run format:check`, `npm run test:contracts`,
`npm run i18n:audit`, and `npm run build`. Serve the built assets on port5190.
With `PLAYWRIGHT_MODULE` and `PLAYWRIGHT_EXECUTABLE` pointing to the locally installed
Playwright and Chromium, run `node scripts/home-live-browser.mjs`.
The browser uses read-only HTTP fixtures and creates no company, order or schedule.
It checks advancing activity, retention during failure, readiness recovery, hidden-tab
poll suspension, empty history, unknown health, no writes, no page errors and no
horizontal overflow across English/German/Dutch/Spanish, light/dark and mobile/desktop.

Deployment and rollback: [Home contract](../../docs/features/home-live-status.md).
Local rollout uses the existing root `.env` without exporting credentials, building
matching API/MCP/invitation-worker/scheduler/worker/web images and updating only those
services with Compose `up -d --no-deps`. No schema migration, database recreation or
remote deployment is part of this change.

## Verification evidence
Verified 2026-09-09:
- Backend: 1925 passed, 9 skipped in 477.70 seconds. Initial readiness tests failed
  on the missing module; final scoped API proof includes safe not-found handling.
- Web: build and formatting passed; 41 contracts and all four translation audits passed.
- Browser: 16 language/theme/viewport combinations passed, including advancing events,
  failure/recovery, hidden-tab suspension, empty/unknown states and a delayed old-company
  response after navigation. No writes, page errors or horizontal page overflow.
- Docs: formatting, 45 tests and production build passed. Lint/spec policy/diff checks passed.
- Matching local containers updated without a migration or data reset.
- Actual API health returned ok. A read-only transaction for the existing
  `Demo Firma 1 Live` returned 20 correctly ordered events and all three readiness
  components ready through the configured live private probes.
- Port8080 serves `index-H4Lw4eLZ.js` and `index-ChhkVqBL.css`, matching verified assets.

Local diagnostic artifacts: `/tmp/reality-home-full-final.log`,
`/tmp/reality-home-browser-isolation.log`, `/tmp/reality-home-docs.log`, and screenshots
under `/private/tmp/reality-home-browser`. These are verification artifacts, not
application storage or durable sources of business facts.

## Rolling graph refinement verification
Run `tests/test_activity_volume.py` for entity classification, duplicate suppression,
UTC boundaries, creation coverage, foreign tenancy and Sandbox HTTP admission.
`home-live-browser.mjs` now verifies the graph instead of the superseded default
list:24h/7d/30d switching, keyboard interval drilldown, advancing values, outage
retention, hidden-tab suspension, delayed old-company responses,16 localized/theme/
viewport combinations and zero writes. Artifact directory:
`/private/tmp/reality-graph-browser`. Existing earlier list evidence is historical.
Final full-suite and local runtime evidence are recorded below after completion.

Focused graph/readiness tests:15 passed. Frontend production build, formatting,
41 contracts and all four translation audits passed. Final graph browser run:
16 combinations passed, including range selection, keyboard drilldown, rising
counts, failures/recovery, hidden-tab suspension and delayed old-company response.
Docs:45 tests plus formatting and production build passed. Lint/spec/diff checks
passed. Graph screenshots use responsive SVG coordinates so axis labels and chart
height remain readable on mobile. Final complete backend suite and rollout remain
T008 until the following runtime evidence is recorded.


Final graph release verified2026-09-09:
- Frozen-source full backend suite:1929 passed,9 skipped in382.68seconds.
- Final16 browser combinations,41 web contracts,4 localization audits, formatting,
  production web build,45 docs tests/docs build, lint/spec/diff checks passed.
- Matching local API/MCP/background/web images updated without migration/data reset.
- Real read-only demo validation returned1441 source buckets and223 recorded entities.
  The newest nonempty bucket's16 records matched its detail total exactly. All three
  readiness components were ready. These counts are observations, not fixed fixtures.
- Port8080 assets:`index-DMpMpUy1.js`, `index-DRLs5dBP.css`.
- Evidence:`/tmp/reality-graph-full-final.log`, `/tmp/reality-graph-browser-final.log`,
  `/tmp/reality-graph-web-final.log`, `/tmp/reality-graph-docs.log`; reviewed screenshots
  under`/private/tmp/reality-graph-browser`.


Hover summary correction verified 2026-09-09:
- Idle, first-bar hover, last-bar hover and pointer leave preserve the exact summary height.
- All 16 language/theme/viewport browser combinations passed against the pinned Docker image; 43 frontend contracts, localization audit, formatting and production build passed.
- Both summary states share a grid cell; the inactive state reserves layout space and is hidden from assistive technology. Count widths and narrow-chart date layout prevent content-dependent wrapping. Decorative Now markers do not intercept bar interaction.
- Frontend-only correction: no API, database or business-rule changes.
- Local 8080 serves tested image `reality-web:hover-summary-20260909` with assets `index-BHh9axz-.js` and `index-BBt5dvwI.css`.
- An isolated source copy at `/private/tmp/reality-hover-release` was used because the active checkout was being edited concurrently. Its `compose.hover.json` pins the image; only web was recreated.
- Evidence: `/tmp/reality-hover-pinned-browser.log`, `/tmp/reality-hover-final-contracts.log`, `/tmp/reality-hover-final-i18n.log`, `/tmp/reality-hover-final-format.log`.


Range preference release (2026-09-09): FR-008 now defaults to 24 hours; FR-012 remembers explicit selection under an opaque user-scoped browser key, across reload and company navigation. Invalid/blocked storage safely falls back, without disabling range changes. Browser regression first failed with 30 instead of 1 day. Final full 16-case graph matrix and focused 16-case image matrix passed, including user isolation and storage failure acceptance. Frontend production build, 43 contracts, localization audit, formatting, spec and diff checks passed. No backend behavior or schema changes.
Local web image: `reality-web:activity-range-20260909`, assets `index-BoeiTI5R.js` / `index-BBt5dvwI.css`; only web recreated. Build snapshot and pinning override: `/private/tmp/reality-range-release/compose.range.json`. Logs: `/tmp/reality-range-red.log`, `/tmp/reality-range-browser.log`, `/tmp/reality-range-image-browser.log`, `/tmp/reality-range-contracts.log`, `/tmp/reality-range-build.log`. Review: requirement/test mapping complete, no critical findings; browser-local scope documented explicitly, without promising device synchronization.
