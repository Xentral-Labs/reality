# Implementation Plan: Costing architecture qualification

**Branch**: `242-inventory-cost-contribution` | **Date**: 2026-09-18 | **Spec**: [spec.md](spec.md)
**Language**: English
**Status**: Production candidate approved and implemented in bounded stages. General
generations/reporting and integrated fixture-J release qualification remain open.

## Summary

The current candidate includes retained receipt costs, bounded FIFO inventory, confirmed
whole-line DB1/DB2, cost inspection, shared query context and the bounded inventory
publication integration described below. The approved production model revises the
initial preimplementation gate: build the candidate before integrated qualification,
without waiving any release budget or activating company policies.

### Initial qualification scope (historical)

The owner's instruction to continue advances the accepted concept into technical planning.
Use the proposed FIFO/specific-identification commercial profile and sequential delivery
as planning assumptions; do not activate a company accounting policy or infer migration
approval. First qualify the cost derivation architecture at the explicitly accepted scale.

The concept requires fixture J before architecture approval. This plan therefore defines
an isolated, test-first architecture experiment, not a production cost ledger, migration
or premature selection of projection storage. Product implementation slices 1–4 remain
gated on the experiment and the subsequent schema/Constitution review.

## Technical Context

- Python 3.12+, Decimal, SQLAlchemy 2 and PostgreSQL; use the existing benchmark harness.
- Existing normalized received amounts: `src/reality/db/components.py`; source identity,
  quantities and corrections: `src/reality/db/core.py` (paths relative to reality-core).
- Existing benchmark: `benchmarks/large_tenant_registers/{dataset,runner,cases,report}.py`.
- Existing projection service: `src/reality/services/projections.py`; scheduled refresh:
  `services/projection_jobs.py` and `jobs/handlers/projections.py`.
- Existing analysis integration: `services/analytics/{inventory_relation,finance_relation,
  compile_sql,graph_model,derivations}.py`, declared by `config/reporting_graph.yaml`.
- Runtime available during planning: Python 3.12.4. Docker socket access was sandbox-denied
  during read-only discovery; no disposable database was created or benchmark executed.
- Scope: fixture J's two tenants, each with 100,000 orders, 1,000,000 movements and the
  fixed cost/matching counts; 4 vCPU/16 GiB reference envelope. Local runs on a different
  envelope are informative, not acceptance evidence for the stated resource budget.

## Constitution Check (blocking gate)

This check applies only to the isolated Phase 0 experiment. It does not approve a
production schema or waive the mandatory plan/tasks/analyze/implement sequence.

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Synthetic authored source amounts and explicit assignment decisions; output never reused as evidence | PASS |
| Reality owns operational state | Retain movement-derived quantities; benchmark staging has no product status writes | PASS |
| Proven schema only | No application migration; isolated experiment relations disappear with disposable database | PASS |
| Tenant + shared service boundaries | Explicit tenant on every experimental relation/query, neighboring full tenant and refusal tests | PASS |
| Spec/test traceability | FR-018 and derivation prerequisites mapped below; failing proofs precede kernel and runner | PASS |
| Explainable web behavior | No product UI change; test response contracts retain source references and freshness | PASS |
| Received values not recomputed | Exact authored inputs; only observations and allocation arithmetic derived | PASS |
| Smallest coherent design | Extend benchmark conventions; compare two strategies without installing a new queue or engine | PASS |

Architecture qualification: **OPEN** (local exploratory runs exist; reference and integrated gates are not certified). Production data model, migrations and final
service design must not be marked approved before fixture J passes or the owner reviews
a revised target/design. Unknown feasibility is not recorded as a passing gate.

## Repository Structure and Layer Changes

Implemented experiment-only files:

```text
packages/reality-core/benchmarks/large_tenant_registers/
  costing_dataset.py      # fixed profile, authored evidence and manifest validation
  costing_kernel.py       # pure Decimal reference/candidate observations, no ORM writes
  costing_cases.py        # bounded reads, regrouping and late-cost workloads
  costing_runner.py       # disposable-target guard, measurements, result publication
packages/reality-core/tests/
  test_costing_spike_contract.py    # small independently computed cases and refusals
  test_costing_spike_postgres.py    # tenancy, read scope, publication and replay
specs/242-inventory-cost-contribution/evidence/
  # environment manifests, JSON results and architecture evidence
```

Reuse existing benchmark lifecycle validation and reporting conventions. Do not change
existing nine-register results, default profile, public tools or application imports.
A prototype kernel is not a second operational rule engine: keep it out of product code;
a later implementation moves reviewed logic into domain/services and removes duplication.

## Design

### Experiment data and provenance

Follow [spike-contract.md](contracts/spike-contract.md) and [data-model.md](data-model.md).
Generate exact deterministic IDs and source-stated totals. Fixed quantities permit
independent expected values without calculating what a real supplier is responsible for.
Benchmark-only insert helpers may populate their own synthetic input tables, following
spec 033's existing fixture convention; they are not a new application write path.

Pin business date to 2026-09-18, seed 234, and 24 prior calendar months. Generate the
control tenant with equal counts and distinct values/identities. Capture both input
and output checksums plus generator/kernel/query versions. Completeness gaps must not
reduce workload by excluding all hard cases from measurement.

### Candidate A: bounded direct observation

Use exact requested order/receipt scope, indexed same-tenant joins and ordered replay
of only required valuation pools. The reporting experiment uses the established allowlisted typed-derived-relation seam:
currently declared service measures are refused by compile_sql with `service_measure`.
A YAML-only declaration is not an executable integration. No invocation of the whole tenant's inventory_rows or
aging_register as a shortcut. Record fetched rows, SQL plans, memory and query counts;
prove filter-before-total and independent source reconciliation.

An order may depend on a long FIFO pool history. Indexes alone do not establish a
bounded enough dependency. Reject this candidate for interactive use if required replay
fails the budgets; do not hide the failure behind page-size truncation.

### Candidate B: rebuildable indexed observations

Run the same kernel over a consistent retained snapshot and publish a disposable derived
generation keyed by tenant, scope, effective cutoff, input watermark and method version.
Index order, item and period lookup paths. Publish generation pointer and completed
watermark atomically. Keep the old generation readable until replacement is complete.

Reuse existing projection lifecycle concepts, not necessarily the existing one-payload-
per-row replacement loop. Measure that loop first where applicable; any required typed
projection relation or partition checkpoint is a future proven schema proposal, not
silently approved by this experiment. Rebuildable output is never financial authority.

Invalidate affected receipt/layer/order dependencies. Late cost evidence can affect many
sales; measure the hottest scope. Input change during reconstruction must not advance the
published watermark beyond the snapshot actually processed. Failed/retried refreshes
cannot publish mixed generations. No API read launches a full rebuild.

### Calculations and identity

Use the accepted cumulative consumption rounding before report filters. Returned goods
become new layers at return time carrying the original consumed cost. Include late freight
and credits, invoice/fulfilment matching and complete/incomplete coverage. Record exact
scope IDs for traceability; do not infer links from SKU, number or dates.

The experimental order, inventory, monthly report, attention and tool response shapes
must express the same canonical observations. Adapter overhead remains separate from
LLM inference: fixture J measures service/tool execution, not external model latency.
Read-only tools requiring live values return not-ready when a bounded exact answer is
unavailable; they never claim a stale generation is current.

### Data and migration impact

None on product schema. Disposable experiment tables use a separate benchmark namespace
and explicit tenant keys. No normal company receives records or policy activation.
Any future production migration needs a separately reviewed typed schema and rollback
proof after architecture qualification. Do not invent the next Alembic revision now.

### Failure, security and tenant behavior

Before any setup write: validate the database name starts with `reality_benchmark_`,
require explicit disposable intent and an empty/identically manifested experimental
namespace. Do not print credentials. Never run against default/shared database settings.
Do not auto-drop a pre-existing database, silently reuse partial fixtures, migrate on
worker startup or use an existing company's initialization authority.

All read scopes use opaque same-tenant keys. Absent/foreign scopes return equivalent
not-found. Prototype refresh publishes derived observations only; it cannot confirm
policy, tax, allocation or zero-cost judgments on behalf of anyone.

## Test Strategy and Traceability

| Requirement | Level | Planned proof | Expected initial failure |
|---|---|---|---|
| FR-005, FR-022 | Domain | test_costing_spike_contract.py: FIFO return C2 and cumulative rounding K2 | No candidate kernel |
| FR-002, FR-003, FR-020, FR-021 | Domain | A/F/K source totals, signed splits, tax/discount bases | No input-normalization contract |
| FR-007, DR-004 | Domain/PostgreSQL | D and K2 cutoffs, generation rollback, late-cost deltas | No reproducible costing observation |
| FR-010–FR-014, FR-024 | Domain/PostgreSQL | E/F/L unmatched scope, complete totals, rates and fan-out | No cost relation |
| DR-001–DR-003, DR-005 | PostgreSQL | Foreign IDs, no evidence mutation, original register results unchanged | No tested experiment boundary |
| FR-018, SC-006 | Benchmark | Fixture J read/refresh/reconstruction cases and environment manifest | No costing benchmark |
| FR-025 | Benchmark prerequisite | Gap and negative-DB observations with counts at scale | No cost finding input relation |

Small tests require exact independent expected values. Run the reduced profile before
large setup; repeat full workloads according to fixture J. A mock of the kernel or
precomputed hard-coded output does not qualify the performance path. The spike's service
response tests do not count as passing web/CLI/MCP integration or production permission
acceptance; those remain required in the relevant delivery slice.

## Rollout and Rollback

No release or application activation. Execute only in a new dedicated disposable target.
Write benchmark results only after validation, retain failure evidence with an explicit
failed outcome, and clean up only resources demonstrably created by this run. Retain
machine-readable manifests and source revision so reviewers can reproduce the decision.

After passing, document the chosen strategy and measured tradeoffs in research.md,
complete production data-model/service contracts, rerun the Constitution Check, generate
traceable implementation tasks, analyze, then implement each slice test-first.

## Review Risks

- A 120-second complete reconstruction over both tenants is not the agreed workload:
  each tenant is measured independently with the second present for isolation/skew.
