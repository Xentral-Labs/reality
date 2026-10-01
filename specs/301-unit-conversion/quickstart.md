# Quickstart: Unit Conversion Between Purchase and Stock Units

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q -p no:randomly \
  tests/test_purchase_units.py tests/test_purchase_unit_adapters.py tests/test_migrations.py tests/finance \
  tests/scenarios/test_catalog_purchasing.py tests/operational_exceptions tests/test_item_oversold.py \
  tests/test_business_journey_catalog.py tests/test_application_catalog.py tests/test_reference_integrity.py
cd ../.. && make docs-generate && make docs-catalog-check && make spec-check lint
cd apps/web && npm run -s test:i18n && npm run -s i18n:audit && npm run build
```

## Manual check

1. An item in pieces, bought in cartons of 12. Order 5 cartons: the purchase shows 5 cartons and 60 pieces open.
2. Receive 5 cartons in the receipt form: the review shows 60 pieces, stock rises by 60, and the receipt shows `5 box (60 pcs)`.
3. A supplier invoice for 5 cartons reports nothing, neither "billed not received" nor "received not billed".
4. A receipt in pallets is refused with its reason.
