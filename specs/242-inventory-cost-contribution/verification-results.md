# Phase 0 execution evidence

Latest work: [source-backed selling costs and DB2](#source-backed-selling-costs-and-db2).
The earlier sections preserve the initial v2 experiment and its historical measurements.

Status: receipt costs, inventory kernel, bounded reviewed inventory service and pure contribution kernel implemented; broader inventory/DB/graph/UI integration and integrated/reference release qualification remain open. Earlier prototype measurements remain historical evidence.

## Authorization and artifact analysis

The owner explicitly requested implementation of the Phase 0 performance experiment.
Before code, tasks.md was generated and spec/plan/tasks were analyzed read-only: 13
bounded tasks, no CRITICAL conflicts for the experiment. Full product requirements were
explicitly deferred rather than falsely covered by prototype tasks. The six unchecked
requirements-checklist entries concern future benchmark/product gates and remained open.
No extension hooks were configured. Application/web/chat edits belonging to other work
were left untouched.

## Test-first evidence

- Kernel test collection initially failed because costing_kernel did not exist.
- PostgreSQL contract collection initially failed because costing_dataset did not exist.
- Partial-return ambiguity test then failed (no refusal for mixed original cost layers);
  the kernel was corrected to require exact partial-return provenance.
- Append-only late-cost/history tests failed because adjustment evidence did not exist;
  the experiment gained an independent same-tenant adjustment relation and cutoff reads.
- Targeted suite after the final precision/guard changes: **20 passed** on isolated PostgreSQL (evidence/costing-tests.txt).
- Complete backend run: **2,900 passed, 9 skipped**, exit 0, in 571.01 seconds
  (evidence/backend-tests.txt). The suite includes one transaction-cleanup warning in
  the existing storyline library HTTP test. The final experiment-only precision and
  guard additions were separately rerun in the 20-test suite; no application code changed.

Ruff passes when invoked from `packages/reality-core`, matching the Makefile contract.
A root-directory Ruff invocation selected different import classification and reported
unrelated imports; no unrelated files were auto-fixed. Spec policy passes after adding
the two new test families to docs/SPEC_COVERAGE_MATRIX.md.

## Environment

PostgreSQL ran in the dedicated `reality-costing-234` container, image postgres:17-alpine,
loopback port 55434, CPU limit 4 and memory limit 8 GiB. The Python benchmark process
ran on the macOS host outside that limit. Other development containers also exist.
Therefore this is not the enforced dedicated combined 4-vCPU/16-GiB reference envelope.
No existing company database was used. Initial and v2 synthetic databases were created
solely for this work. No production migration or product catalog was changed.

## Additional precision review

A maximum Numeric(18,4) fixture exposed a real rounding error with the default Decimal
precision: cost 99999999999999.9999, quantity 99999999999999.9997 and consumed quantity
25000000000000.0000 must produce 25000000000000.0001, not .0000. The failing proof was
observed before setting an 80-digit local intermediate context. Source/output precision
remains four places; no source amount is recomputed or rounded away. A separate failing
proof now rejects finer-than-supported base quantities instead of silently accepting them.

## Evidence status

`evidence/initial-exploration.json` is explicitly superseded: its synthetic late-cost
update mutated input amounts, and its code digest was captured after edits. It is not
accepted qualification evidence. The v2 run uses append-only source-referenced adjustments
and captures the code digest before the run. The final direct and projected runs use the same code digest and baseline adjustment
revision 30, and produce the same reconstruction checksum. The projected run then
appends revisions 31–60 and verifies incremental output against complete reconstruction.
`direct-preliminary.json` is a superseded 20-sample run; final evidence is `direct.json`
and `projection.json`.


## Final measurements and decision

Each of two tenants has 100,000 orders, 10,000 items, 1,000,000 movements,
1,000,000 components, 1,000,000 attribution parts and 600,000 matching parts.
Read timings include serialization, use five concurrent readers and 200 samples per
measured surface after warmup. These are local synthetic measurements.

| Workload | Direct p95 | Projected p95 | Budget |
|---|---:|---:|---:|
| Order explanation | 142.38 ms | 2.47 ms | 500 ms |
| Prototype tool response | Not measured | 3.38 ms | 3,000 ms |
| Inventory page and totals | Not measured | 7.49 ms | 2,000 ms |
| Monthly item report | Not measured | 89.95 ms | 3,000 ms |
| Prototype attention summary | Not measured | 387.99 ms | 2,000 ms |

Direct reconstruction took 12.06–12.41 seconds; reconstruction plus projected publication
took 16.97–20.40 seconds. Thirty late receipt adjustments refreshed 3,000 affected issue
rows each, with p95 217.57 ms while five readers were active. One change per second was
sustained. The 150 reads during these update rounds had p95 67.12 ms; this separate phase
is not the full 200-sample mixed-load protocol.

The reduced CLI smoke run uses a separate fresh target, 20 samples and two updates;
its JSON is retained as execution evidence, not performance qualification.

Provisional architecture: keep one canonical calculation kernel. Use bounded direct
replay for order explanations where it meets the budget, and indexed, rebuildable
observations for inventory and reporting aggregates. Never make derived outputs a
second source of accounting authority. This experiment supports investigating that
architecture; it does not approve production tables or demonstrate product integration.

## Remaining qualification gates

- Enforce the combined dedicated 4-vCPU/16-GiB reference envelope and measure cold cache.
- Run the complete mixed-load protocol and distribute adversarial return, credit, tax,
  partial matching and source-history cases through the full-size dataset.
- Integrate the canonical relation with the existing analysis compiler, actual tools
  and exception register; validate their complete responses and tenant boundaries.
- Prove product freshness, completeness, approval invalidation and source-version history.

`qualification_passed` is intentionally false; exit 2 records successful exploration.
Fixture J, production schema approval and product acceptance remain open. All Phase 0
prototype tasks can close without closing these broader gates.

## Final self-review

The prototype is isolated from application services and migrations. Decimal arithmetic,
append-only late evidence, same-tenant foreign keys, atomic replacement and deterministic
reconstruction are covered by executable proofs. Experimental SQL/COPY is confined to
the disposable benchmark, not a new product persistence path. No public tool/catalog,
scheduled handler, company-setup flow or UI was changed by this work. Existing unrelated
changes were preserved. Human architecture and PR review remain distinct from this
implementation self-review; no merge or deployment was performed.

Final Ruff, formatting, spec-policy and diff whitespace checks passed. The dedicated
experiment container was removed after retaining all reports; existing containers and
company databases were left untouched.


## Continuation: capped adversarial qualification and integration design

Owner authorization covers the next load experiments and a concrete integration design.
Read-only spec/plan/tasks analysis covered T014–T019 with no CRITICAL scope conflicts:
all implementation remains in the disposable experiment; production/schema and exact
reference-host gates remain open. The six reviewer checklist gates remain unchanged.
No extension hooks are configured. The integration contract now lives at
[product-integration.md](contracts/product-integration.md).

Three new behavior proofs failed before implementation: return cost reversal, adversarial
matching/distribution and explicit stale/live responses (`evidence/v3-test-first.txt`).
An additional concurrent-intake proof failed with a PostgreSQL lock timeout before the
publication-only lock correction (`evidence/v3-lock-test-first.txt`). Final targeted suite:
**26 passed in 4.99 seconds**, including refresh failure/rollback/retry and a slow-reader
proof that the input stream remains active throughout mixed load (`evidence/v3-tests.txt`).
No production code changed, so the previous full backend result remains separately
identified historical evidence; the expanded experiment tests are the current proof.

`v3-preliminary.json` exposed input-rate saturation (one-per-second not sustained) even
though query/refresh latency alone met their budgets. It is superseded by the corrected
mixed protocol and frozen-revision publisher. Its code digest intentionally differs.
The early `v3-reduced.json` is likewise a smoke run of the preliminary implementation.
The final runner includes sustained input rate in its measured budget verdict.

Environment: `evidence/v3-environment.json` records actual Docker image IDs and limits.
PostgreSQL is capped at 2 CPUs/4 GiB and Python at 2 CPUs/2 GiB, both without swap.
This enforces a combined upper bound of 4 CPUs/6 GiB. It is stricter in capacity than the
specified envelope but shares an 8-GB Docker VM; it is not a dedicated 16-GiB reference
host, nor certified cold OS cache or SSD I/O evidence. Existing services are untouched.


### Final capped projection result

See [measurement table](evidence/v3-projection.md) and `evidence/v3-projection.json`.
Each tenant retains the fixed one-million-movement profile, including 9,000 receipt-family
returns. Split/partial matching, signed supplier credits and stated nonrecoverable tax are
now distributed through the full fixture. The final run starts at adjustment revision 30
and ends at 61; full replay reconciles **all fields of 609,000 contribution observations
and 10,000 inventory pools**, not just their cost totals.

Three full reconstructions including publication take **19.715 / 20.602 / 19.599 seconds**.
Under five concurrent readers and at least one scheduled change per second, per-surface
p95 is order **29.33 ms**, inventory **34.51 ms**, monthly **89.66 ms**, attention
**126.89 ms**, and tool state response **22.18 ms**. All have 200 samples. Thirty-one
late changes actually commit at the requested cadence; publication p95 is **515.52 ms**,
maximum **712.14 ms**, for 3,000 affected rows per refresh. The final measured local
budgets pass. Python process peak RSS is about 1.14 GiB under its enforced 2-GiB limit.

Readiness matters: only **128/200 mixed tool responses are current**; 72 correctly return
not-ready. Ordinary displays retain explicitly stale output while the conservative
tenant-wide generation is pending. These timings do not establish 200 ready live answers.
The ready read-only phase separately measures 200 current responses per surface; tool p95
is 2.54 ms there. Product live availability therefore remains an explicit gate. The
integration design specifies dependency-scoped freshness plus bounded direct fallback,
with complete manifest consistency for multi-pool aggregates.

The corrected publisher releases the input stream during calculation, freezes the exact
adjustment revision and acquires the tenant lock only for publication. A source arriving
during replay is not mislabeled processed. Failed publication retains the previous
visible generation, and retry catches up. This is proven for immutable synthetic base
inputs and append-only adjustment revisions, not arbitrary product source-history changes.

### Restart probe

The dedicated PostgreSQL container was stopped by its main server's shutdown and then
started again, resetting PostgreSQL shared buffers. Sequential first reads afterward
(`evidence/v3-restart.json`) took order 10.54 ms, inventory 2.95 ms, monthly 28.69 ms,
attention 53.81 ms and tool 0.70 ms, all current at revision 61. No read launches a rebuild.
There is one sample per surface; later reads may benefit from earlier reads. The shared
VM's OS cache was deliberately retained, so this is not the full cold-cache qualification.

### Remaining decision gates after this continuation

1. Exact dedicated reference host and cold OS/database reconstruction with I/O/query
   evidence; the local 4-CPU/6-GiB cap is supplemental, not a revised acceptance target.
2. Bounded reconstruction parts and fenced atomic manifest through the actual shared
   worker, including timeout, outage, retry and competing claims.
3. Compiler contribution-slice grain and actual tool/exception adapter parity and queue
   delta with all four cost classes; synthetic SQL surfaces cannot certify these.
4. Scope-specific live-answer availability, retained source-version/cutoff history,
   review invalidation and remaining FX/ownership/credit matching product cases.

The concrete integration design is complete for review. The feasible local load checks
are executed and recorded; full fixture J and production architecture approval remain
open. No product migration, company policy, catalog or UI is activated by this work.


### Direct comparison under the same cap

The final direct strategy (`evidence/v3-direct.json`) uses the same source digest and
resource limits. It reads input revision 61 after the projection run's appended
changes, so its checksum is not compared with the projection's earlier revision-30
baseline. Across 200 sampled orders and five readers, direct order p95 is
**154.94 ms**; complete reconstruction takes
15.10–16.09 seconds. This supports investigating a bounded direct
fallback; it does not prove its latency under simultaneous update load or arbitrary
production FIFO dependency depth.

Final self-review: experiment-only implementation and proposed integration contracts
preserve source authority, tenant boundaries and one calculation kernel. Ruff, formatting,
local document links and diff whitespace checks passed. Spec policy passed before the
concurrent feature-235 test appeared; its latest global result is recorded below. Source hashes match
the final measured code. No product catalogs or core public functions changed, so no
catalog generation or production migration checks are applicable to this continuation.


### Final shared-workspace gate status

After the final measurements, concurrent feature-235 work added
`packages/reality-core/tests/test_global_search_matching.py`. The last global spec-policy
check fails because that unrelated test family has no coverage-matrix entry yet. Its
implementation was left untouched. T019 remains unchecked until that shared gate is
restored; no claim of fully green repository acceptance is made. Feature-234's own two
test families are mapped, and its 26 tests, lint/format and measured local budgets pass.

`evidence/v3-reduced-final.json`, `v3-projection.json` and `v3-direct.json` have the same
final costing source digest. The final reduced run is a CLI smoke proof, not a latency
qualification. All dedicated costing containers and their disposable anonymous volumes
were removed after evidence was retained; unrelated containers were preserved.


## Scoped live availability continuation

Owner instruction: continue. Spec/plan/tasks T020–T023 preserve the experiment-only
Constitution boundary. Scope/fallback/bound tests failed with the missing live-reader
entrypoint before implementation (`evidence/live-test-first.txt`). The new reader uses
one repeatable-read snapshot, only relevant late-input dependencies, and the same kernel
behind a limit-plus-one preflight. An unaffected order does not inherit tenant-wide lag.
Global aggregate freshness and product gates are unchanged. No extension hooks exist.

The prior backend suite is not rerun for this experiment-only change; the complete
costing test families are rerun against isolated PostgreSQL. Feature-235 files continue
to change independently and remain outside this implementation's scope.


The additional unresolved-target test exposed an unsafe ready answer from direct fallback:
a late component with no known assignment cannot be made scope-current by replaying only
known assignments. The failing proof is retained in `evidence/live-unresolved-test-first.txt`;
the final implementation refuses it as `unresolved_dependency`. Final targeted suite:
**30 passed in 7.92 seconds** (`evidence/live-tests.txt`). This also covers financial-part
limits before replay, selling adjustments, read-only behavior and exact response parity.
The preliminary full run was stopped to include this correction in final timing; its
partial observations are explicitly nonqualifying (`evidence/live-preliminary-aborted.json`).
Its committed immutable input dataset is reused, while derived output is rebuilt.


### Final scoped-live result

[Full measurement table](evidence/live-projection.md), raw `evidence/live-projection.json`
and actual `evidence/live-environment.jsonl` retain the final evidence. Both processes
again have the combined 4-CPU/6-GiB upper bound; the shared VM still does not certify the
exact dedicated reference environment. The final source digest matches the checked files.

**200/200 mixed-load tool responses are current**, comprising **174 projected** responses
and **26 bounded direct** calculations. Half the requested scopes deliberately target the
last order of the changing hot pool. Tool p95 is **1.107 seconds**, maximum **1.987 seconds**,
within its 3-second budget. This closes the measured 128/200 readiness gap from the prior
experiment under a harder hot-pool request distribution; it is not a controlled speed
comparison or a production availability guarantee. Current means assessed at the request's
snapshot, not that missing financial evidence has become complete.

Mixed p95: order display 57.23 ms, inventory 89.64 ms, monthly 192.97 ms, attention 265.70 ms.
Those aggregate/display paths retain explicit stale states while a generation is pending;
only the order-scoped live tool path gains the direct fallback. Thirty-six input changes
sustain the one-per-second cadence throughout all readers. Publication p95 is 1.098 seconds
(maximum 1.125 seconds). All 609,000 observations and 10,000 inventory pools match full
reconstruction. Three reconstructions including publication take 32.641, 30.852 and
42.494 seconds. Local measured budgets pass; `qualification_passed` remains false.

The unresolved-target refusal, movement/financial bounds and snapshot stability are
separate correctness proofs. Their refusal cases cannot be counted as current answers;
the measured current count contains no such refusals. No application migration, actual
MCP adapter, worker handler, accounting policy or production catalog was changed.

### Isolated review and shared workspace

The shared workspace's global spec-policy check now reports four untracked feature-235
test families without coverage mapping (matching, migration, service and web). These
parallel changes were preserved. To evaluate this patch independently, a temporary clean
archive of the tracked baseline was overlaid with the six costing Python files, spec242
and the current coverage matrix. **Spec policy passes in that isolated review**; its
scope and baseline are recorded in `evidence/live-isolated-review.json`, with command
output in `evidence/live-isolated-policy.txt`. This establishes the costing patch's policy
compliance without claiming the shared working tree is green or editing feature235.

The isolated costing test suite also passes: **30 passed in 10.36 seconds**
(`evidence/live-isolated-tests.txt`). Scoped Ruff/format, local links and diff whitespace
checks pass. Temporary review files and all owned costing test containers/volumes were
removed after retaining evidence. T019 remains the shared-workspace final gate, separate
from the now-green isolated costing review and the completed scoped-live experiment.

Next architecture work remains bounded shared-worker reconstruction and actual
reporting/tool/exception integration, followed by the exact reference-host checks and
reviewed production schema. The present result does not authorize or implement those
product changes implicitly.

## Bounded shared-worker continuation (2026-09-18)

T024–T028 follow the reviewed isolated-worker plan. The initial failing import test is
retained in `evidence/worker-test-first.txt`. The implementation adds a frozen generation,
bounded whole-pool ranges, transactional staged rows/cursor and an atomic publication
pointer. Shared queue and real child execution use the static experimental bootstrap;
normal product registry and migrations remain unchanged.

The expanded costing suite passes **38 tests** on local PostgreSQL, including actual
child termination/retry, failed transaction rollback, stale claims, success replay,
foreign scope, archived tenants, canonical monthly relation parity and repeatable-read
consistency during publication. The reduced subprocess run publishes 732 observations
and 12 inventory pools in 0.983 seconds, including a 0.928-second child. This smoke run
uses zero polling delay; full runs use five seconds between enqueue and claim.

The current seven benchmark modules share source SHA-256
`0adc9d510319c25e332ddcb0245a3a8413e4fa8b4c50af1f1831ee5b952ecd4b`.
Resource caps are recorded in `evidence/worker-environment.json`: PostgreSQL two CPU /
four GiB, driver and child together two CPU / two GiB, no swap. This shared Docker
host is not the specified dedicated reference environment. Tests and diagnostic reads
also ran during the first cycle; these supplemental measurements do not qualify that
reference environment.

### Full worker measurements

`evidence/worker-full.json` records two fixture tenants, each with 100,000 orders,
10,000 items, 1,000,000 movements/components/attributions and 600,000 matching rows.
Tenant A rebuilds through 21 bounded ranges and seven real queued child processes per
cycle. Reconstruction, including five-second dispatch pacing and concurrent readers,
takes **94.728 / 93.676 / 100.396 seconds**, below the 120-second experimental target.
The longest child is **12.111 seconds**, below the unchanged 30-second watchdog.
No child handles more than 150,000 movements. Fixture setup and the independent full
replay comparison are outside the reconstruction timer; overall run time is 456.072 s.

Every cycle compares all **609,000 issue/return observations and 10,000 inventory pools**
against direct replay, including costs, revenue, selling costs and resulting coverage.
All three generation checksums are identical. Five concurrent order readers produce
13,572 samples; the largest individual-reader p95 is 16.38 ms. These are narrow SQL
snapshot reads (including initial not-ready/previous-generation responses), not the
actual product tool or full fixture-J mixed-load protocol. Peak combined driver/child
cgroup memory is 1,076,400,128 bytes. Local measured limits pass, while
`qualification_passed` deliberately remains **false** and CLI exit status remains 2.

The experiment now proves bounded shared-worker reconstruction. It does not establish
production source-history cutoffs, automatic late-input follow-up scheduling, generation
retention, fairness in a deployed multi-tenant worker, or the actual reporting/MCP/
exception integration. Its five-second delay simulates polling in a deterministic
driver; it does not measure a deployed scheduler's phase. Exact dedicated reference-host
and cold-cache qualification remain open. No catalog regeneration is required because
no product command, tool, projection, exception, event or MCP schema was changed.

### Final scoped review

A clean archive of baseline `709af5c1a6358be2f004003f37b836ff6095b5bf`, overlaid only
with the seven costing benchmark modules, three costing test families, spec242 and
coverage mapping, passes spec policy. In that isolated tree, the costing suite plus
existing shared-worker and projection-job regressions pass: **65 passed in 60.80 s**
(`evidence/worker-isolated-tests.txt`). Scoped Ruff and formatting pass for all ten
Python files; local Markdown links and diff whitespace checks pass.

The shared workspace policy still reports six feature-235 test families without
coverage mapping. Those parallel files were preserved. T019 remains open for that
shared gate; T024–T028 close only the bounded experimental continuation. The next
product-integration design must map the canonical relation to the actual report
compiler, tool responses and exception register before production implementation.
Owned benchmark containers, volumes and the temporary review checkout are removed
after retaining the measurements; no application database was used or changed.

## Actual adapter design review (2026-09-18)

The owner authorized continuation after the bounded worker proof. This turn changes
only spec242 design artifacts. [Adapter delivery](contracts/adapter-delivery.md) records
exact observed interfaces and proposed implementation slices for the real graph/compiler,
shared tools and operational exception register. It is not an executable adapter or a
new passing production acceptance claim.

Read-only research and an independent review confirmed the mapped-anchor restriction,
ordinary SUM's unknown-value loss, missing costing execution context and eager exception
page/count derivation. The review found two omissions: independent provisional/evidenced/
reviewed support states (FR-014), and attributable/allocated/residual/valuation-effect
breakdowns (FR-011). Both are now explicit in the contract and future tests. In particular,
a numeric estimate cannot complete actual DB or trigger a negative-actual-DB finding.
The two-row partial-cost example independently checks known DB1=40 / DB2=30 with final
amounts unavailable, not apparent DB1=140. Existing rate rules reject zero/negative revenue.

The post-design Constitution Check passes for this planning boundary. Product authority,
history and disposable storage still need their concrete schema review. That is the next
implementation prerequisite; existing gate restrictions were not waived. No runtime tests
were rerun for documentation-only changes; the earlier 65-test evidence remains historical.
No catalogs or generated documentation changed.

The shared spec-policy check still reports unrelated feature-235 coverage omissions
(seven test families at this review). A clean baseline overlay of spec242 and its existing
costing code/tests passes spec policy; evidence is in `evidence/adapter-design-review.json`
and `evidence/adapter-design-policy.txt`. Local links and whitespace checks pass. T029–T030
track completed design only; T019 remains the shared-workspace gate. Temporary review
files are removed after the check. No extension hooks are configured.

The shared `.specify/feature.json` points at concurrently developed feature235. The setup
command safely found its existing plan without overwriting it; subsequent feature path
resolution used the explicit spec242 directory with `--no-persist`, preserving that shared
context. Only spec242 artifacts were edited in this continuation.

## Concrete product data-model review (2026-09-18)

The continuation prepares [production-data-model.md](contracts/production-data-model.md).
Only spec242 planning/review artifacts change. It names first-slice authority and receipt
coverage records, later typed stock/contribution relationships, exact input manifests,
disposable generation indexes, concurrency rules and restricted rollback. No migration
number was reserved and no production models/services/catalogs were changed.

Code-grounded history research confirms:

- Financial components normalize received amounts lazily; cost-centre assignment is not
  receipt attribution. No component row does not prove absence of retained cost evidence.
- `_document_line_reality_exists` checks commitments/postings, not financial components;
  current manual correction behavior is insufficient for admitted immutable cost evidence.
- Existing `emit_business_event` serializes tenant event allocation under the tenant lock;
  source reception and accepted interpretation can be separate transactions.
- Current document headers are not universally immutable, and Movement.occurred_at is not
  a recorded-knowledge timestamp. Source IDs/current values alone cannot replay history.
- Return resolution/promise links do not identify the original issue's cost portions.

Independent review found four substantive omissions, all corrected before presenting
the proposal: typed component replacement plus atomic predecessor-attribution withdrawal;
first-slice correction admission/membership; exact `abs(source_share) * cost_effect`
arithmetic; and recoverable/mixed gross refusal unless an independently received applicable
net/base exists. The proposal additionally forbids review/manifest cycles, specifies fresh
snapshot cursor capture under the brief tenant lock, and names existing composite-FK
prerequisites. Positive- and negative-stated 50 credits both have derived -50 cost effect;
the received values themselves are unchanged.

The proposal's technical Constitution rows pass. Owner/schema approval remains OPEN,
as does integrated/reference qualification. The explicit approval proposal is to build
a reviewed integration candidate and retain those qualifications as mandatory release
gates; the existing pre-implementation gate is not silently changed by this document.
T031–T032 are design/review completions, not product acceptance.

No runtime tests were rerun for documentation-only changes. Prior 65-test evidence remains
historical. Local link/whitespace and isolated spec-policy checks pass; results and scope
are retained in `evidence/production-model-review.json` and
`evidence/production-model-policy.txt`. The shared workspace spec-policy check now also
passes: the earlier parallel feature235 coverage omissions have been resolved independently.
No feature235 files were edited for this review. T019 closes its scoped experiment-review
gate; product/reference qualification is still open. No extension hooks are configured.
Shared feature context and parallel work
are preserved; temporary review artifacts are removed after verification.


## Approved receipt-cost production slice

The owner explicitly approved the four production implementation decisions. The
receipt slice follows the reviewed specification, plan, T033–T045 and
`receipt-implementation-analysis.md`. Earlier prototype-only restrictions are retained
as historical evidence and superseded by that approval. Unchecked product/release
checklist gates remain open; there is no policy activation, deployment or full-product
claim.

Delivered behavior is recorded in `docs/features/receipt-costing.md`: exact received
amounts, signed goods/freight/reduction/tax attribution, explicit six-category scope
review, immutable replacement and movement-correction history, verified sealed
membership, active-owner confirmation, idempotent replay and tenant-safe references.
Read tools call the same service through application dispatch and actual MCP handlers.
The existing company-token HTTP MCP transport cannot supply a human owner; its cost
reads are available and its owner-only proposal is explicitly refused. Authenticated
web chat supplies the required human context. This transport limit is documented and
covered by the real server handler, rather than attributing a company token to a user.
Migration 0064 is static and refuses to delete populated costing history.

### First-slice verification and review

- Test-first failures are retained in `evidence/receipt-domain-first.txt`,
  `receipt-schema-first.txt`, `receipt-services-first.txt`, `receipt-tools-first.txt`,
  `receipt-manifest-first.txt`, `receipt-bound-first.txt` and `receipt-credit-tax-first.txt`.
- Final expanded regression: **85 passed**, including all four new test families,
  migrations, application/tool/data-model catalogs, discovery, reporting deferral and
  HTTP reference (`evidence/receipt-final-regression.txt`). A further invoice-line proof
  passed separately: no duplicate header attribution, shortest component-to-line FK and
  refusal of manual edits after admission (`evidence/receipt-line-proof.txt`).
- The first review caught a missing migration FK declaration, missing membership
  integrity verification, write-side contributor-bound enforcement and a gross-plus-tax
  validation gap. Regression proofs now cover all four. Every new table's migrated
  foreign-key columns are compared with the ORM metadata, not only sampled.
- New same-tenant references are also exercised against PostgreSQL with foreign
  receipt/event IDs. A failed allocation rolls back normalization, input admission and
  its Business Event. Source amounts and old reviewed receipt values survive replacement
  and movement correction.
- Scoped Ruff and spec-policy validation pass. Tool Usage generation is run with the
  Makefile's exact Python command because `/usr/bin/make` is blocked by the machine's
  unaccepted Xcode license; no license or environment setting was changed.
- Complete backend run: **3020 passed, 13 initially failed, 9 skipped**, with the existing
  storyline transaction-cleanup warning (`evidence/receipt-full-backend-parallel.txt`).
  Four failures were the now-fixed gross-tax check, HTTP event-count assertion, frontend
  reference fixture and explicit reporting-table deferral. Nine were company/demo worker
  deadline failures under four-worker contention. All **13 passed** when repeated
  sequentially after correction, without increasing deadlines or changing scheduling
  behavior (`evidence/receipt-full-backend-recheck.txt`). This is not an all-green
  parallel-run claim or evidence of production workload qualification.
- Final review also found that nonrecoverable tax on a supplier credit must share the
  reduction's economic direction. Two first-failing service scenarios now prove both
  positive and negative source signs yield 940.5 from goods 1000 minus credit 50 and
  its tax 9.5. The domain refuses a tax direction contradicting the corresponding
  received-base attribution. The expanded 85-test regression covers this final change.
- The company-token MCP server read/refusal proof and HTTP reference passed together
  (4 tests, `evidence/receipt-adapter-final.txt`). Related frontend catalog checks:
  **11 passed** (`evidence/receipt-web-catalog-tests.txt`). Documentation contracts:
  **4 passed** (`evidence/receipt-docs-tests.txt`). Exact tool-document regeneration
  preserved all generated hashes (`evidence/receipt-docs-idempotence.txt`).
- Spec policy passes, including an explicit working-tree change-policy invocation
  rather than relying on a zero-diff HEAD comparison. Scoped Ruff and `git diff --check`
  pass. Generated pages, JSON, data-model vocabulary, German labels and the frontend
  reference fixture are present in the working tree.
- T033–T045 are complete for this bounded receipt slice. Required full-product/release
  checklist markers remain unchanged. The isolated PostgreSQL test container is removed
  after verification; no existing application database, policy or deployment is changed.

### Remaining product/release work

This is receipt acquisition costing only. Inventory consumption and valuation,
write-down/reversal decisions, order/product/customer/time DB1/DB2, reporting-graph
integration, operational exceptions, demo evidence and UI are subsequent slices.
Full production fixture-J and reference-workload qualification remain release gates.
The first slice deliberately refuses FX/unit conversion, returns and excessive receipt
contributors. Receipts supported only by zero-value evidence remain unknown until a reviewed
zero-cost admission path is implemented. Current review invalidation is conservative across the
company's later input events. No new worker or scheduler registry was introduced.

## Inventory calculation foundation

The owner authorized continuation into inventory/consumption after the receipt slice.
T046–T050 isolate the pure domain stage before the approved service authority/history
work. Spec/plan/tasks analysis found no CRITICAL/HIGH inconsistency for this boundary:
FR-004–007/017/018/022 all map to T047 tests and T048 implementation, with T049 verification
and T050 durable documentation. Full-product requirements remain explicitly open rather
than being claimed as covered by a kernel. No schema expansion or policy activation.
The six reviewer-owned checklist gates remain unchanged; earlier explicit continuation
approval applies. No extension hooks were configured; prerequisite scripts resolve
feature 234 via SPECIFY_FEATURE_DIRECTORY without changing the feature-235 selector.

Test-first evidence: `evidence/inventory-domain-first.txt` records the missing production
module before implementation. The delivered pure module has no production caller.
`evidence/inventory-regression.txt` records **116 passing tests**, including 50 new
inventory cases and all existing receipt/spike/migration/tool/worker tests. These cover
A/B arithmetic, C2 return ordering, K2 residual conservation, maximum Numeric precision,
fractional quantities, exact returns and resales, separate outbound reasons, unknown
costs, immutable late-cost replay, invalid references, duplicate IDs and resource bounds.

Scoped Ruff and format checks pass (`evidence/inventory-scoped-lint.txt`). Global Ruff
reports 13 pre-existing import-order findings, exclusively in feature-235 search
benchmark/migration/tests (`evidence/inventory-lint.txt`). Those files were not modified.
Spec policy including explicit uncommitted working-tree coverage passes
(`evidence/inventory-spec-check.txt`). No commands/catalogs/UI/migrations changed in this
stage, so catalog generation, frontend rebuild and new migration proof are inapplicable.
The complete sequential backend test result is recorded below after completion.

Remaining integration: confirmed valuation policy and economic-owner scope, retained
movement admission/correction history, stock manifests, bounded shared-worker generation
and application read/trace adapters. This kernel does not supply HGB carrying value,
company-wide certified inventory, DB1/DB2 or fixture-J/reference qualification.

Complete sequential backend result: **3,089 passed, 9 skipped, 1 warning**, exit 0,
in 1110.52 seconds (`evidence/inventory-full-backend.txt`). The warning is the existing
storyline transaction-cleanup warning from `tests/conftest.py:117`. Test execution used
the dedicated PostgreSQL 17 container `reality-costing-234-kernel`, loopback port 55439,
with per-session disposable databases. No existing company database was touched. This
run is regression evidence, not reference-host performance qualification. Code/test
hashes are retained in `evidence/inventory-code-sha256.json`.

Final review: pure calculation, immutability, original receipt trace, no database writes,
no source-value recomputation, explicit method, bounded work and scope documentation
match the approved foundation. T046–T048 are delivered. T049/T050 remain unchecked at
the shared completion gate because the global Ruff command is red in unrelated search
files; all scoped checks and the full backend suite pass. Documentation work for T050
is present, but the checkboxes do not claim overall verification/review completion.
The separate full-product/reference release gates remain open independently of this lint
issue. No reviewer checklist markers, unrelated implementation files or company policies
were changed.

## Reviewed bounded inventory service

The owner's "continue" authorizes T051–T056 on top of the approved production model.
Specification, contract, plan and tasks define a complete bounded FIFO item scope with
explicit ownership evidence and economic-issue confirmation. Independent read-only
research found admission-cursor and simultaneous-movement ordering gaps; both were
resolved before code. Final pre-implementation analysis: no remaining CRITICAL/HIGH
finding for this scope, all requirements mapped to test-first tasks, Constitution PASS.
Full-product returns/specific/corrections/partial ownership/graph/UI/reference requirements
remain visibly deferred. Reviewer checklist markers are unchanged; no extension hooks.

Test-first evidence: stock-services-first.txt records missing inventory authority before
implementation. The initial migration invocation used the repository root rather than
the package cwd and failed on Alembic configuration; it is not claimed as a behavioral
migration proof. The later stock-index-first.txt is a genuine failing migration assertion
for the required cutoff index, observed before adding that index. The static final
migration preserves composite FKs, adds the tenant/item/time/ID lookup and refuses a
populated downgrade before any deletion.

Initial service tests exposed unstable hash representations after commit; canonical
Decimal/UTC serialization fixed that without modifying source values. The comprehensive
affected regression passed **177 tests** (stock-regression.txt). Subsequent edge tests and
stale-value masking passed **23 service/migration tests** (stock-final-service-tests.txt).
The final access-index migration separately passed **2 tests** (stock-migration-final.txt).
Final preview/trace metadata additions are covered by the separate final regression below.

Generated documentation completed; related Web catalog tests passed **11 tests** and
selected documentation tests passed **10 tests**. Scope lint and spec policy pass.
Global Ruff still reports the same 13 feature-235 import-order findings; no unrelated
search files were modified. The whole backend is checked sequentially on a dedicated
PostgreSQL 17 instance; the completed result is recorded below.

Final targeted verification: **155 tests passed** in 25.66 seconds
(`evidence/stock-final-regression.txt`), including inventory domain/service/migration,
receipt domain/service/tool/migration and application/data-model/reporting/action
catalog regressions. This run covers the last preview amount and decision-trace fields
added after the whole-suite process started. An initial invocation named a nonexistent
catalog test file and collected no tests; the corrected invocation produced this result.
The whole-suite result therefore complements this final-code check rather than claiming
that every test imported the last metadata-only edits. Final Web catalog and docs tests
again passed 11 and 10 respectively. Generated references are idempotent
(`evidence/stock-docs-idempotence.txt`); scoped Ruff, formatting and explicit working-tree
spec policy pass. No after-implement extension hooks are configured.

Complete sequential backend result: **3,112 passed, 9 skipped, 1 warning**, exit 0,
in 651.35 seconds (`evidence/stock-full-backend.txt`). The warning is the existing
storyline transaction-cleanup warning at `tests/conftest.py:117`. Tests used the dedicated
PostgreSQL 17 container `reality-costing-234-stock` with disposable session databases on
loopback port 55439. The owned container was removed after all runs completed; no existing
company database was touched. This is regression evidence, not reference-host performance
qualification. Final implementation hashes are in `evidence/stock-code-sha256.json`.

Final review: bounded complete item admission, explicit economic ownership/consumption,
original-event ordering, current invalidation, retained historical inputs, Decimal/UTC
hashing, confirmation/replay/rollback, tenant isolation and migration protection match
the reviewed slice. T051–T055 are delivered. T056 remains unchecked at the shared gate
because global Ruff still reports 13 unrelated feature-235 import-order findings;
all scoped checks, final targeted tests and the full backend suite pass. No overall
CI or feature-release completion is claimed. Dedicated Inspector screens, reporting graph
integration, general returns/corrections/partial ownership, company-wide generations,
HGB carrying value and DB1/DB2 remain open in the full-product tasks. No real-company
policy was activated, and no commit, merge or deployment was performed.

## Contribution calculation foundation

The owner's continuation authorizes the next domain stage of the approved commercial_v1
profile. Read-only analysis of the staged spec/plan/tasks found seven relevant FRs mapped
to T057–T060, no unmapped tasks and no CRITICAL/HIGH inconsistencies. Constitution PASS: no
schema, authority, adapter or permission change. The six existing reviewer-owned checklist
markers remain unchanged under prior continuation authorization. No extension hooks.

Test-first evidence: contribution-first.txt records the missing module. Additional
cutoff proof failed with 30 passing tests (contribution-cutoff-first.txt) before the
explicit future-date refusal was implemented. Tests preserve fixture A and partial-scope
examples from contracts/adapter-delivery.md. The calculation retains independent actual
and reviewed coverage, exact signed shares, direct/allocated costs and source trace.
No source totals are recomputed. Date-level cutoff protection complements, but does not
replace, future service admission of exact intraday input history.

The implementation is intentionally a domain foundation with no production caller.
Matching authority, reviewed profile persistence, historical context, aggregate adapters,
reconciliation bridges, HGB and full product/reference qualification remain open.

Final scoped costing regression: **128 passed** in 8.29 seconds, including 31 contribution
cases (`evidence/contribution-regression.txt`). Scoped Ruff and format checks pass.
Spec policy, including explicit uncommitted working-tree coverage, passes. Full Ruff
still reports the same 13 unrelated feature-235 import-order findings; those files were
not modified. No public command, schema or adapter changed, so catalog regeneration,
frontend build and new migration tests are inapplicable to this isolated domain step.
Implementation/test hashes are retained in `evidence/contribution-code-sha256.json`.

Complete sequential backend result: **3,143 passed, 9 skipped, 1 warning**, exit 0,
in 664.09 seconds (`evidence/contribution-full-backend.txt`). The warning is the existing
storyline transaction-cleanup warning at tests/conftest.py:117. No production/test code
changed after this run started. Tests used the dedicated PostgreSQL 17 container
`reality-costing-234-contribution` with disposable per-session databases on loopback
port 55439. The owned container was removed after completion; no existing company
database was touched. No reference-host performance certification is claimed.

Final review confirms the seven scoped requirements and Constitution boundaries: exact
received inputs, joint supported subtotals, independent review coverage, signed amounts,
fixed profile/context, partitioning, trace, bounds and no persisted derivation. T057–T059
are delivered. T060's implementation verification and documentation are present, but
its checkbox remains open at the global lint gate (13 unrelated findings). No overall
CI/release or complete company DB reporting claim is made. Earlier reviewer checklist
markers remain unchanged; no after-implement hooks are configured. No commit, merge,
deployment or company policy activation was performed.

## Current contribution preview

The owner's continuation authorizes the first current read-only service connection.
Five relevant FRs map to T061–T065; the read-only spec/plan/task analysis found no
CRITICAL/HIGH conflict. Constitution PASS: existing exact FKs and source amounts, shared
services/tools, tenant scope, no new schema or authoritative derived amount. Six existing
reviewer-owned markers remain unchanged under prior continuation approval; no hooks.

Test-first evidence: preview-first.txt records the missing service. A deliberate
foreign-customer fixture then exposed a missing referenced-party guard before the fix
(preview-foreign-link-first.txt). Initial integration tests also corrected a fixture
that exceeded its already-fulfilled commitment and an overly broad generated frontend
fixture shape. The corrected affected run passed 130 tests (preview-regression.txt).
Final additions move the read cursor ahead of source loading and prove absent inventory
review; their final regression and whole-backend results follow below.

The delivered tool exposes only a current candidate/known DB1. Confirmed matching,
commercial profile/revenue/selling completeness, partial allocations, retained historical
context, full reporting and HGB assessment are not claimed. All new calculations delegate
to the production kernel; transports implement no accounting rules. Scope is exactly
one fully billed and fulfilled item line, not a tenant-wide derivation.

Final affected regression: **151 tests passed** in 37.29 seconds
(`evidence/preview-final-regression.txt`). This includes domain preview invariants, 19
service cases, receipt/inventory regression, actual tool/MCP parity and catalog/HTTP
boundaries. Web catalog tests passed 11 and selected docs tests passed 10. Generated
references are idempotent. Scoped Ruff and formatting pass; global Ruff retains the
same 13 unrelated search-feature findings. Spec policy includes the explicit uncommitted
working-tree check. Final source/test/catalog hashes are retained in preview-code-sha256.json.
No schema change occurred, so no new migration/downgrade test was needed.

Complete sequential backend result: **3,163 passed, 9 skipped, 1 warning**, exit 0,
in 705.02 seconds (`evidence/preview-full-backend.txt`). The warning is the existing
storyline transaction-cleanup warning at tests/conftest.py:117. Production/test code
remained unchanged throughout this full run. All database tests used the dedicated
PostgreSQL 17 container `reality-costing-234-preview`, disposable per-session databases
and loopback port 55439. The owned container was removed after completion. No existing
company database was used. This is regression evidence, not reference-host qualification.

Final review: the exact current path, received net basis, independent preview coverage,
current inventory check, referenced-party isolation, no-write/no-autoflush behavior and
start/end cursor guard match the reviewed scope. T061–T064 are delivered. T065's checks
and documentation are recorded, but its checkbox remains open at the shared global-lint
gate (13 unrelated feature-235 findings). No overall green-CI, finalized-margin or
feature-release claim is made. No reviewer checklist markers, retained business authority
or company policies were changed. No after-implement hooks are configured. No commit,
merge or deployment was performed.

## Confirmed whole-line contribution

The owner's continuation authorizes this bounded revenue/history stage of the approved
production model. Spec/plan/contract/tasks analysis found no CRITICAL/HIGH conflict in
the staged scope; all scoped obligations map to T066–T071 and their test paths.
Constitution PASS: retained received inputs and explicit decisions, shortest links,
tenant FKs, owner confirmation, no derived monetary authority or automatic policy.
Six existing reviewer-owned checklist markers remain unchanged under prior continuation
authorization; no extension hooks. General profile/context/allocation families remain
future work, not falsely completed by the two-table specialization.

Test-first evidence: db1-first.txt records absent contribution authority before code.
The initial service/migration suite passed 10 tests. The subsequent larger run passed
118 and failed one over-strict test assertion that forbade even exact Movement identity
lookups; it now checks absence of live item-history enumeration while allowing scoped
identity validation, as the existing inventory contract requires. A new current-read
snapshot test then failed before adding READ COMMITTED enforcement (db1-snapshot-first.txt).
Late-cost reaffirmation preserves the old DB1, and tests exercise actual owner/proposal
confirmation, replay, rollback, source protection, uniqueness and tenant constraints.

Migration 0066 is static and contains no runtime model import. It creates only retained
source/binding and review rows plus indexes, preserves same-tenant FKs, supports empty
rollback and refuses populated downgrade before deleting any authority. No background
registry, ledger behavior, global profile activation or dedicated web screen changed.

Final affected regression: **234 tests passed** in 130.37 seconds
(`evidence/db1-final-regression.txt`), covering confirmed contribution, preview/kernel,
receipt/inventory services and migrations, tenant/catalog/HTTP boundaries and shared
tools. Web catalog tests passed 11; selected docs tests passed 10. Generated references
are idempotent. Scoped Ruff and formatting pass. Global Ruff retains the same 13
unrelated feature-235 import-order findings. Working-tree spec policy passes. Final
implementation/test/catalog hashes are retained in db1-code-sha256.json.

Concurrency uses the existing tenant row lock shared by evidence corrections and
fulfilment writers, plus exact proposal/candidate/cursor checks. Read queries use scoped
identity lookups and frozen membership, not live movement enumeration. No runtime
model import is present in the new migration. Current reads reject old repeatable-read
snapshots; explicit frozen review reads remain reproducible.

Complete sequential backend result: **3,180 passed, 9 skipped, 1 warning**, exit 0,
in 2,097.07 seconds (`evidence/db1-full-backend.txt`). The warning is the existing
storyline transaction-cleanup warning at tests/conftest.py:117. Implementation and
test code remained unchanged throughout the full run. Database tests used the dedicated
PostgreSQL 17 container `reality-costing-234-reviewed-db1`, disposable per-session
databases and loopback port 55439. The owned container was removed after completion;
no existing company database was used. This is regression evidence, not reference-host
performance qualification.

Final review: confirmed whole-line matching, immutable source context, scoped profile
approval, exact inventory membership, independent DB1/DB2 coverage, current-staleness
checks, historical reproduction, source protection and tenant isolation match the
reviewed bounded scope. T066–T070 are delivered. T071 has recorded verification and
documentation but remains unchecked because global Ruff still reports 13 unrelated
feature-235 import-order findings. No overall green-CI or feature-release claim is made.
Selling-cost admission and final DB2, partial matches/returns/rebinding, broader profile
and context histories, HGB carrying-value decisions, reporting/Inspector integration and
reference-host qualification remain outstanding. Reviewer-owned checklist markers are
unchanged. No after-implement hooks are configured. No commit, merge, deployment or
real-company activation was performed.


## Source-backed selling costs and DB2

The owner authorized the next selling-attribution stage after confirmed DB1. The linked
spec, plan, contract and T072–T077 were prepared before implementation; read-only analysis
found no CRITICAL/HIGH conflict in this bounded continuation. Eleven FR references map
to the six ordered tasks, with no unmapped task. Constitution PASS: reuse received
component/revision authority, retain only explicit decisions/membership, shortest links,
composite tenant FKs, Decimal, shared owner confirmation and no persisted calculated DB.
Requirements checklist: 46 items, 40 checked, six reviewer-owned markers unchanged under
the existing continuation approval. No extension hooks are configured.

Test-first evidence: selling-first.txt records the missing SellingAssign import before
implementation; selling-migration-first.txt records the absent migration. The first
service run had 25 passes and six test-fixture failures (wrong receipt manifest key,
case-sensitive error match, wrong manual-correction signature); those tests were corrected
to the existing service contract. The next run passed all 18 selling/migration cases.
Additional proofs cover full revision replacement and reassignment away from the sale,
actual foreign source/target scope, composite FK refusal, no-write/frozen reads, corruption,
proposal binding/demotion/replay, missing received net, assignment bounds and precision.


Affected regression: **257 passed** in 138.49 seconds (`evidence/selling-regression.txt`).
Final review clarified incomplete-scope response fields: known direct/allocated subtotals
remain separately labeled; complete direct/allocated cost fields stay absent until all
selling categories are reviewed. Two additional tests prove missing net/bounds and strict
category/precision inputs. The final DB1/DB2/migration run passed **40 tests** in 42.09
seconds (`evidence/selling-final-regression.txt`). These results include fixture A456/38%,
signed credits, independent unknown/zero, complete revision replacement, withdrawal and
reassignment history, actual foreign links and composite FK refusal, immutable evidence,
confirmation/demotion/binding/replay, rollback and frozen no-write reads.

Web catalog tests passed **11**; selected docs tests passed **49**. Generated tool
references are idempotent. Scoped lint/format and working-tree spec policy pass. Global
Ruff retains the same **13 unrelated feature-235 import-order findings**. The final
source/test/catalog hashes are retained in selling-code-sha256.json before the complete
sequential backend run. Static migration0067 has no runtime model import and proves real
upgrade/FK parity, empty downgrade and retained-row refusal before any authority drops.
T072–T076 are delivered; T077 remains open pending the shared full verification gates.


Complete sequential backend result: **3,205 passed, 9 skipped, 1 warning**, exit0,
in 1,293.91 seconds (`evidence/selling-full-backend.txt`). The warning is the existing
storyline transaction-cleanup warning at tests/conftest.py:117. All 15 recorded
implementation/test/catalog file hashes remained unchanged throughout the run.
All database tests used the dedicated PostgreSQL17 container `reality-costing-234-selling`,
loopback port55439 and disposable per-session databases. The owned container was removed
after completion; no existing company database was used. This is regression evidence,
not reference-host performance qualification.

Final review: received net/sign conservation, exclusive acquisition/selling source use,
complete attribution replacement and withdrawal, seven-category completeness, independent
known subtotals, frozen membership/integrity, owner/proposal controls, composite tenant
isolation and migration retention match the reviewed scope. Existing DB1-only digests
remain reproducible. DB2 arithmetic is delegated to the same production contribution
kernel; adapters add no rules. T072–T076 are delivered. T077 has recorded verification,
documentation and review but stays unchecked because global Ruff retains 13 unrelated
feature235 import-order findings. No overall green-CI or full-feature release claim.

Still outstanding: mixed/nonrecoverable selling-tax and FX support, selling replacement
evidence, inventory-sourced packaging consumption, partial revenue/returns/rematching,
general profiles/context history, HGB carrying-value decisions, broad reporting/Inspector
integration and reference qualification. Existing reviewer-owned checklist markers are
unchanged. No after-implement hooks, commit, merge, deployment or company activation.


## Retained-record Inspector integration — 2026-09-19

T078 is refined by T091–T095 and contracts/record-inspection.md. Pre-implementation
analysis found no critical requirement/plan conflict; no schema or new valuation rule is
needed. Existing six reviewer-owned requirement markers retain their prior continuation
authorization and are unchanged. T091–T094 are implemented; T095/T078 remain open until
the shared verification gate is resolved.

One fixed allowlist covers all 24 retained costing families and four explicitly bounded
evidence bridges. Shared cost_record reads expose exact stored Decimal strings, source
and approval links, bilingual family labels and one 25-row retained-membership pager.
Action input/output is excluded; supported link targets are checked in the same tenant.
No flush, projection write, scheduling or current-completeness inference is introduced.
The existing Inspector/register, application tool, MCP and CLI share this boundary.
CLI reads explicitly bypass the historical general-command schema initialization.

Test-first evidence: records-first.txt demonstrates the absent cost_record entrypoint.
The first adapter run exposed CLI initialization of an existing schema; the regression
now forbids init_db during cost-record. The catalog check exposed undocumented page and
language parameters; both are now described and generated references updated.

Affected regression: **142 passed**, including seven new service/adapter/tenant/precision/
redaction/no-write/member-page tests and existing costing, Inspector and catalog coverage
(records-regression.txt). Frontend: **314 passed**, including rendered exact amounts,
source navigation, page reset/back and stale page/company suppression; TypeScript/Vite
production build passes with the existing large-chunk warning. Docs: **73 passed**.
Generated references are idempotent, working-tree spec policy and git diff checks pass.
Scoped Ruff passes; global Ruff still reports **13 unrelated feature235 import-order
findings**, recorded again in records-global-lint.txt. No globally green release claim.

Full backend verification: **3,212 passed, 9 skipped, 1 existing warning**, exit0,
in **729.55 seconds**, using four pytest-xdist workers (records-full-backend.txt).
Each worker uses its own disposable database in the dedicated PostgreSQL17 container
reality-costing-234-records, loopback port55439. No existing company database was used.
The earlier sequential run was deliberately interrupted after 817 passes and two skips
to use the supported worker isolation; it is not counted as full verification.
Backend source/test hashes remained unchanged through the complete run. The warning
is the existing storyline transaction-cleanup warning. The owned test container was
removed after completion.
The remaining convergence tasks T079–T090 are unchanged. This delivery makes retained
evidence explainable; it does not provide grouped company-wide valuation, HGB carrying
value, broader admission or production performance qualification.


Final review: allowlisted fields, exact amounts, shortest validated tenant-safe links,
redacted action bridges, stable retained membership pages, no-write reads and shared
adapters match the bounded inspection contract. UI checks cover navigation and stale
page/company suppression; the production build passes. T091–T094 are delivered.
T095/T078 retain their open markers solely because the required global lint gate has
13 unrelated feature235 findings; do not infer full-feature or release completion.
No commit, merge, deployment, financial approval or company activation was performed.


## Shared retained query context — 2026-09-19

T096 specifies and analyzes contracts/query-context.md against FR-004/007/011/012/014/015/016
and T079. No critical conflict; Constitution Check PASS without schema expansion or
new financial authority. Forty requirement checklist items are checked and six remain
reviewer-owned, under the existing continuation authorization. No hooks are configured.

Tests were written before implementation. The first asynchronous run overlapped initial
code creation and caught a missing datetime import (context-first.txt); it is not claimed
as a missing-module proof. The subsequent integration-first run showed two real failures:
missing cost.query.get registration and an unnecessary live event-maximum scan inside
historical receipt reads. Both were fixed before the affected regression run.

The shared query wraps existing arithmetic. It distinguishes requested/actual cutoffs,
retained scoped identity, policy/ownership/unit/currency, algorithms and independent
freshness. It refuses unsupported cutoff/policy constraints, hides stale current results
behind basis_result, and preserves unknown DB2/carrying value. Canonical generation/profile
authority remains absent. Existing reader response shapes and retained digests are unchanged.
Verification is in progress; no shared completion gate is marked green early.


The HTTP test first returned 404 before the GET adapter existed (context-http-first.txt).
The broader affected run then had 147 passes and one 400-vs-422 refusal-status failure.
The adapter now returns the specified 422 for invalid selectors; the final focused
service/HTTP/CLI/MCP/catalog regression passes **65 tests**, including all eight new tests.
Web: **314 passed**, plus **10** catalog tests after the final adapter declaration.
Docs: **73 passed**. Scoped Ruff/format, spec policy and generated-reference idempotence
pass. Global Ruff retains the same 13 unrelated feature235 import-order findings.

The first four-worker full run was stopped after a scheduled demo-initialization
handler_timeout (397 passes, one failure). The exact existing demo test passed alone
in 8.57 seconds without any timeout or production-code change. This is consistent with
a load-sensitive timing failure; the complete suite is being rerun with two workers.
The test container is dedicated PostgreSQL17, reality-costing-234-context on loopback
port55439. No existing company database or financial policy is changed.


The two-worker retry also encountered the existing company-seeding handler_timeout
(test_live_creation_provisions_and_starts_once[True]); it stopped with 941 passes and
two skips. No job deadline was relaxed. Final full verification is partitioned by the
ten test files referencing seed_company: 84 cases run serially, followed by the
remaining 3,145 cases in four workers. A fresh normal collection found 3,229 unique
node IDs; the two disjoint file sets cover all of them (context-test-partitions.json).
The partition runner remains a temporary test invocation, not production infrastructure.


Final full-baseline execution: **84 passed** in the serial partition and **3,135 passed,
9 skipped, one failed, one existing warning** in the parallel partition. The single
failure was test_repository_spec_policy_passes: a concurrently added feature239 desktop
test briefly lacked its coverage-matrix entry. That entry was subsequently added by the
parallel work; standalone spec policy and its pytest regression now pass. This is not
reported as a clean uninterrupted full-suite pass.

The checkout changed during that run: web/auth.py, db/core.py, jobs/registry.py and
services/tenant_policy.py, plus new desktop/account services and desktop tests. These
changes were preserved, not modified to make costing checks pass. See
evidence/context-concurrent-changes.json. A final focused run against the newer checkout
passed **125 tests**, covering the new query envelope, existing cost records, acquisition,
inventory, DB1/DB2, HTTP and spec policy. Costing and shared adapter hashes remained
unchanged during this final run (context-owned-sha256.json). New desktop tests were not
part of the original 3,229-case collection; no current-checkout full-CI claim is made.

Final docs tests: **73 passed**. Earlier full Web tests: **314 passed**, followed by ten
final catalog checks. No TypeScript implementation changed in this slice. Generated
references are idempotent on the final catalog, scoped Ruff/format and git diff checks
pass. The latest global Ruff snapshot has **17 findings outside the costing changes**
(the existing search-feature findings plus evolving desktop-test import findings).
The global gate remains open rather than chasing unrelated worktree edits.

Final review: current/historical selectors are separated from retained resolved scope;
exact UTC constraints refuse unsupported reconstruction. Policy/profile authority is
not invented, absent/stale answers cannot become current numeric results, coverage gaps
remain independent, historical reads avoid current event maxima, and all four adapters
delegate to the same read service. Existing response shapes and monetary algorithms
remain intact. No new schema, company policy, commit, merge or deployment was introduced.
The owned PostgreSQL container and its anonymous volumes were removed. No post-implement
hooks are configured. T096–T099 are delivered; T100/T079 keep their shared completion
gates open pending a stable full-checkout verification and clean global lint. Generalized
profile authority and canonical generations remain the explicit later T080/T081 work.

## T080 publication domain stage (2026-09-19)

Owner continuation: implement the next narrow generation step. Scope: T101–T103,
not the complete production generation/reporting feature. Existing reviewer checklist
remains 40 checked / 6 open under the previously granted continuation; markers untouched.

Preimplementation scoped analysis: four requirements FR-007/012/014/018 mapped to
T101–T103 (4/4 coverage), zero critical/high/ambiguity/duplication findings in this
stage. Constitution PASS: no source recomputation, schema, authority, scheduler,
adapter or user-facing report change. Domain-only rules cannot prove storage atomicity.
The existing approved production model remains the target; this does not replace it.

Test-first evidence:
- `evidence/publication-first.txt`: collection failed because the new module did not
  exist; this proves missing implementation, not a behavioral assertion failure.
- `evidence/publication-domain.txt`: initial 38 domain cases passed.
- `evidence/publication-context-first.txt`: 3 meaningful failures / 38 passes before
  adding policy/profile/effective-cutoff equality checks; the same key could otherwise
  hide an incompatible valuation basis.

Final review: identities, UTC cutoffs and strict counters are immutable; publication
facts are trusted service input, never caller approvals. Unknown financial coverage is
not equated with failed calculation. Pending freshness preserves the old input cursor.
No imports from the benchmark or alternative financial calculation. Pointer races here
are modeled decisions only; PostgreSQL concurrency, actual input verification and job
claim fencing remain required in T080. No new catalog entry, MCP schema or public tool
changed, so generated-reference regeneration is not required for this domain-only stage.
No extension hooks are configured. No commit, deployment or company activation.

Final verification: `evidence/publication-regression.txt` records **243 passed in
164.05s**, including all 41 new publication tests, existing receipt/inventory/
contribution arithmetic, retained query/record services, reviewed DB1/DB2 and spec
policy. Scoped Ruff/format passed (`publication-scoped-lint.txt`); standalone
spec policy and git diff --check passed. `publication-global-lint.txt` has 16
findings in concurrent desktop/global-search tests, outside this stage. This was
a focused regression run, not a full-checkout CI pass. No frontend behavior changed.
T101–T103 complete; T080 and global release gates remain open.

The owned PostgreSQL17 test container was removed after verification, including
anonymous volumes. Existing application containers were untouched.

## T080 stored inventory integration (2026-09-19)

Scope: T104–T108, contracts/inventory-publication.md. Owner continuation and the already
approved production cache model cover this bounded refinement. No new financial policy
activation, generalized profile authority or company-wide report is inferred.

Preimplementation analysis: FR-007/014/016/018/019 map to T104–T108 (5/5 coverage),
zero critical/high findings in this scope. All eight Constitution principles PASS:
retained inputs and common kernels, three disposable typed caches, shortest review
links, composite tenant constraints, shared services and jobs, test-first proof, no
source recomputation or browser logic. No duplicate queue or staged-work table for
one bounded work unit. Existing checklist remains 40 checked / 6 open under continued
owner authorization. Existing global requirements/tasks remain open.

First proofs and fixes:
- storage-first.txt: missing model prevented collection; not a behavioral failure.
- storage-integration.txt: 10 passed / 2 failed because fixture preparation opened an
  outer transaction around the existing proposal service's commit; corrected the
  independent committed fixture, without changing financial/runtime commit semantics.
- storage-final-integration.txt: 72 passed / 1 failed; new cache table names were missing
  from the coverage matrix, subsequently added.
- storage-focused-final.txt: 41 passed / 1 failed; unfinished-run migration fixture
  lacked the existing manual-job origin fields. Added its request identity/fingerprint.
- storage-migration-final.txt: 2 migration tests pass, including populated disposable
  rollback and refusal while a queued costing run remains. Retained authority survives.

This production path uses real independent PostgreSQL sessions, an actual worker child,
claim fencing, owner revocation, no-autoflush reads and retained cache reconstruction.
The late-commit test proves business intake proceeds during computation and the result
remains pending; atomic publication exposes no intermediate rows. Typed result hashing
refuses cache corruption. Current and historical readers never run FIFO or enqueue work.
The canonical relation is explicitly tenant/generation pinned; it is not registered as
a grouped report yet. Input capture/replay retains the existing 100-movement/20-receipt
bound. Larger T080, T081 and fixture-J release budgets remain open.


Final verification and review:
- Original complete backend collection: **3,312 unique cases**, partitioned without
  overlap; **3,298 passed / 5 failed / 9 skipped**. Evidence: storage-test-partitions.json,
  storage-serial-demo.txt and storage-parallel-rest.txt. This is not a green full run.
- Two failures identified missing classification of the three disposable caches. The
  authority allowlist test now excludes exactly those named caches and verifies actual
  cache IDs are refused as financial records. The reporting coverage test explicitly
  defers these tables to T081's compatible-generation and inventory-cutoff semantics.
  No production authority allowlist or premature grouped measure was added.
- Three existing demo cases hit the unchanged 30-second handler deadline in the full
  partition. Rerun alone: **3 passed in 41.14s** (storage-demo-recheck.txt). No demo or
  timeout behavior was changed by this stage.
- Final focused run against the current shared worker: **141 passed in 53.34s**
  (storage-current-checkout.txt). Includes migration, actual child execution, concurrent
  publication, tenant isolation, record/query, reporting classification and catalogs.
  All 12 tracked source/test hashes remained stable during this final run
  (storage-final-source-check.json).
- Docs: **73 passed**; Web: **314 passed**. Generated references are idempotent.
  Scoped Ruff/format and git diff --check pass. Global Ruff has **11 unrelated findings**
  in global-search tests (storage-global-lint.txt).

Concurrent external desktop work changed shared runner/runtime and desktop files near
completion of the full suite. Those edits were preserved; the final focused tests cover
that worker state, but do not establish a stable unchanged-checkout full-suite pass.
T104–T107 are delivered; T108 and T080 remain open with the global release gates.

Review conclusion: a single existing bounded inventory review can now produce a
rebuildable, atomically published cache through the shared worker. It remains an
observation, never retained financial authority. Unknown carrying value remains unknown;
no HGB assessment, company-wide generation, grouped contribution report, automatic
refresh schedule or UI is claimed. Owned PostgreSQL test infrastructure and volumes
were removed. No application migration, policy activation, commit, merge or deployment.


## Bounded historical inventory selection (2026-09-19)

Owner continuation authorizes the next bounded read step, T109–T112, with no schema
expansion or financial-policy activation. Preimplementation scoped analysis maps all
five FR-007/014/016/018/019 requirements to T109–T112 and the selection test file;
100% scoped task coverage, zero critical/high, ambiguity or duplication findings.
All eight Constitution principles PASS. Individual review knowledge/policy cutoffs are
preserved; selection never invents a common report generation or totals. Existing
reviewer checklist remains 40 checked / 6 open under continuing authorization.
No extension hooks are configured. Existing ignore files cover Python artifacts.

Test-first proof: evidence/selection-first.txt records 15 runtime failures because the
new shared service entrypoint did not exist. Real source-backed fixture preparation
completed; no assertion failure was concealed by a missing module during collection.


Final evidence:
- selection-integration.txt: **89 passed in 46.77s**, including the stored inventory
  reader/builder, actual worker execution and tenant operation catalog. The upper-bound
  acceptance case was added after this run's collection and is covered below.
- selection-regression.txt: **287 passed in 114.79s**, including all 16 selection cases,
  receipt/inventory/contribution/selling calculations, reviewed history, query/record
  reads, reporting coverage and spec policy. Tracked implementation and selection-test
  hashes stayed unchanged during this run (selection-source-check.json).
- selection-docs-tests.txt: **73 passed**. Generated references succeed and are unchanged
  on repeat (selection-docs-idempotence.txt).
- Scoped Ruff and format checks pass (selection-scoped-lint.txt); standalone spec policy
  and git diff --check pass. Global Ruff retains **11 unrelated global-search findings**
  (selection-global-lint.txt). No full-backend or frontend suite was rerun for this
  bounded service-only extension; existing full-checkout/release gates remain open.

Final review: at most 100 exact IDs, explicit tenant constraints on every joined table,
all-or-nothing membership checking, shared checksum/context serialization, deterministic
row order and no current-cursor/pointer lookup. Real two-item tests preserve distinct
knowledge cutoffs and exact single-reader parity. No source values, financial approvals,
worker lifecycle, schema or transport changed. T109–T112 are delivered within their
bounded scope; T080/T081 and all previously open global gates remain open. No extension
hooks, company activation, application migration, commit, merge or deployment.

The owned disposable PostgreSQL container `eb1d7c51310e` and its volumes were removed
after verification; existing application infrastructure was untouched.


## Joint inventory confirmation (2026-09-19)

Owner continuation and the approved production model authorize the next bounded
selected-scope admission step (T113–T116). No schema expansion, company activation or
financial-policy invention. Preimplementation scoped analysis: six requirements
FR-007/014/015/016/018/019 mapped to T113–T116 and test_inventory_batch_review.py;
100% scoped coverage, zero critical/high/ambiguity/duplication findings. All eight
Constitution principles PASS. The existing action/event links prove joint membership;
per-item policy and retained evidence remain authoritative. Existing checklist remains
40 checked / 6 open under continuing authorization. No extension hooks configured.

Test-first proof: batch-first.txt records 5 failures / 6 passes because the new operation
was not registered; malformed-input cases already refused under the old operation
allowlist and are not claimed as meaningful new failing proofs. batch-integration.txt
then records 15 failures / 36 passes: a broad edit accidentally used the admission-only
movement_limit in historical _inputs. Restored its existing MAX_MOVEMENTS reference.
The next run, batch-integration-fixed.txt, records 49 passes / 2 failures: default bound
arguments had frozen constants used by existing configurable-bound tests, and the new
test compared equivalent UTC timestamps as different strings. Resolve limits at call
time and compare parsed instants; neither financial arithmetic nor existing single-item
knowledge timestamp behavior was changed.


Final verification and review:
- batch-focused.txt: **126 passed in 48.01s**, including all 12 batch cases, existing
  inventory admission, stored generation/worker, selection, catalog and spec tests.
- batch-regression.txt: **287 passed in 87.06s**, covering receipt/inventory/contribution/
  selling decisions and arithmetic, tools, retained record/query history, publication
  rules, inventory authority/cache migrations, graph coverage and spec policy.
  Six tracked implementation/test hashes remained unchanged during this run.
- batch-docs-tests.txt: **73 passed**. Schema-driven references regenerate successfully
  and are unchanged on a second generation (batch-docs-idempotence.txt).
- Scoped Ruff/format passes for six files (batch-scoped-lint.txt). Standalone spec policy
  and git diff --check pass. Global Ruff still reports **11 unrelated findings** in
  global-search tests (batch-global-lint.txt). No full-backend or frontend suite was
  rerun for this stage; no frontend code changed. Previous shared release gates stay open.

Review conclusion: exact compatible membership is owner-confirmed once under the shared
lock/savepoint. One action/event/cursor/knowledge timestamp binds the standard retained
item reviews; source inputs and item-specific policies remain distinct. Receipt budget
is constrained in the typed request and actual admission, movement budget during bounded
capture. A deliberately failed second item rolls back both item decisions and the event.
Actual MCP proposal/confirmation/replay and mixed base-unit preservation are verified.
Existing single-review timestamps and financial kernels retain their behavior. Snapshot
context adds its real review_action_id; that field does not assert a shared cache or
company-wide policy. No migration, new queue, startup behavior or automatic activation.

T113–T115 are delivered. T116 retains its shared verification gate while global checks
remain red; T080/T081, joint cache publication, report aggregation, complete production
scale and all previously open release obligations remain open. No commit, merge,
deployment or actual-company policy activation. Reviewer-owned markers were untouched.

Owned PostgreSQL test container `0497d3b29a42` and its volumes were removed after
verification. Existing application containers were untouched.


## Complete joint inventory publication (2026-09-19)

T117–T120 refine the already approved selected inventory model without new schema.
Scoped preimplementation analysis maps seven FR-007/012/013/014/016/018/019 requirements
to those tasks and test_inventory_batch_generations.py: 100% scoped coverage, no critical/
high/ambiguity/duplication findings. All eight Constitution principles PASS. Confirmed
action membership plus existing exact publication rows define completeness; no new
financial authority or fabricated global generation. Checklist remains 40 checked / 6
open under continued owner authorization; no extension hooks are configured.

Test-first: joint-first.txt records eight failing tests for the missing shared services
and unsupported worker action configuration. joint-integration.txt then ended with
exit137 after six passing indicators, without a completed suite result. A concurrent
external shell process was observed issuing a broad pkill against bin/pytest. This is
an interrupted run, not a green verification or an identified costing assertion failure.
The final focused rerun adds four more cases: supported zero inventory, refusal to
relabel independent review, corrupted retained membership and deadline/config guards.


The first complete focused run (joint-focused.txt) recorded **116 passed / 1 failed**.
The actual concurrent-intake test exposed PostgreSQL tenant FK key-share locks after the
first cache insert: intake's tenant FOR UPDATE waited while the next item was still being
computed. A ten-second test pause failed; timeouts were not increased. Refined the plan
and implementation to calculate all missing immutable review observations before any
cache write, then reuse the shared private publisher. Its internal prepared input is
not exposed through any public tool/service arguments. Existing caches skip replay;
a cache disappearing before publication now refuses instead of replaying under FK locks.

The concurrency proof now separately pauses after calculation (late intake succeeds)
and after the first publication write (another session still sees zero committed members).
The corrected publication suite passed **28 tests in 29.53s** (joint-publication-fixed.txt).
The final run additionally covers the disappearing-cache rollback path.


Final verification and review:
- joint-final-regression.txt: **176 passed in 64.81s**, including all 13 joint-publication
  cases, existing single generation/worker, batch confirmation, historical selection,
  cost query/record/publication, application/job catalogs, cache migration and spec gates.
  Six tracked implementation/test hashes stayed unchanged during the final run.
- joint-docs-tests.txt: **73 passed**. Generated references succeed and are unchanged
  on repeat (joint-docs-idempotence.txt).
- Scoped Ruff/format passes for six files (joint-scoped-lint.txt). Standalone spec policy
  and git diff --check pass. Current global Ruff reports **12 unrelated import findings**:
  eleven global-search findings and one in test_chat_confirmation.py. No full-backend
  or frontend suite was rerun for this bounded service/worker extension; shared release
  gates remain open. No frontend behavior or statutory valuation was added.

Review conclusion: exact retained action/input/output/event membership is checked before
building or reading. All missing computations precede cache inserts; the final phase
shares one savepoint and outer commit, existing claim fencing and worker deadline.
Disappearing caches refuse rather than replay under publication locks. Real concurrent
sessions prove convergent same-action builds, intake during computation, and no partial
visibility between member writes. A completed pinned vector supports an acquisition
sum in one confirmed currency and distinct unit quantities. Incomplete cache availability,
stale current input and corrupt cache/membership cannot become an authoritative total.
Zero inventory is explicitly complete and distinct from missing data. Historical reads
are bounded and do not enqueue, flush, replay or query the live event maximum.

The existing job accepts mutually exclusive review/action config and preserves old
review-only serialized fingerprints; old worker tests still pass. No schema expansion,
new registration, schedule, startup migration or financial approval. T117–T119 are
delivered; T120 and all previous full-checkout/T080/T081/release gates remain open.
Company-wide publication, graph/report integration, contribution generations, HGB
carrying assessment and fixture-J qualification are not implied. No commit, merge,
deployment or company activation. Reviewer-owned checklist markers remain untouched.

The owned PostgreSQL container `30fd9b29ad36` and its volumes were removed, including
test databases left by the externally terminated first run. Application containers
were untouched.


## Canonical SQL inventory source (2026-09-19)

T121–T124 refine the relation prerequisite of the approved T081 design. Preimplementation
scoped analysis maps six FR-007/012/013/016/018/019 requirements to these tasks and the
new SQL test file; 100% scoped coverage and no critical/high/ambiguity/duplication findings.
All eight Constitution principles PASS: no schema, authority, financial formula, source
recomputation, queue or UI change. Existing checklist remains 40 checked / 6 open under
continued authorization; no extension hooks configured.

The existing graph's anchored compiler/context/result contracts still need explicit cost
basis support and protected aggregate execution. This stage does not expose a graph node
or bypass that gate. Instead, one shared joined source serves the existing production
selection reader and a flat typed canonical SQL relation. No duplicate monetary kernel.
Test-first evidence: relation-first.txt records 13 failures because the new relation
entrypoint did not exist; source-backed fixture preparation succeeded.


Final verification and review:
- relation-integration.txt: **116 passed in 62.80s**, including actual SQL relation,
  shared selection, joint/single publication, worker/concurrency, catalog and spec tests.
- relation-final.txt: **58 passed in 27.37s**, after adding exact effective/knowledge/
  completion timestamp and processed-cursor parity assertions; includes selection,
  reporting coverage and spec regression checks.
- relation-docs-tests.txt: **73 passed**. No command, tool, view, projection, exception,
  event or MCP schema changed, so no generated-reference regeneration was required.
- Scoped Ruff/format passes for three files (relation-scoped-lint.txt); standalone spec
  policy and git diff --check pass. Global Ruff retains **12 unrelated findings**
  (relation-global-lint.txt). No full-backend or frontend rerun for this internal SQL
  source change; previously open shared release gates remain open.

Final review: bound validation is shared and runs before database access; exact IDs are
frozen. Every join carries a tenant predicate, preserving the one-snapshot grain through
existing uniqueness constraints. Real SQL results retain exact Decimal/time/context values,
ignore mutable Item metadata/publication pointers, and match shared complete-batch totals.
The production selection reader retains its no-flush, bounded-query, checksum, membership
and response contracts. Missing raw relation rows are not silently promoted to complete
coverage or zero. The SQL primitive is not exposed as a graph node or unguarded report.

T121–T123 are delivered. T124 and previous full-checkout/T080/T081/release gates remain
open. The next graph integration must bind a requested confirmed action context, protect
the pinned cache rows through final aggregation, preserve non-additive cutoff/unit rules,
and carry that context through saved reports and transports. Existing graph deferrals
remain accurate. No schema, migration, financial approval, company activation, commit,
merge or deployment. Reviewer-owned checklist markers remain unchanged.

Owned PostgreSQL test container `c061dd1b0f6e` and its volumes were removed after
verification. Existing application infrastructure was untouched.

## Historical inventory graph execution (T125–T128, 2026-09-19)

Scope: the existing JSON graph tool/HTTP API and saved graph reports now consume an
explicit confirmed historical inventory action. The canonical SQL relation aggregates
only a complete checksum-validated selection. Exact generation/snapshot rows are locked
before validation through the final SQL query; concurrent cache deletion/update waits,
while normal tenant intake proceeds. Resolved basis metadata accompanies the values.
Currency/base-unit separation, no temporal buckets/paths, missing context refusal and
lossless saved-query context are enforced. No new schema or accounting formula.

Pre-implementation review of the spec/plan/tasks refinement found zero critical issues.
Requirement coverage: FR-007/012/013/014/016/018/019 all mapped to T125–T128; all eight
Constitution principles PASS. Existing reviewer checklist remains 40 checked / 6 open;
continued implementation authorization does not mark release review complete. The
adapter contract records the bounded historical row-lock alternative explicitly.

Evidence:
- `evidence/report-first.txt`: seven expected failures before implementation.
- `evidence/report-integration.txt`: 295 passed, one old catalog-probe failure. That
  probe assumed every node could execute without a financial context; it now asserts
  the required explicit refusal, and is covered by the final passing run below.
- `evidence/report-final.txt`: 95 passed, including graph expansion/tools/saved reports,
  HTTP propagation, tenant/corruption refusal, no autoflush/replay, bounded query count,
  real PostgreSQL delete/update races, ongoing intake and spec policy.
- `evidence/report-position-regressions.txt`: 19 passed for existing position history.
- `evidence/report-docs-tests.txt`: 73 passed; generated tool/MCP references include the
  typed context and bilingual graph measures.
- `evidence/report-web-tests.txt`: 40 passed for existing analysis/graph contracts.
- Scoped Ruff and diff whitespace checks pass. Global Ruff reports 14 unrelated import
  findings in global-search code/tests/migration and test_chat_confirmation.py; see
  `evidence/report-global-lint.txt`. No clean full-checkout gate is claimed.

T125–T127 are delivered. T128 remains open for the shared complete-release gate, as do
T080/T081 overall. The visual context picker, contribution graph measures, current-mode
reporting, assessed carrying value and full scale qualification remain open. No deployment,
company policy activation, new schedule, merge or commit was performed.

The owned PostgreSQL test container and its volumes were removed after verification.

## Historical inventory selection in Analysis (T129–T132, 2026-09-19)

Delivered: a shared bounded read of retained joint inventory confirmations, registered
through graph.inventory_reviews.list, MCP and the existing analytics HTTP API. The
visual Analysis Builder explicitly chooses a confirmation, preserves it across edits,
saving/reopening and chat handoff, and cancels superseded reads. No implicit latest
selection, financial approval, cache refresh or readiness inference from discovery.
Historical result metadata displays actual cutoffs and selected-item coverage, with
Inspector links to the confirmation and retained reviews. Text editing explains its
unsupported context instead of discarding it. Loading/error/empty/retry/paging and mobile
states are covered; all selector text uses existing localization/formatting.

Pre-implementation spec/plan/task review: FR-012/013/014/016/019 mapped to T129–T132,
zero critical findings, Constitution I–VIII PASS, no schema expansion. Reviewer-owned
checklists remain unchanged. Final review found and repaired the quantity declaration's
mandatory axis: it now names base_unit, allowing the existing editor to add that axis
instead of submitting a unit-incompatible quantity total. No financial formula changed.

Evidence:
- selector-first-backend.txt / selector-first-web.txt: missing discovery service and
  dropped visual context fail before implementation.
- selector-backend-final.txt: 305 passed across affected costing, graph, tools, catalogs,
  analysis and specification regressions.
- selector-final-targeted.txt: 53 passed including the added single-review exclusion
  and direct service/tool foreign-cursor proofs.
- selector-unit-axis-first.txt: expected missing base_unit declaration failure;
  selector-unit-axis-final.txt: 64 final tests passed after correction.
- selector-web-final.txt: 317 tests passed. The earlier full run exposed a missing
  capability-topic mapping for the new MCP read; tool_catalog.json now declares it.
  selector-palette-regression.txt (7) and selector-tool-catalog.txt (3) also pass.
- selector-web-focused.txt: 34 final plan/state tests passed, including automatic
  base-unit grouping, context preservation and late/cleared/failed result suppression.
- selector-browser.txt: real React/Chromium acceptance passes with synthetic HTTP
  fixtures: explicit selection, older page, save/reopen, unavailable basis, clearing,
  discovery error/retry/empty/refresh, Inspector links and desktop/mobile layout.
  Screenshots inspected at /private/tmp/reality-inventory-selector/valuation-*.png.
  These presentation fixtures do not claim production financial data verification.
- selector-build.txt: frontend TypeScript/Vite build passes (existing bundle-size warning).
- selector-docs-tests.txt: 73 passed; selector-docs-reference-tests.txt: 8 passed.
  Generated catalog/MCP references were refreshed after the final unit-axis change.
- selector-i18n-scoped.txt: all 169 analysis interface strings covered in en/de/nl/es.
  Global selector-i18n.txt still has three missing CompanySetupForm strings per non-English
  locale, unrelated to this selector. Global Ruff still has 14 unrelated import findings
  in global-search and chat tests/code; scoped Ruff/format, spec and whitespace pass.

T129–T131 are delivered; T132 and the shared full-release gates remain open. T081's
historical inventory selector is now delivered, while contribution reporting, current
valuation, assessed carrying values and broader qualification remain unfinished. No
production migration, deployment, schedule activation, commit or merge was performed.

The owned selector-test PostgreSQL container/volumes were removed and the owned Vite
preview on port 5189 was stopped after verification. Other running stacks were untouched.


## Contribution SQL arithmetic — T133–T136

Internal SQL aggregation now shares immutable commercial_v1 term definitions with
the existing domain kernel. It preserves independent known/final/coverage counters
and same-slice DB1/DB2 subtotals. Exact PostgreSQL numeric quotient/remainder implements
half-even percentages, including signed ties and extreme supported amounts.

- Pre-implementation analysis: evidence/aggregate-analysis.txt; four requirements mapped,
  no critical findings, no schema expansion. Reviewer checklists unchanged (40/6).
- Test-first proof: evidence/aggregate-first.txt fails importing the absent new helper.
- Focused domain/PostgreSQL proof: evidence/aggregate-targeted.txt, 50 passed.
- Broader costs, contribution, selling, reporting and tenant isolation:
  evidence/aggregate-regression.txt, 171 passed in 149.00 seconds.
- Scoped Ruff and formatting pass for all three changed Python files.
- Spec policy passes after registering the test family in docs/SPEC_COVERAGE_MATRIX.md.
  `make spec-check` itself is blocked by the local unaccepted Xcode license; the exact
  Makefile target command `python3 scripts/check_spec_policy.py` passes directly.
- Global Ruff: evidence/aggregate-global-lint.txt retains 14 unrelated import findings.
- Diff whitespace check passes. No public catalogs, MCP schemas, migrations or UI were
  changed, so no generated catalog or browser artifact requires regeneration.

T133–T135 complete; T136 and the broader release gates remain open. This is internal
arithmetic over an already admitted population, not a tenant/context admission service.
Retained contribution publication, compatible scope confirmation, protected canonical
report relation and graph/UI delivery remain open under T080/T081. The disposable test
container is removed after verification; no company settings or policy were activated.


## Joint contribution confirmation — T137–T140

The existing cost.change proposal accepts contribution_batch_review with 2–10 explicit
positions. It reuses full-line admission and verifies a common retained inventory
action/cutoff/knowledge/event/owner/currency and distinct shipment bindings before
emitting one cost.reviewed event. Every retained contribution review uses that event's
recorded_at. No new tables, source amounts, aggregate totals or report cache are added.
Single-line APIs, revision identities and historical reproduction remain compatible.

- Analysis: evidence/contribution-batch-analysis.txt maps seven requirements without
  critical findings; reviewer checklists remain unchanged (40 checked / 6 open).
- Test-first: evidence/contribution-batch-first.txt fails on the missing operation in
  the actual MCP schema after preparing two genuine sales and joint inventory reviews.
- Initial confirmation regression: evidence/contribution-batch-targeted.txt, 31 passed.
- Final affected contribution, selling, receipt, query, inventory-batch, tool, catalog,
  tenant-isolation and spec tests: evidence/contribution-batch-regression.txt,
  180 passed in 346.59 seconds. Includes common metadata, actual event payload,
  independent DB2 coverage, stale/changed/foreign/revoked refusal, atomic rollback,
  historical replay, request bounds and eight isolated cross-member guards.
- Public documentation regenerated from the new nested MCP schema.
  evidence/contribution-batch-docs.txt: 73 passed;
  evidence/contribution-batch-reference.txt: 8 passed.
  evidence/contribution-batch-generated.txt: repeat generation changes no reference.
- Scoped Ruff/format for all five changed Python files, spec policy and diff checks pass.
- Global Ruff: evidence/contribution-batch-global-lint.txt retains 14 unrelated import
  findings. No frontend behavior changed; no browser or migration test was required.

T137–T139 complete. T140 and broader release gates remain open. This confirms selected
input authority; retained contribution generations and protected canonical graph/UI
reporting remain unimplemented under T080/T081. The owned disposable PostgreSQL
container is removed after verification. No company policy is activated or deployment
performed.


## Stored joint contribution observations — T141–T144

Two disposable tables and static migration0070 retain one complete generation for an
executed contribution_batch_review, with exact per-review consumed cost, nullable
known direct/allocated selling subtotals and completeness. Revenue and dimensions
remain on the retained basis. DB amounts and half-even rates are not stored; the
protected canonical SQL population uses the common coverage-preserving aggregates.

The builder validates exact action/review/event/binding membership and reconstructs
all financial results before any cache insert. Tenant/action/version advisory locking
and one savepoint provide idempotency and all-member publication. Reads lock only the
pinned cache rows through per-position and grouped SQL, validate input/output/action
fingerprints, preserve historical context and avoid FIFO, live-cursor queries and
autoflush. The shared owner-authorized costing.contribution.refresh job uses the same
service and deadline; no schedule or financial approval is created.

Evidence:
- contribution-cache-analysis.txt: eight requirements mapped; no critical findings;
  approved production model refined without a fabricated common item-policy identity.
- contribution-cache-first.txt: expected missing cache model import before implementation.
- Initial execution exposed nullable known selling subtotals; storage now preserves
  absent selling review as null and constrains completeness/non-null consistency.
- contribution-cache-targeted.txt: 13 cache, concurrency, real worker, migration and
  registry tests pass. Includes actual late intake during computation, atomic visibility,
  cache protection through reads, calculation/publication rollback and rebuild reuse.
- contribution-cache-regression.txt: 208 passed, two opt-in built-container smoke tests
  skipped, one old tenant-catalog operation count failed. The two new shared services
  increase classified operations from 511 to 513; the expectation was corrected.
- contribution-cache-final-catalog.txt: all 74 final catalog/tenant/coverage/spec checks pass.
- contribution-cache-final-guards.txt: two strengthened scope/worker authorization tests
  pass, including the actual failed/not_authorized worker run after owner revocation.
- contribution-cache-selling-parity.txt: real received 100 direct + 14 allocated selling
  cost yields stored/read DB1 570, DB2 456 and rate 38%; grouped final DB2 stays null
  beside a second position with unknown selling costs.
- contribution-cache-docs.txt: 73 documentation tests pass.
- contribution-cache-reference.txt: 8 generated-model reference tests pass.
- contribution-cache-idempotence.txt: repeat generation changes no public reference.
- Scoped Ruff/format, spec policy and diff checks pass.
- contribution-cache-global-lint.txt: 14 unrelated pre-existing import findings remain.

T141–T143 complete. T144, broader release/scale qualification and T080/T081 remain open.
No DB graph/UI measures or current/company-wide contribution result are exposed. The
owned disposable PostgreSQL instance is removed after verification; no live company
policy, deployment or automatic refresh is activated.

## Historical contribution graph and selector

T145–T149 bind the stored confirmed contribution population to the existing graph,
shared tools/HTTP and analysis editor. Fixed sources compile through the shared SQL
arithmetic kernel; final DB2 stays unknown when selling costs are incomplete. Filters
precede coverage, grouped rates use grouped totals, currency/base unit stay explicit,
and economic dates use a typed UTC date projection. Cache locks survive through the
final graph statement without locking business intake. No new schema or authority.

Evidence:
- contribution-graph-targeted.txt: initial 23 graph/inventory/coverage tests pass.
- contribution-graph-integration.txt: initial 69 passes and four catalog parse failures;
  the malformed evidence indentation was corrected before final validation.
- contribution-graph-regression.txt: 290 passes, 11 failures. One UTC date projection
  defect, one catalog-preview expectation and a missing explicit discovery registration
  explain all failures; all affected tests are rerun in contribution-graph-final.txt.
- contribution-graph-final.txt: 85 tests pass, including every previous failure,
  actual HTTP/saved scope, monthly grouping, partial totals and concurrent cache guards.
- contribution-ui-contracts.txt: 35 focused question/state tests pass.
- contribution-ui-all.txt: all 319 frontend tests pass.
- contribution-ui-browser.txt and contribution-ui-inventory-regression.txt: actual
  Chromium desktop/mobile checks pass for paged explicit selection, save/reopen,
  unavailable basis, clearing, references and failed/empty discovery retry. Browser
  HTTP fixtures are synthetic; PostgreSQL tests prove financial admission/arithmetic.
- contribution-ui-build.txt: TypeScript and production build pass (existing chunk-size warning).
- contribution-ui-i18n-scoped.txt: all 174 analytics strings covered in en/de/nl/es.
- contribution-graph-docs-tests.txt: 73 docs tests pass; contribution-graph-reference.txt:
  eight reference tests pass. Public references regenerated; idempotence checked.
- contribution-graph-lint.txt: owned lint and format pass. Spec policy and diff pass.
- Global lint retains 14 unrelated import findings. Global localization retains the
  three unrelated CompanySetupForm Anthropic strings missing in de/nl/es.

T148 remains open for global/release gates. T080/T081 remain open for broader production
publication and reference-scale qualification. This implementation exposes only the
explicit historical selected scope; it does not claim current full-company margins.
No live tenant, policy, schedule, deployment or financial confirmation was activated.

Final metadata review: contribution-graph-final-metadata.txt has 63 passing graph,
declaration and inventory regressions. Native derived timestamp properties retain
`time` metadata; economic calendar dates remain explicitly UTC. Final scoped lint and
format pass after formatting the additional assertion. Both browser acceptance scripts
pass; the contribution fixture includes both mandatory grouping axes. The owned Vite
server was stopped and disposable PostgreSQL container removed after verification.

## Selected contribution freshness

T150–T152 add explicit historical/current knowledge mode to the retained contribution
scope and analysis selector. Current reads use READ COMMITTED, retain protected cache
admission and compare the tenant cursor after final aggregate SQL. New events withhold
service rows/groups or refuse the graph with cost_basis_pending. Historical reads avoid
the live cursor. Rebuilding a cache never approves new evidence. No schema, queue,
company activation, deployment or financial write was added.

Evidence:
- contribution-current-first.txt: test-first failure because contribution_snapshot did
  not yet accept mode.
- contribution-current-targeted.txt: 28 initial current/cache/graph tests pass.
- contribution-current-regression.txt: 141 backend regressions pass, including
  missing/ready/pending/history, invalid mode/isolation/cursor, foreign scope, HTTP,
  saved questions, inventory, declaration/catalog and tenant-isolation families.
- contribution-current-saved-final.txt: one strengthened proof confirms save/reopen
  remains ready until actual new business data, then HTTP refuses current but preserves
  historical access.
- contribution-current-race-final.txt: two concurrent proofs pause each reader after
  its final numeric SQL, commit ordinary intake independently, and detect pending at
  the final cursor check. Neither cache locks nor cursor reads block intake.
- contribution-current-web-tests.txt: 36 focused question/editor contracts pass.
- contribution-current-web-all.txt: 320 frontend tests pass.
- contribution-current-browser.txt and contribution-current-inventory-browser.txt:
  real Chromium desktop/mobile acceptance passes. Contribution mode persists through
  selection/save/reopen, pending clears prior values, and historical access remains.
  Synthetic browser responses prove UI behavior; real PostgreSQL proves freshness.
- contribution-current-build.txt: production build passes, with existing bundle warning.
- contribution-current-i18n-scoped.txt: all 176 analysis strings covered in en/de/nl/es.
- contribution-current-docs.txt: 73 docs tests pass; contribution-current-reference.txt:
  eight tests pass. Generated references reproduce byte-identically (idempotence.txt).
- Scoped lint/format, spec policy and diff checks pass.
- Global lint still has 14 unrelated import findings. Global i18n still lacks the three
  unrelated CompanySetupForm Anthropic strings in de/nl/es.

T153 remains open for shared global/release gates. T080/T081/T089 remain open: unchanged
knowledge for a selected fixed cutoff is not company-wide publication, affected-scope
invalidation, a moving cutoff or full fixture-J performance qualification. The result
is current at the final cursor observation only, not after future incoming events.

Owned verification resources cleaned up: temporary Vite server stopped and disposable
PostgreSQL container removed. Final spec policy, diff, owned lint and format pass.

## Exact company population closure

T154–T156 implement an internal pure domain prerequisite in cost_population.py. Exact
expected/evaluated inventory and contribution identities must match once each, within
one tenant/cutoff/watermark/algorithm context and with matching per-subject fingerprints.
Explicit unknown observations complete work while preserving separate acquisition,
carrying-value, DB1 and DB2 coverage. Empty populations have explicit empty coverage.
No financial amount, retained authority, database table, public operation or UI changed.

Evidence:
- company-population-first.txt: test-first import failure before module implementation.
- company-population-targeted.txt: 24 initial membership/coverage tests pass.
- company-population-regression.txt: 155 final population, publication, inventory,
  contribution and received-cost domain tests pass. Pure tests use --noconftest to avoid
  the global PostgreSQL bootstrap; they require no database and prove no SQL behavior.
- The large deterministic case validates 10,000 inventory items and 100,000 whole-line
  contributions, with 90,000 DB2-covered lines. It is not fixture J or an integrated
  latency, memory-envelope, reconstruction or publication benchmark.
- company-population-lint.txt: owned lint and format pass. Spec policy and diff pass.
- company-population-global-lint.txt: 14 existing unrelated import findings remain.

Review: population membership is not monetary integrity, financial approval or proof
that a caller supplied a full company census. The future trusted source/evidence census
must prove that coverage and retain input membership, not just fingerprints. The current
publication guard's single policy ID cannot represent multiple item policies; a reviewed
company-manifest variant is required before integration. Unknown carrying value does
not hide acquisition support; missing DB2 inputs do not suppress supported DB1. Multi-pool
ownership and split commercial matching retain their separate admission requirements.

T157 and T080/T081/T089 remain open. No migrations, database access, company activation,
automatic financial confirmation, scheduling or deployment were performed. Catalog and
browser checks are unchanged because no executable public catalog or UI changed.

## Current source-backed company census

T158–T160 deliver bounded current input discovery through the shared costing service.
This does not publish company values or extend the financial admission boundary.

- company-census-first.txt records the test-first missing-service failure.
- company-census-targeted.txt records eight passing tests and one incorrect test
  expectation: the source interpreter correctly classified the example as unsupported,
  not unresolved. The assertion was corrected to preserve the source classification.
- company-census-regression.txt: 81 tests pass across the census, application catalog,
  tenant-isolation families and population guard. Tests cover unreviewed inventory,
  service/credit lines, header-only documents, superseded source versions, absent and
  ambiguous event provenance, strict combined bounds, isolation and concurrent intake.
  A statement audit proves the exercised census executes at most eight SELECTs and
  does not call flush or the inventory valuation service.
- company-census-lint.txt: all four affected Python files pass lint and format.
- Spec policy and git diff whitespace checks pass.
- company-census-global-lint.txt: 12 unrelated import findings remain in the shared tree.

Review: the returned snapshot is current discovery, not historical financial knowledge.
Economic membership, complete financial inputs and source relevance remain unassessed.
No record fingerprint is treated as a retained manifest or a cost-input fingerprint.
The 100,000 combined record cap is a refusal boundary, not fixture-J qualification.
No public tool, MCP schema, UI, migration or scheduling entry changed in this stage.
T161 and company publication/scale/release gates remain open.

## Manifest-bound company publication prerequisite

T162–T164 extend the pure publication guard with a distinct company basis. The existing
selected-scope basis and callers remain compatible. Exact population closure is required
alongside the existing publication checks; no database/service/UI behavior is exposed.

- company-publication-first.txt: test-first import failure before the company basis existed.
- company-publication-targeted.txt: 92 initial company/selected/population proofs pass.
- company-publication-regression.txt: 185 final tests pass across company/selected
  publication, population closure, receipt cost, inventory and contribution domain rules.
  Additional proofs cover selected/company mixing, changed cutoff/scope, duplicate
  expected members and foreign population context. Pure tests use --noconftest.
- An initial broader invocation included test_cost_query.py, whose service imports require
  REALITY_DATABASE_URL; collection refused without configuration. It was excluded from
  this pure-domain run. No service/database qualification is claimed by these results.
- company-publication-lint.txt: both changed Python files pass lint and format.
- company-publication-global-lint.txt: 12 unrelated import findings remain.
- Spec policy and diff whitespace checks pass. No public catalog/MCP schema, UI, migration
  or scheduled handler changed, so generation/browser/migration checks are not repeated.

Review: the hash binds expected membership/context; it cannot prove that the source
census is complete or retain immutable financial inputs. Company storage must establish
those facts, validate persisted output content and retain fencing through commit. The
current census cannot supply a historical knowledge cutoff or financial input digest.
Unknown observations remain distinct from monetary completeness. T165 and T080/T081/T089
remain open. No company activation, database writes, deployment or worker was performed.


## Retained current company census (approved storage implementation)

Owner approval of the dedicated five-table model was explicitly granted on 2026-09-19.
T168 delivers migration 0071, SQL immutable-history guards, canonical snapshot encoding,
shared retention/metadata/member-page/full-verification services and catalog integration.
The caller owns the clean REPEATABLE READ transaction; no ordinary read writes or enqueues.

Evidence:
- census-storage-first.txt: test-first missing retain service failure.
- census-storage-targeted.txt: initial storage/discovery proofs after implementation.
- census-storage-regression.txt: 77 migration, historical retention, concurrency, discovery,
  catalog, data-model and tenant-boundary checks pass.
- census-storage-final.txt: 122 broader checks pass, including the existing receipt,
  inventory-generation and contribution-generation services.
- census-storage-corrections.txt: 41 final migration/index, retention/serialization,
  ordinary document correction and pricing checks pass.
- census-storage-final-guards.txt: 18 storage proofs pass, including per-member/total
  byte refusal before writes and direct SQL refusal of additions after sealing.
- census-storage-parent-first.txt records the failing regression for a malformed legacy
  cross-tenant document parent; the scoped capture guard now refuses it explicitly.
- census-storage-docs-tests.txt: 73 documentation tests pass.
- census-storage-reference-tests.txt: eight schema/reference tests pass.
- census-storage-docs-idempotence.txt: 15 generated references reproduce byte-identically.
- census-storage-lint.txt: all ten owned Python files pass lint/format. Shared services/core.py
  remains formatted. db/core.py has pre-existing formatting differences in unrelated
  local-OS authentication fields; this stage's import ordering is clean.
- census-storage-global-lint.txt: 12 unrelated import findings remain. Spec policy and
  whitespace checks pass after registering all five tables and three new test families.

Review and limits: retained values remain stable after permitted manual amount changes and
source supersession. Original source payloads retain precision beyond normalized database
amounts. Retained line identities cannot be deleted; normal corrections receive explicit
guidance. Counts, member hashes and complete content are checked before sealing and replay.
Page reads check returned members and explicitly disclaim whole-capture verification.
Capture limits are 100,000 rows, 1 MiB/member and 64 MiB canonical member data; current
query materialization is not a measured memory envelope. No financial input resolver,
company generation, new worker, public adapter or valuation approval was added.

T169 remains open for shared release gates; T080/T081/T089 remain open for financial
resolution, transactionally published company results and fixture-J qualification.
Tests use a dedicated disposable PostgreSQL container. No live company database was
migrated, no policy activated and no deployment or commit performed.

Final follow-up: census-storage-parent-regression.txt records all 29 discovery/storage
checks passing after the malformed-parent fix. Final owned lint/format, spec policy and
diff checks pass. The owned PostgreSQL test container was removed with its temporary
volume after all test processes finished. No extension hooks are configured.


## Bounded retained-census review resolution

T170–T172 add the internal resolve_company_cost_census shared service and its tenant
classification. It verifies the retained census, selects reviews introduced by the captured
event cursor, and delegates all amounts and financial input integrity to existing explicit
historical review readers. No new schema, tool/UI, write, job or financial approval exists.

Evidence:
- census-resolution-first.txt: test-first failure before the service existed.
- census-resolution-targeted.txt: six initial PostgreSQL proofs pass.
- census-resolution-final.txt: all eleven final resolution tests pass, including supported
  remaining acquisition cost (420.0000), DB1 with unknown DB2, supported DB1/DB2 (570.0000 /
  456.0000), later approval excluded from old captures, newer live events preserving old
  capture results, cutoff and exact movement mismatches, economic activity after cutoff,
  foreign tenants, strict bounds/isolation and SELECT-only execution without flush.
- census-resolution-docs-tests.txt: 73 documentation tests pass.
- census-resolution-reference-tests.txt: eight reference tests pass.
- census-resolution-lint.txt: all five affected Python files pass lint and format.
- census-resolution-global-lint.txt: 12 unrelated import findings remain.

The bounded resolver does not establish a common historical financial knowledge boundary,
complete company coverage or a resolved-input manifest. Its limit is ten combined subjects;
full capture verification still uses the existing bounded storage contract. Cursor freshness
is deliberately tenant-wide, not input-specific invalidation. Supported DB1 and missing DB2
remain separate, and unresolved source/header gaps remain visible. No monetary totals or
publication eligibility are produced. Existing selected-scope APIs remain unchanged.
T173 and T080/T081/T089 remain open for shared release, financial manifest, publication
and scale work. No live company data, policy or deployment was changed.

Broader completion evidence: census-resolution-regression.txt records 132 passing tests
covering resolution, retained storage, canonical inventory/contribution/selling reads,
application catalog and tenant-isolation families. This overlaps the eleven final scoped
proofs; counts are not additive. Final spec policy and diff checks pass. The isolated
PostgreSQL test container and temporary volume were removed after both test runs exited.
No extension hooks are configured.


## Confirmed contribution-only event relevance

The private relevance proof checks the complete bounded tenant event interval and requires
a confirmed, executed typed contribution decision with exact event payload and exact
introduced review targets. Only proved non-input changes preserve captured inventory or
another sales line. Unknown events, changed inputs, same-line reviews, incomplete history,
malformed actions and intervals above 100 events remain pending. Canonical financial
readers, economic cutoffs, movement membership and publication guards are unchanged.

Evidence:
- review-relevance-first.txt: the normal stock-plus-DB scenario failed before the fix.
- review-relevance-clean.txt: all 17 targeted PostgreSQL tests pass, including joint
  two-item/two-sale review, action/event/target corruption, foreign actions, missing
  history and invalid/overflow intervals.
- review-relevance-docs-tests.txt: all 73 documentation tests pass.
- review-relevance-lint.txt: the three affected Python files pass lint and formatting.

The earlier review-relevance-targeted.txt is not valid test evidence: a sandbox-denied
connection attempt overwrote the redirected output of a separate stalled run. That owned
process was interrupted; the clean rerun above completed successfully. No result is
inferred from the interrupted run.

This is a narrow writer-relevance proof, not general input-specific invalidation or a
common financial manifest. Company publication and reference-scale qualification remain
open. No new schema, public operation, approval, live migration or deployment is included.

Final regression: review-relevance-regression.txt records 140 passing tests in 250.86s
for relevance, captured resolution, contribution reviews/batches, inventory costing,
retained storage, application catalog and tenant isolation. This includes the 17 targeted
proofs; counts are not additive. Spec policy and whitespace checks pass. T174–T176 are
complete; T177 retains the shared release gates and does not claim company readiness.

After all test runs exited, the owned disposable PostgreSQL container and its temporary
volume were removed. No live company database or unrelated container was changed.


## Common captured review basis

The bounded resolver now returns captured_basis, binding the verified census context,
exact item/sales-candidate membership, selected review vector, own knowledge times,
canonical result digests, freshness proof and gaps. Acquisition, carrying, DB1 and DB2
have separate captured-subject coverage. This does not retain a financial manifest,
supply common historical knowledge, sum money or permit company publication.

Evidence:
- captured-basis-first.txt: observed missing-module failure before implementation.
- captured-basis-targeted.txt: 46 initial basis/resolution/relevance tests pass.
- captured-basis-docs-tests.txt: all 73 documentation tests pass.
- captured-basis-lint.txt: all four owned Python files pass lint and formatting.

Additional final tests cover partial subject coverage with unresolved header gaps,
duplicate expected subjects, invalid/non-finite amounts and real complete DB2 coverage.
The final regression result is recorded below after completion. No public tool, catalog
operation, MCP schema or generated reference changed. Spec policy and whitespace checks
pass; no extension hooks are configured.

The first broader run (captured-basis-regression.txt) exposed an inconsistent refusal
message for a floating-point output. The value was already rejected, but hashing ran
before the monetary-shape check. Validation now precedes hashing. The superseded run
was stopped after the actionable failure; it is not completion evidence. All 24 final
basis tests pass in captured-basis-final.txt, including the corrected case.

Final regression: captured-basis-regression-final.txt records 164 passing tests in
155.93 seconds. This includes the final 24 basis tests and existing captured resolution,
contribution-only relevance, contribution/batch review, inventory costing, retained
census storage, application catalog and tenant isolation. Counts overlap; they are not
additive. The real fully evidenced case retains acquisition value 420.0000, DB1 570.0000
and DB2 456.0000; carrying-value coverage remains separately unknown. The resolver's
existing no-flush/SELECT-only and strict bounds/foreign-scope tests remain green.

Final scoped lint/format, spec policy and whitespace checks pass. T178–T181 are complete
for this additive captured-basis slice; shared release gates and T080/T081/T089 are not
closed. No new storage, common historical knowledge, company publication, live migration,
policy activation, deployment or commit was performed.

After all test processes exited, the owned disposable PostgreSQL container and its
temporary volume were removed. No unrelated container or live database was changed.


## Captured-basis retention proposal (T182)

Prepared contracts/captured-basis-retention.md with three typed tables, exact fields,
alternatives, digest-version transition, internal service boundaries, retention/replay,
transaction and rollback rules, explicit limits and test-first migration/isolation matrix.
Spec, plan, tasks and analysis agree on the pending owner approval boundary T183.
Spec policy and whitespace checks pass. No runtime/schema change was made, so no
additional database or runtime test was needed. No disposable resources were created.

Spec impact: proposal clarification only; implemented behavior remains T178–T181.
The existing approvals do not explicitly cover this distinct captured-selection storage
family. The proposal is ready for owner approval; implementation tasks remain unchecked.


## Approved captured-basis retention (T183–T185)

Owner approval of contracts/captured-basis-retention.md was explicit in this session on
2026-09-19. Migration 0078_captured_cost_basis follows 0071 and implements the three
approved typed tables. Internal costing services retain, read and explicitly replay
pinned captured reviews. No monetary authority, public write tool, scheduler entry,
company knowledge boundary or company publication was added.

Evidence:
- basis-retention-first.txt: observed failure before the version verifier existed.
- basis-retention-targeted.txt: 38 initial version/storage/migration/domain tests pass.
- basis-retention-regression.txt: 189 broader tests pass in 207.25 seconds, covering
  storage/migration, captured basis/resolution, event relevance, inventory/contribution
  reviews, census retention, application catalog and tenant-isolation families.
- basis-retention-final.txt: all 27 final storage/migration checks pass, including
  v1/v2 digests, empty/unknown/historical-only coverage, strict byte limits, same-tenant
  wrong-subject review rejection, direct SQL immutability, foreign FKs, damaged content,
  savepoint rollback, concurrent request retry and full supported DB2 replay. Counts
  overlap with the broader run and must not be added.
- basis-retention-docs-tests.txt: 73 documentation tests pass.
- basis-retention-reference-tests.txt: eight reference/schema tests pass.
- basis-retention-docs-idempotence.txt: 15 generated references reproduce byte-identically.
- basis-retention-lint.txt: all eight scoped Python files pass lint and format.
- basis-retention-global-lint.txt: 14 unrelated import findings remain in shared files
  outside this change. Spec policy and whitespace checks pass.

The pinned replay bypasses latest-review selectors, validates the same census and exact
subject/review relationships, delegates all amounts to canonical historical readers and
compares the complete digest. Metadata inspection calculates no financial amounts and
performs no flush or write. Retention alone leaves publication_eligible=false and cannot
upgrade historical-only values or missing DB2. The real complete case preserves stock
420.0000, DB1 570.0000 and DB2 456.0000.

The current boundary remains ten subjects. Verification may still load the bounded census;
it is not fixture-J or ordinary company-report performance qualification. T185 retains
the shared release gate; company historical context, publication and scale remain open.

Additional required compatibility evidence: basis-retention-generation-finance.txt records
69 passing inventory/batch/contribution-generation, ledger/reversal and payment-atomicity
tests in 48.50 seconds. Final spec policy and whitespace checks pass. T184 is implemented;
T185 stays open for the repository-wide release gate. No live company was migrated, no
policy activated and no deployment or commit performed. No extension hooks are configured.

All test processes exited. The owned disposable PostgreSQL container and temporary
volume were removed; no unrelated database or container was changed.


### Captured known-subtotal summary (T186–T189, 2026-09-19)

The initial test failed on the absent summary module (captured-summary-first.txt).
The first implementation exposed PostgreSQL all-null VALUES columns being inferred as
text; explicit numeric casts fixed that real unknown-cost case. The final test run is
captured-summary-regression.txt: 179 passing tests in 202.04 seconds, including all nine
new summary cases, canonical SQL/domain aggregates, pinned replay/storage/migration,
census resolution/relevance, inventory/contribution graph reporting and catalog/isolation.
The earlier captured-summary-targeted.txt intentionally retains intermediate failure
evidence; it is superseded by the final regression run.

Key proof: revenue 200 with goods cost known for only one position yields known DB1 40,
not 140; missing selling costs preserve DB1 but cannot support DB2. Known zero counts as
covered. Currency/unit and inventory owner/method partitions stay separate; exact Decimal
sums survive large values and all-null monetary columns. Real retained replay preserves
stock 420 and DB1 570, while a joint fixture keeps its different units separate. Later
intake cannot change an old summary. Unknown subjects and document/source gaps remain
visible. Known and unknown summary paths execute SELECT only and never flush. Foreign
tenants cannot read a basis. Invalid membership, overflow and unsupported profiles refuse.

Additional evidence: captured-summary-docs-tests.txt (73 pass),
captured-summary-reference-tests.txt (eight pass), captured-summary-docs-idempotence.txt
(15 references byte-identical), and captured-summary-lint.txt (four files pass lint/format).
The new shared service is classified in the tenant catalog (525 operations).
The src/tests-wide lint check records 12 unrelated import findings in
captured-summary-global-lint.txt; it is not a green repository-wide release gate.
T185 remains open. No live migration, policy activation, publication, deployment or
commit was performed. Full-company context/admission, reporting integration, atomic
publication and reference-scale qualification remain open.

The test processes exited and the owned disposable PostgreSQL container and volume
were removed. No unrelated database or container was changed.


### Captured report publication proposal (T190, 2026-09-19)

Documentation-only review compared the existing captured-basis v2 storage, pure historical
company publication guard, selected-review caches and the approved generic production
cache proposal. The key incompatibility is explicit: captured observation time cannot
satisfy PopulationBasis.knowledge_at, and captured selection is not a historical financial
manifest. The proposed amendment preserves a separate fixed captured-report kind and
known-subtotal semantics, reuses four generic cache names and requires owner acceptance
before migration/runtime work. Existing basis eligibility and financial authority do not
change. The contract includes exact fields, tenant/member constraints, bounded reads,
transactions/CAS/retries, rollback, cleanup, alternatives and test-first acceptance.

Spec policy and whitespace checks pass. No executable files changed for this proposal,
so no runtime test run is claimed or required. T191 is the explicit governance gate;
no database, cache, job, graph relation or report was created.


### Approved captured report storage and services (T191–T193, 2026-09-19)

Owner acceptance authorized the four-table basis amendment. The initial domain test
failed on the absent captured_report module (captured-report-first.txt). Migration 0073
is the sole successor to 0072 and creates only the four approved disposable cache tables.
Same-tenant member links and SQL triggers reject wrong-basis membership, foreign basis,
post-seal edits/deletes/inserts and mismatched publication scopes. Whole unpublished-cache
disposal preserves retained basis/review history. No source or financial authority is copied.

Evidence:

- captured-report-regression.txt: 179 tests pass in 169.13 seconds, including 13 new
  captured-report cases, summary/storage, historical population/publication guards,
  SQL aggregates and executable catalog/tenant-isolation proofs.
- captured-report-publication.txt: the additional publication transition test passes in
  7.81 seconds. Fourteen new report cases therefore pass in total.
- captured-report-generation-compatibility.txt: 58 existing inventory, batch, contribution
  generation and graph-reporting tests pass in 67.04 seconds.
- captured-report-docs-tests.txt: 73 pass; captured-report-reference-tests.txt: eight pass.
- captured-report-docs-idempotence.txt: 15 generated references reproduce byte-identically.
- captured-report-lint.txt: eight owned Python files pass lint and seven pass format.
  The shared db/core.py's unrelated authentication-field formatting is not changed.
- captured-report-global-lint.txt: 12 unrelated import findings remain in shared tests.

Tests exercise real acquisition 420 / DB1 570 / DB2 456, unknown-only observations,
independent null totals/rates, exact numeric admission, tenant refusal for all four
operations, SQL immutability, wrong-basis refusal, migration parity/empty round trip,
failed-build savepoint and caller rollback. Concurrent builders converge with a fresh
transaction retry; concurrent first publishers change one pointer once. Publication
rollback, CAS conflict, equal-cursor ambiguity and obsolete replacements refuse without
changing the published result. Fixed-generation pages and subtotals agree across page
cursors and later events; report reads execute SELECT only and do not replay inputs.
The tenant catalog now discovers 529 classified operations.

This is an internal bounded report cache, not a released company report. T194 graph/
saved-report adapters, shared-worker integration, larger population/chunking and fixture-J
qualification remain open. Sealing/publishing a diagnostic does not grant financial
company completeness, historical common knowledge, carrying assessment or user policy
approval. No live company was migrated, no public command/job was added, and no commit
or deployment was performed. Specification policy and whitespace checks pass.

All test processes exited. The owned disposable PostgreSQL container and volume were
removed; unrelated databases and containers were untouched.

### T194 fixed captured graph context — implementation checkpoint (2026-09-19)

The spec, plan, analysis and task now define one explicit fixed `captured_cost_context`
for standalone inventory/contribution graph questions. The implementation adds typed
captured SQL relations through the existing costing derivations, keeps contribution
final totals/rates suppressed, preserves the generation ID through saved analyses and the
web question model, and adds graph/tool/HTTP integration tests. It never resolves the
publication pointer or replays financial inputs on a graph read.

Final verification: all three new PostgreSQL cases pass, and the combined captured-report,
historical inventory/contribution graph, currentness, reporting expansion and catalog
regression passes 113 tests in 56.62 seconds. Unknown members remain explicit, foreign-
generation reads behave as not found, and saved, tool and HTTP reads retain the same
generation without replay. Thirty GraphSteps tests and the production web build pass;
eight generated-reference tests, docs generation, spec policy, scoped lint/format and
whitespace checks also pass. T194 is complete. No company-scale, worker or financial-
admission claim is made.

### Captured discovery and Analysis selector (T195–T197, 2026-09-19)

Six PostgreSQL discovery tests prove sealed-only family filtering, bounds, tenant-safe
cursors, HTTP parity and no input replay. The combined discovery, fixed graph, application
catalog and HTTP regression passes 55 tests. The tool is registered in command, MCP,
tool-topic and tenant-isolation catalogs; the classified operation count is 531. Analysis
selection clears an incompatible historical context, retains the exact generation and
labels the result as a captured known-subtotal diagnostic. Eight Analysis Builder tests,
30 GraphSteps tests and the production web build pass. No worker, larger population,
historical financial manifest or financial approval is introduced.

### Bounded captured-report worker build (T198–T200, 2026-09-19)

Two PostgreSQL cases prove strict configuration, owner/tenant admission, retry reuse, safe
opaque results and absence of publication. The combined captured-report, scheduled registry,
worker and recovery regression passes 37 tests in 40.20 seconds. The registered child uses
REPEATABLE READ and calls the shared builder; it neither returns amounts nor creates a
schedule. CAS publication, retained census/basis orchestration, larger-company chunking,
fixture-J qualification and financial admission remain open.

### Bounded captured publication worker (T201–T203, 2026-09-19)

Four PostgreSQL worker cases prove strict input, owner/tenant admission, first-pointer
change, unchanged retry and stale-request refusal. The combined captured-report, registry,
worker and recovery regression passes 39 tests in 49.30 seconds. Publication remains a
separate READ COMMITTED transaction over the existing CAS service and returns no values.
It does not build, schedule, select latest or grant financial eligibility. Census/basis
orchestration, larger-company chunk closure, fixture J and financial admission remain open.

### Financial company generation schema (T209–T210, 2026-09-19)

The approved seven-table boundary is implemented in migration 0074 and matching SQLAlchemy
metadata. Five focused PostgreSQL cases prove schema parity, empty round trip, populated
downgrade refusal, sealed manifest/generation immutability and explicit unknown-result
shape. The schema/catalog/index block passes 47 tests; ten selected adjacent 0071–0073
migration cases and eight generated documentation reference tests also pass. Scoped Ruff,
format, spec policy and whitespace checks pass. No manifest admission, generation build,
publication job, public adapter or financial completeness claim is introduced by this
schema slice; those remain T211 onward.

### Financial company generation verification (T211–T217, 2026-09-20)

The approved seven-table company-generation boundary is complete through its internal
service and shared-worker integration. Manifest admission retains the exact census,
review choices, knowledge boundary and unresolved source/header gaps. Deterministic
generation records verified references to canonical per-review caches, represents
unknown results explicitly and publishes one scope-keyed generation through CAS. Fixed
reads remain SELECT-only and cannot enqueue work or follow a newer mutable pointer.

Final executable evidence:

- **116 PostgreSQL tests passed in 144.15 seconds** across migrations 0071–0074,
  retained census and captured basis/report compatibility, manifest admission,
  generation build/publication/read/prerequisite behavior, scheduled registry, worker
  execution and recovery.
- A real two-session publication race, synchronized before CAS, produced exactly one
  successful publisher and one `core.Conflict`. Publication now takes the tenant delivery
  lock before reading either an absent or existing pointer, so first publication is fenced
  as strictly as replacement.
- **63 tests passed in 12.20 seconds** for application and tool catalogs, executable data
  model and specification policy. **Eight generated-reference tests passed**, and the
  documentation generator completed successfully with reproducible generated artifacts.
- Scoped Ruff and `git diff --check` pass. No `.specify/extensions.yml` hooks are
  configured. The first final catalog command was blocked only by sandbox access to the
  local PostgreSQL port; the identical authorized rerun passed.

This closes T217 only. T204–T207 remain unchecked: no cost-finding derivation or four-class
exception activation is claimed. T089 also remains unchecked: the earlier synthetic and
prototype measurements do not qualify the integrated product on fixture J or satisfy its
reference-host release gate. The requirements checklist remains **40/46**, with its six
reviewer gates deliberately unchanged. No deployment, live-company migration, accounting
policy activation or carrying-value authority was performed.

### Unified context and bounded company reads (T218–T220, 2026-09-20)

The retained single-scope query and verified financial company generation now emit the
same deterministic requested/resolved/context-identity/freshness envelope. Company
resolution records its manifest, generation, exact cutoffs, algorithms and event cursor,
while explicitly declaring `independent_member_reviews`; nullable company-level policy
and profile fields are not promoted from independently approved members.

The fixed company report no longer materializes every inventory and contribution row in
Python before slicing. Both families use SQL `LIMIT page_size + 1`, stable input-ID order
and opaque cursors bound to the generation and family. Counts, independent coverage and
known acquisition/DB1 totals are separate SQL aggregates over the same verified fixed
generation. A foreign-generation or cross-family cursor refuses; reads remain SELECT-only
and do not enqueue reconstruction.

Verification evidence: **112 tests passed in 78.72 seconds** across cost context, company
schema/migration/manifest/build/publication/read/prerequisite behavior, scheduler/worker
recovery, application/tool/data-model catalogs and spec policy. Documentation generation
completed and all **eight** generated-reference tests pass. Package-scoped Ruff and format,
plus whitespace checks, pass. This reconciles T100/T108 and closes T079/T080. It does not
qualify fixture J (T089), activate T205–T207 findings, complete grouped operational UI, or
change the reviewer-owned 40/46 checklist.

### Shared cost-finding provider (T204–T205, 2026-09-20)

Eight test-first derivation cases initially failed on the intentionally absent provider.
The implemented provider now pins and verifies the published financial company generation,
reads canonical inventory/contribution rows, and follows retained inventory manifests to
their exact received component authority. It derives routing facts only: no FIFO, DB1/DB2,
source amount or review decision is recalculated.

Stable finding identity excludes disposable generation IDs. Generation/manifest identity,
review and component references remain trace metadata. Unknown acquisition covers unsold
items as well as commercial lines; negative DB1 requires known actual DB1 but not complete
DB2. Pending company knowledge preserves supplied previous rows with explicit stale basis,
while a ready evaluated empty set clears them. Foreign input rows are filtered without
disclosure.

The focused provider suite passes **10 tests**. The final provider, application-catalog and
spec-policy gate passes **68 tests in 17.49 seconds**; existing operational derivation and
company-prerequisite coverage was also included in the preceding 269-case run, where 267
passed and the two catalog failures were the subsequently corrected explicit-operation
registration. Package-scoped Ruff and format pass. T206 has not yet registered or activated
the four classes in the projection-backed operational queue.

### Projection-backed cost exceptions (T206, 2026-09-20)

The operational exception catalog now contains four contiguous classes after all legacy
classes: missing acquisition cost, unassigned cost component, stale cost review and
negative actual DB1. Their causes remain a closed, evidence-backed vocabulary and their
German ERP labels are maintained centrally in the business-resource catalog.

The exceptions projection refresh invokes the cost provider once and stores its rows
beside the unchanged legacy derivations in canonical severity/class/subject order. Cost
classes use projection-only registry entries, preventing live per-class recomputation.
Summary, filtered register, page/count and cost detail read the stored snapshot; detail
does not mislabel a stored cost row as cleared merely because the legacy live derivator is
intentionally empty. Pending company knowledge rehydrates previous cost rows and marks
their basis stale. Projection version 5 forces existing caches through the new builder.

The targeted catalog/projection suite passes **65 tests**. The broader legacy derivation,
explanation, attention, projection-job, application-catalog and spec-policy regression
passes **335 tests in 75.18 seconds**. Documentation generation and all **eight** reference
tests pass; scoped Ruff/format and whitespace checks pass. T207 remains open for final
bounded page/count review and the complete scoped verification record; fixture-J timing
remains exclusively T089.

### Bounded exception reads and final integration (T207, 2026-09-20)

The projection-backed attention register now applies severity, class and free-text filters,
canonical ordering, the 100-row cap, page clamping, `LIMIT` and `OFFSET` in PostgreSQL.
Its page rows, filtered count and projection checkpoint metadata are returned by one SQL
statement and therefore describe one database snapshot. The summary likewise groups by
exception class in PostgreSQL and transfers only the compact class-count object, while
still emitting zeroes for catalog classes without open findings. Target enrichment can see
at most the already bounded page.

An executable SQL-capture regression asserts `LIMIT`, `OFFSET` and server-side search on
the register statement and `GROUP BY` without full-row `json_agg` on the summary statement.
The focused attention suite passes **6 tests**. The complete scoped legacy/new exception,
projection, prerequisite, catalog and spec-policy regression passes **326 tests in 63.83
seconds** from the package root; scoped Ruff also passes. This closes T207 and the parent
integration task T082. It does not claim the fixture-J reference-host timing, reconstruction
or refresh budgets: T089 remains open, and the reviewer-owned checklist remains unchanged.
### Fixed company-generation graph analysis (T221–T224, 2026-09-20)

Inventory and contribution graph questions can now name one opaque verified financial
company generation. The compiler reads that fixed generation directly and never follows a
mutable publication pointer during numeric execution. Company relations expose canonical
currency, base unit, customer, article, channel and economic-time dimensions; inventory
time remains non-additive. Known/final population counts remain separate, DB1 totals and
weighted rates use only their exact covered population, and an incomplete DB2 population
returns unknown rather than an invented zero.

Discovery is a bounded metadata-only read of the currently published verified generation.
The selected identity survives tool, HTTP/MCP, saved-report and Analysis Builder round
trips. Result metadata names independent member authority, manifest/generation identity,
coverage and ready/pending freshness. Tests prove that later evidence can make freshness
pending without changing the fixed historical values, and that discovery/execution neither
write, autoflush, replay, rebuild nor enqueue work.

Final executable evidence:

- **316 backend tests passed in 65.20 seconds** across company generation, legacy inventory,
  contribution and captured graph contexts, reporting declarations and isolation, tool/MCP/
  HTTP surfaces, attention reads, cost findings, catalogs and specification policy.
- **39 frontend contract tests passed** and the production web build completed. The company
  generation selection survives editable-question round trips and the basis explanation is
  rendered from server metadata.
- **73 documentation tests**, **eight generated-reference tests**, the documentation build,
  Prettier, scoped Ruff and Python format checks pass. Running the catalog generator twice
  produced the identical Git diff hash `b74c8efe434ed500cce75cd45bbfb3304ddd2e56`.
- The localization audit is green for English and reports the same ten pre-existing missing
  captured-review/company-setup strings in German, Dutch and Spanish. None is a new
  company-generation string; all strings introduced by T221–T223 have translations.

This closes T224 and parent T081. T089 remains open for fixture-J reference-host latency,
reconstruction and refresh-budget qualification. The reviewer-owned checklist remains
40/46. The unrelated `test_actual_child_timeout_retries_without_partial_publication` case
failed once in a last-failed-only run by returning `retry`; it is outside this scoped graph
closure and was not represented as passing evidence here.
## Later retained cost-context inspection — 2026-09-20

The original T078 allowlist now classifies every costing table introduced by the later
captured and financial company-generation work. Retained company census, captured basis,
company manifest and fixed company generation headers and members resolve through the same
tenant-scoped `cost_record` service. Their shortest real links remain navigable and exact
stored values remain unchanged. Disposable report/snapshot result rows and mutable
publication pointers are a literal refused set; no arbitrary table access was introduced.

Test-first evidence initially failed on all twelve new retained families. The final scoped
backend/adapter/catalog/spec regression passes **88 tests in 32.43 seconds**, including
nine Inspector tests for exact captured membership, company context, tenant non-disclosure,
no autoflush/write, bounded member pages and refused derived rows. All **323 frontend
contract tests** and the production web build pass. Documentation generation, **73 docs
tests**, **eight generated-reference tests**, Prettier, scoped Ruff/format, spec policy and
diff checks pass. A second generator run preserved the same docs diff hash
`476442814cdb532db31bb884c87966a6abad8601`.

T225–T227 are complete. T228, T095 and parent T078 remain open solely because the required
checkout-wide Ruff gate currently reports 400 import-order findings across unrelated
benchmark, finance and unified-workspace files. Applying an automatic repository-wide fix
would rewrite unrelated concurrent work and was not performed. The Make wrappers are also
blocked locally by the unaccepted Xcode license; their underlying Python checks were run
directly. No schema, financial decision, publication, deployment or mutable business write
was added.
## Production specific-identification policy — 2026-09-20

The bounded inventory service now accepts either explicitly confirmed FIFO or evidenced
specific identification. A specific scope must allocate every economic issue to exact
layer-entry and original-receipt identities with conserved quantities. Missing, duplicate,
foreign/unavailable or excess portions refuse the complete review; FIFO refuses specific
portions and no method is selected automatically.

The existing confirmed action retains the exact selections. Review hashing includes their
canonical form, and historical reads revalidate the action input before replaying the same
specific kernel. Migration 0075 widens only the existing policy check constraint and
refuses downgrade while retained specific policies exist. It introduces no new table,
column, duplicated relationship, financial approval or browser-side rule.

Executable evidence: **197 inventory/costing tests passed in 43.11 seconds** across kernel,
service, migration, batch review/publication, historical selection, tools, catalogs and
spec policy. A final **45-test** catalog/MCP/migration gate and **36 targeted frontend
contracts** pass. Documentation generation, **73 docs tests**, **eight reference tests**,
spec policy, scoped Ruff/format and diff checks pass. A second catalog-generation run
preserved docs diff hash `781ec57f8496761ebb7627f9ca66bf62c6bfd68b`.

This completes T229–T232 only. Parent T084 remains open for customer/supplier returns,
loss admission, correction normalization, evidenced opening balances and partial,
consignment or transit ownership. T089 and the shared checkout-wide lint/release gate also
remain open. No company policy was activated and no deployment was performed.

## Reviewed carrying-value bridge (T263–T268, 2026-09-20)

Reality now retains source-backed, owner-confirmed write-down and recovery revisions for
exact remaining inventory members. The pure Decimal reconciliation conserves four-decimal
scope, refuses overlap and ambiguity, and caps recovery at retained acquisition cost.
Current reads accept only a complete verified assessment chain; exact inventory-review and
assessment identities reproduce the historical result. Disposable generations and captured
company bases bind the same cutoff and assessment without turning a derivation into authority.
Acquisition cost and commercial DB1/DB2 are unchanged.

The shared Inspector exposes assessment headers, paged parts and shortest tenant-safe links
to inventory membership and source evidence. The existing `cost.change`,
`cost.inventory.get` and `cost.record.get` paths provide CLI, web/chat and MCP pass-through.
The generated English/German Tool Usage reference includes the historical assessment
parameter and new record vocabulary.

Executable evidence: **198 migration, tenant, costing, generation, census, captured-basis,
Inspector and reporting tests passed in 166.35 seconds**. The final focused Inspector/tool
slice passed **16 tests**. Scoped Ruff, specification policy and whitespace checks pass,
and Tool Usage regeneration completed successfully. The checkout-level
`docs-catalog-check` still reports the expected generated diff against `HEAD` because this
working tree contains the uncommitted generated changes from the broader spec-234 work;
the generated files themselves contain the new parameter and were regenerated twice.

This closes T263–T268 and parent T086. It introduces no automatic legal-policy selection,
posting, compliance certification or alternative web business rule.

## Evidence-backed allocation and conversion (T269–T275, 2026-09-20)

The owner approved one immutable source-backed conversion revision with exact
`Numeric(28,12)` numerator/denominator and nullable same-tenant links from acquisition and
selling attribution parts. The shared `cost.change` boundary now confirms weighted
acquisition and selling allocations using explicit `manual`, `equal` or admitted-quantity
drivers. A pure Decimal kernel allocates signed four-decimal totals by largest absolute
remainder and stable opaque target ID, preserving exact residuals and original source signs.

Currency conversions retain the original source share and derive the target observation at
read time. The same result flows through receipt cost and reviewed DB2; unit conversion
authority is retained separately and cannot be used as a monetary basis. Revisions require
the exact predecessor. Conversion chains, inverse lookup, current rates, inferred skonto,
tax duplication and automatic postings remain unsupported.

The Inspector exposes conversion evidence, ratio, action/event and predecessor links. The
existing application tool, CLI, web/chat and MCP paths use the same services. English and
German Tool Usage references were regenerated with the new record vocabulary and command
schema.

Executable evidence: **177 allocation, conversion, migration, receipt, inventory,
contribution, generation, tenant, Inspector and tool tests passed in 368.78 seconds**. A
focused Inspector/tool pass completed **17 tests**, and the final conversion/contribution
slice completed **47 tests**. Scoped Ruff, specification policy, documentation generation
and whitespace checks pass. As elsewhere in this shared uncommitted checkout,
`docs-catalog-check` cannot be represented as a clean-HEAD diff until the accumulated
generated spec-234 documentation is committed; generation itself completed repeatedly.

This closes T269–T275 and parent T087 without changing received evidence, activating a
company policy or creating ledger entries.
## Operational cost explanation — first T088 slice (2026-09-20)

T276–T280 refine the UI delivery without introducing schema or browser-side business rules.
T277 is complete: the typed Web client calls the existing read-only `/cost-query` endpoint,
and one reusable React explanation owns freshness, gap wording, display-only money formatting,
exact retained values and Inspector navigation. Warehouse item previews use it as the first
T278 integration; Analysis reuse and exact document-line Orders/Finance entry points remain open.

Evidence: the test-first contract initially failed all three checks, then passes 3/3 after
implementation. The production frontend build passes (2,002 modules). The existing PostgreSQL
HTTP boundary test passes 1/1 with seven deselected, proving the Web endpoint returns the same
tenant-scoped service context and refusals. Targeted Prettier and `git diff --check` pass.
The localization audit has no missing strings introduced by this slice; it remains globally red
on ten pre-existing strings in CompanySetupForm and InventoryValuation for de/nl/es. Fixture M
has not been run, so its separate deferred SC-002 qualification remains open without blocking
the delivered T088 implementation.

The follow-up completes T276 and T278. Warehouse mounts the shared explanation for the exact
item, and historical Analysis basis uses the same explanation frame and trace hierarchy. The
contract suite passes 5/5 and the production build remains green. A dedicated real Chrome
browser harness passes ready, stale and uninitialized cost responses, locale-rounded money plus
exact four-decimal retained value, six-decimal unit cost, missing carrying evidence, Inspector
routing, two tenant scopes and absence of business mutation requests. The screenshot is retained
at `/private/tmp/reality-234-cost-browser/inventory-cost-explanation.png`. Playwright Core was
installed only in `/private/tmp/reality-playwright-runtime`; no project dependency was added.

T279 is complete without a new endpoint. The existing Document Inspector supplies exact
document-line IDs and, for customer orders, exact billed invoice-line IDs. Finance requests
contribution only for sales-invoice lines; Orders requests it only for explicitly linked billed
invoice lines. Supplier documents, aggregate document IDs and human document numbers never become
contribution scope. The shared component keeps DB1 and DB2 independent. Static executable contract
tests now pass 5/5 and the 2,003-module production build passes.

### T280 technical closeout status

The Fixture M moderator script, controlled setup, exact success rule and empty five-participant
result table are recorded in `fixture-m-usability-protocol.md`. Its status remains **ready to run**;
zero participant sessions are claimed and SC-002 remains open.

Current technical evidence:

- Dedicated Chrome acceptance passes exact/display precision, six-decimal unit cost, ready/stale/
  uninitialized states, missing carrying evidence, Inspector routing, two tenants and no business
  mutation. Contract tests pass 5/5; the production Web build passes.
- Cost query plus retained Inspector regression passes 17/17 from `packages/reality-core`.
- Docs generation, 73 Docs tests, eight reference tests and the Docs production build pass.
- Spec policy and whitespace checks pass. No Spec Kit extension hooks are configured.
- The full backend run was stopped after a PostgreSQL wait with 429 passed and no failures in
  841.89 seconds; it is not a passing full-suite result. The isolated second purchase-to-pay story
  then passes 1/1 in 49.55 seconds, so the interrupted full run is retained as incomplete evidence.
- Global Ruff currently reports 35 import-order findings in shared files outside this UI slice.
  Global `web-build` stops at four pre-existing formatting differences before its test/build steps;
  the owned-file Prettier check passes. The localization audit has ten pre-existing missing strings
  in CompanySetupForm and InventoryValuation; no T088 string is missing.
- `docs-catalog-check` regenerates successfully but remains dirty against HEAD because the shared
  checkout already contains uncommitted costing catalog/docs output. This UI slice changes no
  command, tool, projection, exception, event or MCP schema.

The operational T088 implementation is delivered. T280 remains visibly open as the
owner-deferred external usability qualification; the shared dirty-worktree/global gates
remain part of T090 and must be coordinated rather than inferred complete from this slice.

## Integrated fixture J qualification gate — T089 foundation (2026-09-20)

T281–T285 refine T089 so harness completion cannot be confused with reference-host
qualification. T281 and T282 are complete. The existing large-tenant benchmark package now
contains a fail-closed product-evidence evaluator for schema `reality.fixture-j.product.v1`.
It accepts only the unchanged full two-tenant cardinalities, seed and business date; actual
product entrypoints; the dedicated 4-vCPU/16-GiB local-SSD envelope; all five cold and 20+200
warm read protocols; query/serialization/resource evidence; tenant isolation; three equal
reconstructions including one declared cold-cache run; thirty highest-volume refreshes; and
the specified concurrency, atomicity, recovery, watermark and retained-input proofs. It returns
all refusal reasons rather than accepting a partial report.

Executable evidence: `test_costing_product_qualification.py` passes 4/4 against the local
PostgreSQL test environment, and scoped Ruff plus `git diff --check` pass. The tests prove that
reduced/prototype evidence, any missing workload proof, a tenant leak, checksum divergence and
each exceeded budget remain red.

T283 is also complete. `ProductWorkloads` times the shared `cost.query.get` service/tool path for
order and inventory detail, the shared graph engine for the bounded 100-row inventory page,
compatible totals and caller-supplied monthly product/customer question, the shared exception
page plus count, and the registered MCP cost-query handler. Every result is deterministically
serialized and hashed. Adapter tests prove tenant propagation and exact shared entrypoint use;
the combined qualification/adapter suite passes 7/7.

T284 is now delivered below. T285 remains open and owner-deferred; no reference-host pass is claimed.

## Owner-deferred external qualification (2026-09-20)

The owner currently has neither five suitable operations participants nor a separate
4-vCPU/16-GiB reference host. The owner explicitly decided that these unavailable external
resources do not block provisional technical closeout of feature 234. Fixture M (T280/SC-002)
and the dedicated reference-host execution (T285 and that portion of SC-006) remain visible,
open follow-up qualifications. No moderated-usability or reference-host performance claim may
be made until their original protocols pass. Local production orchestration T284 and the shared
automated closeout T090 remain ordinary technical work and are not deferred by this decision.

## Local product qualification orchestration — T284 (2026-09-20)

T284 is complete. `product_runner.py` binds the production workload adapters to the full-default
protocol of 20 warmups, 200 timed samples, 30 one-per-second refresh changes, five concurrent
readers and one projection worker. It captures cold reads, serialized hashes, SQL query/row
evidence, resource samples and five control-tenant probes. Three supplied retained manifests are
built, idempotently retried, CAS-published and read back through the production company-generation
services; the envelope retains reconstruction duration, checksum, atomic publication and retry
recovery evidence. Reduced counts are allowed only as explicit harness-test configuration and
cannot pass the unchanged fail-closed evaluator.

Executable evidence: runner, workload-adapter and qualification suites pass **9/9** in 1.82
seconds; scoped Ruff passes after formatting. No T285 reference-host result is claimed.

## Local technical closeout follow-up — T090 (2026-09-20)

The local 234-owned closeout is green. The final focused set passes **16/16** and covers the
canonical demo costing profile, twelve-week history coexistence, generated action reference,
exception/reference counts, reporting-graph coverage, product runner, workload adapters and the
fail-closed qualification evaluator. The selling migration boundary and actual child-process
timeout/retry atomicity add **3/3** passing checks. The benchmark child now accepts the same
bounded optional session-info input as the production runner; the 0067 migration assertion
correctly excludes the conversion-basis relationship introduced only by migration 0081.

Shared gates completed locally:

- Spec policy passes, including the new product-runner coverage-matrix entry.
- Package-wide Ruff passes after 36 mechanical import-order repairs.
- Web formatting, **328 tests**, all four-language audits and the production build pass.
- Docs generation, **73 tests** and the production build pass.
- `git diff --check` passes. Generated catalog pages are reproducible but differ from HEAD because
  this feature's catalog and generated output are intentionally still uncommitted in the shared
  worktree; `docs-catalog-check` therefore cannot use a clean-HEAD assertion as a completion claim.

The complete backend run executed all 3,816 collected tests in 25:41: **3,793 passed, 9 skipped,
14 failed**. Isolation separated one order-dependent pass and repaired six 234/shared-catalog
failures: action fixture drift, demo-history coexistence, exception count, reporting-graph table
coverage, the historical selling-migration comparison and benchmark child-process protocol.
Seven reproducible failures remain in concurrent non-234 work: profile-scope fixture setup, two
manual-document-correction retry assertions, Storyline chat evidence, two unified credit journey
assertions and one unified invoice-credit assertion. They are not silently attributed to 234 and
keep the shared T090 checkbox open until coordinated and followed by a green complete rerun.

2026-09-21 canonical-demo regression: the live browser showed the confirmed
six-position DB1/DB2 valuation but its selection was unreadable because setup retained
the confirmation without publishing its disposable generation. T287 adds a failing
service regression and builds the generation through the shared costing application
service immediately after the confirmed batch review. The complete demo-costing test
file passes 6/6; combined directly affected setup and costing files pass 18/18. This
adds no financial authority: all values continue to derive from retained reviews and
source evidence, while the generation remains disposable.

Owner-deferred T280 and T285 remain the only unavailable external qualifications. They do not
invalidate the local 234 implementation evidence, and no moderated-usability or reference-host
performance result is claimed.

2026-09-21 operational verification: a fresh live-demo invoice became stale as new
synthetic evidence arrived. The shared response still carried exact retained
`basis_db1=150.0000` and `basis_db2=125.0000`; the operational component now displays
those recorded values beneath the existing retained/not-current warning instead of
incorrectly showing “Not evidenced”. Visible port-8080 verification confirmed DB1
EUR 150 and DB2 EUR 125 with their exact four-decimal values and Inspector trace.

2026-09-21 stale-inventory follow-up: visible port-8080 verification showed that the
Warehouse explanation hid the service's retained `basis_acquisition_value` whenever live
demo events made the current review stale. T289 now displays that exact retained value
beneath the existing non-current warning, preserves an unsupported carrying value as
unknown and performs no browser arithmetic. The test-first contract failed before the
change and passes 5/5 afterward; the dedicated real-Chrome harness passes ready, stale and
uninitialized cases, exact retained precision, Inspector routing, tenant switching and
GET-only behavior. The production Web build passes. On the fresh `Reality Live Demo Watch`
tenant, Coast Storage Box and Ridge Backpack truthfully show retained acquisition value
EUR 0.00: their selected latest reviewed company-owned scopes had no remaining acquisition
value, while later operational stock is outside that frozen review. The UI no longer
misstates that retained zero as absent evidence.

The owner rejected zero-valued retained stock as unsuitable canonical demo behavior. T290
removes fixture A's synthetic 40-unit supplier-return cleanup: the received acquisition
evidence remains EUR 1,050 for 100 units, the sale still consumes 60 units at EUR 630, and
the latest retained inventory context now preserves the intended 40 company-owned units at
EUR 420. The separate exact signed customer-return story remains. The regression failed
first because the previous latest basis was stale with zero remaining value; it now proves
the stale retained basis carries quantity 40.0000 and acquisition value 420.0000. The full
demo-costing and company-setup set passes 35/35 in 193.43 seconds.
