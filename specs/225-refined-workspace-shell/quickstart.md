# Validation

Install the existing web dependencies and provide the repository PostgreSQL test
configuration for backend gates. Start Vite on an isolated port, e.g. 5225.

```sh
gmake spec-check
gmake lint
gmake web-build
gmake docs-catalog-check
UNIFIED_BASE_URL=http://localhost:5225 PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node apps/web/scripts/refined-shell-browser.mjs
```

Also run collapsible-navigation, live-simulation-header and page-title-counts browser
scripts with the same environment. Inspect captured desktop/rail/mobile screenshots
in light/dark themes; verify menus are not clipped, chat starts at y=0 on desktop,
and long labels fit. Fixture data proves UI behavior only, not business effects.

Backend tests follow `scripts/ci_backend_changes.py`; this feature has no backend-affecting paths.
The optional backend run and its timeout recheck are documented in verification.md.
