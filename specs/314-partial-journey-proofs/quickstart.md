# Quickstart: Journey Proof Stories, Round Three

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q -p no:randomly \
  tests/test_movement_reasons.py tests/test_payment_candidates_reference.py tests/test_shop_line_gaps.py \
  tests/scenarios/test_catalog_stock_and_returns.py tests/scenarios/test_catalog_purchasing.py \
  tests/scenarios/test_catalog_sources.py tests/test_business_journey_catalog.py \
  tests/operational_exceptions tests/test_migrations.py tests/test_shop_order_changes.py
cd ../.. && make docs-generate && make docs-catalog-check && make spec-check lint
```

## Guide check

Ask the Guide in English and German and expect the promoted journey:

- F04: "a return arrived without an announcement" / "Retoure ohne Anmeldung eingegangen"
- F08: "refund paid before the goods came back" / "Erstattung vor Eingang der Retoure"
- H09: "stock arrived without a purchase order" / "Wareneingang ohne Bestellung"
- P02: "payment arrived before the order" / "Zahlung kam vor dem Auftrag"
- P05: "shop order without a price" / "Shop-Bestellung ohne Preis"
- P08: "open orders at go-live" / "offene Aufträge bei Go-live"
