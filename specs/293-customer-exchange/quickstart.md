# Quickstart: Customer Exchange

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q \
  tests/test_customer_exchanges.py \
  tests/test_customer_exchange_adapters.py \
  tests/operational_exceptions/test_derivation.py -k exchange \
  tests/scenarios/test_catalog_stock_and_returns.py \
  tests/test_business_journey_catalog.py
# completeness gates for a new tool, table and event
PYTHONPATH=src ../../.venv/bin/python -m pytest -q \
  tests/test_application_catalog.py tests/test_tool_catalog.py \
  tests/test_reporting_graph_coverage.py tests/test_schema_indexes.py \
  tests/test_refusal_gate.py tests/test_migrations.py tests/tenant_isolation \
  tests/test_agent_command_parity.py tests/test_capability_catalog.py tests/test_action_discovery.py
cd ../..
make docs-generate && make docs-catalog-check   # after staging
make spec-check lint
cd apps/web && npm run i18n:audit && node --test scripts/action-discovery.test.mjs
```

## Manual check (Web)

1. In a practice company, deliver and invoice an item, and record its return on the Warehouse page.
2. On the return movement row, choose **Exchange**, pick another variant, review, and confirm.
3. The replacement appears in the delivery work list. Reserve it and dispatch it.
4. The operational queue shows neither "Returned and not credited" nor "Shipped and not billed" for it. The movement explanation names the exchange.
5. Repeat with an announced return: exchange before arrival, then withdraw the announcement. "Exchange without return" appears.
