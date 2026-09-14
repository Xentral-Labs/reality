---
description: "Requirement-traceable large-tenant register benchmark tasks"
---

# Tasks: Large-Tenant Register Benchmark

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the behavior they prove. The full 10,000-order run is
an explicit acceptance gate, not part of the normal fast suite.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Record specification and plan approvals and confirm no clarification markers remain in `specs/033-large-tenant-register-benchmark/spec.md`, `specs/033-large-tenant-register-benchmark/plan.md`, and `specs/033-large-tenant-register-benchmark/checklists/requirements.md`
- [x] T002 Confirm every Constitution Check row remains PASS and no schema, migration, public interface, or new dependency is planned in `specs/033-large-tenant-register-benchmark/plan.md`
- [x] T003 Run `$speckit-analyze`, record its findings in `specs/033-large-tenant-register-benchmark/checklists/requirements.md`, and resolve all Critical, High, and Medium findings before implementation

---

## Phase 2: Foundational Contracts and Failing Proof

**Purpose**: Freeze shared profiles, cases, result validation, and red tests before
building the generator or runner.

- [x] T004 [P] [FR-003] [FR-004] [FR-005] Add the executable nine-family case/profile declarations with stable IDs and requirement mappings in `packages/reality-core/benchmarks/large_tenant_registers/cases.py`
- [x] T005 [P] [FR-011] [FR-012] Add failing result-contract tests for required fields, redaction, deterministic semantic comparison, and Markdown rendering in `packages/reality-core/tests/test_large_tenant_register_contract.py`
- [x] T006 [P] [FR-003] [FR-010] Add failing catalog-contract tests for all nine families, required operation shapes, unique case IDs, and a single gate in `packages/reality-core/tests/test_large_tenant_register_contract.py`
- [x] T007 [P] [FR-009] [DR-003] Add failing SQL-evidence tests for tenant predicates, filter/count/order/limit ordering, bounded statement capture, and safe bind-value handling in `packages/reality-core/tests/test_large_tenant_register_contract.py`
- [x] T008 [FR-011] [FR-012] Implement the canonical Pydantic v2 result model, semantic repeat comparison, JSON/schema export, and derived Markdown rendering in `packages/reality-core/benchmarks/large_tenant_registers/report.py`
- [x] T009 [FR-009] Implement scoped SQL statement and PostgreSQL plan observation without credential/payload retention in `packages/reality-core/benchmarks/large_tenant_registers/query_evidence.py`

**Checkpoint**: The case and report contracts execute independently; dataset-dependent
tests remain red for the expected missing generator/runner.

---

## Phase 3: User Story 1 — Reproduce the Large-Tenant Read Proof (P1)

**Goal**: Build and validate deterministic reduced/full datasets and run all required
register cases from one entrypoint.

**Independent Test**: Generate the same profile twice and confirm exact cardinalities,
sample traces, catalog cases and semantic outcomes; an incomplete setup or failed case
must fail the command.

### Tests

- [x] T010 [US1] [FR-001] [FR-002] [DR-001] [DR-002] [DR-004] [DR-005] Add failing reduced-profile tests for deterministic external identities/cardinalities, same-day orders, line distribution, stable opaque IDs within one completed dataset, immutable SourceRecords, shortest links, Decimal values, and no schema expansion in `packages/reality-core/tests/test_large_tenant_register_contract.py`
- [x] T011 [US1] [FR-002] [FR-010] Add failing tests for partial-dataset rejection, repeat-setup behavior, unsafe target rejection, stage failure, and non-zero runner exit in `packages/reality-core/tests/test_large_tenant_register_contract.py`
- [x] T012 [US1] [FR-003] [FR-012] [FR-013] Add failing reduced-profile integration proof that the complete ordered catalog runs twice with identical semantic results while timings may differ in `packages/reality-core/tests/test_large_tenant_register_contract.py`

### Implementation

