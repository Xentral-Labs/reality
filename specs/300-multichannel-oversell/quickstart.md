# Quickstart: Multichannel Oversell, Deadlines and Peak Intake

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q -p no:randomly \
  tests/test_item_oversold.py tests/test_deadline_due_soon.py tests/test_peak_intake_benchmark.py \
  tests/scenarios/test_catalog_orders_and_shipments.py tests/operational_exceptions \
  tests/test_business_journey_catalog.py tests/test_application_catalog.py tests/test_reference_integrity.py
cd ../.. && make docs-generate && make docs-catalog-check && make spec-check lint
cd apps/web && npm run -s test:i18n && npm run -s i18n:audit && npm run build
```

## Measurement

On a quiet machine and a disposable database, run the benchmark from `contracts/findings-and-benchmark.md`:
- with `--processes 1`, then `--processes 4`;
- record both in `results.md`.

## Manual check

1. Order 6 of an item with 4 in stock from the shop and 2 from a second channel, plus 1 more from the shop. "Artikel überverkauft" names both channels with a shortfall of 3.
2. A purchase order for 3 clears it.
3. An order of the second channel promised tomorrow and fully reserved shows "Liefertermin gefährdet". Shipping clears it.
