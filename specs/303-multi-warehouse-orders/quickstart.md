# Quickstart: Orders Served From Several Warehouses

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q -p no:randomly \
  tests/test_multi_warehouse_reservations.py tests/test_stock_in_another_location.py \
  tests/test_multi_warehouse_adapters.py tests/test_fulfillment_readiness.py tests/test_shipments.py \
  tests/operational_exceptions tests/scenarios/test_catalog_orders_and_shipments.py \
  tests/test_business_journey_catalog.py tests/test_application_catalog.py
cd ../.. && make docs-generate && make docs-catalog-check && make spec-check
cd apps/web && npm run -s test:i18n && npm run -s i18n:audit && npm run build
```

## Manual check

Set up an item with 6 in Hamburg and 40 in Munich, and a customer order for 10 at Hamburg.

1. Reserve the order: 6 are reserved in Hamburg. "Bestand in anderem Lager" names Munich with 40 available.
2. From the finding, "Dort reservieren" reserves 4 in Munich through the review. The finding clears, and the delivery is ready with reservations in both warehouses.
3. Ship Hamburg's 6 as one package and Munich's 4 as another: the promise is fulfilled.
4. A second order for 5 at Hamburg with Hamburg empty: "Umlagerung vorbereiten" moves 5 from Munich. The finding clears after the transfer, and the order reserves at home.
5. Reserving at a location without stock is refused with its reason.