- A local Docker host may not match the 4-vCPU/16-GiB envelope; disclose enforcement or
  report an exploratory run without claiming qualification.
- Existing projection rows are text payloads with whole-result replacement. Adding an
  unbounded JSON result to them may move rather than solve the performance bottleneck.
- Phase 0 lacks real product adapter costs; later slice gates must repeat end-to-end
  service timings. Passing the spike is necessary, not sufficient for final release.
- Owner continuation permits planning; it does not activate a tenant's accounting policy.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | No product authority/schema change in Phase 0 | Direct calculation remains a measured candidate | Not applicable |

## Execution notes

The owner subsequently authorized Phase 0 implementation. The disposable experiment
uses its own `costing_spike` namespace and explicit received-component references;
it neither changes application metadata nor adds public core functions. The first
exploration was superseded before qualification because synthetic late-cost mutation
was replaced with append-only adjustment evidence and a prior-knowledge replay test.
Retain that first result only as explicitly superseded evidence.

The experimental runner deliberately returns exit code 2 for exploratory completion,
never a green architecture gate. Full fixture J qualification requires the exact
reference envelope and all adversarial/full integration cases, not just matching
cardinalities and favorable local timings. A failed run retains a failed result.


## Qualification continuation

Owner authorization covers further experiment implementation and integration planning.
Constitution Check above remains PASS for this isolated continuation; no production
schema or policy is activated. Version the generator v3 instead of rewriting v2 evidence.
Returns replace a subset of receipt-family movements and retain exact earlier issue
identity. Original purchase inputs are assigned to actual receipts, never used to price
returns. Signed supplier reductions and nonrecoverable-tax components remain stated
amounts. Aggregate split matching before the movement join; partial/unmatched revenue
makes contribution incomplete rather than duplicating COGS or inventing zero revenue.

Add checkpoint input revision and consistent-snapshot read metadata; a live read refuses
stale output while display reads retain explicit stale state. Freeze the append-only adjustment revision before replay and lock only for publication;
new evidence may commit during replay and remains pending beyond that frozen revision. Compare complete observation
and inventory output after mixed load, not just costs. Measure five concurrent readers,
200 samples per surface while 30 one-per-second adjustments arrive; report per-surface
mixed timings, publication latency, immutable evidence and reconstruction checksums.

The available Docker VM has 8 CPUs and 8,218,251,264 bytes RAM, so the exact dedicated
16-GiB reference environment is unavailable. Run PostgreSQL with 2 CPUs/4 GiB and Python
with 2 CPUs/2 GiB (combined upper bound 4 CPUs/6 GiB, no swap) using existing images.
Record container settings and cgroup observations. Do not change global Docker settings
or stop unrelated services. OS cold-cache eviction is not safe on this shared VM; report
that qualification gap explicitly. Preserve reference qualification as pending.

Integration research runs independently and writes contracts/product-integration.md.
Tests precede experiment changes, then targeted PostgreSQL/pure suites, lint/spec gates
and full-size capped run. A new full backend run is unnecessary unless product code
changes; the prior full-suite evidence and the final experiment suites are distinct.


### Measured concurrency correction

The first capped v3 run exposed delayed input commits when replay held the tenant lock.
A PostgreSQL test reproduced the conflict with a concurrent intake and 100-ms lock timeout.
Scoped replay now reads an explicit immutable adjustment revision without the tenant
lock and publishes that revision under a short lock. It cannot mark evidence received
during replay as processed. Superseded publication is refused. The synthetic base inputs
are immutable; this is not a substitute for product source-version snapshots.

The mixed-load producer now stays active until all five readers finish their 200 samples,
with at least 30 adjustments, instead of potentially stopping while a slow reader is still
running. Record actual update count, input timing and response-state distribution. A
not-ready refusal is a truthful state response, not a successful current cost answer;
ready read-only timings and mixed-load availability must be reported separately.


## Scope-specific live reads

Constitution Check: PASS for this experiment-only continuation; no new production schema,
public function or catalog. Reuse the immutable v3 fixture and append-only adjustments.
Resolve an order's pool and movement prefix. Only adjustments after the completed global
checkpoint that target that prefix or the order's selling components invalidate it;
unassigned/unknown targets conservatively invalidate. Assess this under REPEATABLE READ.
If unaffected, serve its published result with explicit requested-scope assessment metadata.
If affected, preflight at most 5,000 movement rows, 20,000 financial parts and 20,000
adjustment rows using limit-plus-one checks, then call the existing kernel at the observed
input revision. Exceeding any cap refuses without replay. No full replay, publication or
job submission is allowed from the reader. Missing initial output is not-ready.

Prove direct/projected complete-value parity, unrelated pool and foreign tenant behavior,
fee and receipt corrections, refusal-before-replay, snapshot races and read-only behavior.
Measure at least 200 live requests under updates, deliberately targeting the hot changed
pool as well as distributed orders; report route and readiness counts. Preserve global
aggregate freshness and the already open reference-host/product gates.


## Bounded shared-worker experiment

Constitution Check: PASS for isolated qualification only. Source evidence remains
immutable, staged outputs are disposable and tenant-scoped, and no product metadata or
migration is changed. New files: costing_generations.py (staging and reads), costing_worker.py
(static benchmark bootstrap for the existing shared runner), costing_worker_runner.py
(disposable lifecycle and timing), and tests/test_costing_spike_jobs.py. Extend derive
with a bounded pool range; all paths still use the same Decimal kernel.

A generation has tenant, opaque ID, frozen adjustment revision, algorithm version,
planned pool ranges and cursor. Stage observation/inventory rows by generation. Each
range holds at most 50,000 movements; an oversized indivisible pool is refused. A child
process handles at most three ranges (150,000 movements), checks its deadline between
ranges, and stays under the existing 20-second statement/30-second child bounds. The
final transaction switches only the tenant's published-generation pointer. Old generation
rows stay readable; a restart continues from the committed cursor. No global copy/delete
of all published observations occurs at handoff. Cross-range inputs are immutable in v3;
only append-only adjustments are cut off. Product source-version snapshot proof remains
separate.

Use public Tenant/AppUser/ScheduledJob/ScheduledJobRun tables only in the disposable test
database, with synthetic control tenant IDs matching the fixture IDs. Reuse
scheduled_jobs.enqueue_projection_run, claim_next, execute_claim and record_failure.
The experiment temporarily binds the existing projections.refresh definition to a fixed
benchmark-only configuration/handler while preserving its actual authorize function.
A static child bootstrap loads that binding then calls the unchanged shared child_main.
The benchmark process adapter delegates watchdog/settlement to execute_process, replacing
only its fixed module launch with that static bootstrap. No caller-selected module,
second queue, altered timeouts or production registration is introduced. Normal worker
startup continues to refuse the experimental configuration.

Measure complete rebuild, child durations, publication, frozen-revision parity and
concurrent old-generation reads; include 5-second inter-job pacing so the result does
not hide the default worker poll interval. Test lost-response replay, failed work,
retry, stale claims, archived/foreign tenant refusal and concurrent arrivals. Full
reference-host and product adapter gates remain open even if this fixture passes.

## Product adapter delivery design

Status: planning complete for the adapter boundary; production implementation remains
subject to the already recorded schema and qualification gates. The owner's continuation
authorizes this concrete design. See [adapter-delivery.md](contracts/adapter-delivery.md)
for exact fields, implementation paths, failure semantics and test-first slices A–E.

Current code review confirms three necessary changes beyond catalog declarations:
(1) a canonical selectable at its own grain, because the compiler always joins an ORM
anchor today; (2) coverage-aware aggregation and ratio semantics, because SUM skips
unknown inputs; (3) an explicit pinned context throughout graph/tool/exception results.
The exception page currently derives the full live list before pagination, so its
page/count integration must be qualified with existing classes as well as new ones.

The smallest compatible extension preserves existing anchored derivations and ordinary
sum semantics. New costing declarations opt into the validated selectable, context and
covered aggregate contract. Saved questions retain their requested context; execution
resolves the actual generation. Existing graph.ask is reused for grouped reports;
proposed detail tools call the same canonical costing service. No second calculation
engine, arbitrary formulas, new queue or browser calculation is introduced.

### Post-design Constitution Check

| Principle | Concrete design evidence | Result for this design |
|---|---|---|
| Source → Evidence → Reality | Matched slices trace through movements and reviewed attribution to components/evidence | PASS |
| Reality owns state | Derived generations/findings, no document fulfillment or cost status fields | PASS |
| Proven schema only | Production authority/storage prerequisite remains explicit; no migration or table approval inferred | PASS |
| Tenant/shared service boundaries | Identity-derived tenant, same service on every surface, foreign generation refusal, no-autoflush reads | PASS |
| Spec/test traceability | Existing FR/DR mapped to slices A–E and named test families; no unimplemented acceptance marked complete | PASS |
| Explainable UI | Decimal values, known subtotals, coverage and basis metadata; bounded provenance | PASS |
| Received values | Exact stated amounts retained; only allocations and observations derived | PASS |
| Simplicity | Narrow graph extension and shared snapshot reads; preserve established APIs and classes | PASS |

This PASS certifies the design's stated boundary, not production readiness. Implementing
it requires a separately concrete and reviewed production evidence/history/storage model
and per-slice task generation/analysis. Full integrated qualification needs an actual production integration candidate. This
design makes its prerequisites concrete without claiming that those prerequisites have
passed. Prepare and review the production schema/history proposal next; any revision of
the existing pre-implementation qualification gate must be explicit owner review of that
concrete proposal, never an inference from a restricted fixture override.

Spec impact: existing target requirements clarified at the integration boundary; runtime
behavior unchanged. Rollback/retention and saved-report incompatibility rules are in the
adapter contract. No repository-wide tool/schema/catalog generation is needed until
those executable definitions actually change.

## Concrete production schema proposal

The owner's next continuation authorizes preparation of the schema/history proposal,
not silent activation of the previously gated production slices. See
[production-data-model.md](contracts/production-data-model.md) for fields, same-tenant
constraints, revision/conservation rules, input membership, indexes, rollback and proofs.

