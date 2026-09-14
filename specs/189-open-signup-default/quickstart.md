# Validation

Use the repository virtual environment and disposable PostgreSQL test database.
Run make spec-check, make lint, make test, make web-build, make site-build and
make docs-build. Record actual results here after execution.

Focused proof: tests/test_access_admission.py, tests/test_user_access.py and
 tests/test_platform_admin_overview.py. Verify unset/blank, zero and finite modes,
replay and transitions; no remote service changes are part of these tests.

## Evidence

- Initial policy regression proof: unset/blank and unlimited-to-finite tests failed against the old implementation as expected.
- Focused admission/access/admin suite: 31 passed; additional concurrency/default/admin run: 23 passed.
- `make lint`: passed after import formatting.
- `make spec-check`: passed after registering the new test family in the coverage matrix.
- `make web-build`: passed; 152 tests; all four language audits passed (1,803 strings each).
- `make site-build`: passed; 62 tests; all four language audits passed (480 strings each).
- `make docs-build`: passed; four generator tests, 67 Node tests, complete documentation build. Generated catalog output has no diff.
- Full backend suite: `pytest -n 4` passed with 2,460 passed, 9 skipped and one SQLAlchemy transaction-cleanup warning in 476.99 seconds, using separate disposable PostgreSQL databases. The initial serial run was interrupted after 200 passing tests to use the existing parallel test support.
- Browser visual check was not completed: Chrome was actively being changed by the user; no live deployment or account was modified.
- Existing non-fatal frontend bundle-size warnings remain.
