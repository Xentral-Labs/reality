# Quickstart: Invoiced Not Shipped, Down-Payment and Pro-Forma Invoices

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q -p no:randomly \
  tests/test_down_payments.py tests/test_proforma_invoices.py tests/test_billed_not_shipped.py \
  tests/test_billing_document_adapters.py tests/scenarios/test_catalog_finance.py \
  tests/test_fulfillment_readiness.py tests/operational_exceptions tests/test_migrations.py \
  tests/test_business_journey_catalog.py tests/test_application_catalog.py tests/tenant_isolation
cd ../.. && make docs-generate && make docs-catalog-check && make spec-check lint
cd apps/web && npm run -s test:i18n && npm run -s i18n:audit && npm run build
```

## Manual check

1. A prepayment order of 1,000: record a down-payment invoice of 300 and pay it. Readiness shows 300 received and 700 required.
2. Record the final invoice: the paid 300 is proposed. Confirm it; the final invoice is open for 700.
3. Pay 700. The order is ready to ship.
4. Invoice 5 of another order line before shipping. "Invoiced but not shipped" lists it on the Attention page and in the month-end billing section; ship 5 and it clears.
5. Record a pro-forma for an order: it appears on the order, with no open item.