First candidate slice: receipt basis, component basis, signed attribution revision/parts,
receipt review/categories, component replacement and correction admission, plus durable
input manifest and typed members. Shared received
financial components stay authoritative; positive cost-centre assignments keep their
current meaning. No FIFO policy is needed merely to explain an individual receipt's
acquisition cost. Subsequent inventory and DB slices add their explicitly proven typed
policy, ownership, matching, return and context-history records. Do not migrate every
future target entity in the first slice.

Read-only history audit found that SourceRecord versions alone do not freeze all product
inputs: manual document headers can change, movement economic time is not knowledge time,
and source arrival precedes interpretation. The chosen design reuses tenant-serialized
event sequences, admits immutable normalized inputs and seals exact manifest membership.
Manual evidence used for costing requires an append-only correction path and protection
from destructive edits. Later document/line context versions preserve contribution
grouping history. Bootstrap declares the earliest supported knowledge boundary.

### Constitution and architecture review status

| Check | Evidence | Result for proposal |
|---|---|---|
| Received authority | Existing FinancialComponent values, exact source shares, no generated unit-price authority | PASS |
| Shortest links | Receipt basis -> Movement; component basis -> FinancialComponent; typed matching/return targets | PASS |
| Schema proof | Each family names calculations/joins/constraints and FR evidence; first slice separated | PASS |
| Tenant/confirmation | Composite FKs, active-owner execution, expected revision, shared lock order and action replay | PASS |
| Historical trace | Retained input membership/event cursor; no cache FK owns financial decisions | PASS |
| Storage discipline | PostgreSQL, Decimal, shared workers, bounded stage/cursor, no new scheduler | PASS |
| Migration/rollback | No migration identifier reserved; destructive financial-history downgrade refuses | PASS |
| Owner/schema approval | Concrete proposal prepared; not inferred from planning instructions | OPEN — implementation gate |
| Integrated/reference qualification | Existing exploratory evidence remains non-release evidence | OPEN — proposed release gate after explicit owner approval |

The OPEN rows are not claimed as a passed implementation Constitution Check. All
technical proposal principles pass at the design boundary; self-review cannot approve
production expansion. The owner is asked to review the concrete four decisions in the
proposal, including the explicit gate-order revision needed to test actual integration.
No feature code, migration, company settings or runtime registry changes in this turn.
Per-slice tasks/analyze and test-first implementation follow that review. Referenced
shared scheduling contract and adapter-delivery limits remain binding.


## Approved receipt-cost implementation

The owner accepted the four concrete production decisions. This supersedes earlier
planning-only and pre-implementation qualification restrictions. The Constitution Check
is PASS for the approved first-slice schema and implementation: received evidence,
shortest typed links, tenant scope, explicit owner confirmation and immutable history
remain mandatory. Full integrated/reference qualification is now a release gate.
No company policy activation or release is part of this implementation.

Implement in `domain/costing.py`, `db/costing.py`, `services/costing.py` and
`tools/costing.py`. Register a single typed `cost.change` proposal command and read-only
`cost.receipt.get` / `cost.evidence.get` tools through the existing application/MCP
pipeline. Reuse its atomic finance-command execution while enforcing an authenticated
active owner and explicit confirmation for costing even in auth-disabled environments.
Public services also enforce action/actor/evidence binding, not only adapter permission.

The first slice uses bounded receipt-scoped manifests (at most 100 contributing component
revisions); larger or ambiguous scope refuses before capture. These operational bounds
are explicit and do not claim full-tenant reconstruction. Domain allocation/tax/sign
rules are pure Decimal. Input normalization reuses finance components without invoking
their cost-centre decisions. Same-currency base-unit receipts are the initial supported
scope; unreviewed conversions/ownership/inventory/DB remain unavailable rather than zero.
Manual replacement evidence is a distinct immutable received document/component, with
atomic predecessor retirement; it creates no posting or payment.

Migration 0064 follows the current checkout's 0063 head; this is migration ordering only,
not a semantic dependency on global search. The migration is static, enforces tenant
constraints and refuses a destructive populated downgrade. Shared core edits are narrow
hooks for registered metadata and admitted-evidence correction protection; preserve the
parallel feature235 changes. First-slice proofs precede implementation. Full required
backend and migration suites, scoped lint, tenant/catalog/spec/docs checks follow.

## Inventory calculation foundation (approved continuation)

Implement `domain/inventory_costing.py` as a pure, typed Decimal calculation over a frozen
pool supplied by future shared services. No persistence, endpoints, new dependencies or
company activation. Do not import benchmark code into production. Preserve the measured
prototype's cumulative rounding principle, but require exact structured return portions,
retain original receipt identity across return chains, and separate outbound reasons.
Use immutable Pydantic inputs and dataclass outputs, explicit method selection, canonical
UTC ordering, and local Decimal precision 80. Reject above 10,000 events or 20,000 total
input/output portions before publishing any result. No partial result on refusal.

Constitution Check: PASS. Results are derived observations; opaque provenance references
remain in every portion; no source amount is recomputed, no business table/query or
adapter rule is added. Tenant isolation and policy/ownership authorization remain the
responsibility of the not-yet-exposed service boundary. No migration or rollback work is
needed for this pure module; removal changes no retained financial authority.

Test first: fixture A/B consumption, C2 return ordering, K2 monetary residuals, late-cost
replay, exact selection, repeated/partial returns, unknown-cost quantities, shortages,
invalid data, UTC ordering, immutability and bounds. Run the complete costing regression
family against disposable PostgreSQL, scoped Ruff and spec policy. Also run the complete backend suite sequentially to avoid the previous parallel
worker watchdog contention; this isolated domain module has no existing production
import or observable adapter change. Frontend,
migration and generated-catalog checks are unchanged by this stage.

## Reviewed bounded inventory service

Use contracts/inventory-service.md for this approved continuation. Constitution Check:
PASS for retained source inputs and explicit decisions, shortest typed links, same-tenant
FKs, trusted owner confirmation, read-only derivation, PostgreSQL/Decimal and bounded
reads. No new technology/dependency. Economic ownership is explicitly confirmed; shipment
alone does not establish consumption. All five table families are proven by FR-004–008,
FR-015/016/019; no disposable calculation cache is needed for this bounded scope.

Add request models in domain/costing.py; models in db/inventory_costing.py; static 0065
migration; private inventory helpers in services/inventory_costing.py delegated by public
services/costing.py; read tool and existing cost.change proposal/MCP extensions. Tests
precede implementation. Keep unrelated feature-225/235 changes intact. Existing global
search import-order findings remain a separately reported shared completion gate, not
an unresolved inventory requirement or Constitution exception.

Run inventory/receipt/migration/permission/catalog/isolation tests, then complete backend
regression, scoped/full lint, spec policy and generated-document checks. Full reference
qualification and later return/specific/correction/ownership expansion remain release
work; do not mark full US2/DB product complete. Reads do not replay live tenant history.

## Contribution calculation foundation

Implement domain/contribution.py with frozen Pydantic inputs, immutable dataclass
outputs and local Decimal precision 80. One trusted context encloses at most 10,000
matched slices. Each input carries the same context; mismatches refuse, including
tenant, generation, policy, profile revision and effective/knowledge cutoffs. Only
commercial_v1 is supported. Aggregate by a fixed dimension allowlist; partition currency
and base unit unconditionally. Preserve original slices as trace and preserve direct
versus allocated selling cost. No database, service, tool, graph or UI registration.

Constitution Check: PASS. This is read-time arithmetic on supplied evidence/decisions,
not authority creation; references are opaque, money uses Decimal, no schema expansion
or new dependency, and no authorization boundary is exposed. The future service owns
match conservation, revision admission, authorization and retained document context.
Removal has no persisted-data effect. No migration or catalog generation is needed.

Tests first in tests/test_contribution.py: fixture A, adapter-delivery's partial-scope
examples, independent selling coverage, zero/negative revenue, signed corrections,
weighted rates, missing dimensions, currency/unit/context separation, bounds, duplicate
identities, precision and immutability. Run costing regression, full sequential backend,
scoped/global lint and spec policy; keep unrelated shared-gate findings visible.

## Current contribution preview

Constitution PASS: read-only derivation follows existing true FKs and received net
evidence; no schema, policy activation, stored match, source recomputation or adapter
rule. Implement private services/contribution.py through public costing.contribution_preview;
reuse finance.components received evidence, inventory_cost and domain/contribution.py.
Extend domain context with an explicit preview mode and absent generation/profile
revision; force final amounts/rates unavailable in that mode even with reviewed inputs.

Bound each ambiguity probe to two rows and reuse the existing bounded inventory read.
Only one full invoice line and one full shipment are supported; no allocation, graph
aggregation or historical endpoint. Check every lookup's tenant, exact commitment/
customer/owner, quantity/unit/currency, live correction flags and retained consumption.
READ COMMITTED is required and a changed start/end event cursor refuses. No migration.

Tests first: fixture A known DB1=570; unknown DB2/final DB1, exact trace, no writes,
foreign tool/MCP/service access, missing net, stale inputs, ambiguous billing/shipments,
quantity/unit/currency/customer mismatch and concurrent event change. Register command,
resource, action-discovery and tenant vocabulary; regenerate docs and fixture commands.
Run targeted domain/service/catalog/adapter tests then complete sequential backend,
scoped/global lint, docs/catalog and working-tree spec policy gates.

## Confirmed single-line contribution

Use contracts/contribution-service.md for this continuation. Constitution PASS: typed
retained source/context inputs and confirmed full-quantity binding, shortest FKs through
line/movement basis/inventory member, composite tenant isolation, Decimal/UTC, no stored
DB or consumed value. Two narrowly proven table families implement the approved revenue
match/history design without premature general allocation/profile infrastructure.

Add db/contribution.py and static migration 0066; extend domain/costing.py requests and
services/costing.py dispatch/protection, with private confirmed helpers in
services/contribution_reviews.py. Reuse production contribution/inventory kernels and
current candidate validation. Add public reviewed_contribution and shared tool/MCP reads.
Tests precede implementation, especially immutable replay and duplicate-quantity guards.
Snapshot hash canonicalization reuses the existing Decimal/UTC inventory helper.

