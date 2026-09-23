# Quickstart: Validate Live Demo Cost Readiness

## Prerequisites

- PostgreSQL-backed local stack with API, Web, scheduler and worker from the same
  revision.
- An authenticated owner account eligible to create a Sandbox.
- No manual cost refresh during the acceptance run.

## Automated proof

```bash
make spec-check
.venv/bin/pytest -q packages/reality-core/tests/test_demo_costing_profile.py
.venv/bin/pytest -q packages/reality-core/tests/test_company_setup_jobs.py
.venv/bin/pytest -q packages/reality-core/tests/test_demo_data_intake.py
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

## Fresh-company story

1. Create a new Sandbox using `international_demo` with live simulation enabled.
2. Observe Company created, profile preparation, calculation and Ready in the setup
   dialog. Do not press a Finance refresh control.
3. When ready, enumerate all items with positive physical stock through the shared
   Warehouse/API read. Each must be current, have a positive acquisition basis and an
   explanation linked to retained evidence.
4. Enumerate the profile's declared contribution lines. Each must have current DB1 and
   DB2 with received revenue, consumed acquisition cost and selling-cost explanation.
5. Sample at least three inventory scopes and three contribution lines through Web and
   MCP. Compare opaque identity, value, unit/currency, cutoff, freshness and reason.

## Live-cycle story

1. Record the current event cutoff and allow one order/settlement cycle to complete.
2. Confirm retained scopes whose physical and reviewed-cost evidence did not change stay
   current without a manual refresh.
3. Add one relevant movement and withdraw one selling-cost attribution in a test fixture;
   confirm current reads become stale/unavailable while historical reviewed results stay
   addressable.
4. Replay the intake request and confirm no duplicate source, movement, review, financial
   posting or source-control transition.

## Failure and isolation story

1. In a test fixture, remove one required acquisition-evidence link before readiness.
   Setup must fail with a bounded evidence diagnostic and no trusted zero.
2. Retry with restored evidence; the same company receipt completes without duplicating
   setup or restarting a later-paused source.
3. Submit a foreign tenant's scope identity to the costing read service. It must behave
   as not found and reveal no foreign details.
4. Verify an existing historical demo tenant is unchanged by deployment.

## Recorded evidence (2026-09-22)

- PostgreSQL setup initialization suite: 14 passed in 141.65 seconds.
- Demo Data intake/settlement suite: 15 passed in 52.32 seconds.
- Fresh-profile Web/shared-tool/MCP parity: three inventory and three contribution
  scopes passed with byte-equivalent response envelopes.
- Production Web build, setup-progress contract, Spec policy, formatting and the four
  locale audits passed.
- `company-setup-live-browser.mjs` exercised the real stack at `localhost:8080` with
  API `:8000`, MCP `:8001`, docs `:8083`, PostgreSQL scheduler and worker. It retained
  the completed calculation before Ready and observed:
  `calculation:current`, `calculation:done`, `ready:waiting`, `ready:current`.
- The visible dialog measured `576 x 529` at `(432, 235.5)` in a `1440 x 1000`
  viewport: exact horizontal and vertical centering. Screenshots are retained under
  `/private/tmp/reality-251-browser/` for local review.
- Operational recovery proof: a worker still running the prior profile contract first
  refused profile version 12; after replacing worker/scheduler from the same revision,
  the retained request retried the same company and completed without a second setup
  identity. A loaded worker also produced one `handler_timeout`; its retry completed
  with the same run and prior state preserved.
