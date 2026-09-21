# Tasks: Inventory cost and contribution

**Current restart checkpoint (2026-09-19):** T192/T193 delivered; resume at T194.
Read [HANDOFF.md](HANDOFF.md) for exact remaining work, approvals and verification.
Older convergence descriptions record the state when written; later completed subtasks
and the handoff distinguish delivered functionality from open release gates.

Initial Phase 0 scope (historical): implement the owner-authorized isolated experiment
in plan.md, not product slices 1–4. Later sections record subsequent production approvals.

## Phase 1: Gates

- [x] T001 Record Phase 0 authorization and review plan.md/spec.md.
- [x] T002 Verify Phase 0 Constitution Check in plan.md and analyze these tasks.

## Phase 2: Failing proofs

- [x] T003 [US1] [FR-002, FR-003, FR-020, FR-021] Add source cost/assignment tests in packages/reality-core/tests/test_costing_spike_contract.py.
- [x] T004 [US2] [FR-005, FR-007, FR-022] Add FIFO, returns, cumulative rounding and revised-cutoff tests in packages/reality-core/tests/test_costing_spike_contract.py.
- [x] T005 [US6] [FR-018, DR-001, DR-002, DR-003, DR-004, DR-005] Add dataset guard, tenant, projection atomicity, scope and reconstruction tests in packages/reality-core/tests/test_costing_spike_postgres.py.

## Phase 3: US1/US2 calculation prerequisites

- [x] T006 [US1] [FR-002, FR-003, FR-020, FR-021] Implement exact received-cost composition and allocation in packages/reality-core/benchmarks/large_tenant_registers/costing_kernel.py.
- [x] T007 [US2] [FR-005, FR-007, FR-022] Implement ordered FIFO/specific returns and cumulative rounding in packages/reality-core/benchmarks/large_tenant_registers/costing_kernel.py.

## Phase 4: US6 qualification

- [x] T008 [US6] [FR-018, DR-001, DR-002, DR-003] Implement isolated deterministic PostgreSQL input schema, fixed cardinalities, reduced profile and manifest guards in packages/reality-core/benchmarks/large_tenant_registers/costing_dataset.py.
- [x] T009 [US6] [FR-010, FR-011, FR-012, FR-013, FR-014, FR-024, FR-025, DR-004] Implement direct and projected observation workloads with exact scope, atomic publication and gap reporting in packages/reality-core/benchmarks/large_tenant_registers/costing_cases.py.
- [x] T010 [US6] [FR-018, SC-006] Implement measured runner, checksums, truthful pass/refusal/result evidence in packages/reality-core/benchmarks/large_tenant_registers/costing_runner.py.
- [x] T011 [US6] [FR-018] Execute reduced and full runs in a dedicated PostgreSQL target and record actual limits/results in specs/242-inventory-cost-contribution/evidence/.

## Final review

- [x] T012 Run appropriate tests, Ruff and spec checks; record failures and architecture decision in specs/242-inventory-cost-contribution/verification-results.md.
- [x] T013 Update specs/242-inventory-cost-contribution/quickstart.md with actual commands and scope, and review new files against the Constitution.

## Dependencies and coverage

T001–T002 -> tests T003–T005 -> T006–T008 -> T009 -> T010 -> T011–T013.
Pure kernel tests and PostgreSQL contract test authoring can be independent, but shared
implementation files are sequential. No production UI, permission service or migration
is delivered. US5 permissions remain existing product behavior; experiment guards prove
only its disposable target/tenant boundaries. US3/US4 semantics are exercised as calculation
prerequisites, not advertised as implemented product stories. All experiment requirements
in plan.md map to test tasks T003–T005 and implementation tasks T006–T010. Full product
FR-001, FR-004, FR-006, FR-008, FR-009, FR-015–FR-017, FR-019, FR-023, FR-026–FR-027 and
adapter/authorization parts of the other requirements remain future slices.


## Execution scope clarification

Completed implementation tasks mean the isolated prototype exists and its small contract
proofs pass; they do not close their corresponding product FRs. T011 records exploratory
execution, not a passing architecture gate. Full reference-environment, adversarial-history,
product-derived-relation and exception/freshness qualification remains open after these
measurements and must precede approval of the production schema. No incomplete product
story is marked delivered by these task checkboxes.


## Continuation: US6 qualification and product integration design

- [x] T014 [US6] [FR-018] Add adversarial distribution, split-join, return conservation and stale/live tests in packages/reality-core/tests/test_costing_spike_postgres.py and test_costing_spike_contract.py.
- [x] T015 [US6] [FR-005, FR-010, FR-018] Implement v3 inputs and canonical return/partial-match observations in packages/reality-core/benchmarks/large_tenant_registers/costing_dataset.py, costing_kernel.py and costing_cases.py.
- [x] T016 [US6] [FR-018, DR-004] Implement concurrent 200-sample workloads, checkpoint freshness and full reconciliation in packages/reality-core/benchmarks/large_tenant_registers/costing_runner.py and costing_cases.py.
- [x] T017 [P] [US6] [FR-012, FR-024, FR-025] Document concrete system integration and acceptance proofs in specs/242-inventory-cost-contribution/contracts/product-integration.md.
- [x] T018 [US6] [FR-018] Run reduced/full capped PostgreSQL experiments and preserve actual settings/results under specs/242-inventory-cost-contribution/evidence/.
- [x] T019 Review integration, rerun experiment tests/lint/spec gates and record remaining gates in specs/242-inventory-cost-contribution/verification-results.md and quickstart.md.

Dependencies: T014 -> T015 -> T016 -> T018 -> T019; T017 is independent research.
Reference-host certification is not implied by T018 execution. Production tasks follow
separate schema/architecture review, not these experiment task checkboxes.


T019 verification note: local costing tests, formatting, lint, links and capped measurements
pass. The final global spec-policy check is blocked by the concurrently added, unmapped
feature-235 `test_global_search_matching.py` test family. Keep this task open until the
shared gate is green; do not modify that separate implementation to claim completion.


## Continuation: scoped live availability

- [x] T020 [US6] [FR-018, DR-004] Add failing scope, fallback, bound and parity proofs in packages/reality-core/tests/test_costing_spike_postgres.py.
- [x] T021 [US6] [FR-018, DR-004] Implement bounded read-only live order responses in packages/reality-core/benchmarks/large_tenant_registers/costing_cases.py.
- [x] T022 [US6] [FR-018] Measure hot-pool and distributed live routes during mixed load in packages/reality-core/benchmarks/large_tenant_registers/costing_runner.py; retain evidence under specs/242-inventory-cost-contribution/evidence/.
- [x] T023 Record live availability results and remaining gates in specs/242-inventory-cost-contribution/verification-results.md and contracts/product-integration.md.

T020 -> T021 -> T022 -> T023. Read-only cross-artifact review finds no CRITICAL scope
conflict: this closes an experimental availability gap, not production integration or
the exact reference-host gate. The shared feature-235 coverage gate remains separate.


Current T019 context: isolated baseline-plus-costing review now passes spec policy and all
30 costing tests (see live-isolated-review.json and live-isolated-tests.txt). The shared
working tree still has separate feature-235 coverage gaps; retain this final shared gate
as open. T020–T023 are complete for the explicitly bounded prototype scope.


## Continuation: bounded shared worker

- [x] T024 [US6] [FR-018, DR-004] Write failing staged-generation and shared-claim tests in packages/reality-core/tests/test_costing_spike_jobs.py.
- [x] T025 [US6] [FR-018, DR-004] Implement frozen staging, bounded ranges and atomic published relation in packages/reality-core/benchmarks/large_tenant_registers/costing_generations.py and costing_cases.py.
- [x] T026 [US6] [FR-018, DR-005] Exercise the existing shared queue/child watchdog through the static experimental adapter in packages/reality-core/benchmarks/large_tenant_registers/costing_worker.py.
- [x] T027 [US6] [FR-018] Execute reduced/full worker qualification with actual poll pacing in packages/reality-core/benchmarks/large_tenant_registers/costing_worker_runner.py; retain evidence under specs/242-inventory-cost-contribution/evidence/.
- [x] T028 Record shared-worker limits, integration implications and checks in specs/242-inventory-cost-contribution/verification-results.md and contracts/product-integration.md.

T024 -> T025 -> T026 -> T027 -> T028. Cross-artifact analysis: no CRITICAL conflict for
this isolated continuation; the temporary bootstrap is explicitly a qualification seam,
not a production runtime registration or an authorization bypass. Full product source
history and normal startup integration remain distinct future gates.

## Continuation: actual product adapter design

- [x] T029 [US3, US5, US6] [FR-010–018, FR-024–027] Audit actual compiler, graph/tool and exception page/count boundaries and record the concrete delivery contract in contracts/adapter-delivery.md.
- [x] T030 [US3, US5, US6] [FR-011, FR-014, FR-015, DR-001–005] Review context, grain, support states, partial aggregates and generation races; update plan.md, research.md, data-model.md, quickstart.md and verification-results.md.

These are completed design/review tasks, not production implementation tasks. The next
step is a concrete production evidence/history/storage proposal for owner review,
followed by per-slice test-first tasks and analysis. Slices A–E in adapter-delivery.md
remain unimplemented. No prototype or planning result closes the product/reference gate.

## Continuation: concrete production data model

- [x] T031 [US1–US6] [FR-001–027, DR-001–005] Audit received evidence, manual corrections, event ordering and exact receipt/return/revenue relationships; specify fields, constraints, input retention and staged storage in contracts/production-data-model.md.
- [x] T032 [US1, US2, US5, US6] [FR-003/005/007/014/015/019/020, DR-001–005] Review replacement/sign/tax/correction/history invariants, migration/rollback and the concrete first-slice approval boundary; update the linked plan, research, model and validation guide.

These completed entries record preparation/review only. Product migrations, domain and
service implementation remain unstarted. Owner review of the concrete model and proposed
qualification ordering precedes detailed implementation tasks and consistency analysis.
No prior implementation gate, company policy or release qualification is marked approved.


T019 closure at the production-model review: shared and isolated spec policy now pass;
the earlier costing/worker regression and scoped lint evidence remains applicable to
unchanged experiment code. The parallel coverage omission was fixed independently.
This closes the experiment review task, not product implementation, full CI of parallel
features, or fixture-J/reference qualification. See production-model-review.json.


## Approved first product slice: receipt acquisition cost and coverage

- [x] T033 Record owner schema/implementation approval and release-gate ordering in spec.md, plan.md and contracts/production-data-model.md.
- [x] T034 [US1] [FR-002/003/020/021/022] Add failing signed conservation/tax/precision tests in packages/reality-core/tests/test_costing_domain.py.
- [x] T035 [US1] Implement typed receipt-cost requests and pure validated contribution rules in packages/reality-core/src/reality/domain/costing.py.
- [x] T036 [US1] [DR-001–005] Add failing schema/migration/history-link proofs in packages/reality-core/tests/test_costing_migration.py.
- [x] T037 [US1] Implement approved receipt/evidence/attribution/review/manifest models in packages/reality-core/src/reality/db/costing.py and migrations/versions/0071_receipt_costing.py.
- [x] T038 [US1] [FR-001–003/007/014–016/019] Add failing receipt A, tax/credit/partial coverage, revisions/history, stale/demotion/foreign and rollback tests in packages/reality-core/tests/test_costing_services.py.
- [x] T039 [US1] Implement shared receipt/evidence reads, reviewed attribution and sealed receipt manifests in packages/reality-core/src/reality/services/costing.py.
- [x] T040 [US5] [FR-007/015/019] Implement admitted evidence protection, typed replacement and correction capture in services/costing.py and narrow hooks in services/core.py; prove them in tests/test_costing_services.py.
- [x] T041 [US5] [FR-016/019/027] Add proposal/confirmation/replay and actual read-tool/MCP proofs in packages/reality-core/tests/test_costing_tools.py.
- [x] T042 [US5] Wire typed cost.change and cost.receipt.get/cost.evidence.get through tools/costing.py, tools/finance.py, tools/application.py and mcp/catalog.py.
- [x] T043 Register exact commands/events/resources/tenant checks in packages/reality-core/config/ catalogs and docs/SPEC_COVERAGE_MATRIX.md; generate Tool Usage reference.
- [x] T044 Run complete required backend/migration suites, scoped lint, spec/tenant/catalog/docs gates; retain evidence in specs/242-inventory-cost-contribution/evidence/.
- [x] T045 Review implementation against the approved first slice; record delivered behavior and remaining inventory/DB/release gates in verification-results.md and docs/features/receipt-costing.md.

Dependency order: T033 -> T034 -> T035 -> T036 -> T037 -> T038 -> T039 -> T040 ->
T041 -> T042 -> T043 -> T044 -> T045. Domain and migration proof authoring can be
reviewed independently; shared core/dispatch edits remain sequential. Tests precede
the behavior they prove. Completing this slice does not complete inventory valuation,
commercial DB adapters, full fixture J or product release.

## Inventory foundation: US2 calculation before service integration

