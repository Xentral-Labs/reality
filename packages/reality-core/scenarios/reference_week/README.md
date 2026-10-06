# Reality Reference Week / Reality Referenzwoche

Canonical protocol: [Reality Referenzwoche](../../../../docs/scenarios/reality-reference-week.md).
Its first 24 hours are the Reality Referenztag. `scenario.yaml` is the executable
versioned input and independent oracle. It explicitly states all commercial amounts;
there are no taxes in this fixture, so the stated net and gross amounts coincide.
`simulator.py` maps fixture labels to returned opaque IDs and calls normal application
proposal and confirmation services. No direct ORM business writes or new core rules.

## Start the first day

Prerequisites: repository Python dependencies installed, an existing **local test**
PostgreSQL database migrated through the usual Alembic setup, and an eligible verified
local account. Obtain its opaque user ID from your normal local account/admin tools.
The runner does not create users, credentials, mandates or external integrations.
`REALITY_DATABASE_URL` must select that local database; never paste credentials into
reports. Every invocation creates a new Empty / practice Sandbox and returns its ID.

From the repository root, run the acceptance proof:

```bash
cd packages/reality-core
../../.venv/bin/pytest tests/scenarios/test_reference_week.py -q
```

For a retained local run against your configured database:

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m scenarios.harness.runner \
  --actor-id <existing-local-user-id> --scope day --confirm
```

Use `--scope week` for all seven days. `--confirm` approves the exact authored fixture
for this trusted local invocation; it grants no future agent authority. Existing
account/company authorization, proposal validation and confirmation remain active.
There is no automatic retry or resume. A fresh invocation gets a new run/company.

The final line links to `artifacts/reference_week/<run-id>/report.md` (relative to the
repository root). Exit code 0 means passed; 1 means a retained run failure; invalid
arguments/fixtures refuse before company creation. Explicit `--output` changes the
artifact parent. Read `manifest.json`, `events.jsonl`, `checkpoints.jsonl` and
`report.json` for exact source/proposal/receipt IDs and expected/actual/delta.

Expected day end: stock A/B/C **0/6/0**, four sales orders, customer A4 open,
supplier A20/C10 open, no active reservations or ledger entries. Expected week end:
stock **7/4/4**, W1 **4/4/4**, W2 **3/0/0**, ten sales orders, one cancelled customer
line, no open deliveries or active reservations, no ledger entries.

## Scope of the proof

This adapter tests **manual-source core replay** in an independent practice Sandbox.
Each proposal is observed before approval to prove no accepted effect. E13 replays
S3's retained executed proposal receipt; it does not inject or validate a Shopify
webhook and does not claim raw external source-idempotency coverage. Movement actions
are recorded through the normal confirmed `movement_create` service, without assuming
a carrier or physical integration. E28 records a return announcement with customer
fixture text; no mailbox capture or outgoing mail is performed.

The actual return is linked to its preceding announcement; announced-but-not-arrived
quantities are checked separately from customer delivery fulfillment.

The controller checks after every event, including intermediate reserve/ship events
in multi-stage rows. Full line quantities/statuses, stated commercial amounts,
locations and master/order counts are fixed in the YAML. Exact movement-type totals
at week end independently reconcile opening, receipts, returns, shipments and loss.
The observer retains all affected record identities and checks lineage/invariants.
It does not verify materialized projections or timing decisions made by an AI agent.

The pytest proofs use disposable PostgreSQL databases and rolled-back companies.
Their reports are verification artifacts, not a persistent company in your account.
Retained command-line runs keep their local company for inspection, including on
failure. Do not repair a failed run to make its report green.

## Adding the next scenario

The broader next step is the
[Reality Company Simulator](../../../../docs/scenarios/company-simulator.md), with
general-company and Shopify-company profiles and configurable duration. Shopify
payment/payout and external-intake oracles follow original-source analysis. Reuse
the harness where its contracts fit; do not copy fixed reference-week expectations
as the only correct result of a reactive agent game. Changing an accepted fixture
creates a new version.