The approved full model's general profile/context families remain future work: this
review captures only exact admitted whole-line context and scope-specific profile approval.
No schema expansion beyond the two proven families, scheduler change or new dependency.
Run migration/FK/rollback, costing/service/tool/isolation/catalog tests, then full sequential
backend, scoped/global lint, documentation generation/idempotence and spec gates.

## Source-backed selling allocation and DB2

Constitution PASS for this approved production-model continuation. Reuse component and
attribution revision authority, add only typed selling targets and review membership/
category decisions proven by FR-011/014/015/016. Same-tenant FKs and existing owner
confirmation/serialization enforce boundaries. No stored DB2, source recomputation,
new dependency, alternative adapter logic or background work.

Implement contracts/selling-service.md in domain/costing.py, db/contribution.py,
services/selling_costs.py and existing costing/contribution review delegates. Extend
tools/costing.py schema; static0067 migration. Add tests before code for arithmetic,
sign/conservation, exact target, source-family exclusivity, tax/currency, zero/unknown,
revision/withdrawal/history, confirmation/isolation/rollback and migration retention.
Run full costing/catalog/migration regressions, complete backend, lint, docs generation
and spec gates. Shared global-lint findings remain an explicit completion gate.

## Retained record inspection

Constitution PASS: read-only retained inputs, shortest real FK links, tenant-scoped fixed
allowlist, explicit bridge redaction, no source recomputation/schema/background work.
Implement contracts/record-inspection.md in domain/cost_records.py, private
services/cost_records.py behind public costing.cost_record, tools/costing.py and the
existing application/MCP/CLI registration. Web api delegates to that same tool; extend
Inspector/register metadata and existing page controls without browser business rules.
Tests precede implementation; exact values and frozen-record meaning remain independent
of current valuation state. Use current catalog generator and preserve concurrent work.


## Shared retained cost-query context

Constitution Check: PASS. Implement contracts/query-context.md without schema changes.
Use domain/cost_query.py for typed selectors and compatible retained basis identity;
services/cost_query.py delegates existing inventory/contribution readers and resolves
only their shortest retained policy/review links. services/costing.py exposes cost_query.
Tools/MCP/CLI and the thin web/api.py GET adapter use the same service; no browser
calculation is needed.
Tests/test_cost_query.py precedes implementation and proves cutoff constraints, tenant
boundaries, historical isolation, unchanged arithmetic and unknown/current/stale states.
No migration or generalized profile authority is needed for this bounded query surface.
A published-generation context remains a later extension; null generation/profile
revision fields explicitly prevent treating single-scope approval as global approval.

The contribution algorithm identity is exported by domain/contribution.py itself and
referenced by the query envelope; adapters do not maintain their own version label.


## Generation publication guard

Constitution Check: PASS for this domain-only stage of T080. No schema, source values,
financial authority, scheduler or adapter changes. Implement
domain/cost_generation.py after tests/test_cost_generation.py. Typed immutable context
contains exact retained-manifest identity, policy/profile identities, UTC cutoffs and
algorithm version. Publication checks consume trusted storage facts; they do not claim
to verify an FK, authenticate a caller or acquire a database lock.

Use constant-size completion counters rather than loading work items or derived rows.
Explicit compare-and-swap expectations prevent the future service from silently replacing
a newer pointer. Input sealing, content verification and actual counts must be supplied
by the future transactional service. Publication disposition and cost evidence coverage
remain independent. No generic workflow engine or dependency is needed.

Tests cover business races, incomplete capture/work, count mismatch, tenant/context
isolation, backward cursor, idempotent publication and late evidence. Run costing domain
regressions, spec policy and scoped lint; keep storage/concurrency/full-suite acceptance
open. This stage cannot close T080 or claim a usable grouped-report generation.


## Stored inventory generation integration

Constitution Check PASS: reuse retained CostInventoryReview membership and existing
financial kernels; persist disposable observations only. Three typed caches are the
smallest schema that separates retained input identity, canonical numeric observation
and atomic publication. Approved production model section7 and owner continuation
cover this refinement. Single bounded work needs no staged-work table or new queue.

Tests precede db/cost_generations.py and static migration0069, followed by private
services/inventory_generations.py, public costing.py wrappers, the scoped selectable
in services/analytics/costing_relation.py and jobs/handlers/costing.py registration.
No tool/UI adapter is introduced yet. No existing cost-query response changes.
Update data_model/resource/tenant isolation catalogs and durable contracts. Migration
rollback discards caches only and refuses unfinished jobs; retained authority survives.

Run PostgreSQL migration/concurrency/worker and costing regression suites, catalog/spec,
scoped/global lint, generated documentation and required backend checks. No fixture-J
or whole-tenant performance assertion follows from this bounded integration. Existing
review checklist and shared full-release gates remain separate.

## Bounded historical inventory selection

Continuation of the approved T080 bounded-read work, without schema expansion. Add
`inventory_cost_snapshots` to services/costing.py, delegating to the private generation
service. Validate a concrete list/tuple of 1–100 distinct nonempty string identities
before database access. In no_autoflush, check tenant and issue one joined query over
generation, snapshot, review and policy with explicit tenant constraints on every
relation. Pin exact IDs; never resolve publication pointers or query live event maxima.
Sort by generation ID, reject missing members before constructing any response, validate
each persisted checksum through the same helper as the single reader, and reuse its
context serialization. Return `mode=historical_selection`, count, rows and persistence
flags, with no invented common context or aggregate. Existing single-read shapes stay
unchanged. No schema/migration, graph/tool/API/CLI change or worker registration.

Constitution Check: all eight principles PASS. Shortest retained links and tenant scope
remain; source values and approvals are untouched; this is a bounded read of disposable
observations. No UI logic or new infrastructure. Rollback removes the new reader only.
Test first in tests/test_inventory_snapshot_selection.py: real source-backed two-item
reviews, exact single-read parity, different cutoffs, stable order, foreign/missing
member equivalence, corrupt output, validation and two-query/no-flush/no-replay proof.
Update tenant operation classification and coverage evidence; run affected costing,
catalog/spec and scoped lint checks. Existing global release gates remain open.

## Joint inventory confirmation

Refine the approved inventory review model without schema expansion. Reuse the real
review -> action and review -> event links as joint-confirmation identity. Domain
InventoryScope contains the existing single-item scope fields/validators; InventoryReview
adds the existing Change/operation fields unchanged. InventoryBatchReview adds 2–10
scopes and validates distinct items plus identical effective cutoff, owner and currency.
Expand CHANGE and the existing cost.change schema, not a second mutation entrypoint.

Private inventory service converts each scope into the existing item request with the
batch reason/cursor, checks members in stable item-ID order and passes remaining batch
movement/receipt budgets to the same admission logic. Preview rechecks the event cursor
after reading all members. Execution already holds the tenant lock and savepoint; emit
one existing cost.reviewed event, then reuse existing _execute with its recorded_at
as the explicit common knowledge time. Individual paths retain their previous timestamp
behavior. No batch sum or new approval row. Return confirmed action identity, common
cutoffs/event and per-item retained review responses. Stored contexts expose the actual
review action ID so downstream code can distinguish joint from independent confirmation.

Constitution Check: all eight principles PASS. Existing shortest links/tenant boundaries,
confirmed owner decisions, received evidence and FIFO kernel are reused. No schema,
queue, source recomputation, browser rule or duplicate authority. Rollback disables the
new operation while preserving already retained standard reviews and action history.
Tests first in tests/test_inventory_batch_review.py: domain shape/compatibility, real
MCP proposal and confirmation/replay, common retained context and historical rebuild,
stale/foreign/permission refusal, total bounds and injected second-item rollback. Run
costing/catalog/spec regression, generated docs/idempotence and scoped/global lint.
Full release, broad scale and reporting gates remain open.

## Complete joint inventory publication and totals

No new schema: immutable batch action membership plus the existing per-review publication
rows define readiness. All-members-present is a derived predicate, not a second authority
or a new financial approval. Add private services/inventory_batch_generations.py behind
public costing.build_inventory_batch_generation and inventory_batch_snapshot. Resolve
an executed cost.change InventoryBatchReview, validate exact retained review/policy
membership against action input/output and the shared cost.reviewed event. Bound every
membership query to eleven rows and use existing tenant/action FK indexes.

Build under READ COMMITTED, a tenant/action/version advisory transaction lock and one
savepoint; call the existing builder in stable review-ID order with the same deadline.
Do not hold the tenant business lock. Existing member caches are reused; failure rolls
back only the attempted work. Read pins the entire publication vector in one query,
checks completeness, then reuses the bounded checksum-validating selection reader.
At most eight statements independent of selected membership count. Decimal totals use
a local precision context and unit partitions; no cacheless financial replay. Historical
is default; current mode samples the event cursor last and suppresses stale numbers.

Extend existing costing.inventory.refresh config to exactly one of review_id/action_id,
preserving old review configs and version1 meaning. Recheck owner and scope; return only
counts and opaque generation references. Existing claim fencing, timeout, rollback and
migration job guard cover both forms. No new schedule, queue or startup migration.
Constitution: all eight principles PASS; shortest retained links, scoped queries, no
source recomputation, no schema/authority/UI expansion. Rollback removes new entrypoints
and batch config support only after draining those runs; retained reviews remain readable.

Test first in tests/test_inventory_batch_generations.py: source-backed complete/partial
read, sums/unit partitions, corruption/non-disclosure, no-flush/eight-query/historical
behavior, failed second build, retries, independent concurrent sessions, late intake and
actual shared worker child. Run affected costing/job/catalog/spec and scoped/global
checks, generated references and documentation tests. Full release gates stay open.


Publication-lock refinement from the real concurrency proof: compute every missing
member through the existing retained historical reader before inserting any cache rows.
Cache inserts acquire PostgreSQL tenant FK key-share locks; therefore running subsequent
financial replay after the first insert could block intake's tenant FOR UPDATE lock.
Pass only these internally verified observations to the shared private publisher, then
publish all members in the short final phase. Existing caches need no replay. If a cache
observed present disappears before publication, refuse/retry rather than replay after
writes have started. A brief commit/publication lock is permitted; blocking intake through
financial computation is not. The test separately pauses during computation to admit late
intake and between member writes to prove readers see no partial committed publication.

## Canonical SQL inventory reporting foundation

