# Quickstart: Shop Order Changes and Refunds

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q \
  tests/test_shop_order_changes.py tests/test_shop_refunds.py tests/test_order_line_items.py \
  tests/test_shop_order_change_adapters.py \
  tests/test_shopify_update_guard.py tests/test_shopify_and_explain.py \
  tests/scenarios/test_catalog_sources.py tests/test_business_journey_catalog.py
PYTHONPATH=src ../../.venv/bin/python -m pytest -q \
  tests/test_application_catalog.py tests/test_tool_catalog.py tests/test_refusal_gate.py \
  tests/tenant_isolation tests/operational_exceptions tests/test_reference_integrity.py
cd ../..
make docs-generate && make docs-catalog-check   # after staging
make spec-check lint
cd apps/web && npm run i18n:audit
```

## Manual check

1. Ingest a Shopify order with two lines, reserve one.
2. Send a version lowering one line: the promise is revised and cites the version.
3. Send a version raising a line: it waits with `quantity_increased`; nothing changes.
4. Ship a line, send a refund with restock `return`: a `sales_refund` document appears on the order
   and a return announcement waits for the goods.
5. Send `cancelled_at` after shipment: it waits with `cancelled_after_shipment` and names the
   return announcement as the next step.
6. Ingest an order with an unknown SKU: known lines are promised; the unknown line is reported and
   gets its promise once an item is assigned.