- [x] T046 [US2] [FR-004–007/017/018/022] Record the approved calculation boundary and Constitution review in spec.md, plan.md and research.md; analyze consistency before implementation.
- [x] T047 [US2] [FR-004–007/017/018/022] Add failing FIFO/specific/return/rounding/unknown/bounds proofs in packages/reality-core/tests/test_inventory_costing.py.
- [x] T048 [US2] [FR-004–007/017/018/022] Implement the pure production kernel and exact provenance in packages/reality-core/src/reality/domain/inventory_costing.py.
- [ ] T049 [US2] [FR-005/007/022] Verify conservation and immutable replay with adversarial cases in packages/reality-core/tests/test_inventory_costing.py; run costing regression, lint and spec gates.
- [ ] T050 Document calculation delivery and pending policy/ownership/service integration in docs/features/receipt-costing.md, docs/SPEC_COVERAGE_MATRIX.md and verification-results.md.

T046 -> T047 -> T048 -> T049 -> T050. This is the independently testable domain stage;
US2 as an application feature remains open until authority/history and shared-service
integration, generation and adapter tasks from the approved production contract ship.
No new public inventory command or company policy is introduced by these tasks.

Inventory foundation verification: 116 costing regressions and the complete sequential
backend suite (3,089 passed, 9 skipped) pass. Scoped lint/format and spec policy pass.
T049/T050 remain unchecked at the shared completion gate: global Ruff reports 13
unrelated feature-235 import-order findings. The domain implementation and delivery
documentation are present; no overall green-CI/release claim is made. See
verification-results.md and evidence/inventory-*.txt.

## Reviewed bounded inventory service: US2 / US5

- [x] T051 [US2] [FR-004–008/014–019/022/027] Record and analyze approved service scope in spec.md, plan.md and contracts/inventory-service.md.
- [x] T052 [US2] [FR-004–008/014–019/022] Add failing service/history/ownership/isolation/rollback proofs in packages/reality-core/tests/test_inventory_costing_services.py and migration proofs in tests/test_inventory_costing_migration.py.
- [x] T053 [US2] [DR-001–005] Implement typed request, retained authority and static migration in domain/costing.py, db/inventory_costing.py and migrations/versions/0072_inventory_costing.py.
- [x] T054 [US2] [FR-004–008/014–019/022] Implement bounded confirmed admission and historical read in services/inventory_costing.py, delegated through services/costing.py.
- [x] T055 [US5] [FR-016/019/027] Extend existing application/MCP tools and catalog/tenant/data-model/resource vocabulary; prove actual dispatcher behavior in tests/test_inventory_costing_services.py.
- [ ] T056 Run required regression, migration, catalog, docs, lint and spec gates; record exact results and remaining gates in verification-results.md and docs/features/receipt-costing.md.

T051 -> T052 -> T053 -> T054 -> T055 -> T056. Historical full-product checklist markers
remain reviewer-owned. T049/T050 global-lint status remains separately visible.

T056 verification evidence is recorded: 3,112 full-backend tests passed (9 skipped),
155 final targeted tests passed, 11 Web catalog and 10 docs tests passed; generated
references are idempotent, scoped lint/format and spec policy pass. The checkbox remains
open because the shared global lint gate retains 13 unrelated feature-235 findings.
The dedicated test container was removed. Full-product qualification remains separate.

## Contribution calculation foundation: US3

- [x] T057 [US3] [FR-010–014/016/022] Specify and analyze the approved pure calculation boundary in spec.md and plan.md.
- [x] T058 [US3] [FR-010–014/016/022] Add failing arithmetic, coverage, context, partition, trace and bound tests in packages/reality-core/tests/test_contribution.py.
- [x] T059 [US3] Implement immutable matched-slice aggregation in packages/reality-core/src/reality/domain/contribution.py.
- [ ] T060 Verify costing and full backend regressions, lint and spec gates; document scope and evidence in verification-results.md, docs/features/receipt-costing.md and docs/SPEC_COVERAGE_MATRIX.md.

T057 -> T058 -> T059 -> T060. No full US3, matching-service, reporting, HGB or release
completion is implied. Earlier shared global-lint gates remain separately visible.

T060 evidence: 128 scoped costing tests and 3,143 full-backend tests passed (9 skipped);
scoped lint/format and working-tree spec policy pass. The checkbox remains open because
global Ruff retains the 13 unrelated feature-235 findings. Documentation and final review
are recorded in verification-results.md; the disposable test container was removed.

## Current contribution preview: US3 / US5

- [x] T061 [FR-010/011/014/016/019] Specify, review and analyze the bounded current preview in spec.md and plan.md.
- [x] T062 Add failing preview-mode and service evidence/trace/gap/isolation tests in tests/test_contribution.py and tests/test_contribution_services.py under packages/reality-core.
- [x] T063 Implement preview context and read-only service in domain/contribution.py, services/contribution.py and services/costing.py; typed input in domain/costing.py.
- [x] T064 Register shared read tool/MCP and catalogs; update generated documentation and prove dispatcher parity.
- [ ] T065 Verify full/scoped gates and document delivered preview plus outstanding confirmed matching/revenue history/reporting in verification-results.md and docs/features/receipt-costing.md.

T061 -> T062 -> T063 -> T064 -> T065. This read-only preview introduces no confirmed
match authority or finalized commercial result. Earlier global-lint gates remain open.

T065 evidence: 151 final affected tests, 3,163 full-backend tests (9 skipped), 11 Web
catalog tests and 10 docs tests pass. Generated references are idempotent; scoped lint,
format and explicit working-tree spec policy pass. The global lint gate still reports
13 unrelated feature-235 findings, so this shared completion checkbox remains open.
Verification and final review are recorded; the dedicated test container was removed.

## Confirmed single-line commercial contribution: US3 / US5

- [x] T066 [FR-007/010–016/019/022, DR-001–005] Record and analyze the bounded reviewed service in spec.md, plan.md and contracts/contribution-service.md.
- [x] T067 Add failing service/history/confirmation/isolation/uniqueness tests in packages/reality-core/tests/test_contribution_reviews.py and migration proof in tests/test_contribution_migration.py.
- [x] T068 Implement typed request, retained basis/review and static migration in domain/costing.py, db/contribution.py and migrations/versions/0073_contribution_reviews.py.
- [x] T069 Implement confirmed service, frozen reads and admitted document protection in services/contribution_reviews.py and services/costing.py.
- [x] T070 Wire cost.contribution.get, contribution_review and MCP/catalog/resource/tenant vocabulary; generate docs and verify shared dispatch.
- [ ] T071 Run complete regression and required gates; record exact results and remaining selling/partial/history/reporting gates in verification-results.md and docs/features/receipt-costing.md.

T066 -> T067 -> T068 -> T069 -> T070 -> T071. Scope is one whole invoice line and
shipment; DB2 and full-product release remain separate. Reviewer checklist markers and
earlier shared global-lint completion gates are not changed.

T071 evidence: 234 affected tests, 3,180 full-backend tests (9 skipped, 1 existing
warning), 11 Web catalog tests and 10 docs tests pass. Generated references are
idempotent; scoped lint, formatting and working-tree spec policy pass. The global
lint gate retains 13 unrelated feature-235 findings, so this checkbox remains open.
Final review and remaining scope are recorded in verification-results.md. The owned
disposable PostgreSQL container was removed after the complete backend run.

## Source-backed selling allocation and reviewed DB2: US3 / US5

- [x] T072 [FR-003/007/011–016/019/020/022] Specify and analyze contracts/selling-service.md and linked spec/plan/model.
- [x] T073 Add failing domain/service/history/isolation and migration tests in packages/reality-core/tests/test_selling_costs.py and test_selling_migration.py.
- [x] T074 Implement typed selling inputs, three retained tables and static0067 migration in domain/costing.py, db/contribution.py and migrations/versions/.
- [x] T075 Implement source-conserving selling revisions, contribution review membership and DB2 derivation in services/selling_costs.py and shared costing delegates.
- [x] T076 Extend cost.change schema, catalogs/tenant evidence and generated documentation; prove shared tool/MCP parity.
- [ ] T077 Run scoped/full regression and required gates; document exact evidence, final review and remaining scope.

T072 -> T073 -> T074 -> T075 -> T076 -> T077. Earlier shared completion gates and
reviewer-owned checklist markers remain unchanged.


T077 evidence: 257 affected regression tests, 40 final DB1/DB2/migration tests,
3,205 full-backend tests (9 skipped, 1 existing warning), 11 Web catalog tests and
49 docs tests pass. Generated references are idempotent; scoped lint/format and spec
policy pass. Global Ruff retains 13 unrelated feature235 findings, so this checkbox
remains open. Final review and remaining scope are in verification-results.md. The owned
PostgreSQL test container was removed after the complete run.

## Phase 5: Convergence

Assessment date: 2026-09-19. This append-only assessment compares present production
code with the approved complete feature, including its bounded continuation contracts.
It does not reopen delivered slice arithmetic or treat experimental benchmark code as
production implementation. Earlier tasks and reviewer-owned markers remain unchanged.

Scope checked: all 27 FRs, seven SCs (SC-002 is a later moderated product-validation
obligation, not an automated pass), eight Constitution principles and five architectural
boundaries: retained authority, frozen context, canonical relations, shared adapters and
bounded scheduled publication. Findings: six missing and seven partial; twelve HIGH and
one MEDIUM. No newly demonstrated Constitution violation or unrequested implementation
was found in this scoped assessment; this is not a security or full code-correctness audit.

- [ ] T078 [HIGH] Complete cost-record inspection per FR-016/023/027 and SC-003/005 (partial). Write tenant/non-disclosure and actual web/CLI/MCP round-trip tests first, then add shared record readers and shortest source/decision links for the costing tables in services/costing.py, services/inspector_register.py, web/api.py, cli/app.py and the existing tools/MCP catalogs. Evidence: service traces expose opaque cost IDs, while the Inspector register/route has no cost families; resource vocabulary alone does not resolve a reference. Include bounded member pagination, exact Decimal display, historical decision labels and centrally maintained German terminology; never turn record inspection into a new calculation authority.
- [x] T079 [HIGH] Implement a reusable cost-query context per FR-004/007/011/012/014/015/016 and plan: adapter-delivery section 2 (partial). Add context/isolation/history tests before extending domain/costing.py and shared services with requested versus resolved effective/knowledge cutoffs, compatible policy/profile scope, algorithm identity and explicit freshness. Evidence: contribution reviews currently use their own IDs as scoped profile/generation identities; the pure aggregate kernel correctly refuses incompatible contexts. Preserve existing review digests and do not relabel independently approved single-line reviews as one company-wide profile. Document and review any required retained schema before its migration.
- [x] T080 [HIGH] Deliver production canonical cost generations and bounded reads per FR-007/012/014/018 and plan: adapter-delivery sections 2–3 (missing). Write publication-race, rollback, retained-input reconstruction and bounded page/total tests first; implement production services/costing.py and services/analytics/costing_relation.py using the existing shared job/projection registry and the approved generation contract. Evidence: staging/publication and worker qualification live under benchmarks/large_tenant_registers, while production has only per-item/per-line reads. Pin one generation across rows, totals and cursors; reads must not enqueue work or scan the whole tenant. Keep requested-scope current assessment distinct from a stale global generation; no automatic financial approvals.
- [x] T081 [HIGH] Integrate grouped cost/contribution questions with the existing graph and saved reports per FR-012/013/014/016/023/024 and SC-004. Partial-scope known subtotals, complete totals, weighted rates, fan-out refusal, dimensions, currency/unit partitions and saved fixed/current context are verified through T221–T224. The implementation reuses graph.ask and the Analysis Builder, preserves non-additive inventory time semantics and adds no second report engine.
- [x] T082 [HIGH] Add cost findings and bounded queue/count integration per FR-014/015/018/025 and plan: adapter-delivery section 5 (missing). Write stale-generation, clearing, stable-identity, negative-supported-DB1 and legacy-class regression tests first. Extend operational_exception_catalog.yaml and services/{exceptions,projections,read_contracts}.py plus web/read_models.py and shared tool reads with missing acquisition cost, unassigned component, stale review and negative actual DB1. Evidence: the catalog retains the agreed-purchase-price comparison but has none of the four planned actual-cost classes. Include unsold receipts/components, current-versus-unevaluated state and one compatible page/count basis; do not clear findings merely because reconstruction is pending.
- [x] T083 [HIGH] Seed the canonical source-backed costing demo through existing application services per FR-026 and SC-007. International-v2 retains source-backed inventory, DB1 and DB2, plus deliberate missing-cost and late-cost/return stories through normal services.
- [x] T084 [HIGH] Connect the existing inventory kernel's broader cases to production admission/history per FR-004/005/006/007/008/017 and SC-001/003/005. The bounded service now admits evidenced openings, specific selection, original-issue customer returns, supplier returns, confirmed losses, correction normalization and complete evidenced economic-owner partitions while preserving return-time FIFO order, original consumption provenance and the separation between custody/location and ownership.
- [x] T085 [HIGH] Expand production commercial matching beyond one whole invoice and shipment per FR-002/003/007/010/011/017 and SC-001/003/004/005. Separate immutable match revisions now cover split/partial billing and fulfilment, signed sales credits/returns, direct-service and shipping-only scope, free goods, evidenced kit/production inputs, exact conservation, rematching/history and explicit unresolved WIP without weakening legacy whole-line reviews or storing derived margin authority.
- [x] T086 [HIGH] Implement the separate acquisition-to-carrying-value bridge per FR-001/009/015/016/019 and SC-001/003. Source-backed owner-confirmed assessment revisions now derive a separate current or historical carrying value with exact scope, recovery ceiling, cutoff, evidence trace and tenant boundary. Acquisition cost and commercial DB1/DB2 remain unchanged; no statutory posting or compliance certification is claimed.
- [x] T087 [HIGH] Complete evidence-backed allocation and conversion boundaries per FR-002/003/013/020/021/022 and SC-001/003. Owner-confirmed weighted acquisition/selling allocations now use deterministic signed largest remainders, explicit residuals and stable target IDs. Immutable source-backed conversion revisions preserve original shares while currency observations derive at read time; unit authority is kept distinct. Tax buckets, reductions and skonto boundaries remain explicit and no payment difference or current rate is inferred.
- [x] T088 [HIGH] Connect operational cost explanations and display semantics per FR-001/011/014/016/022/023/024 and SC-003. The shared Warehouse, Orders, Finance and Analysis surfaces now expose retained values, independent gaps/freshness, locale-formatted display values, exact precision and Inspector links without browser-side business rules. The separate SC-002 moderated qualification remains explicitly deferred in T280 and is not claimed by this implementation checkbox.
- [ ] T089 [HIGH] Qualify the real integrated product on fixture J per FR-018, SC-006 and plan: reference-host release gate (partial). Extend the existing benchmark harness to actual order, inventory page/totals, grouped report, exception page/count and serialized chat/MCP entrypoints after their implementation. Evidence: exploratory benchmark generations and bounded service regressions do not establish the required integrated reference-host budgets. Retain cold/warm p95, tenant isolation, resource envelope, complete reconstruction and affected-receipt refresh measurements; enforce the stated 500 ms/2 s/3 s read, 120 s reconstruction and 30 s refresh budgets without quietly reducing the workload.
- [ ] T090 [MEDIUM] Close shared verification and release evidence per Constitution V, SC-001/003/004/005 and the existing T049/T050/T056/T060/T065/T071/T077 gates (partial). Recheck the actual global-lint findings rather than assuming the recorded 13 still apply, coordinate any unrelated changes, and run required full backend/frontend/migration/catalog/spec gates after the remaining implementation. Update truthful feature status and evidence only after passing; keep reviewer-owned markers and deployment/merge authority separate. Evidence: each delivered slice has recorded regression proof but its shared completion checkbox remains open; the full feature must not be inferred complete from single-line DB1/DB2 tests.

