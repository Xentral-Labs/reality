# Quickstart: Dunning Run and Escalation

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q \
  tests/finance/test_dunning_runs.py \
  tests/finance/test_dunning_run_adapters.py \
  tests/finance/test_commercial_edges.py \
  tests/scenarios/test_catalog_finance.py -k "dunning or N04" \
  tests/test_business_journey_catalog.py
# completeness gates for new tools, tables, events and refusals
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

1. In a practice company, set the dunning schedule on the Finance page: 7 days / 0, 14 days / 5,
   14 days / 10.
2. Post three customer invoices due at different dates in the past.
3. Prepare a dunning run for today: each invoice appears at level 1 with its days overdue;
   deselect one and confirm. Two notices are recorded; the deselected invoice is not.
4. Pay one reminded invoice, then prepare a run 14 days later: the paid invoice is gone, the
   other is proposed at level 2 with a fee of 5.
5. After level 3, hand the invoice to collection with a reason: the customer shows a delivery
   hold "Collection", and the next run lists nothing for it.
