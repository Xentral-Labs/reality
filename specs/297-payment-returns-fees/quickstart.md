# Quickstart: Chargebacks, Returned Direct Debits and Payment Fees

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q \
  tests/finance/test_payment_returns.py tests/finance/test_payment_return_adapters.py \
  tests/finance/test_settlement_flows.py tests/scenarios/test_catalog_finance.py \
  tests/test_business_journey_catalog.py
PYTHONPATH=src ../../.venv/bin/python -m pytest -q \
  tests/test_application_catalog.py tests/test_refusal_gate.py tests/tenant_isolation \
  tests/test_migrations.py tests/test_schema_indexes.py tests/operational_exceptions \
  tests/test_reference_integrity.py
cd ../.. && make docs-generate && make docs-catalog-check && make spec-check lint
cd apps/web && npm run i18n:audit && npm run build
```

## Manual check

1. Post an invoice of 100 and a customer payment of 100.
2. On the payments list, record "Payment returned": direct debit return, fee 3.50 charged on.
3. The invoice is open again and names the return; "Payment returned" is on the Attention page;
   the customer owes the fee as its own charge.
4. Pay the invoice again: the finding clears.
5. Record a payment of 97 for an invoice of 100 with a payment fee of 3: the invoice is settled.
