# Validation

Use the local PostgreSQL test server on port 54329. Tests create and remove uniquely
named databases; they do not write to the application database.

From packages/reality-core:

```sh
../../.venv/bin/pytest tests/test_shopify_update_guard.py tests/test_shopify_and_explain.py tests/test_interpretation_coverage.py
```

Expected: changes after reservation, partial delivery and full delivery retain the
original operational records and quantities. Coverage reports review; duplicates and
explicit retries cannot create replacement promises. HTTP exposes the same reason.

From the repository root run make test, make lint, make spec-check, make web-build,
make site-build and make docs-build. See tasks.md for recorded verification evidence.
