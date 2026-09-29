# Quickstart: Customer Exchange

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q \
  tests/test_customer_exchanges.py \
  tests/test_customer_exchange_adapters.py \
  tests/operational_exceptions/test_derivation.py -k exchange \
  tests/scenarios/test_catalog_stock_and_returns.py \
  tests/test_business_journey_catalog.py
# completeness gates for a new tool, table and event
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

1. In a practice company, deliver and invoice an item, and record its return on the Warehouse page.
2. On the return movement row, choose **Exchange**, pick another variant, review, and confirm.
3. The replacement appears in the delivery work list. Reserve it and dispatch it.
4. The operational queue shows neither "Returned and not credited" nor "Shipped and not billed" for it. The movement explanation names the exchange.
5. Repeat with an announced return: exchange before arrival, then withdraw the announcement. "Exchange without return" appears.

## Evidence (2026-09-29)

CI on PR #259 (a2bf3d17): 24 of 24 checks green. Manual Web check on an isolated stack
(`docker compose -p reality293`, API 8100, Web 8180, own database) with the platform owner in
the bootstrap company:

1. A delivered, invoiced unit came back: the queue showed *Returned and not credited* (control).
2. *Exchange returned goods* (Warehouse, More actions) for another item: the review showed the
   returned goods, the replacement and "No money moves"; confirming recorded it.
3. The return's explanation named the exchange and the replacement delivery; the credit finding was
   gone. The replacement appeared in *Reserve stock* and *Record shipment* like any delivery; after
   shipping, neither *Shipped and not billed* nor *Returned and not credited* was reported.
4. An advance exchange against an open announcement (replacement quantity defaulted to the exchanged
   quantity), replacement shipped, announcement withdrawn: *Exchange without return* appeared with
   exchanged 1, arrived 0, unreturned 1, shipped 1 and the reference. No credit note, payment or
   refund document exists in the company.

Observations for follow-up (not blocking): the review cards show opaque item and delivery IDs
instead of names; the shared dialog title prints the tool key and says "shipment change" (as for
return dispositions); exception impacts print "1.0000" (existing formatting).