T090 local closeout note (2026-09-20): Spec policy, global Ruff, Web formatting/i18n/328 tests/production build, Docs generation/73 tests/production build, whitespace, the 16-test focused 234 closeout, selling migration boundary and worker retry atomicity pass. The complete backend run reached 3,793 passed and 9 skipped but remains red on seven reproducible tests owned by concurrent non-234 document-correction, Storyline and credit-verification changes. Generated catalog output is current but necessarily differs from HEAD in this uncommitted feature worktree. Keep T090 open until those shared-suite failures are coordinated and the complete suite is rerun green.

## Phase 19: Integrated fixture J qualification (T089 refinement)

- [x] T281 [T089] Add fail-closed contract tests for the full-profile/reference-host manifest, all five integrated read workloads, cold/warm samples, tenant isolation, reconstruction equality, affected-receipt refresh, resource evidence and unchanged fixture-J cardinalities.
- [x] T282 [T089] Implement a reusable product qualification evaluator in the existing large-tenant benchmark package. It may certify only complete evidence produced by real application entrypoints and must return every refusal reason for incomplete or reduced evidence.
- [x] T283 [T089] Add the executable product harness adapters for shared cost-query/order, bounded inventory page plus totals, grouped graph report, exception page plus count and serialized MCP/tool reads. Reads use application services and do not write, enqueue or fall back to the costing-spike relations.
- [x] T284 [T089] Add reconstruction/refresh orchestration and reference-envelope capture for the production company-generation path. `product_runner.py` preserves the full 20+200/30-change defaults, captures cold/warm product reads and SQL evidence, runs five readers beside one refresh worker, executes three retained manifests through production generation build/retry/CAS-publication/report services, and captures resources and control-tenant probes. The focused suite passes 9/9; T285 remains deferred and unclaimed.
- [ ] T285 [T089] **DEFERRED — NON-BLOCKING FOR PROVISIONAL TECHNICAL CLOSEOUT.** Run the unchanged full fixture J on the dedicated 4-vCPU/16-GiB reference host and retain the signed/versioned result when that environment is available. Until then, make no reference-host performance claim and keep this qualification visibly open.
- [x] T286 Record the owner's 2026-09-20 decision that unavailable external participants and dedicated reference hardware do not block provisional technical closeout; retain T280/T285 as explicit later qualifications and do not mark their claims as passed.

### Dependency and handoff notes

T078 is the next independently useful implementation slice: it exposes existing
retained evidence without needing a new valuation policy, grouped margin or schema.
T079 establishes the common context before T080; T081 and T082 consume T080's same
basis. T084/T085/T087 expand admitted input coverage and must integrate with that context
before claiming full fixture coverage. T086 owns the separate carrying-value branch.
T088 can begin with supported detail after T078, but grouped/full-business acceptance
requires T079–T087. T083's complete return case depends on T084/T085 and all demo writes
must follow the reviewed initialization contract. T089 qualifies the resulting product;
T090 closes the required shared verification gates. No dependency is permission to
activate a company's accounting policy or to implement an unreviewed schema.

Convergence outcome: tasks_appended (13 tasks, T078–T090). Before each implementation
slice, refine its exact acceptance tests and schema if needed, perform the required
spec/plan/tasks consistency analysis, then use speckit-implement. A repeated convergence
assessment should inspect these existing tasks and avoid appending duplicate work.

Gap-type tally correction: five findings are missing (T080/T081/T082/T083/T086)
and eight are partial; the twelve-HIGH/one-MEDIUM severity tally is unchanged.

## Record-inspection implementation detail for T078

- [x] T091 [FR-016/023/027] Specify and analyze contracts/record-inspection.md; retain existing reviewer checklist ownership.
- [x] T092 Write failing tenant/bridge/precision/pagination/no-write/shared-adapter tests in packages/reality-core/tests/test_cost_records.py.
- [x] T093 Implement fixed typed read scope and shared retained-record service in domain/cost_records.py, services/cost_records.py and services/costing.py.
- [x] T094 Wire cost.record.get, MCP, CLI and existing web Inspector/register with paging and bilingual labels; update catalogs and generated docs.
- [ ] T095 Run backend/frontend/catalog/spec gates and final review; document delivery and remaining gates before closing T078.

T091 -> T092 -> T093 -> T094 -> T095. No new schema or company policy is introduced.


T095/T078 verification evidence: 142 affected backend tests; full backend 3,212 passed,
9 skipped and one existing warning; 314 frontend tests; 73 docs tests; production web
build; scoped lint/format; generated-reference idempotence and working-tree spec policy.
The isolated PostgreSQL container was removed. Implementation and final review are
documented in verification-results.md. Global Ruff retains 13 unrelated feature235
findings, so these shared completion markers remain open. T091–T094 are delivered.


## Shared retained query context for T079

- [x] T096 [FR-004/007/011/012/014/015/016] Review/analyze contracts/query-context.md against approved requirements; no new schema.
- [x] T097 Write failing domain/service/history/tenant/no-write/tool/CLI tests in tests/test_cost_query.py.
- [x] T098 Implement domain/cost_query.py, services/cost_query.py and the shared cost_query entrypoint, preserving existing review digests and response shapes.
- [x] T099 Add cost.query.get, MCP cost_query_get, CLI cost-query and the thin HTTP GET adapter; update catalogs, generated references and durable contract.
- [x] T100 Verify affected/full backend, catalog/docs/spec/lint and review the completed scope; retain open shared gates if red.

T096 -> T097 -> T098 -> T099 -> T100. Generalized generation/profile authority is not
introduced; T079's reusable retained-scope context does not close T080/T081.


T096–T099 delivery evidence: the shared retained query envelope is implemented across
service/tool/MCP/HTTP/CLI without a schema change. Final focused current-checkout
verification passes 125 tests; Web 314 plus ten final catalog checks; docs 73; scoped
lint/format and generated-reference idempotence pass. The complete collected baseline
ran in disjoint partitions: 3,219 passed, nine skipped, one transient spec-coverage failure
from concurrent feature239 work. Spec policy passes on recheck. See verification-results.md
and context-test-partitions.json. T100/T079 remain open because the checkout changed
during full verification and the final global Ruff snapshot retains 17 unrelated findings.
Owned test infrastructure was removed; reviewer-owned checklist markers remain unchanged.


### Production publication guard: T080 domain stage

- [x] T101 [FR-007/012/014/018] Specify/review/analyze contracts/generation-publication.md; no schema or activation.
- [x] T102 [FR-007/012/014/018] Add tests/test_cost_generation.py before implementing domain/cost_generation.py; prove publication refusal and late-evidence semantics.
- [x] T103 [FR-007/012/014/018] Verify domain regressions, spec policy and scoped lint; review authority boundaries and record evidence.

T101 -> T102 -> T103. This is the first domain stage of T080. Transactional storage,
retained input capture, shared worker registration, canonical SQL rows, bounded reads
and real publication-race tests remain required before T080 is complete.

Publication domain stage verified: 243 focused domain/service/spec regressions pass;
scoped Ruff/format and diff checks pass. Evidence: publication-regression.txt and
publication-scoped-lint.txt. The global Ruff run retains 16 unrelated desktop/search
findings. T080 remains open; no production publication or grouped report is claimed.


### Stored inventory generation integration (bounded T080 continuation)

- [x] T104 [FR-007/014/016/018/019] Review/specify/analyze contracts/inventory-publication.md and cache schema refinement before implementation.
- [x] T105 [FR-007/014/016/018/019] Write tests/test_inventory_generations.py and tests/test_inventory_generation_migration.py first for real stored replay, isolation, rollback, concurrency, jobs and migration.
- [x] T106 [FR-007/014/016/018/019] Implement db/cost_generations.py, migration0069, services/inventory_generations.py and analytics/costing_relation.py; expose public costing.py maintenance/read services.
- [x] T107 [FR-007/014/018/019] Register jobs/handlers/costing.py in shared jobs/registry.py; preserve existing permission, claim and transaction boundaries.
- [x] T108 Verify migrations, concurrency, worker/costing regressions, catalogs/docs/spec and scoped/global gates; record limitations without closing T080.

T104 -> T105 -> T106 -> T107 -> T108. Multi-pool generation, contribution profile
authority, grouped reports, automatic invalidation scheduling and fixture-J remain open.


Stored integration evidence: final current-checkout focused verification **141 passed**;
Docs **73 passed**, Web **314 passed**, scoped lint/format and reference idempotence pass.
Original full backend result: **3,298 passed / 5 failed / 9 skipped**. Two cache-table
classification failures were fixed and covered by the final run; three demo timeout
cases passed alone. Concurrent shared-worker changes and 11 unrelated global lint
findings prevent claiming a clean full-checkout gate. T108 and T080 remain open.
See verification-results.md and evidence/storage-full-backend.txt. Owned test database
was removed; no company activation or deployment occurred.

### Bounded historical inventory selection

- [x] T109 [FR-007/014/016/018/019] Specify/review/analyze bounded historical selection; preserve per-review authority without schema expansion.
- [x] T110 [FR-007/014/016/018/019] Add tests/test_inventory_snapshot_selection.py first for real multi-item parity, two-query reads, non-disclosure, corruption and selection bounds.
- [x] T111 [FR-007/014/016/018/019] Implement shared costing.inventory_cost_snapshots and private joined reader; reuse checksum/context logic and classify tenant boundary.
- [x] T112 [FR-007/014/016/018/019] Verify affected regressions/catalog/spec/lint, record review and keep full T080/T081/release gates open.

T109 -> T110 -> T111 -> T112. This selection exposes independently pinned historical
rows; it does not establish common knowledge capture or additive report semantics.


Historical selection delivery: 89 integration tests and 287 final costing/history/
selection regressions pass; docs 73 passed; scoped lint/format, spec policy and reference
idempotence pass. Global lint still has 11 unrelated findings. Evidence is recorded in
verification-results.md and evidence/selection-*.txt. No full-checkout green claim;
T080/T081 and the previous shared verification gates remain open.

### Joint retained inventory confirmation

- [x] T113 [FR-007/014/015/016/018/019] Specify/review/analyze common action/event confirmation without new schema.
- [x] T114 [FR-007/014/015/016/018/019] Add tests/test_inventory_batch_review.py first for compatible scope, real owner/MCP confirmation, replay, stale/foreign refusal, shared context, bounds and atomic rollback.
- [x] T115 [FR-007/014/015/016/018/019] Implement typed batch request, bounded shared admission/execution and cost.change schema; expose actual review-action identity in stored contexts.
- [ ] T116 [FR-007/014/015/016/018/019] Verify affected regressions/catalog/docs/spec/lint and review authority/rollback; record remaining full release/reporting gates.

