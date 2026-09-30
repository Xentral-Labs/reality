# Quickstart: Automatic Credit Hold

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q -p no:randomly \
  tests/test_credit_exposure.py tests/test_credit_hold.py tests/test_credit_hold_adapters.py \
  tests/scenarios/test_catalog_finance.py tests/operational_exceptions \
  tests/test_unified_customer_holds.py tests/test_business_journey_catalog.py \
  tests/test_application_catalog.py tests/tenant_isolation tests/test_refusal_gate.py
cd ../.. && make docs-generate && make docs-catalog-check && make spec-check lint
cd apps/web && npm run -s test:i18n && npm run -s i18n:audit && npm run build
```

## Manual check

1. Give a customer a credit limit of 1,000 and post an invoice of 700, due last month.
2. Enter an order of 400. On the Attention page, the order is held, and the hold names the limit, the 700 overdue, the 400 ordered and the exposure of 1,100.
3. As a member who is not an owner, releasing is not offered; the tool refuses.
4. As the owner, release it with the reason "Paid by bank transfer today, confirmed by phone". The order can be reserved and shipped.
5. Enter an order of 200 for a customer with room under the limit: nothing is held.
