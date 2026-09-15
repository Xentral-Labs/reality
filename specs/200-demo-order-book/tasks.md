# Tasks: Demo order book spreads across customers

1. Extend the scenario suite first: distinct buyers, concentration bound, comparison
   family consistency, invoice and credit-note party, three suppliers, stable mapping.
2. Author the vocabulary in `demo/international.py`: full `CUSTOMERS` pool, derived
   `DEMO_DATA_CUSTOMERS`, `ORDER_CUSTOMERS`, `WEEKLY_CUSTOMERS`, `SUPPLIER_ITEMS`.
3. Resolve the buyer per order in `services/demo_profile.py` for order, invoice,
   credit note and `external_customer_reference`; seed the full pool.
4. Update the pinned party count and the stated customer counts in the profile
   contract and the company setup/demo feature documentation.
5. Run the focused suites, then the full PostgreSQL pytest run; record verification.