T113 -> T114 -> T115 -> T116. A confirmed selection is not a company-wide profile or
a single atomically published cache; T080/T081 remain open.


Joint confirmation evidence: 126 focused tests and 287 final costing/history/migration
regressions pass; docs 73 pass; generated references are idempotent, scoped lint/format
and spec policy pass. Global lint retains 11 unrelated findings. T116 and existing
T080/T081/release gates remain open; no common cache/report completion is claimed.
See verification-results.md and evidence/batch-*.txt. No new schema or company activation.

### Complete joint inventory publication

- [x] T117 [FR-007/012/013/014/016/018/019] Specify/review/analyze all-member readiness and pinned totals without new schema.
- [x] T118 [FR-007/012/013/014/016/018/019] Write tests/test_inventory_batch_generations.py first for completeness, sums/units, tenant/corruption refusal, bounded reads, atomicity/concurrency and actual worker execution.
- [x] T119 [FR-007/012/013/014/016/018/019] Implement private joint builder/reader and public costing services; extend existing job config and tenant classification.
- [ ] T120 [FR-007/012/013/014/016/018/019] Verify affected costing/worker/catalog/docs/spec/lint and record remaining full-report/release gates.

T117 -> T118 -> T119 -> T120. Immutable action membership and complete exact member
publications establish selected-scope readiness; no company-wide generation is implied.


Joint publication evidence: 176 final regression tests pass, including real concurrency,
worker execution, complete/zero/partial values, immutable membership and disappearing-cache
rollback; docs 73 pass. Scoped lint/format, spec policy and generated-reference idempotence
pass. Global lint has 12 unrelated findings; T120 and prior release gates remain open.
See verification-results.md and evidence/joint-*.txt. This delivers a complete selected
inventory observation, not a company-wide or contribution report generation.

### Canonical SQL inventory relation

- [x] T121 [FR-007/012/013/016/018/019] Specify/review/analyze the typed generation-pinned relation and unimplemented graph execution boundary.
- [x] T122 [FR-007/012/013/016/018/019] Write tests/test_inventory_costing_relation.py first for actual SQL/service parity, numeric/partition semantics, isolation, stable history and invalid input.
- [x] T123 [FR-007/012/013/016/018/019] Implement the shared SQL source and canonical selectable in analytics/costing_relation.py; make the existing selection reader consume it without response changes.
- [ ] T124 [FR-007/012/013/016/018/019] Verify relation/selection/cache regressions and catalog/docs/spec/lint; retain grouped-report and shared release gates.

T121 -> T122 -> T123 -> T124. This is a SQL integration prerequisite, not a completed
graph.ask or Analysis Builder feature.


Canonical SQL source evidence: 116 integration tests and 58 final relation/selection/
reporting-coverage/spec regressions pass; docs 73 pass. Scoped lint/format passes;
global lint retains 12 unrelated findings. T124 and previous release gates remain open.
See verification-results.md and evidence/relation-*.txt. This is a shared production SQL
source; graph.ask/Analysis Builder cost-context integration is still required.

### Historical inventory graph execution

- [x] T125 [FR-007/012/013/014/016/018/019] Review/specify/analyze typed historical graph context and protected aggregation without schema expansion.
- [x] T126 [FR-007/012/013/014/016/018/019] Write tests/test_inventory_graph_reporting.py first for graph/tool/saved-report parity, refusals, bounded reads and concurrent cache protection.
- [x] T127 [FR-007/012/013/014/016/018/019] Implement domain context, protected shared read, canonical compiler binding, bilingual graph declaration and tool metadata; refuse lossy text formatting.
- [ ] T128 [FR-007/012/013/014/016/018/019] Verify affected inventory/reporting/docs/catalog/spec gates and record remaining UI, DB and full-release work.

T125 -> T126 -> T127 -> T128. JSON graph/saved-report scope only; T081's visual
context selector, contribution reporting and complete release verification remain open.

Historical graph delivery: 95 final report/tool/HTTP/saved-query tests and 19 existing
position-history regressions pass; docs 73 and web contracts 40 pass. The preceding
296-test integration run had 295 passes and one catalog-probe assumption corrected and
verified in the final run. Scoped lint/spec pass; 14 unrelated global import findings
keep T128 and broader release gates open. See verification-results.md and report-*.txt.

### Historical inventory selector

- [x] T129 [FR-012/013/014/016/019] Review/specify/analyze shared confirmation discovery and lossless visual selection; no schema expansion.
- [x] T130 [FR-012/013/014/016/019] Add tests/test_inventory_review_options.py and frontend plan/state tests first for pagination/tenancy and preserved context with stale-response suppression.
- [x] T131 [FR-012/013/014/016/019] Implement shared discovery, graph tool/API/catalog registration, typed frontend context and localized selector/result basis in the existing Analysis Builder.
- [ ] T132 [FR-012/013/014/016/019] Verify database/UI/build/i18n/docs/spec gates and record remaining contribution/current/scale/full-release work.

T129 -> T130 -> T131 -> T132. No financial confirmation, cache refresh or company activation
is performed by this read-only selector.

Historical selector delivery: 305 affected backend regressions pass; 64 final backend
checks pass after the base-unit declaration fix. Web contracts 317, final focused state
tests 34, docs 73 and documentation-reference tests 8 pass; real Chromium acceptance
and frontend build pass. All analysis translations pass in four languages. T132 remains
open because global import and unrelated CompanySetupForm localization gates are red.
See verification-results.md and evidence/selector-*.txt.


### Coverage-preserving contribution SQL arithmetic

- [x] T133 [FR-011/012/014/022] Specify/review/analyze the internal SQL arithmetic contract and explicit admission boundary.
- [x] T134 [FR-011/012/014/022] Add tests/test_contribution_aggregates.py first for PostgreSQL/domain parity, incomplete groups and exact half-even ratios.
- [x] T135 [FR-011/012/014/022] Share fixed domain terms and implement analytics/contribution_aggregates.py without storage or public measure registration.
- [ ] T136 [FR-011/012/014/022] Verify arithmetic/domain/reporting regressions, lint/spec and record remaining publication/report/release gates.

T133 -> T134 -> T135 -> T136. Internal arithmetic only; a successful aggregate does
not establish source admission, compatible context, unique grain or complete caches.

Contribution arithmetic evidence: 50 focused tests and 171 broader contribution,
selling-cost, query/report and tenant-isolation regressions pass. The 256 state
combinations execute in PostgreSQL and match the Decimal domain kernel. Scoped
lint/format, spec policy and diff checks pass. T136 remains open because global lint
still has 14 unrelated import findings. No public contribution report is enabled.
See verification-results.md and evidence/aggregate-*.txt.


### Joint contribution confirmation

- [x] T137 [FR-007/011/012/014/015/016/019] Specify/review/analyze common confirmed contribution membership using existing authority records.
- [x] T138 [FR-007/011/012/014/015/016/019] Write tests/test_contribution_batch_review.py first for shared basis, atomicity, tenant/owner/stale refusal and replay.
- [x] T139 [FR-007/011/012/014/015/016/019] Implement typed batch scope, shared contribution validation/execution and existing cost.change schema dispatch; regenerate public references.
- [ ] T140 [FR-007/011/012/014/015/016/019] Verify contribution/inventory/cost tools, tenant/catalog/docs/spec/lint and record outstanding report/release gates.

T137 -> T138 -> T139 -> T140. Confirmation creates retained input authority only;
it neither materializes nor claims a usable grouped-report generation.

Joint contribution evidence: 31 initial confirmation regressions and 180 final affected
cost/service/tool/catalog/tenant/spec tests pass, including all new cross-member guards.
Docs 73 and reference tests 8 pass; generated references reproduce byte-identically.
Scoped lint/format, spec policy and diff checks pass. T140 remains open because global
lint retains 14 unrelated import findings; T080/T081 and overall release remain open.
See verification-results.md and evidence/contribution-batch-*.txt.


### Stored joint contribution observations

- [x] T141 [FR-007/011/012/014/016/018/019/022] Specify/review/analyze the two-table historical observation contract and exact action membership.
- [x] T142 [FR-007/011/012/014/016/018/019/022] Add tests/test_contribution_generations.py and tests/test_contribution_generation_migration.py first for real cache/worker/concurrency/rollback and SQL parity.
- [x] T143 [FR-007/011/012/014/016/018/019/022] Implement scoped cache schema/static migration, shared builder/reader/canonical SQL, shared job and catalog/documentation integration.
- [ ] T144 [FR-007/011/012/014/016/018/019/022] Verify affected costing/reporting/worker/migration/tenant/docs/spec/lint and preserve broader graph/scale/release gates.

T141 -> T142 -> T143 -> T144. Historical selected-scope observation only; no automatic
financial confirmation, current/full-company result or DB graph/UI exposure.

Stored contribution evidence: 13 initial cache/migration/registry proofs pass; the broad
run has 208 passes and two opt-in container skips, with one old catalog-count expectation
corrected from 511 to 513. All 74 final catalog/tenant/coverage/spec checks pass. Two
strengthened authorization/scope guards and the real 100+14 selling-cost fixture also
pass. Docs 73 and reference tests 8 pass; generated references reproduce unchanged.
Scoped lint/format, spec and diff checks pass. T144 remains open because global lint
still has 14 unrelated import findings and container/reference release qualification
remains outstanding. See verification-results.md and evidence/contribution-cache-*.txt.

### Historical contribution graph execution

- [x] T145 [FR-012/014/022] Specify/review/analyze fixed contribution measure sources and exact historical graph context.
- [x] T146 [FR-012/014/022] Add contribution graph regression tests before implementation.
- [x] T147 [FR-012/014/022] Integrate protected canonical contribution relation, fixed aggregate measures and saved/HTTP graph execution.
- [ ] T148 [FR-012/014/022] Verify affected graph/costing/catalog/docs gates and record remaining UI/release qualification.

T145 -> T146 -> T147 -> T148. No implicit selection, refresh or financial approval.

- [x] T149 [FR-012/014/022] Integrate and verify contribution metadata discovery and the existing analysis selector, saved context, historical references and financial coverage labels.

Historical contribution delivery: 85 final affected backend checks, 319 frontend tests,
35 focused editor contracts, 73 docs and eight reference tests pass. Real contribution
and inventory browser acceptance and frontend build pass; all 174 analytics strings
are translated. T148 remains open for known global lint/localization and broader
release qualification. See verification-results.md and contribution-graph/ui evidence.

### Selected contribution freshness

- [x] T150 [FR-007/014/018] Specify/review/analyze selected-cutoff current reads and the final cursor boundary.
- [x] T151 [FR-007/014/018] Add service/graph race, isolation, history and frontend mode tests first.
- [x] T152 [FR-007/014/018] Implement shared current snapshot/graph guards and explicit selector mode without financial writes.
- [ ] T153 [FR-007/014/018] Verify regression/browser/catalog/docs/spec gates and record outstanding company/scale/release work.

T150 -> T151 -> T152 -> T153. Current describes knowledge freshness of the selected
confirmed scope at its fixed cutoff, never complete company coverage or a new review.

Selected freshness delivery: 28 initial and 141 broader backend checks pass; the final
saved-report proof and both strengthened final-SQL race proofs pass. All 320 frontend
tests, both real-browser flows, production build, 73 docs tests and eight reference
tests pass. All 176 analysis strings have translations. T153 remains open for known
global lint/localization and full-release gates; company publication and fixture J
remain separate. See verification-results.md and contribution-current-* evidence.

### Exact company population closure

- [x] T154 [FR-007/012/014/018] Specify/review/analyze full-population membership independently of financial coverage.
- [x] T155 [FR-007/012/014/018] Write domain closure tests first for omitted/duplicate/stale/mixed-context rows and independent financial gaps.
- [x] T156 [FR-007/012/014/018] Implement typed internal company population closure without new schema or authority.
- [ ] T157 [FR-007/012/014/018] Verify domain/spec/lint and document required census/publication integration and outstanding release gates.

T154 -> T155 -> T156 -> T157. A pure closure proof is a builder prerequisite; it does
not establish that a supplied census includes every company subject. The future scoped
source/evidence census must prove that independently before any company-wide claim.

Population guard evidence: 24 initial and 155 final domain regressions pass, including
exact closure of 10,000 synthetic inventory items and 100,000 contribution lines. This
is an algorithmic census case, not fixture-J or service/SQL latency qualification. Owned
lint/format, spec policy and diff checks pass. T157 remains open for shared release
gates; global lint retains 14 unrelated import findings. No database or UI changed.

Next integration starts with the source-backed expected-population census and retained
manifest, not another arithmetic or selector extension. Prove movement knowledge from
recorded business-event membership (Movement has no universal recorded-at field), include
unreviewed/uninterpreted gaps, retain each subject's own policy/review revisions and
extend the single-policy publication interface before company worker integration.

### Current source-backed company census

- [x] T158 [FR-007/014/018] Specify/review/analyze current snapshot census and explicit evidence/temporal gaps.
- [x] T159 [FR-007/014/018] Write PostgreSQL census tests first for unreviewed subjects, scope/isolation/bounds and concurrent intake.
- [x] T160 [FR-007/014/018] Implement tenant-scoped builder census through shared costing service and register its boundary.
- [ ] T161 [FR-007/014/018] Verify affected tests/catalog/spec/lint and record retained-manifest/publication/scale gaps.

