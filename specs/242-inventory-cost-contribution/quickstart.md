# Validation guide: costing architecture experiment

Status: experiment implemented; production costing and full architecture qualification
are not implied. Use only a dedicated disposable PostgreSQL target.

## Code and unit/PostgreSQL contracts

From the repository root, point `TEST_POSTGRES_ADMIN_URL` at a PostgreSQL instance in
which the test harness may create and drop its own uniquely named test databases:

```bash
.venv/bin/python -m pytest packages/reality-core/tests/test_costing_spike_contract.py packages/reality-core/tests/test_costing_spike_postgres.py -q
python3 scripts/check_spec_policy.py
```

From `packages/reality-core`, run `../../.venv/bin/ruff check .`. Test coverage includes
FIFO and specific identity, partial return ambiguity, signed allocation, cumulative
rounding, unknown costs, exact tenant links, atomic publication, scoped refresh and
append-only late evidence with prior-knowledge reproduction.

## Disposable benchmark setup

Provision a new PostgreSQL database named `reality_benchmark_costing_234_v3` (or another
name beginning `reality_benchmark_`). Set `REALITY_DATABASE_URL` without printing its
credentials. The runner refuses normal database names, missing disposable confirmation,
nonempty fresh targets, foreign tables and mismatched reuse manifests. It creates only
its experimental namespace; no Alembic application migration is necessary.

From repository root:

```bash
PYTHONPATH=packages/reality-core/src:packages/reality-core .venv/bin/python -m benchmarks.large_tenant_registers.costing_runner \
  --profile full --seed 234 --business-date 2026-09-18 \
  --strategy projection --confirm-disposable \
  --output specs/242-inventory-cost-contribution/evidence/projection.json
```

For comparable baselines, run direct first and projection second: projection appends
late evidence, so subsequent reuse changes the knowledge revision. Run the direct strategy with `--reuse` on the same validated input manifest and a separate
output file. Use `--profile reduced` on another fresh disposable database for quick runs.
The defaults are 200 measured samples per projected read workload and 30 late-cost
updates; smaller `--samples`/`--updates` explicitly produce nonqualifying exploratory
results. Reuse preserves appended late evidence, which is included in subsequent results.

## Result interpretation

Exit 2 means completed **exploration, not qualification**. An exception/nonzero failure
retains a failed report. JSON records exact two-tenant cardinalities, code digest, data
version, checksums, timings, memory, environment and explicit missing qualification
conditions. Do not treat a fast synthetic result as proof of product adapter correctness.

The current prototype covers regular receipt/issue/transfer history at scale; detailed
return/tax/credit arithmetic is independently tested on small cases. Product projection
freshness/approval behavior, full adversarial workload distribution and the enforced
combined 4-vCPU/16-GiB reference host remain qualification work. No result marks these
as passed. See verification-results.md for actual outcomes and next architecture steps.

Remove only databases/containers created for this experiment after retaining evidence.
Never run the benchmark or its synthetic initialization against an active company.


## V3 capped run and integration review

The v3 generator keeps fixture J counts while distributing receipt-family returns,
signed supplier reductions, stated nonrecoverable tax and split/partial matching.
Full projection runs use at least 30 updates and keep the one-per-second input stream
active until all five readers finish 200 measured requests each. Report `states` with
latency: a fast `not_ready` response is not a current cost answer. The frozen-revision
publisher allows new evidence during replay; a failed refresh retains the old generation.

The recorded run uses the locally available `postgres:17-alpine` and `reality-api:latest`
images; exact immutable image IDs and resource settings are in `evidence/v3-environment.json`.
Use a fresh database/container name on rerun; never attach to an active company database.
For the same cap, start PostgreSQL with `--cpus 2 --memory 4g --memory-swap 4g` and the
Python runner with `--cpus 2 --memory 2g --memory-swap 2g`. Run the Python container in
the isolated PostgreSQL container's network namespace. Mount the repository read-only
at `/workspace`, a dedicated result directory read-write at `/evidence`, set its working
directory to `/workspace/packages/reality-core` and `PYTHONPATH=src:.`, and use
`--entrypoint python`. Set `COSTING_GIT_REVISION` to the actual checkout revision when
the runtime image has no Git. The report independently hashes the costing source files.

