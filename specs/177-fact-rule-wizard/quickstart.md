# Validation

Run `make spec-check`, `make lint`, `make test`, `make site-build`, `make web-build`,
`make docs-catalog-check`. In `apps/web`, run `npm run test:contracts` and
`npm run i18n:audit`. Serve the web app with its existing Vite dev server; set
`BASE_URL`, `PLAYWRIGHT_MODULE`, `PLAYWRIGHT_EXECUTABLE` for the repository browser
harness and run `node scripts/fact-rule-wizard-browser.mjs` and
`node scripts/guided-rules-browser.mjs`.

Expected: five stages with no navigation writes; every real write reviewed; source
identity/value retained; draft saved before simulation; edits invalidate test state;
activation confirmed and no historical replay; closing/reopening preserves only saved
milestones. Inspect desktop and 390px screenshots, focus and four language variants.
Fixtures intercept business calls so validation does not change a real company.
