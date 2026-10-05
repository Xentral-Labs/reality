# Validation

Run `make spec-check`, `make lint`, `make test`, `make docs-generate`,
`make docs-catalog-check`, `make web-build`, `make docs-build` and the Web browser suite.
Targeted PostgreSQL proof: `cd packages/reality-core && ../../.venv/bin/pytest -q
 tests/test_default_operational_cases.py tests/test_operational_case*.py tests/test_case*.py`.
Apply migration 0145 before starting the matching application, scheduler and worker.
Check `/operational-cases/status`: enabled with complete coverage only after bounded
rollout and consumer completion. No owner enable action is needed. Internal runs show
no user actor; historical owner adoption remains in its original table.
Do not downgrade populated responsibility/rollout history or deploy through this task.
