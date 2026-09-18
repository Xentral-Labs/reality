# Validation

Use repository PostgreSQL test setup. Run:

```sh
cd packages/reality-core
../../.venv/bin/pytest tests/test_order_journey.py
cd ../../apps/web
node --test scripts/order-journey-layout.test.mjs
npm run test:contracts
npm run build
```

Run `npm run test:journey-browser` with the same PLAYWRIGHT_MODULE, PLAYWRIGHT_EXECUTABLE and Vite server setup as existing browser suites. It must prove order selection, grouped members, Inspector action, partial history, stale-order reads, retries and mobile containment. Then run repository lint, full pytest, web-build and spec-check gates.

Manual review: open Business Graph, fit latest activity, select a sales order, compare linked reservation/movement history with the existing Inspector, switch time range, load older events, inspect evidence, use keyboard, test 390px and 1440px. Never interpret loaded counts as company totals or current state as historical state.