T158 -> T159 -> T160 -> T161. Census is current discovery, not a financial assessment.
No raw census fingerprint is accepted as a complete cost-input fingerprint.

Census evidence: 81 affected PostgreSQL, application-catalog, tenant-isolation and
population tests pass. Owned lint/format, spec policy and diff checks pass. T161 remains
open for shared release gates (global lint currently has 12 unrelated import findings).
Retained financial-input manifests, company publication and fixture J remain unimplemented.

### Manifest-bound company publication prerequisite

- [x] T162 [FR-007/012/014/018] Specify/review/analyze the company basis and exact population binding without fabricated policy identity.
- [x] T163 [FR-007/012/014/018] Add test-first company publication proofs in packages/reality-core/tests/test_company_cost_publication.py.
- [x] T164 [FR-007/012/014/018] Integrate company population closure into packages/reality-core/src/reality/domain/cost_generation.py while preserving selected publication guards.
- [ ] T165 [FR-007/012/014/018] Verify domain regression/spec/lint and document retained storage, service fencing and reference-scale gates.

T162 -> T163 -> T164 -> T165. This domain prerequisite does not deliver durable
company input retention, a worker or report. T080/T081/T089 remain open.

Company publication prerequisite evidence: 92 initial and 185 final domain tests pass.
Owned lint/format, spec policy and diff checks pass. T165 remains open for shared release
gates; 12 unrelated global import findings remain. No company manifest was persisted or
published; historical input resolution, storage, service fencing and fixture J remain open.

### Retained census schema proposal

- [x] T166 [FR-007/014/018/019] Prepare the concrete typed current-census storage proposal, alternatives, retention/transaction boundaries and test matrix in contracts/company-census-retention.md.
- [x] T167 [FR-007/014/018/019] Record owner approval of the five-table proposal; finish schema/domain analysis before implementation. This is not automatic approval from the earlier financial-manifest model.
- [x] T168 [FR-007/014/018/019] After T167, write migration/service/serialization/concurrency/isolation tests first, then implement typed immutable census storage, shared capture/read services and catalogs per the approved contract.
- [ ] T169 [FR-007/014/018/019] Verify migration/replay/rollback/corruption/tenant regression, generated references, spec/lint and final contract review; preserve financial-resolver/publication/scale release gates.

T166 -> T167 -> T168 -> T169. No new table or migration is implemented by T166.

T167 approval: owner explicitly answered yes to the five-table proposal on 2026-09-19.

T168 delivery: migration 0071 and typed immutable current-census storage implemented.
122 broader backend checks, 41 correction/migration/serialization checks, 18 final storage
guards, 73 docs checks and eight reference checks pass (overlapping suites, not additive).
Generated references are reproducible. Owned lint/format and spec checks pass; T169 remains
open for shared release gates, including 12 unrelated import findings. Financial input
resolution and company publication are not delivered by retained discovery alone.

Final scoped follow-up: all 29 discovery/storage tests pass after adding explicit refusal
of malformed legacy document-parent links. Owned verification resources were removed.

### Bounded retained-census review resolution

- [x] T170 [FR-007/012/014/019] Specify/review/analyze captured-time review selection, independent gaps and strict builder bounds.
- [x] T171 [FR-007/012/014/019] Add PostgreSQL tests first in packages/reality-core/tests/test_cost_census_resolution.py.
- [x] T172 [FR-007/012/014/019] Implement shared captured-review resolution and tenant catalog classification without new authority or arithmetic.
- [ ] T173 [FR-007/012/014/019] Verify affected storage/review/catalog/isolation regressions and document the remaining financial-manifest/publication/scale gates.

T170 -> T171 -> T172 -> T173. Existing approved financial reads are reused; no company
financial manifest or common historical knowledge boundary is established by this step.

Resolution evidence: 132 broader backend tests and all eleven final captured-context proofs
pass, plus 73 docs and eight reference checks. Owned lint/format, spec and whitespace checks
pass. T173 remains open for shared release gates (12 unrelated import findings); complete
financial manifests, company publication and reference-scale qualification remain open.
Owned PostgreSQL verification resources were removed.

### Confirmed contribution-only event relevance

- [x] T174 [FR-007/014/019] Specify/review/analyze the closed non-invalidating writer contract for retained-census resolution.
- [x] T175 [FR-007/014/019] Add test-first action/event/membership and normal stock-plus-DB proofs in packages/reality-core/tests/test_cost_review_relevance.py, reusing the existing captured-resolution fixtures.
- [x] T176 [FR-007/014/019] Implement bounded private relevance proof and integrate the captured resolver without changing other readers or financial approval.
- [ ] T177 [FR-007/014/019] Verify affected resolver/review/storage/isolation regressions, docs/spec/lint and record remaining common-manifest/scale/publication gates.

T174 -> T175 -> T176 -> T177. Contribution-only confirmation is a proved non-input
change, not permission to ignore all cost.reviewed events.

Relevance verification: all 17 targeted tests and 140 broader resolver/review/storage/
catalog/isolation tests pass (overlapping, not additive). All 73 documentation tests,
owned lint/format, spec policy and whitespace checks pass. T177 remains open for shared
release gates; the previously recorded unrelated lint findings are not addressed here.
The common financial manifest, company publication and scale qualification remain open.

### Common captured review basis

- [x] T178 [FR-007/012/014/019] Specify/review/analyze exact captured-basis assembly and independent coverage without inventing historical knowledge.
- [x] T179 [FR-007/012/014/019] Add test-first unit and PostgreSQL proofs in packages/reality-core/tests/test_cost_captured_basis.py.
- [x] T180 [FR-007/012/014/019] Implement domain/cost_captured_basis.py and integrate the existing captured resolver without schema, totals or publication.
- [x] T181 [FR-007/012/014/019] Verify affected regressions, docs, spec and scoped lint; record remaining retained-financial-manifest, publication and scale gates.

T178 -> T179 -> T180 -> T181. This is one common captured review vector, not a historical
financial manifest. Existing reviewer-owned checklist markers remain unchanged.

T178–T181 scoped verification: 164 affected backend tests pass, including all 24 final
captured-basis tests (overlapping counts), plus 73 documentation checks. Four owned
Python files pass lint/format; spec policy and whitespace checks pass. No generated
public vocabulary changed. Full-company retained financial manifests, publication,
reference-scale qualification and the existing shared release gates remain open.

### Proposed durable captured review selection

- [x] T182 [FR-007/012/014/019] Prepare the concrete three-table retention proposal, alternatives, version/lifecycle semantics and test matrix in contracts/captured-basis-retention.md; check spec/plan consistency.
- [x] T183 [FR-007/012/014/019] Obtain and record owner approval of the new captured-selection storage family before schema/runtime implementation.
- [x] T184 [FR-007/012/014/019] After T183, add tests first in test_cost_captured_basis_storage.py and test_cost_captured_basis_migration.py; implement domain versioning, typed storage/migration and shared retain/read/replay services per contract.
- [ ] T185 [FR-007/012/014/019] Verify migration/atomicity/concurrency/retention/replay/isolation and existing financial regressions, catalogs/generated references, spec/lint; preserve company-publication and scale gates.

T182 -> T183 -> T184 -> T185. T182 changes documentation only; no three-table schema
approval is inferred from the previous five-table census approval.

T183 approval: the owner explicitly answered yes to the concrete three-table proposal
on 2026-09-19. T184 implementation is authorized; live migrations and release are excluded.

T184 delivery: migration 0072 and the three approved typed retention tables are implemented
with shared retain/metadata/replay services. Version 2 separates lifecycle flags; v1 export
verification remains explicit. 189 broader backend tests, 27 final storage/migration tests,
69 generation/finance regressions, 73 docs tests and eight reference tests pass (overlapping
suites, not additive). Generated references reproduce byte-identically. Scoped lint, spec
and whitespace pass. T185 remains open for shared release gates: 14 unrelated import
findings persist. Company context/publication and reference-scale qualification remain open.

### Bounded captured known-subtotal summary

- [x] T186 [FR-007/011/012/014/019] Specify/review/analyze known-subtotal semantics, partitioning and explicit company-publication limits.
- [x] T187 [FR-007/011/012/014/019] Add test-first coverage in packages/reality-core/tests/test_cost_captured_summary.py.
- [x] T188 [FR-007/011/012/014/019] Implement the private summary and shared costing entrypoint using canonical replay and existing SQL contribution aggregates.
- [x] T189 [FR-007/011/012/014/019] Verify summary/replay/aggregate/reporting/isolation regressions, catalogs/docs/spec/lint and record remaining full-company release work.

T186 -> T187 -> T188 -> T189. This internal known-subtotal summary is not a second
report engine or a published company valuation.

T186–T189 scoped verification: 179 affected PostgreSQL/backend tests pass, including
nine new summary tests. Documentation checks pass (73 docs tests and eight reference
tests); all 15 generated references reproduce byte-identically. Four owned Python files
pass lint/format, and specification/whitespace checks pass. The package-wide src/tests
lint check still reports 12 unrelated import findings; T185 and the overall release gate
remain open. No full-company admission/publication or reference-scale qualification is
claimed by this bounded internal summary.

### Captured report publication: concrete model amendment

- [x] T190 [FR-007/012/014/018/019] Prepare and review contracts/captured-report-publication.md against existing retained selection, generic cache and publication contracts; document exact model amendment, alternatives, limits and tests. Documentation only.
- [x] T191 [FR-007/012/014/018/019] Obtain owner acceptance of the captured-report semantics and four-table generic cache slice referencing captured basis instead of a historical financial manifest.
- [x] T192 [FR-007/012/014/018/019] After T191, specify final schema/guards, analyze and add failing domain/storage tests before implementing the captured report generation and publication tables.
- [x] T193 [FR-007/012/014/018/019] Add service/concurrency/read-isolation tests first; implement build, CAS publication and fixed-generation bounded reads under the approved contract.
- [x] T194 [FR-012/014/016/018/019/023] Add test-first fixed `captured_cost_context` coverage for graph/tool/HTTP and saved analyses; integrate typed captured inventory/contribution relations through the existing compiler and aggregate definitions; verify unknown coverage, partitions, fixed-generation retention, tenant/refusal/no-replay behavior and historical compatibility; run scoped catalogs/docs/spec/lint gates while retaining explicit company-scale and financial-admission release gates.

T190 -> T191 -> T192 -> T193 -> T194. The first report remains a bounded captured
selection with known subtotals, not final company totals. T079–T081 remain open until
their broader requirements and actual adapter/runtime proofs are satisfied.

T194 delivered: the fixed captured generation runs through the existing graph compiler,
graph tool and HTTP adapter, persists unchanged in saved analyses and round-trips through
the web question model. Typed inventory/contribution relations reuse canonical aggregates;
unknown members, coverage and tenant refusal remain explicit, while historical contexts
retain their semantics. The scoped regression passes 113 backend tests, 30 GraphSteps
tests, the production web build, eight generated-reference tests, docs generation, spec
policy, scoped lint/format and whitespace checks. Company-scale, worker and financial-
admission release gates remain open.

### Captured report discovery and Analysis selector

- [x] T195 [FR-012/014/016/019/023/024] Add failing tenant/bounds/cursor/no-replay tests for sealed captured-generation discovery through the shared graph tool and HTTP adapter; implement bounded metadata discovery without resolving amounts or granting financial approval.
- [x] T196 [FR-014/016/023/024] Add frontend contract tests and connect the Analysis selector/result explanation to `captured_cost_context`, preserving historical selectors and the exact saved generation identity.
- [x] T197 [FR-012/014/016/019/023/024] Verify captured/historical graph, tool, HTTP, MCP/catalog, frontend, docs, spec and scoped lint gates; update truthful limitations without closing worker, scale or financial-admission gates.

T195 -> T196 -> T197. Discovery lists only sealed generation metadata and counts; graph
execution still verifies cached content. Selection never follows a mutable latest pointer,
never exposes foreign cursor existence and never labels the captured diagnostic as a
complete company valuation.

### Bounded captured-report worker build

- [x] T198 [FR-007/014/018/019] Specify and test an owner-authorized `costing.captured_report.refresh` job for one sealed retained basis, including strict configuration, tenant/actor refusal, retry reuse and safe result references.
- [x] T199 [FR-007/014/018/019] Register the database-only handler and execute it under the builder's required REPEATABLE READ isolation, calling the shared captured-report service without publication or financial approval.
- [x] T200 [FR-007/014/018/019] Verify worker/registry/captured-report regressions, catalogs/docs/spec/lint and record that CAS publication, larger populations, chunk closure and fixture-J qualification remain open.

T198 -> T199 -> T200. This worker builds only the disposable cache for an already sealed
captured basis. It does not retain a new census/basis, follow a latest pointer, publish the
generation or relax the ten-subject bound.

T198–T200 delivered: the strict owner-authorized job revalidates one sealed retained basis,
runs its shared builder under REPEATABLE READ and returns one opaque generation reference.
Retry reuses the same verified cache and no publication row is created. Two new worker
cases and the 37-test captured-report/registry/worker/recovery regression pass. CAS
publication, census/basis orchestration, larger-company chunk closure and fixture J remain
open.