The final runner arguments are:

```text
-m benchmarks.large_tenant_registers.costing_runner --profile full --strategy projection
--confirm-disposable --output /evidence/v3-projection.json
```

Use `--reuse` only for an already validated matching v3 dataset. The recorded final run
reuses the initialized full fixture after the preliminary run; its starting adjustment
revision is explicit in the report. Fresh v3 generation installs the same-tenant return
FK; the reused preliminary fixture had that constraint added and validated before the
final run. `v3-preliminary.json` is retained as the observed concurrency failure, not as
final qualification. All reported values remain synthetic and disposable.

Review [product-integration.md](contracts/product-integration.md) before creating product
tasks: compiler slice grain, bounded shared jobs, complete scoped invalidation, atomic
publication and owner confirmations are explicit design prerequisites. The exact
reference-host and integrated worker/adapter gates remain open regardless of local speed.


For the restart probe, restart only the disposable PostgreSQL container after a completed
publication, then call `costing_runner.workload` once for order, inventory, monthly,
attention and tool through the capped Python container. Record states and individual
timings separately from p95 runs. PostgreSQL shared-buffer reset does not evict the shared
VM OS cache, and later reads in that sequence are not independently cold.


## Scoped live availability

The current runner's tool workload uses `live_order_read` and targets the last hot-pool
order on half its requests. Use a fresh disposable database with the same capped Docker
commands above and output to `live-projection.json`; the fixture stays v3, while source
hashes distinguish the live-reader revision and its attribution lookup index. Compare
`mixed_measurements.tool.states` and `.routes`, not only timing. Readiness is independent
of whether all acquisition/revenue evidence is complete. The reader itself never writes
or triggers a job; a refused input bound is a valid explicit not-ready state.

### Bounded worker experiment

From `packages/reality-core`, with `PYTHONPATH=src:.` and a fresh disposable PostgreSQL
URL whose database name starts with `reality_benchmark_`:

```sh
python -m benchmarks.large_tenant_registers.costing_worker_runner \
  --profile reduced --confirm-disposable --cycles 1 --poll-seconds 0 \
  --output /tmp/costing-worker-reduced.json
```

Use a separate fresh database for `--profile full --cycles 3 --poll-seconds 5`.
Exit status 2 deliberately denotes exploratory results, even when measured limits pass;
inspect `status`, `measured_limits_passed` and `qualification_passed` in the JSON.
The module requires the shared core dependencies and launches the real watchdog's
child process through a fixed experimental bootstrap. It does not start or alter the
normal deployed worker. `--reuse` only admits the fixture schema and four queue/control
tables after validating fixture cardinalities and tenant scope.

### Review the actual adapter delivery boundary

Read [adapter-delivery.md](contracts/adapter-delivery.md) alongside the cited compiler,
report, tool and exception functions. This is a design review, not a runnable product
feature. Acceptance vectors for its future test-first slices include:

1. Fixture A gives the same EK, consumed/remaining cost, DB1/DB2 and rates through all
   shared surfaces, with the same pinned context and evidence trace.
2. Two revenue-100 slices with costs 60/unknown yield known DB1 40 and final DB1 null;
   they must never produce apparently complete DB1 140.
3. Complete acquisition/revenue but missing selling cost keeps DB1 available while
   DB2 is incomplete. Legitimate zero remains distinct from missing evidence.
4. Concurrent publication cannot mix old metadata with new values, page totals or
   finding counts. Historical questions reproduce retained knowledge or refuse.
5. Actual exception page/count tests include legacy and new classes, initial missing
   basis and downstream snapshot lag; no read schedules or rebuilds anything.

Named future test families and implementation paths are in slices A–E. Do not run a
nonexistent product command or mark these vectors passed based on prototype results.

### Review the production schema proposal

Read [production-data-model.md](contracts/production-data-model.md), especially the
first-slice fields, retained manifest membership, correction workflow and approval scope.
This remains design review; no new product command or migration exists yet.

