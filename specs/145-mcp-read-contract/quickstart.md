# Validation Guide

Use Python 3.12+, project dependencies and the repository temporary PostgreSQL test database service on localhost:54329. From packages/reality-core run `python -m pytest tests/test_mcp_read_contract.py tests/test_agent_discovery.py -q`, then the complete `pytest -n 2 --dist loadscope` suite and `ruff check .`. From root run `make spec-check`. Run frontend and docs quality commands declared in .github/workflows/quality.yml; regenerate MCP reference after schema edits.

On a separately authorized tenant, call inventory_read with view=location and a known location_id; records show local stock/unit. Follow business_records_discover.next_cursor with the same family/query until has_more=false. Read finance_balances.balances per currency. Explain a retained closed order by document ID. These are read calls, but authentication telemetry may persist. No deployed tenant or mutation is required for local automated proof.
