# Quickstart: Specialized Workspace Views

## Focused proof

```bash
.venv/bin/pytest -q packages/reality-core/tests/test_application_catalog.py packages/reality-core/tests/test_http_boundary.py
cd apps/web
npm run format:check
npm run test:i18n
npm run build
npm run i18n:audit
```

Expected: classifications compose deterministically; bounded reads enforce membership, allowlisting, paging, and search; every workspace shows at most five direct Views; `More views` searches the complete set; specialized routes render readable tables.

## Acceptance walkthrough

1. In Order Operations, find Orders, Fulfillment blockers, and Supply & demand through `More views`.
2. In Warehouse Operations, find Warehouse Queue and the shared specialized Views.
3. Verify empty, populated, loading, no-results, paging, and error states.
4. Verify a bookmarked specialized route works with another workspace preference.
5. Verify Tenant usage and Price resolution do not appear.
6. Verify no mutation occurs and trace identifiers remain available.

## Full gates

```bash
make spec-check
make lint
make test
make web-build
```

Final results are recorded after implementation. Red checks mean incomplete.

## Implementation evidence — 2026-09-03

- Direct-View limit amendment: the focused frontend contract failed only on the expected `DIRECT_VIEWS = 5` assertion before implementation (14 passed, 1 failed).
- Direct-View limit verification: 15/15 focused navigation contracts passed; formatting, production build, spec policy, and diff checks passed. The existing production chunk-size warning remains unchanged.
- Intended failing proof: three frontend contracts failed for missing classification, launcher, and bounded client before implementation.
- Focused catalog/HTTP proof: 30 passed.
- Product Web: 58/58 contracts passed; formatting passed; production build passed with the existing chunk-size warning; strict i18n passed at 815/815 for English, German, Dutch, and Spanish.
- Lint and diff checks passed.
- Complete backend behavior: 375 passed and 7 skipped; the sole remaining failure is the repository-wide spec-policy test caused by concurrent, out-of-scope `specs/050-docs-localization/spec.md` missing its required Language and Requirement Traceability declarations.
- `make spec-check` passed in an isolated checkout of Feature 049. The shared working tree remains blocked by the same concurrent Spec 050 issue, not by Spec 049.
- A second isolated full-suite attempt reached 371 passed and 7 skipped; its five migration-only failures were caused by the temporary worktree lacking the repository-local Alembic configuration link, not by application behavior.
- Automated desktop/mobile navigation and responsive contracts passed. Visual browser review remains open because no controllable browser was available in the execution environment.
