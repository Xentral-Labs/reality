# Validation

Use local PostgreSQL test setup from `docs/TEST_STRATEGY.md`. Run `cd packages/reality-core && ../../.venv/bin/pytest tests/test_operational_previews.py`, then repository `make test lint spec-check web-build docs-catalog-check`. Run the preview Playwright script against local Vite with PLAYWRIGHT_MODULE and PLAYWRIGHT_EXECUTABLE configured. Inspect sales/purchase orders, partial fulfillment, stock, reservations/movements, shipments, invoices/payments/journal at desktop and 390px. Confirm history labels, zero/missing values, full explanation and no writes.
