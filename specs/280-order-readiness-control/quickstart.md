# Quickstart: Order Readiness Control

## Focused validation

```bash
.venv/bin/pytest -q packages/reality-core/tests/test_materialized_projections.py packages/reality-core/tests/test_unified_orders_api.py packages/reality-core/tests/test_fulfillment_readiness.py
cd apps/web && npm run test:i18n && npm run i18n:audit && npm run build
```

## Browser story

Open Sales → Readiness with ready, partial-stock and unpaid-prepayment orders. Verify exact blockers,
line quantities, payment evidence, freshness warning and Document/Commitment Inspector links at
390px and 1440px. No interaction before an explicit reviewed action may issue a mutation request.

## Verification record (2026-09-26)

- Web production build passed.
- All 402 Web contract tests passed.
- English, German, Dutch and Spanish localization audits passed.
- 99 focused PostgreSQL projection, HTTP-boundary and incremental-derivation tests passed.
- `make lint`, `make spec-check` and `make docs-catalog-check` passed.
- Interactive browser execution remains open because no browser surface was available in the session.