Refine T081's relation prerequisite without exposing premature graph measures. Extend
services/analytics/costing_relation.py with one validated, tenant-constrained join source
over existing generation/review/policy/snapshot tables and a flat typed selectable with
explicit stable column names. Refactor inventory_generations._read_selection to use
that same source while preserving its membership/checksum/context response contract.
Keep the existing constant-size single-snapshot relation unchanged. No new ORM fields,
migrations, adapters, financial formulas or disposable output population.

Constitution: all eight principles PASS. Exact generation IDs, shortest retained links,
explicit tenant predicates and canonical Decimal values preserve authority. Tests first
in tests/test_inventory_costing_relation.py: real two-item SQL/service parity, typed
numeric columns, grouped currency/unit semantics, tenant/invalid-input isolation, empty
versus zero, and stability against live Item metadata and publication-pointer changes.
Run affected inventory/cache/concurrency/catalog/spec regressions, scoped/global lint
and documentation gates. SQL compilation and execution against PostgreSQL is required;
a string-only query test is insufficient. Rollback restores the private selection join.

The graph integration still needs an explicit requested context, a protected read basis
through final aggregate execution and saved-query/transport propagation. A selectable
alone does not satisfy those requirements. Existing grouped-report deferrals stay open.

## Historical inventory graph execution

T125–T128 implement the bounded JSON/report slice of T081. Add InventoryCostContext to
Traversal, validate root-only costing questions before SQL, and register costing.inventory
as a canonical (already complete) SQL derivation. The compiler uses its typed subquery
directly instead of joining another snapshot anchor. Existing anchored derivations stay
unchanged. Declare bilingual inventory_valuation properties and two unit-aware measures.

The private joint reader gains an internal protection option: after pinning publication
IDs, SELECT FOR SHARE OF generation,snapshot in deterministic ID order, verify all rows
exist, then run the existing checksum reader. Locks last through the caller transaction,
so deletion/update cannot invalidate checked values before aggregation. Publication-pointer
changes do not matter after pinning. This bounded row-lock strategy replaces a new
repeatable-read transaction (tools already start a transaction for tenant admission).
It locks disposable cache rows only, not tenant/intake rows. No schema changes.

Compiler results carry resolved basis metadata; graph tools/API pass it through. Saved
Traversal definitions naturally retain typed context. The path formatter explicitly
refuses unsupported context. SQL preview uses an empty typed canonical relation, never
JSON materialization. Do not add UI controls in this slice. Constitution I–VIII PASS:
existing authority, scoped shortest links, Decimal, shared services, no writes/approval.
Rollback removes the additive graph node/context only; retained costing remains intact.

Test first in tests/test_inventory_graph_reporting.py: actual SQL sums/partitions,
context refusal, missing/foreign/corrupt inputs, saved-report round trip, empty filters,
historical stability, no autoflush/replay, bounded reads, and independent-session cache
mutation protection. Run inventory and reporting regression suites, docs generation/tests,
spec policy and scoped/global lint. Keep overall T080/T081/release gates open.

## Historical inventory selector

T129–T132 extend the approved T081 UI slice. Add a read-only inventory_review_options
service using existing retained review/policy/action/party tables with explicit tenant
predicates. One grouped query identifies executed joint confirmations (2–10 retained
reviews sharing cutoffs/owner/currency); continuation resolves an exact same-tenant action
in that relation. Order by retained event sequence; limit 1–50 plus one continuation row.
Expose metadata only, not readiness, totals or new authority. graph.ask remains the
integrity/coverage admission boundary. No history replay, cache read/build or writes.

Register graph.inventory_reviews.list through existing graph schemas/application tools,
command/resource/tenant catalogs, and a thin analytics API endpoint. The Analysis Builder
uses that same read via graphApi. Add typed request/basis metadata to api.ts and preserve
context in Plan/planOf/question; new ordinary list plans carry none. A separate selector
component handles paged discovery/loading/error/empty states without choosing a default.
Changing/clearing context uses the existing request-generation cancellation boundary.
Result basis comes from the backend, not client calculations. Disable text conversion
for inventory context with a localized explanation; retain normal editor behavior.

Constitution I–VIII PASS: no schema or accounting changes, shared services, scoped reads,
explicit human selection, no financial mutation. Tests first: real PostgreSQL pagination,
tenancy, bounds/no-flush/no-replay/tool/HTTP, visual-plan round trip and deferred-response
state tests. Verify frontend build/i18n, reporting/costing/catalog regressions, generated
docs, spec and lint. Rollback removes selector/discovery only; saved context remains
supported by the historical graph executor. DB1/DB2 graph/UI and overall release remain open.


## Contribution SQL arithmetic prerequisite

T133–T136 refine approved T081 without schema or surface expansion. Export immutable
commercial_v1 term definitions from domain/contribution.py and consume them in both
the existing Decimal kernel and analytics/contribution_aggregates.py. The latter builds
typed SQLAlchemy aggregate expressions over already admitted amount/state columns;
it performs no I/O and is not an authorization or canonical population resolver.
Callers must establish tenant/context, unique slice grain and currency/unit partitions
before use. No JSON population, source matching, pagination, or adapter-side formulas.

Use conditional sums of same-slice expressions and independent state counters. Empty
aggregates have zero known/counters and null final values. Use exact PostgreSQL numeric
quotient/remainder to implement the domain half-even percentage rule; PostgreSQL round
alone rounds ties differently. Do not persist any aggregate or duplicate source values.

Constitution I–VIII PASS: pure derived arithmetic, shared fixed profile, Decimal/numeric,
no schema/authority expansion, no reads/writes or new public service. Rollback removes
the internal helper and restores equivalent domain term literals. Tests precede code:
real PostgreSQL parity for all 256 input-state combinations, fixture A, partial groups,
preview/empty/zero, signed returns, weighted rates, rounding ties and large values.
Run domain and SQL tests, affected reporting regressions, scoped/global lint and spec
policy. T080/T081 and release remain open until retained contribution publication,
compatible report admission and graph/UI integration are separately implemented.


## Joint contribution confirmation prerequisite

T137–T140 refine the approved contribution review model without schema expansion.
Factor ContributionScope from ContributionReview and add ContributionBatchReview with
2–10 distinct positions to the existing CHANGE union and cost.change MCP schema. Use
`positions` rather than the inventory-only `scopes` property to preserve both schemas.
Private contribution_reviews._check_batch reuses every single-line admission and then
checks distinct shipment basis and common retained inventory action/cutoff/knowledge/
event/owner/currency through tenant-scoped shortest links. Recheck the tenant cursor
after the bounded preview. Execute within the existing owner/action binding, tenant
lock and savepoint. Pass the shared cost.reviewed event's recorded_at to each member
without changing single-line output or digest semantics. Return stable ordered member
results plus explicit common basis and profile_scope_action_id, never aggregate values.

Constitution I–VIII PASS: confirmed authority through existing tables/action/event,
received source values unchanged, shortest tenant-scoped links, same shared services,
no new schema/scheduler or company policy activation. Existing reviewer checklist
continuation applies. Rollback removes batch dispatch after outstanding proposals are
resolved; retained individual reviews remain reproducible via existing historical reads.

Tests first in tests/test_contribution_batch_review.py: actual two-item inventory and
revenue preparation, preview without writes, owner confirmation, exact shared event/time,
DB1/independent DB2, replay/history, stale/foreign/revoked owner, duplicate/bounds,
incompatible inventory scope and second-member failure rollback. Existing contribution,
selling and inventory-batch tests, tenant/catalog, generated docs and spec/lint checks
follow. T080/T081 remain open pending protected retained report publication/integration.


## Stored joint contribution observations

T141–T144 continue the approved production disposable-generation model. Add two cache
tables in db/cost_generations.py and static migration 0070: cost_contribution_generation
(action_id, algorithm_version, completed_at, output_hash; unique tenant/action/version)
and cost_contribution_snapshot (generation_id, review_id, goods_cost,
known_direct_selling_cost, known_allocated_selling_cost, selling_complete; unique
tenant/generation/review). All IDs are opaque and links use composite tenant FKs.
Money is NUMERIC(18,4). Revenue/dimensions remain on retained revenue basis through
review, never copied. Derived DB amounts/percentages are not persisted.

One fixed algorithm and atomic bounded generation make a separate mutable publication
pointer unnecessary. Existence means complete publication; corrupt/incomplete stored
output refuses. Downgrade drops only disposable caches and refuses unfinished
costing.contribution.refresh jobs. No startup migrations or new queue.

Private services/contribution_generations.py validates executed action input/output
against retained reviews, revenue bases, inventory members/reviews/policies and the
actual event. Reuse historical reviewed_contribution for all financial reconstruction
before writes, under a tenant/action/version advisory lock and savepoint. Exact
membership plus input/output digest checks guard publication. Do not fabricate one
policy_revision_id for multiple item policies to fit a single-policy domain guard.
The action supplies joint authority; individual retained policy IDs remain visible.

Historical reader uses no_autoflush, pins and locks only generation/snapshot rows
FOR SHARE, verifies complete membership and digest, then executes a typed canonical
SQL relation through contribution_aggregate_columns for positions and unit/currency
groups. The digest includes retained fields used by the SQL relation, all selected
review hashes and canonical cached values. No live cursor or source-history scans.
Public costing services expose build_contribution_generation/contribution_snapshot.
Register owner-authorized costing.contribution.refresh in the shared job registry,
returning counts and references only. No direct new tool/UI endpoint.

Constitution I–VIII PASS for the approved staged cache model: justified numeric fields
serve bounded SQL reads; authority stays on retained inputs; shortest scoped links,
no source recomputation or financial worker approval. Tests precede implementation:
true joint scope, cached/domain/SQL parity, no replay/no flush, partial DB2, stable
history, corruption/foreign/missing refusal, atomic failure/deadline, same-action
concurrent build and worker execution/revocation; migration constraints/rollback.
Update catalog/tenant/coverage/docs; T080/T081 and full scale/release remain open.

### Historical contribution graph implementation