### Bounded captured-report publication worker

- [x] T201 [FR-007/014/018/019] Add strict owner/tenant/CAS/retry tests for a separate `costing.captured_report.publish` job accepting one sealed `generation_id` and explicit nullable `expected_previous_id`.
- [x] T202 [FR-007/014/018/019] Register the READ COMMITTED publication handler over the shared CAS service, returning only pointer-change counts and an opaque generation reference.
- [x] T203 [FR-007/014/018/019] Verify publication concurrency/rollback, registry/worker, docs/spec/lint and preserve larger-population, orchestration, fixture-J and financial-admission gates.

T201 -> T202 -> T203. The job never builds, selects latest, accepts amounts or upgrades
the captured diagnostic into financial company publication.

T201–T203 delivered: the separate owner-authorized job revalidates one sealed generation
and delegates to the tenant-serialized CAS service at READ COMMITTED. First publication,
same-generation retry, stale expected pointer, strict input and foreign-tenant behavior are
covered. Four new job cases and the 39-test captured-report/registry/worker/recovery suite
pass. The pointer remains diagnostic-only; broader orchestration and scale gates stay open.

### Shared cost findings

- [x] T204 [FR-014/015/018/025] Add failing derivation tests for missing acquisition cost, unassigned component, stale review and supported negative actual DB1, including unsold subjects, stable identity, clearing, incomplete-scope refusal, pending preservation and tenant isolation.
- [x] T205 [FR-014/015/025] Implement one tenant-scoped cost-finding provider over retained authority and verified published observations; reuse shared costing services/selectables and keep generation identity in basis metadata rather than finding identity.
- [x] T206 [FR-018/025] Register four contiguous operational exception classes and integrate their rows with the existing projection-backed page/count/register/explanation contract, exposing compatible cost-basis freshness without read-time reconstruction.
- [x] T207 [FR-014/015/018/025] Verify new and legacy exception derivations, projection refresh, bounded page/count, catalogs/generated docs, tenant isolation, spec and scoped lint; keep fixture-J p95/reconstruction/refresh qualification in T089.

T204 -> T205 -> T206 -> T207. No schema, financial approval, second exception queue or
browser-side business rule is introduced. T082 closes only when all four classes share the
same projection snapshot and clearing/freshness contract; T089 remains the scale release
gate. T204 may establish failing acceptance proofs now; T205/T206 remain blocked until T080
delivers the exact financially admissible company generation. Diagnostic captured reports
and independent per-review publications are not substitutes for that prerequisite.

T204 delivered: eight focused acceptance tests define the internal derivation seam and
cover unsold acquisition gaps, unassigned components, stale-review identity, supported
negative DB1 with independently incomplete DB2, incomplete-DB1 refusal, evaluated clearing,
pending preservation and foreign-tenant filtering. The red run fails only because
`_derive_cost_findings` is intentionally absent. No class registration or production read
path was activated at that checkpoint; T205/T206 remained blocked until T080 closed.

T205 delivered: one tenant-scoped provider consumes only the verified published company
generation, its canonical inventory/contribution selectables and component membership from
the retained inventory manifests. It emits missing acquisition cost, unassigned component,
stale review and supported negative actual DB1 routing facts without replaying FIFO or DB
arithmetic. Finding identity remains class plus business subject; generation, manifest,
review and component references remain causal basis metadata. Pending publication preserves
the supplied previous findings as stale. Ten focused provider/derivation tests and the final
68-test catalog/spec gate pass; the tenant catalog now classifies 537 operations. T206 still
owns class registration and projection-backed queue activation.

T206 delivered: the four classes occupy contiguous ranks 35–38 after the legacy catalog,
share the closed cause vocabulary and central English/German resource labels, and are
materialized only through the existing exceptions projection refresh. Page, class count,
register and stored cost-detail reads consume that same snapshot and expose its verified
cost-basis metadata. A pending company generation reuses the prior cost rows with explicit
stale basis instead of clearing them. The projection version is advanced to force safe
reconstruction; no read triggers the provider or a rebuild. The combined legacy/new
exception and projection regression passes 335 tests, and generated reference tests pass.
T207 remains the final bounded-read/catalog/spec/lint verification gate.

### Financial company generation approval gate

- [x] T208 [FR-007/012/014/018/019] Obtain explicit owner approval for the concrete seven-table financial company manifest/generation/publication boundary in `contracts/company-generation-publication.md` before adding migration, runtime services or implementation tasks.

T208 is a product/schema governance gate. Approval covers only retained typed company
inputs, reusable verified cache references, explicit unknown results and scope-keyed CAS
publication. It does not activate accounting policy, approve amounts, authorize carrying
value storage or close fixture-J and release gates.

T208 approved by the owner on 2026-09-19 in response to the concrete seven-table proposal.

### Financial company generation implementation

- [x] T209 [US6] [FR-007/012/014/018/019] Add failing PostgreSQL model/migration tests for the seven tenant-scoped tables, composite foreign keys, sealing immutability, exact header/source gap counts and canonical gap-digest constraints, unknown-result checks and downgrade protection in `packages/reality-core/tests/test_company_generations.py` and `packages/reality-core/tests/test_company_generation_migration.py`.
- [x] T210 [US6] [FR-007/012/014/019] Implement SQLAlchemy models and migration `0080_company_generations` in `packages/reality-core/src/reality/db/company_generations.py`, `packages/reality-core/src/reality/db/core.py` and `packages/reality-core/migrations/versions/0080_company_generations.py`; update executable data-model and resource catalogs, with callable tenant-isolation registration following the service entrypoints in T212.
- [x] T211 [US6] [FR-007/012/014/019] Add failing manifest admission tests for committed-cursor/knowledge capture, exact census population, per-subject fingerprints, explicit unknowns, exact unresolved header/source gap binding, idempotent retry, stale/foreign review refusal and rollback in `packages/reality-core/tests/test_company_generation_manifest.py`.
- [x] T212 [US6] [FR-007/012/014/019] Implement owner-authorized retained manifest admission over the existing census resolver and canonical review readers in `packages/reality-core/src/reality/services/company_generations.py` and expose only the shared internal entrypoint from `packages/reality-core/src/reality/services/costing.py`.
- [x] T213 [US6] [FR-007/012/014/018/019] Add failing generation/worker/CAS/read tests for deterministic chunks, explicit unknown completion, checksum corruption, lost-response retry, concurrent publication, pending preservation, one-generation pages/totals and no read-side enqueue in `packages/reality-core/tests/test_company_generation_jobs.py` and `packages/reality-core/tests/test_company_generation_reads.py`.
- [x] T214 [US6] [FR-007/012/014/018/019] Implement deterministic generation build/finalization, verified references to canonical per-review caches, scope-keyed CAS publication and fixed-generation relations/reads in `packages/reality-core/src/reality/services/company_generations.py`, `packages/reality-core/src/reality/services/analytics/costing_relation.py` and `packages/reality-core/src/reality/services/costing.py`.
- [x] T215 [US6] [FR-007/014/018/019] Register strict owner-authorized manifest/build/publish jobs through `packages/reality-core/src/reality/jobs/handlers/costing.py`, `packages/reality-core/src/reality/jobs/registry.py` and the existing runner isolation contract; return only counts and opaque references.
- [x] T216 [US6] [FR-012/014/018/025] Bind company-generation identity/freshness into the existing projection and cost-finding prerequisites without activating T204–T207 derivations in `packages/reality-core/src/reality/services/projections.py`, `packages/reality-core/src/reality/services/attention_reads.py` and `packages/reality-core/src/reality/services/analytics/costing_relation.py`.
- [x] T217 [US6] [FR-007/012/014/018/019] Verify migration parity/rollback, manifest/generation/publication concurrency, worker recovery, canonical read compatibility, catalogs/generated docs, spec policy and scoped lint; record that T204–T207 findings and T089 fixture-J qualification remain separate gates in `specs/242-inventory-cost-contribution/verification-results.md`.

T209 -> T210 -> T211 -> T212 -> T213 -> T214 -> T215 -> T216 -> T217. Tests precede
their implementation. No public mutation, automatic financial decision, carrying-value
schema, diagnostic-report promotion or fixture-J claim is included.

T209/T210 delivered: revision 0074 and matching SQLAlchemy metadata add the approved seven
tables with typed same-tenant links, exact gap bindings, explicit unknown shapes, sealed-row
guards and populated downgrade refusal. Five focused PostgreSQL cases, the 47-test
schema/catalog/index block, ten adjacent 0071–0073 migration cases and eight generated-doc
reference tests pass. Callable tenant-isolation registration remains correctly deferred to
the T212 service entrypoint.

T211/T212 delivered: the shared costing service now admits one owner-authorized, current
retained census under the tenant lock, captures a new financial knowledge time, persists
exact typed known/unknown members and canonical population/gap fingerprints, seals
atomically and reuses an identical sealed manifest before any latest-review resolution.
Fifteen manifest/census PostgreSQL tests and 58 application-catalog/spec-policy tests pass;
the public REPEATABLE READ census resolver contract remains unchanged.

T213/T214 delivered: deterministic manifest ranges reuse or build typed per-review
caches, record explicit unknown completion, verify cache and company checksums, seal only
after exact work closure, publish through a scope-keyed CAS pointer and expose fixed-
generation SELECT-only pages, totals, coverage and freshness. Company reads never follow
a mutable latest pointer or enqueue maintenance.

T215 delivered: the shared registry exposes strict `costing.company_manifest.admit`,
`costing.company_generation.build` and `costing.company_generation.publish` jobs. Each
worker invocation revalidates the active company owner and tenant-scoped sealed input,
the build honors the common deadline, and results contain only bounded counts and opaque
manifest/generation references.

T216 delivered: one protected, tenant-scoped prerequisite pins and verifies the newest
published company generation and reports `unavailable`, `ready` or `pending` with its
opaque generation/manifest identity and event cursors. Attention summary/register reads
carry that block beside existing projection freshness without activating any T204–T207
cost class, rebuilding data or clearing legacy findings.

T217 delivered: migration parity and downgrade protection, manifest/generation build and
publication races, worker retry/recovery, fixed canonical reads, generated references,
catalogs, spec policy and scoped lint all pass. The final PostgreSQL regression contains
116 passing tests; the catalog/data-model/spec-policy gate contains 63 passing tests and
the documentation reference gate contains eight passing tests. T204–T207 cost findings,
T089 fixture-J qualification and the six open reviewer-checklist items remain separate
release gates and are not closed by this implementation.

T195–T197 delivered: sealed captured generations have a bounded SELECT-only discovery
service and shared graph/MCP/HTTP read tool; tenant-scoped cursor refusal and no-replay
behavior are tested. Analysis can select one fixed generation for inventory or contribution,
clears an incompatible historical context and explains that the result is a captured known-
subtotal diagnostic rather than financial approval. Fifty-five backend/HTTP/catalog tests,
eight Analysis Builder tests, 30 GraphSteps tests and the production web build pass.

T191: explicit owner approval received on 2026-09-19 for the concrete amendment.

T192/T193 delivered: migration 0073, the four approved cache tables, captured publication
guard and internal build/publish/read/discard services. Fourteen new cases pass across
the 179-test regression and the additional one-test publication run; 58 existing
generation/reporting tests also pass (overlapping suites are not additive coverage).
73 docs tests, eight reference tests and all 15 generated-reference identity checks pass.
Eight owned Python files pass lint; seven pass format. The shared db/core.py has an
unrelated existing authentication-field format finding outside this import-only change.
The src/tests-wide check still reports 12 unrelated import findings. Spec/whitespace
checks pass. T194, general release gates, company-scale and historical financial
admission remain open. No public adapter, live migration or deployment was performed.

## Phase 6: Convergence

- [x] T218 [FR-004/007/011/012/014/015/016] Extend the shared requested/resolved cost-query context across retained single-scope reviews and the verified published company generation, with explicit generation/freshness identity and compatible policy/profile metadata without relabeling independent reviews as one company policy (partial).
- [x] T219 [FR-007/012/014/018] Replace the in-memory company report slice with generation-bound opaque cursors, SQL-bounded inventory/contribution pages and SQL counts/totals that preserve one verified generation and never scan all generation rows merely to return one page (partial).
- [x] T220 [FR-004/007/011/012/014/015/016/018] Verify the unified context and bounded company reads across history, pending/current state, cursor isolation, publication races, no-write/no-enqueue behavior, catalogs, generated docs, spec policy and scoped lint; reconcile T100/T108 and close T079/T080 only when this evidence is green (partial).

T218–T220 delivered: retained single-scope and financial company-generation reads now
share deterministic requested/resolved/freshness context semantics. Company context names
its authority as independent member reviews and never invents a company policy/profile.
Company inventory and contribution pages use generation/family-bound opaque cursors and
SQL `LIMIT`; counts, coverage and totals are calculated in SQL over the same fixed
generation rather than loading every row into Python. The final combined regression passes
112 tests, generated references pass eight tests, documentation regenerates successfully,
and scoped lint/format and whitespace checks pass. T100/T108 and their parent T079/T080
are reconciled as complete; fixture-J qualification remains T089.

