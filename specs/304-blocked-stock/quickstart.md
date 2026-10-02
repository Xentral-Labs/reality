# Quickstart: Blocked Stock and Best-Before Dates

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q -p no:randomly \
  tests/test_stock_blocks.py tests/test_stock_block_readers.py tests/test_stock_block_adapters.py \
  tests/test_inventory_tracking_reservations.py tests/operational_exceptions \
  tests/scenarios/test_catalog_stock_and_returns.py tests/test_business_journey_catalog.py
cd ../.. && make docs-generate && make docs-catalog-check && make spec-check
cd apps/web && npm run -s test:i18n && npm run -s i18n:audit && npm run build
```

## Manual check

1. 20 in stock: block 5 for quality from the warehouse view. Available shows 15 and blocked 5 with the reason, and a reservation of 20 gets 15.
2. Release 3 of the 5: available 18, blocked 2.
3. Receive 10 with "of which blocked 4, damage": 4 are blocked. Scrap them: stock falls by 4 and the block is closed.
4. An expired lot shows "Stock expired". "Block" from the finding blocks it, and the finding clears.