Reuse contribution_generations._resolve/_load and contribution_relation; register
a canonical costing.contribution node without schema changes or new authority.
Add a typed explicit historical context and fixed contribution measure sources
compiled exclusively through contribution_aggregate_columns. Restrict admission to
standalone questions and explicit currency/base-unit partitions. Use existing graph
tools, HTTP and saved-report services. Tests cover partial/complete filtered groups,
weighted ratios, missing/corrupt/foreign bases, saved context and no FIFO/flush.
Constitution check: PASS; scoped immutable authority, protected disposable cache,
shared arithmetic and no alternative adapter rules. UI selection follows this graph
contract; release/scale qualification remains separate.

Reuse the existing valuation selector and basis components with an explicit contribution
variant, a shared bounded discovery service/tool and thin HTTP route. Extend the typed
question roundtrip and catalog percent unit. Verify save/reopen/no-auto-selection/error
behavior in the real browser, plus transport/tenant discovery regressions. No new schema.

### Selected contribution freshness (T150–T153)

Extend the existing shared contribution snapshot reader with validated historical/current
mode and private freshness helpers. Read the tenant's existing event cursor after final
SQL; reject cursor regression and non-READ-COMMITTED current reads. Historical reads
do not touch the live cursor. Graph admission validates mode before exposing canonical
SQL and calls the same final guard after aggregation, including empty filtered results.
No new schema, job, mutable pointer, algorithm or financial authority. The existing
contribution context overrides the historical-only mode without changing inventory.
Reuse selector cancellation/error handling and preserve current mode on selection.

Constitution check I–VIII PASS: shared tenant-scoped read, no ORM writes/FIFO replay,
existing cursor and retained authority, explicit bounded scope and honest freshness.
Tests first cover initialized/missing/pending/history, invalid mode/isolation, rebuilding
an old scope, late intake between admission and final SQL, no intake lock, save/restore
and browser toggling. Run existing contribution/inventory, graph, catalog, UI and docs
checks. This prerequisite does not close company publication or fixture-J qualification.

### Company population closure before storage/publication

T154–T157 introduce an internal pure domain boundary in domain/cost_population.py.
Use distinct typed inventory-item and contribution-line entries rather than a generic
record registry. A frozen PopulationBasis binds tenant, exact cutoffs, committed input
cursor and fixed allowlisted algorithm. Expected subjects retain canonical input SHA256
fingerprints; evaluated subjects must match the exact expected identity and fingerprint.
Each fingerprint is produced by the future trusted census/input resolver and includes
its own policy/review revisions or missing-input state. It is not supplied by users.

Require exact set equality independently for inventory and contribution, including
duplicate detection on both sides. Refuse tenant/context mismatch before returning
coverage. Count independent known/unknown dimensions after membership closes, preserving
empty/partial/complete states. DB2 known requires DB1 known within a contribution row.
This O(n) background-builder validation performs no database reads, numeric derivation,
worker scheduling or financial confirmation. It does not run on report read paths.

Constitution I–VIII PASS: no schema expansion, dependency or authority; typed opaque
identities, exact retained-input boundary, unknown costs preserved, public APIs unchanged.
Tests precede implementation: missing/extra/duplicates despite equal counts, tenant and
cutoff/watermark/algorithm mismatch, stale fingerprints, input order, empty population,
independent four-metric coverage, strict counts/states and a large deterministic census.
Run domain regressions plus spec/lint checks. No browser/catalog regeneration is needed
for this internal-only module. Census storage, chunked builders, atomic publication and
fixture-J qualification remain subsequent integration work under T080/T081/T089.

### Current source-backed census (T158–T161)

Add private services/cost_census.py behind costing.capture_company_cost_census. Require
REPEATABLE READ before reads, validate aware cutoff and strict combined record bound.
Within no_autoflush, validate tenant and obtain pg_current_snapshot(), statement timestamp
and visible event watermark. Use tenant-scoped outer event aggregates and stable ID order
to retain movements without exact recorded events. Load invoice/credit headers and lines
independently of reviews. Include all candidate lines with unassessed economic scope;
report empty headers. Enumerate latest source versions via scoped anti-exists and join
current ImportJob/InterpretationOutcome using tenant, source, job and attempt identities.

Each result is metadata/record fingerprints only. Distinguish record fingerprints from
PopulationExpectation input fingerprints, which require policy/matching resolution.
No persistent manifest, financial state or new tool/API is introduced. Census records
and gaps are bounded; amount arithmetic stays absent. Public service is classified in
the tenant catalog. Constitution I–VIII PASS: source/reality discovery, shortest links,
no schema, explicit unknowns, shared service and read-only snapshot isolation.

Tests first use real PostgreSQL/application services: unreviewed movements and invoice/
credit/service lines, future movement exclusion, header-only gap, source pending state,
missing/duplicate events, strict bounds, wrong isolation, no writes/FIFO, foreign/missing
tenants, repeatability under concurrent intake and no lock on ordinary intake. Run
affected census/domain/catalog/isolation checks and document retained-manifest/company
worker integration as open. This is not the full-scale chunked census yet.

### Company publication domain integration (T162–T165)

Extend domain/cost_generation.py with a distinct CompanyGenerationBasis containing the
PopulationBasis context, kind=company, scope key, retained manifest ID, canonical expected
population hash and company-v1 orchestration version. No fictitious policy/profile fields.
Generation accepts the existing basis or this company variant. The existing publication
function requires ExpectedPopulation and EvaluatedPopulation for company candidates;
selected-scope calls remain compatible and refuse extraneous population arguments.

Canonical hashing sorts typed subject identities, includes the complete PopulationBasis
and input fingerprints, and uses SHA256 over deterministic JSON. The hash binds membership;
it does not substitute for retained members. Compare candidate context/hash, call exact
close_population and compare actual/expected row counts to closure before allowing the
existing publication guard. Reject company/selected context mixing; allow new company
manifest/member revisions within the same tenant/scope/effective cutoff. Compare complete
same-ID candidates, refuse obsolete cursors and preserve compare-and-swap retry semantics.

Constitution I–VIII PASS: no schema, dependency, authority, financial arithmetic or API
extension. This is trusted builder validation, not a user-supplied sealed-manifest claim.
Storage must establish historical admission, retained revisions, hashes and locks. Rollback
removes the unused company variant; existing selected services continue using their basis.
Tests first cover mixed per-subject fingerprints, canonical ordering, manifest substitution,
missing/duplicate/context-mismatched outputs, row-count mismatch, foreign tenants, no
population proof, financial unknowns, empty scope, retries, stale work and pointer races.
Run the publication/population and costing domain suites, scoped lint, spec and diff gates.

### Proposed retained census storage (T166–T169; owner approved)

Design: contracts/company-census-retention.md. Five tenant-scoped tables separate current
observation retention from CostInputManifest financial admission. A clean REPEATABLE READ
transaction captures typed members and exact mutable values atomically, with request-key
idempotency, strict row/byte bounds, same-capture header links and immutable sealed history.
Reads inspect frozen values; full verification remains builder work. No public write tool,
financial approval, scheduler entry or report computation is added in this proposed stage.

Constitution design check: I/II/IV/V/VI/VII/VIII PASS as proposed; III schema use cases
are documented and owner schema approval was granted on 2026-09-19. The approval is narrower than financial-manifest or publication
readiness. No revision number is reserved; recheck actual Alembic head at implementation.

Proposed files: db/cost_census.py, a new reviewed migration, private
services/cost_census_storage.py, shared services/costing.py entrypoints and an internal
record collector in services/cost_census.py. Test files: test_cost_census_storage.py and
test_cost_census_migration.py, plus existing census, catalog and tenant regression tests.
Update data_model.yaml, resource_catalog.yaml, tenant_isolation_catalog.yaml and generated
references as part of implementation. The table/transaction/rollback/test contract is in
the proposal; historical financial resolution is separately required after this stage.

Retention implementation detail: use explicit version-1 column allowlists and full UUID
capture/member identities. The existing manual-line correction service checks retained
line references before deletion and returns domain guidance; it still allows otherwise
permitted edits, whose old values remain in the snapshot. Test this FK consequence at
the service boundary rather than exposing a raw IntegrityError.

### Retained review resolution (T170–T173)

Add private services/cost_census_resolution.py behind costing.resolve_company_cost_census.
Require REPEATABLE READ and no_autoflush. Reuse full retained-census verification and its
validated member rows, without re-reading mutable source amounts. Group captured movements
by observed item identity; keep all retained sales lines. Enforce max_subjects 1..10 before
any valuation calls. Select same-tenant reviews through introduced BusinessEvents at or
before the captured cursor. Use canonical inventory_cost/reviewed_contribution with explicit
review IDs so integrity checks, costing and separate DB2 coverage stay centralized.

Compare exact captured movement identities to retained inventory-member movement identities;
compare review context/cursor to captured cutoff/cursor. Contribution joins its retained
inventory member/review to validate the inventory cutoff, and compares economic_at. Return
per-subject result only at compatible captured context; otherwise return historical basis_result
and explicit gaps. Return opaque review IDs/content hashes as references, not as a complete
company financial input fingerprint. Keep unresolved source and header gaps separately.

Constitution I–VIII PASS: no schema, authority, policy activation, public adapter or shared-job
extension. Existing readers perform arithmetic; the resolver only joins retained contexts.
Test before implementation: unreviewed/service/credit candidates, compatible stock and DB1,
missing DB2, older cutoff/cursor, later review ignored, exact membership mismatch, bounds,
foreign census, unsupported isolation and no flush/write. Run affected storage/cost review,
catalog/isolation tests and spec/lint. No new migration or browser check is required.

### Contribution-only event relevance (T174–T177)

Introduce private services/cost_review_relevance.py for the retained-census resolver only.
Within its existing REPEATABLE READ transaction, inspect at most 100 same-tenant events
between the selected review cursor and census cursor (query 101 to detect overflow).
Require event_type cost.reviewed, schema v1, action subject/action identity, exact payload
operation contribution_review or contribution_batch_review, same-tenant executed
cost.change with recorded actor/decision time, and validated typed action request.
Query the persisted contribution reviews and revenue bases for that exact introducing
event/action, prove exact unique target-line set against the request and matching event
sequences. Refuse missing/extra/duplicate/foreign or malformed evidence. Do not trust just
the event label, a JSON target ID, or action output.