- [x] T013 [US1] [FR-001] [FR-002] Define fixed-seed reduced/full profiles, deterministic external identities, expected cardinalities, flow distribution, and sentinel definition while permitting new opaque database IDs after explicit rebuild in `packages/reality-core/benchmarks/large_tenant_registers/dataset.py`
- [x] T014 [US1] [FR-001] [DR-001] [DR-002] [DR-004] [DR-005] Implement a disposable-database batch fixture and validate it against representative Source/Evidence/Reality traces and existing domain invariants in `packages/reality-core/benchmarks/large_tenant_registers/dataset.py`
- [x] T015 [US1] [FR-002] [FR-010] Require a `reality_benchmark_` database name, empty business tables on first setup, and `--confirm-disposable`; implement lifecycle states, partial-state failure, explicit reuse/rebuild rules, and setup/read timing separation in `packages/reality-core/benchmarks/large_tenant_registers/runner.py`
- [x] T016 [US1] [FR-003] [FR-010] [FR-012] Implement ordered case orchestration, repeat execution, semantic comparison, failing exit behavior, and validated report emission in `packages/reality-core/benchmarks/large_tenant_registers/runner.py`
- [x] T017 [US1] [FR-013] Register only the reduced contract test in the normal test suite and document the explicit full profile command in `specs/033-large-tenant-register-benchmark/quickstart.md`

**Checkpoint**: User Story 1 independently creates a deterministic dataset and runs the
nine-family proof, but acceptance still requires the boundedness/isolation assertions in
User Story 2.

---

## Phase 4: User Story 2 — Trust Bounded and Isolated Results (P2)

**Goal**: Prove page/count/filter/order/aggregate correctness, structural query bounds,
and complete target/control tenant separation at benchmark cardinality.

**Independent Test**: Execute selective and non-selective cases with equal sort values
and control sentinels, then inspect results and SQL evidence for every register family.

### Tests

- [x] T018 [P] [US2] [FR-004] [FR-005] [FR-006] Add failing assertions for default/max page size, complete filtered totals, beyond-first-page matches, zero matches, and stable adjacent pages in `packages/reality-core/tests/test_large_tenant_register_contract.py`
- [x] T019 [P] [US2] [FR-007] Add failing multi-page complete-result aggregate assertions for every covered register/dashboard value in `packages/reality-core/tests/test_large_tenant_register_contract.py`
- [x] T020 [P] [US2] [FR-008] [DR-003] Add failing sentinel assertions across all catalog-covered rows, totals, aggregates, searches and related lookups; record option/inspector endpoints as outside this catalog in `packages/reality-core/tests/test_large_tenant_register_contract.py` and `specs/033-large-tenant-register-benchmark/checklists/requirements.md`
- [x] T021 [P] [US2] [FR-009] Add failing structural assertions for each high-cardinality statement and projection-refresh path in `packages/reality-core/tests/test_large_tenant_register_contract.py`

### Implementation and evidence

- [x] T022 [US2] [FR-003] [FR-004] [FR-005] [FR-006] Execute each catalog case through its existing callable in `packages/reality-core/src/reality/web/read_models.py` and record page/count/filter/order observations in `packages/reality-core/benchmarks/large_tenant_registers/cases.py`
- [x] T023 [US2] [FR-007] Add complete-filtered-set aggregate observations and expected-value comparison without deriving truth from visible pages in `packages/reality-core/benchmarks/large_tenant_registers/cases.py`
- [x] T024 [US2] [FR-008] [DR-003] Populate overlapping-number sentinel data and apply common isolation assertions to every case outcome in `packages/reality-core/benchmarks/large_tenant_registers/dataset.py` and `packages/reality-core/benchmarks/large_tenant_registers/cases.py`
- [x] T025 [US2] [FR-009] Attach safe statement/plan evidence to every applicable case and fail unbounded or Python-materialized high-cardinality work in `packages/reality-core/benchmarks/large_tenant_registers/query_evidence.py` and `packages/reality-core/benchmarks/large_tenant_registers/cases.py`
- [x] T026 [US2] [FR-004] [FR-005] [FR-006] [FR-007] [FR-008] [FR-009] If and only if red evidence proves a contract violation, implement the smallest correction with a focused regression in `packages/reality-core/src/reality/web/read_models.py`, `packages/reality-core/src/reality/services/projections.py`, and `packages/reality-core/tests/test_large_tenant_register_contract.py`; record N/A when no remediation is required