Review with receipt fixture A, late-freight fixture D and split matching/return cases:

- Identify the exact received components and source signs; trace each reviewed part to
  its receipt Movement without adding redundant document/order/source FKs.
- Check source shares and tax buckets reconcile; a positive-stated credit can reduce
  acquisition cost without rewriting its source amount.
- Freeze a review at cursor N; later interpretation, correction or attribution must not
  change that review's membership. Unsupported older knowledge is explicitly refused.
- Confirm that deleting calculated generations leaves enough retained evidence and
  decisions to replay the review; destructive downgrade must not remove them silently.
- Separate the first receipt-cost delivery from later remaining-stock valuation/DB;
  neither FIFO activation nor complete sales margins are promised by the first slice.

After owner approval: generate detailed first-slice tasks, analyze prerequisites, observe
failing domain/service/tenant/migration proofs, then implement through shared services.
Full qualification includes production input admission/manifest capture time, not only
the reconstruction interval already measured on immutable synthetic fixtures.

## Production inventory domain foundation

The calculation module is `reality.domain.inventory_costing`; its explicit method is
`fifo` or `specific`. It accepts only typed frozen events for one already-established
pool. There is deliberately no application command for inventory yet. To verify the
foundation with the repository PostgreSQL test setup:

```bash
cd packages/reality-core
../../.venv/bin/pytest -q tests/test_inventory_costing.py
```

The examples prove fixture A consumption 630/rest 420 and fixture B FIFO consumption
1280/rest 1120, return-time FIFO order and original receipt trace through resale, unknown
coverage and four-decimal conservation. Service integration still needs confirmed
policy, economic ownership and retained movement/manifest membership; supplying arbitrary
current movements to the kernel is not a supported company valuation workflow.

## Confirmed bounded inventory service

Use the repository's normal disposable PostgreSQL test setup, then run:

```bash
cd packages/reality-core
../../.venv/bin/pytest -q tests/test_inventory_costing_services.py tests/test_inventory_costing_migration.py
```

The end-to-end fixture confirms receipt goods 1000, freight 100 and reduction 50, then
60 economic shipment units. Inventory preview and confirmed reads return 40 remaining
units / 420 acquisition value and 630 consumption. A subsequent 50 freight amount first
requires an updated receipt review, then an explicit new inventory review, producing
440 remaining / 660 consumed while the old review still returns 420 / 630.

`cost_change_propose` with operation `inventory_review` prepares policy, whole-history
and receipt ownership/cost declarations; an active human owner must confirm the bound
action. See contracts/inventory-service.md and docs/features/receipt-costing.md for the
required fields and supported scope. `cost_inventory_get` takes `item_id` and optional
`review_id`; current stale values are unavailable and `basis_*` fields explain the old
cutoff. The test also exercises the actual MCP handler and foreign review refusal.

Migration 0065 must be applied through the normal deployment migration process before
using these tools in a real installation. Test execution does not migrate an existing
company database or activate any company policy. No deployment is part of this work.

## Contribution foundation verification

Run `pytest -q tests/test_contribution.py` from packages/reality-core with the normal
disposable PostgreSQL test configuration. The repository conftest requires PostgreSQL
even though this module is pure. Fixture A must yield DB1 570, DB2 456 and rates 47.5/38.
The partial-scope fixture must yield known DB1 40 and DB2 30 with final amounts absent;
missing selling evidence must preserve independently complete DB1. Inspect retained
slices for evidence/review references and explicit support states. No application
command or live company DB result is introduced by this stage.

## Current contribution application preview

Read `cost.contribution.preview` with `document_line_id` for a sales invoice line.
A supported exact whole-line scenario yields known_db1 570 from received net 1200 and
reviewed consumption 630; final db1/db2/rates stay null with missing review/selling basis.
Inspect the trace's order line, commitment, shipment, inventory review and used receipts.
The MCP equivalent is `cost_contribution_preview`. No historical review argument exists.
Run tests/test_contribution_services.py plus domain/costing/catalog regressions; current
input changes and foreign references must not yield a complete or leaked result.

