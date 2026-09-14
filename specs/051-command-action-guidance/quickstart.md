# Quickstart: Command Action Guidance

## Automated validation

```bash
make spec-check
.venv/bin/pytest -q packages/reality-core/tests/test_application_catalog.py packages/reality-core/tests/test_http_boundary.py
cd apps/web && npm test -- --run workspace-actions-contract && npm run i18n:audit && npm run build
```

## Manual acceptance

1. Open a workspace and select More actions.
2. Confirm every result explains its business effect and any prerequisites appear on a separate `Requires` line.
3. Search using a word that appears only in an effect and confirm the action remains visible.
4. Select an action and confirm the same effect appears beneath the form title during entry and review.
5. Repeat at desktop and mobile widths in English, German, Dutch, and Spanish.

## Expected result

Users can understand what every classified Action does before selection and throughout confirmation. No mutation behavior changes.

## Verification record — 2026-09-03

- Failing proof: the new frontend contract failed because `action.description` was absent. The initial backend attempt was blocked by sandbox access to local PostgreSQL rather than product behavior.
- Focused backend after implementation: 9 passed, 24 deselected.
- Frontend contracts: 59 passed.
- Frontend formatting: passed.
- Strict localization audit: English, German, Dutch, and Spanish each passed 817/817 catalog keys with no missing or invalid values; the Action contract additionally checks every classified Command effect in all three translation catalogs.
- Production build: passed. Vite retained its existing informational bundle-size warning.
- Ruff: passed.
- Complete PostgreSQL suite: 378 passed, 7 skipped, 1 failed only because the concurrent untracked `specs/050-docs-localization/spec.md` does not yet satisfy repository spec policy.
- `make spec-check`: Spec 051 passes; the repository command remains red only for the same two incomplete Spec 050 policy requirements.
- Visual acceptance: not run because the configured in-app/external browser runtime reported that no browser was available.
