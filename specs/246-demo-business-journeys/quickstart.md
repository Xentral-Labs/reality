# Quickstart: Complete Demo Business Journeys

1. Create a fresh canonical demo company.
2. Run `pytest -q packages/reality-core/tests/scenarios/test_international_demo.py`.
3. Inspect the stable references listed in `docs/features/demo-data-catalog.md` across
   Sales, Purchasing, Warehouse and Finance.
4. Confirm every document has a document date, completed credits have the expected
   remaining balance, and deliberately open journeys appear as exceptions.
5. In Finance, verify `SPAY-002` closes `SINV-002` with a separate
   EUR 1 reduction, `CPAY-009` and `SPAY-005` retain EUR 10 available credit,
   and `CPAY-006` closes its invoice through a separate EUR 0.50
   accepted-small-remainder adjustment.
6. Verify visible numbers use their canonical type family (`ITEM-`, `SO-`, `PO-`,
   `INV-`, `SINV-`, `CN-`, `SCN-`, `CPAY-`, `SPAY-`) and that every catalog table
   includes an exact UI path under **How to find it** / **So findest du es**.

Verified locally on 2026-09-21:

- `tests/scenarios/test_international_demo.py`: 10 passed.
- `tests/finance/test_adjustments.py`: 18 passed, including migration coverage.
- `tests/test_company_setup_initialization.py` plus profile history: 15 passed after
  updating the intentional version-5 document count and source-reference assertions.
- `make spec-check`, Ruff, `git diff --check`, `make docs-catalog-check` and the Docs
  production build passed.
- The rebuilt local stack serves the German guide on port 8083 with all four exact
  payment references and the “So findest du es” UI-navigation column.