## Phase 7: Convergence

- [x] T221 [FR-012/014/016/023/024] Specify and test an explicit fixed company-generation graph context for both inventory and contribution questions, reusing the verified financial generation without following a mutable publication pointer or inventing a common policy/profile (partial).
- [x] T222 [FR-013/014/024] Extend the canonical company inventory/contribution relations and compiler admission with exact dimensions, independent known/final coverage, weighted contribution rates, currency/unit partitions, fan-out refusal and non-additive inventory-time semantics (partial).
- [x] T223 [FR-023/024, SC-004] Propagate the fixed company-generation context and resolved basis through graph.ask, saved reports, HTTP/MCP and the existing Analysis Builder selector/result explanation without adding a second reporting engine or browser-side financial rules (partial).
- [x] T224 [T081] Verify partial and complete company totals, unknown members, current-versus-pending freshness, fixed historical stability, tenant isolation, no-write/no-replay behavior, legacy inventory/contribution/captured contexts, catalogs/generated docs, frontend contracts, spec policy and scoped lint; close T081 only when all evidence is green while retaining T089 (partial).

T221 -> T222 -> T223 -> T224. The graph context always names one opaque verified
generation. Reads never publish, rebuild, enqueue work or reinterpret independent member
reviews as one company accounting policy. Fixture-J latency and reconstruction remain T089.

T221–T224 delivered: Analysis can bind inventory and contribution questions to one opaque,
verified company generation. Canonical graph relations preserve exact currency/unit and
business dimensions, independent coverage, explicit unknowns, DB1 totals and weighted DB1
rates; DB2 remains unknown when its contributing population is incomplete. The shared
tool, HTTP/MCP surface, saved report and Analysis Builder round-trip the same fixed context
and explain its authority and ready/pending freshness without rebuilding or selecting a
newer publication. The final scoped backend regression passes 316 tests; 39 frontend
contract tests, both production builds, 73 documentation tests and eight generated-
reference tests pass. Generated references are reproducible, and scoped Ruff, format and
Prettier checks pass. This closes T081. Fixture-J qualification remains T089, and the ten
pre-existing untranslated captured-review/company-setup strings per non-English locale
remain outside this slice; every newly added company-generation string is translated.

## Phase 8: Convergence

- [x] T225 [T078] [FR-016/023/027] Classify every costing table added after the original retained-record contract as either inspectable retained evidence/decision context or explicitly non-authoritative generation/publication infrastructure; update `contracts/record-inspection.md` without widening arbitrary table access (partial).
- [x] T226 [T078] Add failing coverage, tenant/non-disclosure, shortest-link, exact-value, bounded-membership and no-write tests for newly inspectable captured basis, company census, manifest and fixed company-generation records in `packages/reality-core/tests/test_cost_records.py` (partial).
- [x] T227 [T078] Extend the fixed record vocabulary and shared Inspector service for the approved new retained families, reuse existing web/CLI/MCP adapters and centralized English/German labels, and keep disposable rows/publication pointers refused (partial).
- [ ] T228 [T095/T078] Run the affected backend/frontend/catalog/docs/spec/lint gates, record exact evidence and close T095/T078 only when green while retaining the broader feature and fixture-J gates (partial).

T225 -> T226 -> T227 -> T228. No schema, valuation calculation, publication action or
current-completeness claim is introduced. New support tables must be classified explicitly;
only retained records needed to explain a public opaque reference become inspectable.

T225–T227 delivered: the fixed Inspector vocabulary now includes retained company census,
captured-basis, company-manifest and fixed company-generation context plus their exact
member/input records. Shortest tenant-checked links connect those headers to their retained
evidence; existing web, CLI and MCP adapters need no parallel path. Disposable snapshot/
result rows and mutable publication pointers remain explicitly refused. T228 remains open
because the checkout-wide Ruff gate reports 400 pre-existing import-order findings outside
this slice; the three owned Python files pass Ruff and format.

## Phase 9: Convergence

- [x] T229 [T084] [FR-004/005/007] Specify the bounded production contract for evidenced specific identification in `contracts/inventory-service.md`: exact issue/loss/supplier-return layer selections retained in the confirmed action, stable entry/receipt identities, no automatic method choice and no schema expansion (partial).
- [x] T230 [T084] Add failing domain/service/history/tenant/replay tests for specific policy confirmation, exact selection conservation, unavailable/foreign/duplicate portions, frozen historical reads and unchanged FIFO behavior in `packages/reality-core/tests/test_inventory_costing_services.py` (partial).
- [x] T231 [T084] Extend the shared inventory request and service admission/replay path to execute confirmed specific selections through the existing kernel and retained review/action boundary; preserve existing tools/adapters and refuse unselected or excess portions atomically (partial).
- [x] T232 [T084] Verify inventory, costing, proposal/replay, catalog/spec and scoped lint gates; record that customer/supplier returns, loss admission, correction normalization, opening balances and consignment/transit ownership remain required before closing T084 (partial).

T229 -> T230 -> T231 -> T232. This slice adds no table, derived authority, silent policy
default or browser rule. The existing confirmed action is the retained authority for the
exact specific selections; the review keeps its existing shortest policy and movement links.

T229–T232 delivered: confirmed inventory scopes may now select `specific` and must retain
an exact issue/layer-entry/original-receipt/quantity allocation in the existing confirmed
action. The review digest binds those selections and historical reads revalidate/replay the
same input through the existing kernel. Migration 0075 only widens the existing policy
constraint from FIFO to the two reviewed methods and refuses downgrade while a retained
specific policy exists; it adds no table, column or relationship. The combined inventory
regression passes 197 tests, the final catalog/MCP/migration gate passes 45 tests, targeted
frontend contracts pass 36 tests, and docs/spec/scoped lint gates pass. T084 remains open
for return/loss admission, correction normalization, evidenced opening balances and
consignment/transit ownership.

## Phase 12: Convergence

- [x] T241 [T084] [FR-005/006/007/017, Constitution I/III] Obtain explicit owner approval for one tenant-scoped immutable `cost_opening_basis` authority linking the existing opening-stock Movement, economic-owner Party, evidence SourceRecord, source-stated total acquisition cost/currency, confirming event/action/reason and schema version; update `contracts/inventory-service.md` before schema work and do not fabricate a purchase receipt (missing).
- [x] T242 [T084] Add failing domain/service/migration/history/tenant tests for zero-cost versus unknown cost, multiple opening layers, FIFO/specific consumption, exact currency/unit/quantity, missing/foreign evidence, owner mismatch, correction replacement, frozen replay, hash tampering and populated downgrade refusal in `packages/reality-core/tests/test_inventory_costing_services.py` and `test_inventory_costing_migration.py` (missing).
- [x] T243 [T084] After T241 approval, add the approved SQLAlchemy model and migration `0083_inventory_opening_basis.py`, same-tenant composite links, immutable retained-value constraints, downgrade guard, data-model/Inspector vocabulary and English/German resource labels without changing the existing physical opening-stock action (missing).
- [x] T244 [T084] Extend the shared inventory request, admission, retained digest/replay and kernel mapping so explicitly evidenced opening-stock movements enter as opening receipt layers while unknown/unreviewed openings remain valuation gaps; preserve source-stated totals, owner scope, corrections, action confirmation and no-write reads (missing).
- [x] T245 [T084] Verify inventory, receipt-cost, Inspector, contribution, generation, tool/MCP, catalog, generated-doc, spec, migration and scoped lint gates; keep consignment/transit ownership open before closing T084 (partial).

T241 -> T242 -> T243 -> T244 -> T245. The proposed opening basis is retained evidence/
decision authority, not calculated inventory value. Its amount is recorded exactly as
stated by the selected source and confirmed by the owner; unit cost, remaining value and
consumption stay read-time observations. Unknown cost never becomes zero.

T241–T245 delivered: approved migration 0077 and `cost_opening_basis` retain one exact
source-backed total, currency and economic owner for an existing opening-stock movement,
without fabricating a receipt or storing derived inventory value. Confirmed requests bind
every opening, SourceRecord and owner into the historical review digest; FIFO and specific
consumption share the existing kernel, zero remains distinct from unknown, correction
replacement uses only the effective identity, and foreign/missing/tampered inputs refuse.
The Inspector exposes the retained authority with English/German labels and inventory reads
return its opaque basis and source references. The focused inventory/migration/Inspector
regression passes 106 tests, the final adjacent system regression passes 121 tests,
documentation generation is reproducible, and scoped Ruff, format, spec-policy and
whitespace checks pass. T084 remains open only for consignment/transit ownership.

## Phase 10: Convergence

- [x] T233 [T084] [FR-005/007/017] Specify bounded production admission for customer returns, supplier returns and confirmed loss in `contracts/inventory-service.md`: explicit movement classifications, original issue/layer/receipt return parts, exact supplier-return selections and no inference from settlement links alone (partial).
- [x] T234 [T084] Add failing service/migration/history tests for FIFO and specific customer returns, split/cumulative original-issue conservation, supplier returns, confirmed losses, incomplete/foreign/excess parts, unchanged earlier consumption and populated downgrade refusal in `packages/reality-core/tests/test_inventory_costing_services.py` and `test_inventory_costing_migration.py` (partial).
- [x] T235 [T084] Extend the shared inventory request, retained action replay, movement/member constraints and service calculation/read shapes for return/loss observations while preserving original issue provenance, return-time layer order, tenant scope and atomic refusal (partial).
- [x] T236 [T084] Verify inventory/contribution/generation/tool/catalog/docs/spec and scoped lint gates; keep correction normalization, evidenced opening balances and consignment/transit ownership open before closing T084 (partial).

T233 -> T234 -> T235 -> T236. Physical movement type and settlement links are evidence,
not cost allocation authority. The confirmed action retains exact cost portions; no return,
loss or supplier-return cost is inferred from location, document text or mutable state.

T233–T236 delivered: FIFO and specific reviews now admit explicitly classified customer
returns, exact supplier returns and confirmed outbound losses through the existing retained
action boundary. Customer return parts preserve original issue/layer/receipt provenance,
restore cost at return time and cannot cumulatively exceed the original sale; prior issue
observations remain unchanged. Migration 0076 widens only the existing movement/member
constraints and refuses downgrade when retained return/loss inputs exist. The final focused
inventory/migration regression passes 84 tests, the adjacent tool/catalog/contribution/
generation/spec regression passes 104 tests, generated documentation is reproducible, and
scoped Ruff plus whitespace checks pass. T084 remains open for correction normalization,
evidenced opening balances and consignment/transit ownership.

## Phase 11: Convergence

- [x] T237 [T084] [FR-005/007/017] Specify canonical inventory correction normalization in `contracts/inventory-service.md`: original plus compensation cancel, an optional replacement becomes the sole effective physical/economic input at its authored economic time, correction event identity and reason remain provenance, and no source-stated movement is rewritten (partial).
- [x] T238 [T084] Add failing service/history/tenant tests for correction without replacement, same-kind and changed-kind replacement, corrected receipt cost/ownership requirements, corrected issue/return allocation references, equal-time ordering, stale-current versus frozen historical reads, incomplete/foreign chains and action replay in `packages/reality-core/tests/test_inventory_costing_services.py` (missing).
- [x] T239 [T084] Implement one bounded tenant-scoped correction normalizer in `services/inventory_costing.py`, retain exact correction/event membership in the review digest, admit only the normalized effective movements into the existing kernel and preserve original/replacement provenance without adding calculated authority or duplicating core correction rules (missing).
- [x] T240 [T084] Verify inventory, receipt-cost, contribution, generation, tool, catalog, generated-doc, spec and scoped lint gates; record correction behavior and keep evidenced opening balances plus consignment/transit ownership open before closing T084 (partial).

T237 -> T238 -> T239 -> T240. Normalization consumes the existing append-only
MovementCorrection chain; it does not mutate movements, infer an economic replacement,
or treat the compensating physical movement as a new inventory-cost event. Historical
reviews continue replaying only their retained, hashed inputs.

## Phase 13: Convergence

- [x] T246 [T084] [FR-005/008/017, Constitution I/III/V] Obtain explicit owner approval for one immutable tenant-scoped `cost_inventory_ownership_part` authority linking review, movement basis, economic-owner Party, evidence SourceRecord and exact positive movement quantity; require complete disjoint quantity conservation per movement and never infer ownership from location, shipment state or document kind (missing).
- [x] T247 [T084] Specify partial/consignment/transit ownership in `contracts/inventory-service.md`: owner-filtered receipt/opening/issue/return/loss/transfer portions, proportional receipt-cost observation at read time, unchanged ownership through transit unless explicitly reallocated, ambiguity refusal and compatibility with existing full-owner reviews (missing).
- [x] T248 [T084] Add failing domain/service/migration/history/tenant tests for two-owner receipt splits, consigned stock exclusion, transit preservation, explicit ownership transfer, partial issues/returns/losses, FIFO/specific conservation, correction replacement, gaps/overlap/excess, foreign evidence, frozen replay, hash tampering and populated downgrade refusal (missing).
- [x] T249 [T084] After T246 approval, add the approved SQLAlchemy model and migration `0084_inventory_ownership_parts.py`, same-tenant composite links, positive/exact retained constraints, downgrade guard, Inspector/data-model/resource vocabulary and English/German labels while preserving existing full-owner history (missing).
- [x] T250 [T084] Extend the shared inventory request, admission, retained digest/replay and kernel mapping to partition each effective movement by explicitly evidenced economic owner; derive proportional acquisition-cost observations only at read time and keep physical locations/transit states non-authoritative (missing).
- [x] T251 [T084] Verify inventory, opening/receipt cost, Inspector, contribution, company generations/graph, tool/MCP, catalog, generated-doc, spec, migration and scoped lint gates; close T084 only if every ownership ambiguity refuses and all evidence is green (partial).