For inventory all proved contribution-only reviews are non-invalidating. For contribution,
any event containing the queried line remains invalidating. Every other event and interval
overflow is conservative. Return proof metadata (from/to cursor, proved event IDs) in the
resolver for traceability; no new financial input fingerprint or common knowledge cutoff.
Canonical costing, cutoff/movement checks and unknown coverage remain unchanged. No new
schema, public command, confirmation, job or activation. Constitution I–VIII PASS.

Tests first: ordinary stock plus DB confirmation simultaneously available; other-line
review allowed; same-line/unknown/unconfirmed/malformed/foreign/missing/duplicate proof
refused; late costs still pending; bounded overflow; no SQL writes or flush. Run resolver,
review/storage and tenant regressions. This is a closed writer contract, not general
input-specific invalidation or company publication.

### Common captured review basis (T178–T181)

Extend the existing resolver response with captured_basis; do not add a parallel public
service or schema. Add domain/cost_captured_basis.py with a pure, canonical assembly helper
for trusted verified service data. Bind census ID/hash, tenant, effective_at, observed_at,
snapshot identity and event cursor. Exact expected identity sets come from the verified
census collector already loaded by services/cost_census_resolution.py, independently of
the resolved rows. Validate exact unique membership and result/selected review identity.

Each vector member retains selected review ID/hash, scope state/gaps, canonical result
digest, own knowledge time, policy/profile and linked inventory identity, and the full
freshness proof. Reuse canonical census digest serialization and existing Coverage;
derive coverage solely from available result fields, never basis_result. Preserve
header/source gaps in the digest. Keep publication_eligible=false and retained=false.
The digest is an observation integrity binding, not financial admission or the fingerprint
accepted by company publication. A future retained financial manifest must explicitly
establish its supported knowledge model; this assembly does not waive that gate.

Tests first: exact/duplicate/missing/extra membership, mixed context, canonical ordering,
zero/null/empty and independent DB1/DB2 coverage, historical basis not counted, altered
result/proof/gap changing digest, old capture stability, real joint goods reviews,
unreviewed header/source gaps, tenant/bounds, SELECT-only and no flush. Run existing
resolver/relevance, inventory/contribution, storage and catalog/isolation regressions.
No migration/rollback beyond reverting this additive response field is required.
Constitution I–VIII PASS: approved scope, existing authority, shortest retained links,
scoped collector, no schema, no alternative arithmetic or publication.

### Proposed captured-basis retention (T182–T185)

Design: contracts/captured-basis-retention.md. Three typed tables retain the existing
read-time basis vector, using census and selected review references. They do not reuse
the receipt manifest's historical knowledge_at contract or mutate sealed census rows.
Version 2 separates lifecycle flags from canonical digest content; verify existing v1
exports without relabelling their digests. No derived monetary authority or new scheduler.

After owner schema approval, implement domain versioning, db/cost_captured_basis.py, a
fresh-head migration, private services/cost_captured_basis.py and three internal costing
entrypoints. Reuse canonical readers and census verification. No public write adapter.
Add migration/service/replay/rollback/concurrency/isolation tests first, then extend the
executable data-model/resource/tenant catalogs and regenerate documentation. Explicit
bounds are ten subjects, 1 MiB per member/header and 8 MiB total; no scale qualification.

Constitution technical design I–VIII PASS: source/authority preserved, shortest typed
links, scoped queries/FKs, service boundary, tests first and explicit immutable retention.
Governance: the owner explicitly approved the new three-table captured-selection family
at T183 on 2026-09-19. Implementation follows that approval. Existing scope approval authorizes proposal
preparation, but the earlier census approval is not silently broadened. See the contract
for exact invariants, alternatives, transaction/rollback and acceptance test matrix.

T183 gate update: explicit owner approval received on 2026-09-19. The complete Constitution
Check for this three-table slice now passes; proceed test-first under the contract.

### Captured known-subtotal summary (T186–T189)

Add a bounded internal costing.captured_cost_summary service backed by private
services/cost_captured_summary.py. Call pinned replay once; never reconstruct selection
or read mutable invoice/item values. Bind returned groups, coverage, unavailable rows
and gaps to the retained basis ID/digest. The caller supplies no amounts or row arrays.

Build at most ten typed SQL VALUES rows solely from verified canonical replay output.
This internal calculation input is neither a graph/compiler relation nor an arbitrary
JSON recordset adapter. Contribution aggregation reuses the existing fixed
contribution_aggregate_columns(reviewed=False): canonical received net, consumed goods
cost and independently supported direct/allocated selling cost. Do not introduce a new
DB formula or manufacture a shared ContributionContext. Explicit preview arithmetic
keeps all final totals/rates absent. Inventory uses fixed numeric SUM/count observations
partitioned by currency/base unit/method/owner; no new FIFO or unit-cost calculation.

Read-only builder diagnostics only; do not feed these VALUES into graph.ask or bypass
its canonical retained-generation relation. The eventual report integration still uses
the approved publication/SQL relation contract. No schema, UI, cache or scheduling change.
Register the one shared service in tenant isolation and regenerate applicable catalogs.
Constitution I–VIII PASS for the approved staged summary scope.

Tests first: real fixture stock/DB1/DB2, multi-position missing-selling DB2 subset, unknown
and stale subjects, mixed currency/unit/ownership partitions, empty/known-zero, no
percentage averaging, exact Decimal amounts, stable old basis after new intake, tenant
refusal and SELECT-only/no-flush. Include existing SQL aggregate/kernel, replay/storage,
reporting and tenant/catalog regressions.

### Approved integration: captured report publication

#### Fixed captured graph context (T194)

Constitution I–VIII PASS for this bounded integration. Add a frozen
`CapturedCostContext(generation_id)` to the existing traversal request. It is mutually
exclusive with `inventory_cost_context` and `contribution_cost_context`, valid only on the
corresponding standalone valuation nodes, and never resolves `cost_publication`. The
compiler continues to use the existing `costing.inventory` and `costing.contribution`
derivations; their relation loaders dispatch to a typed captured SQL relation only when
this explicit context is present. The relation joins cached rows to retained basis members
and generation/basis/census metadata, preserving shortest evidence links and tenant scope.
Contribution aggregates reuse `contribution_aggregate_columns(reviewed=False)` so final
totals/rates stay null while known subtotals and coverage remain visible. Inventory exposes
sum/count coverage columns from the same row relation.

Tests precede implementation and prove fixed-generation graph/tool/HTTP execution, saved
analysis reopening after a newer publication, unknown-member coverage, partitioned
currency/unit/owner/method results, foreign/missing/unsealed refusal, no fan-out, no replay,
and continued historical-context behavior. This adds no mutation adapter, worker,
larger-population support, financial admission or second arithmetic engine.

#### Captured report discovery and selector (T195–T197)

##### Bounded captured-report worker build (T198–T200)

##### Bounded captured publication worker (T201–T203)

Keep publication in a separate default READ COMMITTED worker transaction. Its strict
configuration contains `generation_id` and nullable `expected_previous_id`; authorization
revalidates the active owner and sealed same-tenant generation. The handler calls the
existing tenant-serialized CAS service and returns only whether the pointer changed plus
the opaque generation reference. Same-generation retry is unchanged; stale, ambiguous,
obsolete or wrong-previous requests fail atomically. No latest selection or financial
eligibility is introduced.

##### Shared cost findings (T204–T207)

Constitution I–VIII PASS without schema expansion. Add four contiguous catalog classes
after the existing class ordering and one internal cost-finding provider in
`services/exceptions.py`. The provider reads retained costing authority and verified
published observations through shared costing services/selectables; it does not replay
FIFO, approve reviews or treat disposable output as authority. Every query and relationship
is explicitly tenant-scoped. Finding identities exclude generation IDs, while causal values
and trace carry the exact review/component/generation basis and freshness.

Tests precede implementation and cover missing acquisition cost, unassigned component,
stale review, supported negative DB1, incomplete-scope refusal, unsold subjects, stable
identity, clearing, pending preservation, foreign-tenant non-disclosure and coexistence
with legacy classes. Register the classes in the executable exception/resource/reference
catalogs and regenerate documentation. The existing projection refresh materializes the
combined canonical list; projection-backed page/count/register reads remain the only
operational queue basis. Extend their metadata only as needed to expose consumed cost basis
and lag without adding another queue or read-time rebuild. Fixture-J performance remains a
separate T089 qualification gate. T205/T206 depend on T080's financially admissible exact
company generation and must not consume the diagnostic captured-report publication or
promote per-review caches into a complete company basis.

Constitution I–VIII PASS without schema expansion. Register one strict owner-authorized
database-only job with exactly `basis_id`. Admission and execution revalidate the sealed,
same-tenant retained basis. The runner opens REPEATABLE READ for this job, matching the
existing builder contract, and the handler calls `build_captured_cost_generation` with no
direct ORM output writes. Retry reuses the verified generation; the safe result contains
counts and one opaque `cost_generation` reference, never amounts. CAS publication remains
a separate READ COMMITTED operation and is not silently combined with this transaction.

Constitution I–VIII PASS without schema expansion. Add one bounded SELECT-only discovery
service over sealed `cost_generation` rows joined to their retained basis/census and
optional publication pointer. It returns identity, capture/effective metadata, family
counts, algorithm, publication marker and current/pending freshness, never amounts or an
approval claim. The opaque continuation is tenant-scoped and ordered by captured event
sequence plus generation identity. Expose it through the existing graph tool/MCP/HTTP
adapter and use it in the Analysis selector for either valuation node. Selecting a captured
generation clears the historical context and vice versa; saved questions retain the exact
generation ID. Captured result explanation names the retained basis and coverage and does
not assume historical `knowledge_at`, owner or complete company value.

See contracts/captured-report-publication.md for the concrete four-table amendment to
the approved generic cache model, exact service/transaction boundaries, alternatives and
test-first acceptance matrix. Reuse retained selection and canonical arithmetic; keep
the captured diagnostic branch distinct from historical financial company publication.
Owner acceptance at T191 authorizes the captured report runtime and migration.
Constitution I–VIII PASS; the schema/basis amendment governance gate is closed.
The implementation analysis found no critical inconsistency in this bounded slice.

