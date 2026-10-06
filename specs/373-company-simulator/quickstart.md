# Quickstart

See [simulator launch and coverage](../../packages/reality-core/scenarios/company_simulator/README.md). Run from packages/reality-core with an eligible existing owner, a configured local PostgreSQL and explicit --confirm. Use --days 1–30 and --operator prompt/delayed/idle.

Verification: pytest tests/scenarios/test_company_simulator.py tests/scenarios/test_reference_week.py, then make lint and make spec-check. Complete backend suite logs are retained under artifacts/company_simulator/.
