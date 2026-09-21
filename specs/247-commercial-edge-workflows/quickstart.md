# Quickstart: Commercial Edge Workflows

## Prerequisites

Apply migrations and start PostgreSQL, API, worker, web and docs. Create a fresh international live-demo company and wait until setup reports ready.

## Validation journeys

1. Record the documented level-2 reminder with a EUR 5 fee; inspect invoice, notice, charge, balance and source.
2. Accept the documented partial bad debt; inspect the remaining aging amount, then reverse it.
3. Clear the documented customer deposit partially and fully into its final invoice; repeat for the supplier case and inspect excess credit.
4. Inspect an order revised from ten to twelve and fulfilled with twelve; verify twelve is refused on an unrevised control order.
5. Follow English and German demo guidance without a manual finance refresh.

## Required checks

```bash
make spec-check
make lint
make test
make web-build
make docs-catalog-check
cd apps/web && npm run i18n:audit
```

Expected: all gates pass; every mutation is confirmed and tenant-scoped; documented references resolve to stated records and amounts.
