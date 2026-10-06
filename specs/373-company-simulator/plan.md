# Implementation plan

## Constitution Check

| Boundary | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Existing manual-source proposals retain source/order/movement receipts; journal links accepted command IDs. |
| Tenant ownership | PASS | Fresh empty Sandbox owned by the launch principal; normal tenant-scoped read services. |
| Authoritative amounts | PASS | Profile states exact customer line/header amounts and supplier pack amount; no observed-value oracle. |
| Application boundaries | PASS | Existing proposal/approval tools; no direct ORM writes, schema changes or production rule duplication. |
| Confirmation | PASS | Explicit local --confirm covers only finite shipped profile and built-in policies. No arbitrary AI autoapproval. |
| Time and scheduling | PASS | Finite local ordinal controller; application timestamps remain real; no new production job queue. |

## Design
`profiles/general_company/scenario.yaml` authors exogenous customer requests and fixed known supplier terms. `world.py` owns released goals, conditional world arrivals and independent expected quantities. `operators.py` consumes copied released views. `controller.py` accepts supported policy decisions through the production proposal bridge and compares actual Reality after each day. Supplier arrivals are conditional on accepted purchase receipts. Customer arrival is explicit simulated world evidence following dispatch, not a production logistics claim.

Per-order quantity/fulfillment/amount expectations come from authored demand or the stated supplier pack. Opaque commitment/document/source IDs come from accepted receipts. The observation never manufactures expectations. Core discrepancy stops progression; business misses continue; execution uncertainty retains journals without retry.

No migration or generated API/catalog changes. Runs create new companies rather than mutating a baseline. Tests use temporary PostgreSQL companies rolled back by existing fixtures; CLI runs retain accepted state through normal services. Recovery/resume is unsupported and must reconcile receipts first.

## Verification
Tests precede the implementation files. Acceptance compares prompt/delayed/idle operators, conditional purchase timing, future-view isolation, short horizons, confirmation, unreviewed profile refusal, oracle mismatch and unknown execution. Retain fixed day/week regression tests. Run complete backend suite, make lint, make spec-check and whitespace review.

## Deliberate remaining slices
Finance and package/destination evidence have researched existing APIs but are not claimed in this slice. Real Shopify mappings await authentic examples. These are required before calling the simulator a complete company rehearsal.