**Checkpoint**: Reduced tests prove every boundedness/correctness/isolation behavior via
the same catalog that the full run will execute.

---

## Phase 5: User Story 3 — Carry the Baseline Forward Honestly (P3)

**Goal**: Produce neutral evidence for final acceptance, close only the documented baseline gap, and make the
larger capacity idea reuse the work without overstating it.

**Independent Test**: Validate the full result and inspect Spec 016 plus the capacity idea
for exact proven/unproven boundaries.

### Tests and acceptance evidence

- [x] T027 [US3] [FR-011] [FR-012] [SC-001] [SC-002] Run the full 10,000-order catalog twice and generate schema-valid neutral evidence in `specs/033-large-tenant-register-benchmark/evidence/benchmark-result.json` and `specs/033-large-tenant-register-benchmark/evidence/benchmark-result.md`
- [x] T028 [US3] [SC-003] [SC-004] [SC-005] [SC-006] Review all nine families for zero over-limit, unstable-page, incorrect-total/aggregate, tenant-leak, or structural-query failures and record the candidate evidence review in `specs/033-large-tenant-register-benchmark/evidence/benchmark-result.md`
- [x] T029 [US3] [FR-014] [FR-015] [SC-007] Add failing documentation-policy assertions for the Spec 016 evidence closure and capacity-idea proven/unproven boundary in `packages/reality-core/tests/test_spec_policy.py`

### Documentation closure

- [x] T030 [US3] [FR-014] Prepare FR-015, SC-007, Open Questions, Requirement Evidence and traceability as a proposed Verified-as-is closure citing the neutral result in `specs/016-web-product/spec.md`; it becomes accepted only with product-owner final review
- [x] T031 [US3] [FR-015] Update the established-baseline, reusable-artifact and remaining-work sections in `docs/ideas/ecommerce-capacity-baseline.md` without promoting the idea or claiming throughput in `docs/ideas/ecommerce-capacity-baseline.md`
- [x] T032 [US3] [FR-011] [SC-005] Ensure the retained neutral result and summary identify revision, schema, environment, dataset, cases, timings, outcome and limitations in `specs/033-large-tenant-register-benchmark/evidence/benchmark-result.json` and `specs/033-large-tenant-register-benchmark/evidence/benchmark-result.md`

**Checkpoint**: The feature's evidence is complete, the baseline/idea accurately state
what is proven, and product-owner final review is recorded.

---

## Final Phase: Cross-Cutting Review

- [x] T033 [SC-008] Run `$speckit-converge` if implementation diverged, then `$speckit-analyze`; resolve all Critical, High, and Medium findings and record the result in `specs/033-large-tenant-register-benchmark/checklists/requirements.md`
- [x] T034 [FR-013] Run Ruff, the focused reduced contract, and the complete PostgreSQL backend suite from `packages/reality-core`, recording commands and outcomes in `specs/033-large-tenant-register-benchmark/evidence/benchmark-result.md`
- [x] T035 [FR-011] Validate `specs/033-large-tenant-register-benchmark/evidence/benchmark-result.json` with the canonical Pydantic v2 model, compare its exported schema with `specs/033-large-tenant-register-benchmark/contracts/benchmark-result.schema.json`, and rerun `python3 scripts/check_spec_policy.py`
- [x] T036 [DR-001] [DR-002] [DR-003] [DR-004] [DR-005] Review the final diff for Source → Evidence → Reality, document non-centrality, opaque IDs, tenant scope, immutable sources, shared reads, and absence of unproven schema in `specs/033-large-tenant-register-benchmark/checklists/requirements.md`
- [x] T037 Confirm no frontend, i18n, browser, API-route, public CLI, migration, or deployment gate applies and document that N/A review in `specs/033-large-tenant-register-benchmark/checklists/requirements.md`
- [x] T038 Obtain product-owner final review for the evidence and implementation, then record approval in `specs/033-large-tenant-register-benchmark/checklists/requirements.md`

