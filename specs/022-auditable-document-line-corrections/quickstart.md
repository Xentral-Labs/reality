# Quickstart: Validate Manual Document-Line Corrections

## Focused backend proof

```bash
cd packages/reality-core
pytest -q tests/test_document_corrections.py tests/test_master_data_api.py
```

Expected: add/update/remove, exact audit with actor-context coverage, forced event-failure
rollback, protected Reality, external Source, stale edit, current-state no-op, rejected
repeated ID-less addition, API, and tenant cases pass.

## Catalog and invariant proof

```bash
cd packages/reality-core
pytest -q tests/test_application_catalog.py tests/test_operational_fields.py tests/tenant_isolation
ruff check .
```

Expected: the Web/API command and isolation operation are registered, and no Document
operational field is introduced.

## Web proof

```bash
cd apps/web
npm run build
npm run i18n:audit
npm run test:i18n
```

Manual acceptance:

1. Create a manual Document with two lines.
2. Correct one description, remove one line, add another, and save.
3. Reopen and verify current values and retained IDs; inspect one correction event.
4. Link Reality and verify economic correction fails while description-only correction succeeds.
5. Save from two sessions and verify a stale divergent second save requests reload.
6. Compare the Web request/result with the API contract for the same snapshot and record
   that both show the same resulting lines, revision, conflict, and guidance semantics.

## Full regression

```bash
cd packages/reality-core
pytest -q
```

Only after every gate passes may `006/FR-008` and the coverage matrix become verified.

## Observed validation — 2026-08-31

- Focused correction, API, catalog, and isolation suites: PASS.
- Ruff: PASS.
- Complete PostgreSQL backend suite: PASS — 205 passed, 7 skipped.
- Spec policy: PASS.
- Web production build: PASS; only the pre-existing Vite chunk-size advisory remains.
- Localization audit: PASS — 775/775 entries covered in EN, DE, NL, and ES.
- Localization contract tests: PASS — 9 passed.
- Schema/rollback review: PASS — no model, Alembic, or migration file changed.
- `006/FR-008` baseline closure: recorded after all automated gates passed.
- Manual Web/API parity: PASS — verified by the product owner on 2026-08-31 against the
  final local containers at `http://localhost:8080/`.
- Final owner review: APPROVED on 2026-08-31.