T191 gate closed: owner approved the concrete four-table amendment on 2026-09-19.
Constitution I–VIII PASS. Implementation paths: domain/captured_report.py,
db/captured_report.py, services/captured_report.py, shared costing entrypoints, migration
0079_captured_report (current sole head 0072), executable catalogs and tests/test_captured_report.py.
Tests precede implementation: domain cursor/CAS/context refusals, real migration parity,
tenant/member/shape/immutability guards, real build/retry/rollback/read and publication,
unknown/partial/decimal/pagination behavior, concurrency and cache deletion. No public
adapter, shared worker or financial approval is created by the internal storage slice.

### Proposed financial company generation storage (T080 continuation)

Design: contracts/company-generation-publication.md. Seven typed tenant-scoped tables
separate retained financial-input authority from disposable company calculation results.
The manifest retains one sealed census, an actual committed cursor/knowledge timestamp,
typed inventory/contribution members with their own optional approved reviews and complete
input fingerprints, plus exact unresolved header/source gap counts and a canonical gap
digest. The generation result tables reference existing checksum-verified
inventory/contribution caches or explicit unknown results; they do not copy source amounts
or introduce a second calculation engine. A scope-keyed CAS row publishes only after exact
population, persisted member, checksum, work/count and cursor guards pass.

Constitution I–VIII PASS: shortest typed authority links, explicit tenant FKs,
PostgreSQL/SQLAlchemy storage, received-value preservation, shared worker/services and no
browser rules. The owner approved this concrete seven-table boundary on 2026-09-19.
Implementation remains test-first and does not broaden the approved authority.

### Proposed partial commercial matching (T085)

See `contracts/commercial-matching.md`. Preserve the legacy one-line/one-shipment tables
unchanged and introduce a separate append-only commercial match revision with typed
inventory and direct-evidence parts only after explicit owner approval. This is the
shortest model that supports partial/many-to-many billing, exact frozen inventory cost
portions, signed returns and service/free-goods dispositions without storing calculated
margin or weakening historical constraints.

Constitution I–VIII PASS conditionally: every proposed table is tenant-scoped and links
the shortest retained authority; source-stated revenue remains distinct from derived cost;
confirmation uses the shared application service and no document status, location or
human number becomes authority. The owner approved this boundary on 2026-09-20; the
schema gate is closed for the test-first implementation described here.

### Canonical source-backed costing demo (T083)

Version the immutable international baseline to `international-v2`; do not change the
ongoing `demo_data` order generator into a costing authority. The baseline adds three
named, bounded stories through `services/demo_profile.py`: a complete fixture-A trade,
a deliberately incomplete missing-cost trade and a late-cost/return trade. Every amount,
quantity and relationship begins in a lossless `demo_profile` SourceRecord and reaches
the ordinary Document/DocumentLine, Movement and cost application services. The manifest
retains only opaque references, coverage labels and the profile version; it does not copy
derived DB1/DB2 values as authority.

The complete story states net revenue 1,200 EUR, receives 100 pcs with acquisition cost
1,050 EUR, ships and bills 60 pcs, and explicitly reviews its inventory and commercial
match so the existing read services derive remaining quantity 40 valued at 420 EUR,
fulfilled/billed quantity 60 cost-matched at 630 EUR and DB1 570 EUR. Its reviewed
selling-cost inputs reproduce the separately specified fixture-A DB2 only through the
existing contribution services. The missing-cost story deliberately omits acquisition
cost authority and must remain quantity-visible but financially incomplete. The late
story first retains an incomplete basis, then adds separately sourced late cost and an
explicit signed customer return matched through the reviewed return/commercial authority;
historical revisions remain readable.

Initialization uses a new private profile-costing orchestrator called only inside the
existing `company_setup.initialize` transaction and `_profile_scope`. The authority is
bound to the exact run, owner, tenant, transaction and fixed `international-v2` recipe.
It may call the same costing preview/execute services used by `cost.change`, but it may
not accept arbitrary adapter input, authorize other finance commands, commit independently
or survive the initialization transaction. Proposal/action and business-event records
remain the audit authority; no direct ORM creation of cost approvals is permitted.

Replay uses the existing active-run completion marker: an active/archived run is a no-op,
an interrupted pre-publication transaction rolls back atomically, and a retry uses the
same source external IDs and request identity. Live Demo Data connection/start remains
after baseline initialization and its later pause/stop state is never reset by request
replay. No schema, job registration, queue, schedule or browser timer is added.

Tests precede implementation and cover identical-request replay, interrupted initialization,
foreign/removed-owner refusal, inability to use the authority outside the bound setup
transaction, preservation of a later paused/stopped Demo Data connection, exact compatible
quantity coverage, the visible missing-cost gap, late-cost/return history, source lineage
and truthful capability wording. Constitution I–VIII PASS: the slice reuses normal source,
evidence, reality, costing and scheduler boundaries; it records received values, derives
observations only on read and adds no schema or alternate business rules.

### Acquisition-to-carrying-value bridge (T086)

Implement the smallest reviewed bridge on top of the retained inventory review. One
immutable assessment revision references the exact inventory review,
effective/knowledge cutoff, predecessor, kind (`write_down` or `recovery`), owner action,
reason and introduced business event. Child scope parts reference exact remaining
inventory members, source evidence, quantity and the source-stated total assessed value
for that quantity. They do not duplicate item, owner or policy links. Unit values are
display-only derivations and never received authority.

The domain calculator reconciles each assessed part against the frozen acquisition-cost
portion. A write-down must state a non-negative value below that ceiling. A recovery must
supersede a prior assessment for the same exact scope and may restore value only up to
the historical acquisition-cost ceiling. Unassessed remaining quantity retains
acquisition value. Mixed currency/unit, consumed/non-remaining members, overlapping
parts, stale expected sequence, foreign-tenant links and unsupported precision refuse
before writes. No percentage, market value, legal conclusion or posting is inferred.

The shared inventory read derives `carrying_value`, acquisition-to-carrying adjustment,
assessment state and exact trace from retained inputs. Current reads become stale after
relevant changes; explicit review/assessment identities reproduce historical answers.
Generation, captured-basis and reporting consumers receive the same service result and
continue to expose independent acquisition/carrying coverage. Tools and adapters call
the service through the existing confirmed `cost.change` path.

Migration rollback removes the nullable assessment identity and carrying observation from
the disposable inventory cache before dropping the new assessment header and part tables;
it refuses while retained assessment history exists. The change does not alter source
payloads, movements, inventory acquisition reviews, commercial cost, DB1/DB2 or ledger
entries.

Constitution Check: PASS. Source evidence and explicit owner judgment remain authority;
carrying value is derived. The shortest links are assessment → inventory review and part
→ inventory member/source. Every table and query is tenant-scoped. Tests precede domain,
storage, service, tool and adapter implementation. PostgreSQL, Decimal, UTC, immutable
revisions and the shared proposal/confirmation boundary are retained.

## T087 allocation and conversion design

Implement in domain → services → tools/adapters order. First add a pure Decimal allocator:
normalize neither weights nor source amounts; calculate exact proportional quotas, truncate
toward zero to four decimal places, then assign remaining 0.0001 increments by descending
absolute remainder and ascending opaque target ID. Restore the source sign after allocating
its absolute magnitude. Return exact residual when the requested total is below capacity.

Weighted acquisition allocation is a new `cost.change` request variant that resolves to the
existing `CostPart` representation before persistence. Existing explicit `assign` remains
compatible. Preview and execution call the same allocator and bind its canonical inputs to
the proposal hash; execution rechecks event sequence, evidence fingerprint and owner. No
additional allocation table is needed because exact confirmed shares already are the
business decision and the action retains the proposal inputs.

Non-identity conversion requires one retained `cost_conversion_basis_revision` plus one
nullable same-tenant conversion-basis FK on each of `cost_attribution_part` and
`cost_selling_attribution_part`. The revision contains only source evidence, kind, exact
from/to codes, positive `Numeric(28,12)` numerator/denominator, effective time, predecessor
and the normal event/action audit. Each part retains its original source share; converted
quantities or monetary values remain read-time observations. A guarded migration must
validate existing rows, enforce tenant FKs and refuse downgrade while conversion history
exists. Conversion chains and automatic inverse lookup refuse.

Service checks prohibit currency conversion for tax classification, inferred skonto,
conversion chains, inverse lookup and mixed conversion kinds in one part. Identity paths
continue without a conversion record. Unit conversion is admitted only where the target
quantity remains exactly representable at four decimals. Currency results use the same
four-decimal allocation boundary before inventory or contribution consumption.

Constitution Check: PASS subject to explicit owner schema approval. The proposed basis is
the smallest typed authority repeatedly joined and constrained by costing; source payloads
and values remain unchanged, relationships use shortest same-tenant links, derived amounts
are not persisted as evidence, and all adapters retain the shared confirmation boundary.
Tests precede the domain kernel, then schema, service, tool and documentation changes.

Rollback: remove the nullable attribution link only after proving it unused, then refuse
to drop populated conversion revisions. No existing attribution, receipt, inventory,
contribution or ledger history is rewritten.

Owner approval recorded 2026-09-20: the conversion revision, both typed nullable part links,
`Numeric(28,12)` ratio precision and closed `quantity`/`equal`/`manual` driver vocabulary are
approved for test-first implementation. This does not approve policy activation or posting.

## T088 operational explanation delivery

Implement one read-only React cost-explanation component over the existing tenant-scoped
`GET /cost-query` adapter. Keep the returned context/result dictionaries intact at the API
boundary and interpret only their documented presentation fields. The component owns display
hierarchy, localization, freshness/gap wording and Inspector links; all calculations remain in
`reality-core` services. Mount inventory explanations inside the existing Warehouse inline
preview using the row's opaque item ID. Reuse the component from Analysis and later from exact
document-line contribution previews rather than introducing page-specific calculations.

Tests precede UI code: a browser contract fixture must prove no mutation request, exact retained
values in the explanation, display-only currency rounding, stale-basis labeling, missing-value
wording, trace navigation and company switching. TypeScript build, formatting, i18n audit and
the affected browser harness are technical gates. Fixture M's moderated five-user protocol is
recorded separately and stays open until real participant evidence exists. No migration, new
financial authority, browser cache or alternate API is introduced.