## Dependencies and Execution Order

```text
Specification/plan gates
        |
        v
Foundational contracts + failing proof
        |
        v
US1 deterministic setup and one runner
        |
        v
US2 boundedness/correctness/isolation proof
        |
        v
US3 full evidence and honest baseline closure
        |
        v
Cross-cutting analysis, suites and final review
```

- US1 depends on foundational contracts.
- US2 depends on the US1 dataset and runner but remains independently testable through
  its focused cases.
- US3 depends on passing US1 and US2 because only the full proven run may close Spec 016.
- T030–T032 must not run before T027–T028 pass.
- T038 is the final approval gate after every technical and documentation check.

## Parallel Opportunities

- T004, T005, T006 and T007 touch separable declarations/test concerns and can be
  prepared in parallel before T008–T009 integrate them.
- T018–T021 define independent behavioral, aggregate, isolation and structural failures.
- T030 and T031 edit separate documents after neutral full evidence exists; T038 is the
  product-owner acceptance gate for the complete proposed closure.
- Full benchmark execution is intentionally serialized to preserve deterministic
  database state and comparable repeat runs.

## Implementation Strategy

1. **MVP (US1)**: deterministic reduced/full dataset and one reproducible runner covering
   all nine families with a validated result contract.
2. **Contract proof (US2)**: complete boundedness, correctness, stable paging, aggregate,
   tenant and structural SQL evidence; remediate only actual failures.
3. **Acceptance (US3)**: execute the full two-run proof, retain evidence, close Spec 016,
   and update the larger idea's reuse boundary.
4. **Finish**: converge/analyze, full tests, policy checks and product-owner final review.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-002 | T010–T011 | T013–T015 | Implemented |
| FR-003 | T006, T012 | T004, T016, T022 | Implemented |
| FR-004–FR-006 | T018 | T022, T026 | Implemented |
| FR-007 | T019 | T023, T026 | Implemented |
| FR-008 | T020 | T024, T026 | Implemented |
| FR-009 | T007, T021 | T009, T025–T026 | Implemented |
| FR-010 | T006, T011 | T015–T016 | Implemented |
| FR-011–FR-012 | T005, T012, T027 | T008, T016, T032 | Implemented |
| FR-013 | T012, T034 | T017 | Implemented |
| FR-014–FR-015 | T029 | T030–T031 | Accepted |
| DR-001–DR-002 | T010, T036 | T014 | Implemented |
| DR-003 | T007, T020, T036 | T024–T025 | Implemented |
| DR-004–DR-005 | T010, T036 | T013–T014 | Implemented |
| SC-001–SC-006 | T027–T028, T033 | T030–T037 | Implemented |
| SC-007–SC-008 | T027–T028, T033 | T030–T038 | Accepted |

## Phase 7: Convergence

- [x] T039 Populate distinguishable control-tenant Source/Evidence/Reality and financial records for all nine register families, then assert zero foreign rows, counts, aggregates, searches, related lookups, and projections per FR-008 and US2/AC4
- [x] T040 Add database-complete filtered aggregates for Open items and Payments through shared read models/API responses and prove values exceed one visible page per FR-007 and US2/AC5
- [x] T041 Validate sampled payload hashes, immutable SourceRecords, Document/Line/Commitment shortest links, ledger balance, and batch-fixture parity with existing invariants per DR-001, DR-002, DR-005, and plan: dataset setup
- [x] T042 Make the checked-in benchmark result schema exactly equal to the canonical Pydantic v2 export and validate the retained result through that model per FR-011 and T035
- [x] T043 Extend every applicable catalog family with zero-match, invalid/min/max page size, categorical/date/Decimal filter and stable equal-sort cases; record bounded option/inspector endpoints as outside this catalog per FR-003–FR-006 and Edge Cases
- [x] T044 Rerun reduced/full proofs after convergence, refresh neutral evidence and tested-content digest, and update coverage/checklist records per FR-012–FR-015 and SC-001–SC-008
