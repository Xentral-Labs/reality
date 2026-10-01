# Quickstart: Reorder Point and Replenishment Proposal

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q -p no:randomly \
  tests/test_reorder_points.py tests/test_reorder_point_reached.py tests/test_reorder_point_adapters.py \
  tests/test_migrations.py tests/operational_exceptions tests/scenarios/test_catalog_purchasing.py \
  tests/test_business_journey_catalog.py tests/test_application_catalog.py tests/test_reference_integrity.py
cd ../.. && make docs-generate && make docs-catalog-check && make spec-check lint
cd apps/web && npm run -s test:i18n && npm run -s i18n:audit && npm run build
```

## Manual check

Set up an item bought in cartons of 12 with one supplier on a purchase price list, stocked in two locations: 12 in Hamburg and 100 in Munich.

1. On the item, set a reorder point of 20 and a quantity of 48 for Hamburg, through the review. Do the same for Munich.
2. Exceptions shows "Meldebestand erreicht" for Hamburg only. It states 12 available, 0 incoming, 4 cartons proposed, and the supplier and price.
3. "Prepare purchase order" opens the order form prefilled. Confirm it: the entry disappears and the purchase shows 4 cartons, 48 pieces open.
4. Add a second supplier to a purchase list for the item and set Munich's point above its stock: the entry names no supplier and says that several price it.
5. Remove Munich's point through the review: its entry disappears.