T246 -> T247 -> T248 -> T249 -> T250 -> T251. Ownership parts retain stated quantity
and evidence only. They never store a derived unit cost, invent an ownership transfer or
reinterpret a physical transfer/in-transit status. Existing full-owner reviews remain
historically reproducible and need no rewrite.

T246–T251 delivered: complete evidenced owner partitions are retained and hashed for
every effective movement while only the selected owner's positive portion enters the
existing FIFO/specific kernel. Receipt/opening cost remains source-stated authority and
is observed proportionally at read time. Consigned stock is excluded, transit cannot
invent title, corrections bind only effective replacement identities, and gaps, excess,
duplicates, foreign evidence and tampering refuse atomically. The broader adjacent run
has 270 passing tests; the corrected Inspector/company-graph slice passes 26 tests, all
eight inventory migration tests pass, generated-doc tests pass 8, and scoped Ruff,
spec-policy and whitespace gates pass.

T237–T240 delivered: bounded inventory admission now normalizes the shared append-only
MovementCorrection chain. Original and compensation cancel; an optional replacement is
the sole effective input at its authored economic time and is classified explicitly by
the confirmed request. Replacement receipts require fresh receipt-cost review and ownership
evidence. Correction identity, members, event and reason are bound into the retained review
digest; incomplete or tenant-inconsistent chains refuse, action replay stays idempotent and
older reviews remain reproducible. The focused inventory/migration regression passes 90
tests, the adjacent receipt-cost/tool/contribution/generation/catalog/spec regression passes
121 tests, documentation generation is reproducible, and scoped Ruff, format, spec-policy
and whitespace checks pass. T084 remains open only for evidenced opening balances and
consignment/transit ownership.

## Phase 14: Partial commercial matching

- [x] T252 [T085] [FR-002/003/007/010/011/017, Constitution I/III/IV/V/VIII] Obtain explicit owner approval for the separate immutable tenant-scoped `cost_commercial_match_revision`, `cost_commercial_inventory_part` and `cost_commercial_direct_part` authority in `contracts/commercial-matching.md`; preserve legacy full-line reviews and do not weaken their uniqueness or infer matching.
- [x] T253 [T085] After approval, add failing domain/service/migration/history/tenant tests for split and partial billing/fulfilment, signed sales credits with exact returns, free goods, direct-service and shipping-only scope, evidenced kit/direct input, unresolved WIP, conservation gaps/overlap/excess, foreign evidence, rematch/replay/tampering and populated downgrade refusal.
- [x] T254 [T085] After T253, implement pure signed conservation and deterministic allocation over explicit portions without storing derived revenue, unit cost, margin or conversion authority.
- [x] T255 [T085] After T252 approval, add the reviewed SQLAlchemy tables and next linear migration with same-tenant composite links, append-only superseding revisions, immutable-part guards, Inspector/data-model/resource vocabulary and populated downgrade refusal.
- [x] T256 [T085] Extend shared contribution candidate/review/read services and the existing `cost.change` request to admit complete explicit match revisions, observe frozen inventory/direct cost at read time, preserve legacy reviews and refuse ambiguous or stale scope atomically.
- [x] T257 [T085] Verify contribution, inventory/returns, selling cost, Inspector, generations/graph, tool/MCP, catalog, generated-doc, spec, migration and scoped lint gates; every supported conservation and historical replay case is green. The broader repository still has independent pre-existing import-order findings and an experimental `costing_spike` child retry failure outside this feature scope.

T252 -> T253 -> T254/T255 -> T256 -> T257. T083 remains blocked until the signed
late-cost/return demo case can use this reviewed matching authority. No migration or
implementation begins while T252 is open.

## Phase 15: Canonical source-backed costing demo

- [x] T258 [T083] [FR-026/SC-007, Constitution I/IV/V/VIII] Add failing canonical-profile tests for same-request replay, atomic interrupted retry, exact owner/run/tenant initialization authority, rejection outside that scope and preservation of later Demo Data pause/stop controls.
- [x] T259 [T083] Add failing source-lineage and quantity-coverage stories for complete fixture A (100 received, 60 fulfilled/billed and cost-matched, 40 remaining and valued), one visibly incomplete missing-cost trade, and one late-cost/signed-return history; add the remaining fixture-A DB2 assertion through existing read services.
- [x] T260 [T083] Version `demo/international.py` and the canonical manifest contract to `international-v2`; add stable authored source inputs and bounded case vocabulary without changing the ongoing `demo_data` generator's default missing-cost semantics.
- [x] T261 [T083] Implement the private fixed-recipe profile-costing orchestrator in `services/demo_profile.py` and a transaction/run/owner-bound initialization scope in `services/tenant_policy.py`; call existing costing preview/execute services, retain normal proposal/event audit and prohibit direct ORM financial approval or independent commits.
- [x] T262 [T083] Reconcile the company-setup/demo durable contract and canonical profile contract, then verify focused company setup, scheduling, costing, return, replay, tenant-isolation, spec and scoped lint gates before closing T083.

T258/T259 -> T260/T261 -> T262. T260 may define fixed source vocabulary while the
failing tests are being authored, but no initialization behavior changes before T258/T259
demonstrate the gaps. This phase adds no schema, schedule, queue, browser timer or claim
that ongoing unreviewed synthetic orders are fully costed.

T083 is delivered: international-v2 preserves the 16-item operational baseline while
adding three named source-backed costing stories. Fixture A derives 420 EUR remaining
acquisition value, 630 EUR matched fulfilled cost and 570 EUR DB1 from retained authority;
90 EUR direct and 24 EUR allocated selling costs derive 456 EUR DB2 at 38%. The
missing-cost case stays explicitly unreviewed and the signed credit uses the exact
original issue/return portion. New received finance detail is retained by the shared
manual-document service instead of being recomputed. Active and pending setup owners use
only the fixed transaction/run/tenant/intent-bound authority. The earlier 132-test
regression gate remains green for the inventory/DB1/return slice; the final DB2 change
passes 76 focused demo, company-setup, selling-cost, contribution and commercial-matching
tests. Scoped Ruff and spec policy pass separately.

## Phase 16: Reviewed carrying-value bridge

- [x] T263 [T086] [FR-009/015/019, SC-001/003] Add failing domain and service stories for exact remaining-scope write-down, partial scope, recovery ceiling, predecessor continuity, cutoff replay, source trace, owner/member authorization, staleness and tenant non-disclosure.
- [x] T264 [T086] Implement pure Decimal carrying-value reconciliation with source-stated total assessed values, exact four-decimal conservation, overlap/refusal rules and acquisition ceiling; never infer unit values, assessment values or legal policy.
- [x] T265 [T086] After T264, add the guarded PostgreSQL migration plus tenant-scoped SQLAlchemy assessment revision and scope-part models, with static-SQL, upgrade/downgrade and cross-tenant FK tests. The header links only the exact inventory review; parts link exact inventory members and source evidence.
- [x] T266 [T086] Extend the shared `cost.change` preview/confirmed-execution service with immutable source-backed write-down/recovery revisions, owner revalidation, expected-sequence fencing and atomic event/action audit.
- [x] T267 [T086] Derive current and historical carrying value through the inventory read and propagate the same result into generations, captured basis and coverage without creating calculated authority or changing commercial acquisition cost/DB1/DB2.
- [x] T268 [T086] Add record inspection, tool/MCP/CLI/web pass-through and catalog labels through existing shared services; regenerate Tool Usage and run focused/full migration, tenant, costing, reporting, docs, spec and lint gates before closing T086.

T263 -> T264 -> T265 -> T266 -> T267 -> T268. No task closes while the retained historical
answer, acquisition ceiling, owner confirmation or tenant boundary is red.

T267 direct-read checkpoint: current reads accept only the complete verified assessment
event chain for the selected inventory review, derive carrying value and its bridge while
preserving acquisition cost, and become stale again after any other later event. Explicit
review plus assessment identities reproduce the historical result without a current-event
query. Generation/captured-basis propagation binds the assessment identity, knowledge/event
context and carrying observation in disposable output. Cache reads verify the combined
hash and never replay inventory; Census relevance admits only verified retained assessment
events for the selected review and preserves independent carrying coverage.

## Phase 17: Evidence-backed allocation and conversion

- [x] T269 [T087] [FR-002/003/020/021/022, Constitution I/III/VIII] Owner approved the exact immutable `cost_conversion_basis_revision`, `Numeric(28,12)` ratio, closed driver vocabulary and nullable same-tenant links from both acquisition and selling attribution parts on 2026-09-20. No conversion chain, inverse lookup, policy activation or posting is authorized.
- [x] T270 [T087] Add failing pure-domain tests for signed four-decimal largest-remainder allocation, stable opaque-ID ties, partial residual, negative purchase reductions, zero/negative weights, duplicate targets, unsupported precision and exact conversion numerator/denominator behavior.
- [x] T271 [T087] Implement the pure Decimal allocation and conversion kernels with no ORM, source mutation, inferred driver or stored derived authority.
- [x] T272 [T087] Add failing service stories for weighted receipt and selling allocation, explicit-versus-weighted exclusivity, bucket capacity, nonrecoverable-tax double-count prevention, evidenced skonto versus payment shortfall, stale proposal, owner/member authorization, history and tenant non-disclosure.
- [x] T273 [T087] After T269 approval, add the guarded PostgreSQL conversion-revision migration and SQLAlchemy model/link with static-SQL, upgrade/downgrade, immutability and cross-tenant composite-FK tests.
- [x] T274 [T087] Extend the shared `cost.change` preview/confirmed execution service to resolve weighted requests into exact existing attribution parts and to admit only explicitly selected source-backed conversion revisions; preserve original shares and derive converted observations at read time. Currency revisions flow through receipt cost and reviewed DB2; unit revisions are retained but explicitly refused as monetary authority, while the pure exact-quantity boundary remains available for a future typed quantity consumer.
- [x] T275 [T087] Add Inspector, CLI/web/MCP pass-through, catalog labels and source/conversion traces through existing shared services; regenerate Tool Usage and verify receipt, inventory, contribution, generation, tenant, migration, docs, spec and scoped lint gates before closing T087.

T269 -> T270 -> T271 -> T272 -> T273 -> T274 -> T275. T270/T271 may proceed while the
schema review is open because they add only pure arithmetic. T273 and all non-identity
conversion behavior remain blocked until T269 is explicitly approved. No task infers a
weight, tax treatment, skonto, exchange rate, unit ratio or financial posting.

## Phase 18: Operational cost explanations (T088)

- [x] T276 [FR-001/011/014/016/022/023/024, SC-003] Add the failing Web API and browser contract tests for inventory/contribution explanations, exact values, display rounding, freshness, missing basis, Inspector links, tenant switching and absence of mutations.
- [x] T277 [FR-001/014/016] Add typed `costQuery` client support and one reusable read-only cost explanation component; keep service arithmetic authoritative and stale retained basis visibly non-current.
- [x] T278 [FR-001/016/022] Mount the inventory explanation in the existing Warehouse item preview and reuse its presentation contract in Analysis without adding a second detail route.
- [x] T279 [FR-011/014/016/023/024] Connect exact document-line contribution entry points in Orders and Finance where the shared read model exposes an unambiguous scope; keep DB1 and DB2 coverage independent.
- [ ] T280 [SC-002/003] **DEFERRED — NON-BLOCKING FOR PROVISIONAL TECHNICAL CLOSEOUT.** Run the recorded fixture-M protocol when five suitable participants are available; at least four must complete the task within two minutes. Until then, make no moderated-usability claim. Automated technical gates remain part of T090.

T276 -> T277 -> T278 -> T279. T280 is an owner-deferred external qualification and does
not block provisional technical closeout. T279 must not infer a document-line identity
from a document number or aggregate document. Automated gates cannot complete SC-002.

- [x] T287 [FR-011/012/014/016] Add a canonical-demo regression proving its confirmed six-position contribution batch has a readable historical generation, and publish that disposable generation from the normal profile seed service.
- [x] T288 [FR-011/014/016] Show retained `basis_db1` and `basis_db2` in stale operational explanations under the existing non-current warning; never derive or present them as current authority.
- [x] T289 [FR-007/014/016] Add a stale-inventory browser regression and show retained `basis_acquisition_value` and unit cost under the existing non-current warning; keep unsupported carrying value unknown and perform no browser calculation.
- [x] T290 [FR-007/014/026, SC-007] Add a canonical-demo regression proving the latest inventory context retains fixture A's 40-unit, EUR 420 acquisition basis, then remove the synthetic cleanup that made the demonstrable valued stock disappear while preserving the signed customer-return story.