## Confirmed whole-line contribution

Read cost.contribution.preview and retain its candidate_hash/event_sequence. Prepare
cost.change operation contribution_review with document_line_id, expected_candidate_hash,
expected_event_sequence, profile=commercial_v1, profile_confirmed=true, revenue_complete=true,
the exact proposed_economic_at as economic_at and a reason. An authenticated active
owner explicitly confirms the unchanged proposal. Read cost.contribution.get for current
DB1, or pass its review_id for retained history. DB2 stays unknown.

Verify tests/test_contribution_reviews.py and tests/test_contribution_migration.py in
disposable PostgreSQL. Late-cost reaffirmation must produce DB1 540 while the original
review reproduces 570. Reusing either complete quantity, changing admitted evidence,
foreign scope, stale proposals and old-snapshot current reads must refuse.

## Verify reviewed DB2

Propose/confirm selling_assign with received net evidence and exact sold-line shares.
Refresh the existing bounded inventory review after input events, then propose/confirm
contribution_review with all seven selling_categories. Read cost.contribution.get:
fixture A must retain DB1 570, show direct90/allocated24, and finalize DB2 456/38%.
Withdraw/revise a contributor: current output becomes stale; exact old review_id must
still reproduce456. Without the checklist DB2 stays unknown; confirmed zero finalizes
DB2 only if no active costs contradict that declaration.


## Inspect retained costing evidence

After creating a review through the confirmed costing workflow, inspect its exact ID:

```sh
reality cost-record cost_contribution_review REVIEW_ID --tenant-id TENANT_ID --language de
reality cost-record cost_contribution_review REVIEW_ID --tenant-id TENANT_ID --page 2
```

Use MCP `cost_record_get` or application tool `cost.record.get` with `kind`, `record_id`,
optional `page` and `language` for the same data. In the existing Inspector record
register, select a cost family, open a record and follow source/decision/member links.
The Inspector labels these as retained evidence, not current valuation completeness.


## Query a cost answer and its retained basis together

```sh
reality cost-query inventory ITEM_ID --tenant-id TENANT_ID
reality cost-query contribution INVOICE_LINE_ID --tenant-id TENANT_ID --review-id REVIEW_ID
```

HTTP GET `/api/tenants/{tenant_id}/cost-query`, MCP `cost_query_get` and
`cost.query.get` accept kind (`inventory`/`contribution`),
scope_id and optional review_id/effective_at/knowledge_at/policy_revision_id. Compare
resolved authority and freshness separately from the result's evidence gaps. Only exact
retained cutoffs are supported; unsupported constraints refuse. Stale current queries
have result=null and expose the old answer only as basis_result. No canonical generation
or company-wide commercial profile is implied by the returned single-scope identity.

### Stored retained inventory scope (T080 bounded integration)

After explicit owner confirmation of an inventory review and deployment of migration0069,
use existing operator commands (replace the placeholders with same-tenant identities):

```bash
reality-worker jobs run costing.inventory.refresh --tenant TENANT --actor OWNER \
  --request-id inventory-cache-1 --config-json '{"review_id":"REVIEW"}' --json
reality-worker once --tenant TENANT --max-runs 1 --json
```

The shared service `inventory_cost_snapshot(session, tenant_id, item_id)` reads the
result without recalculation; `review_id=...` or `generation_id=...` pins history.
No new browser/tool surface is claimed. Late evidence keeps the stored basis but makes
current freshness pending; `allow_previous=True` explicitly permits that prior value.
Rebuilding the same review cannot approve later freight or change its fixed input set.

## Pending company-generation validation

After explicit approval and implementation of
contracts/company-generation-publication.md, validate in this order: migration parity and
downgrade protection; manifest capture/replay/tenant refusal; deterministic worker chunks;
exact known/unknown population closure; CAS rollback/concurrency; one-generation page,
totals and finding reads; then the unchanged fixture-J qualification. Until approval, no
migration or runtime command exists and captured reports must continue to state that they
are diagnostic only.
