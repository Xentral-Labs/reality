# Specification Quality Checklist: Invoice Settlement Dates in One Read

**Purpose**: Validate specification completeness and quality before implementation
**Created**: 2026-10-11
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] Focused on user value and business needs
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Edge cases are identified
- [x] Scope is clearly bounded by Non-Goals
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] Every functional requirement maps to a test task and an implementation task
      (`tasks.md`, Requirement Coverage)
- [x] `graph_ask` was tried first and found not to be a bounded operational read (`plan.md` Research)

## Verification Evidence

| Gate | Command | Result |
|---|---|---|
| New tests observed failing first | `pytest tests/finance/test_settlement_flows.py -k "due_date or due_on"` before the change | 2 failed, `KeyError: 'due_date'` |
| Focused finance suites | `pytest tests/finance/test_settlement_flows.py tests/finance/test_fee_open_receivables.py tests/scenarios/test_catalog_finance.py` | 71 passed |
| Finance, isolation and catalog gates | `pytest tests/finance tests/tenant_isolation tests/test_application_catalog.py tests/test_tool_catalog.py tests/scenarios/test_catalog_finance.py tests/test_reporting_graph_tools.py` | all pass serially; under `-n 6` against one local PostgreSQL, 7 unrelated tests failed and each passed on a serial rerun |
| Lint | `ruff check src tests/finance --no-cache`; `ruff format --check` on changed files | pass; the full `ruff check .` with ruff 0.17.0 reports one pre-existing RUF100 in `tests/test_cost_census_serialization.py`, unchanged by this feature |
| Spec policy | `make spec-check` | passed |
| Generated docs | `make docs-generate`, then `make docs-catalog-check` | regenerated and committed; check clean |
| Complete backend suite | CI shards on the pull request | not run locally |
