# Quickstart

From packages/reality-core, configured local PostgreSQL and an active admitted owner:

```sh
../../.venv/bin/python -m scenarios.company_simulator.controller --actor-id OWNER --confirm --days 30
../../.venv/bin/python -m scenarios.company_simulator.controller --actor-id OWNER --confirm --profile shopify --days 30
```

See [controller/profile map and supervision contract](../../packages/reality-core/scenarios/company_simulator/README.md). Complete/Shopify profiles create ordinary named local test companies; operational uses the original Sandbox. No external provider/mail connection is made.

Acceptance includes prompt/delayed/idle/wrong-destination company comparisons, credit/refund checkpoints, exact-review boundaries, private future isolation, exogenous Shopify payouts and unmatched-vs-unallocated balances. Logs/XML and retained comparison reports are stored in artifacts/company_simulator/.

The default complete-v2 run also records local customer/supplier threads and baseline replies. Open the separate viewer to inspect them. A full prompt month has 106 messages (37 incoming, 69 simulated replies), 28 exercised families and unchanged stock/finance milestones. `idle` has no agent replies; an external complete-profile operator may return a `reply` command to store an unsent draft with exact subject/body and a released incoming message ID. Run the four correspondence-specific tests in `test_complete_company.py` and the viewer browser check with `SIMULATOR_RETAINED_RUN` pointing to a saved complete-v2 prompt run.
