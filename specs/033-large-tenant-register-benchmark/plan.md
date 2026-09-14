# Implementation Plan: Large-Tenant Register Benchmark

**Branch**: `codex/033-large-tenant-register-benchmark` | **Date**: 2026-09-02 | **Spec**: [`spec.md`](spec.md)

**Language**: English for all repository artifacts and review evidence.

**Status**: Specification and plan approved by the product owner on 2026-09-02.

## Summary

Close `016/FR-015` with a deterministic PostgreSQL benchmark fixture containing at
least 10,000 same-day sales orders and supported related records. Exercise the nine
core register families through `reality.web.read_models`, capture structural SQL
evidence as well as correctness/timing observations, and write a versioned JSON result
plus a human-readable summary. Reuse the same case catalog at reduced cardinality in
normal pytest, while keeping the full run explicit. Remediate only benchmark-proven
violations of the existing large-tenant contract, then update Spec 016 and the separate
100,000-orders/day capacity idea with an exact evidence boundary.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, existing Reality services and Web
read models, pytest; no new benchmark framework

**Storage**: Ephemeral PostgreSQL benchmark database using the current Alembic schema;
versioned JSON/Markdown evidence contains measurements but no business records

**Testing**: pytest reduced-cardinality contracts; explicit full PostgreSQL benchmark;
ruff; full Python suite; Spec policy

**Project Type**: Existing backend/service application with a repository-only benchmark
harness and no public runtime interface

**Constraints**: Fixed UTC business date and seed; Decimal values; opaque IDs; immutable
SourceRecords; strict tenant scope; product read boundaries only; default page size 50,
maximum 100; setup time excluded from read measurements

**Scale/Scope**: 10,000 sales-order Documents within one business day, deterministic
multi-line distribution, related SourceRecords/DocumentLines/Commitments plus supported
reservation, movement, financial and projection records, one control tenant, and nine
register families. This is a read-cardinality proof, not a throughput or concurrency claim.

## Constitution Check *(blocking gate)*

*GATE: Passed before research and re-checked after design.*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Dataset contract preserves SourceRecord → Document/Line → applicable Reality links and validates samples | PASS |
| Reality owns operational state | Benchmark generates/reads Commitments, Reservations, Movements and LedgerEntries; no delivery/payment fields are added to Documents | PASS |
| Proven schema only | No table, column, migration, or production persistence is planned | PASS |
| Tenant + shared service boundaries | Cases call existing tenant-scoped Web read models; a sentinel tenant proves all result classes and SQL predicates | PASS |
| Spec/test traceability | One case manifest maps every FR/DR to reduced tests and the full evidence run | PASS |
| Explainable web behavior | Sampled order results retain their shortest Source/Evidence/Reality links; browser behavior is unchanged | PASS |
| Smallest coherent design | Reuse existing reads and dependencies; add one test-only harness and remediate only observed contract failures | PASS |

Post-design review remains PASS: all new persistent data exists only in an ephemeral
benchmark database under the existing schema, the runner is outside product runtime,
and its read cases call the same read models as Product Web.

## Repository Structure and Layer Changes

```text
packages/reality-core/
├── benchmarks/
│   └── large_tenant_registers/
│       ├── __init__.py
│       ├── dataset.py
│       ├── cases.py
│       ├── query_evidence.py
│       ├── report.py
│       └── runner.py
├── src/reality/
│   ├── services/projections.py      # only if a measured defect exists
│   └── web/read_models.py           # only for proven remediation
└── tests/
    └── test_large_tenant_register_contract.py

specs/033-large-tenant-register-benchmark/
├── {spec.md,plan.md,research.md,data-model.md,quickstart.md,tasks.md}
├── contracts/{benchmark-case-catalog.md,benchmark-result.schema.json}
├── evidence/{benchmark-result.json,benchmark-result.md}
└── checklists/requirements.md

docs/ideas/ecommerce-capacity-baseline.md
specs/016-web-product/spec.md
```

**Files/layers affected**: The benchmark harness is development-only and imports
production service/read boundaries in the permitted dependency direction. Product
modules change only if a red contract demonstrates that current behavior violates the
approved Web contract. No Web client, API route, CLI command, model, or migration is
added.

## Design

### Reality flow

The fixed-seed generator uses batch-oriented PostgreSQL fixture inserts to create one
source-system identity and immutable SourceRecords, sales-order Documents with one or
more DocumentLines, customer-delivery Commitments, and a deterministic supported mix of
Reservations and Movements. A smaller deterministic financial subset preserves the
existing invoice/payment and balanced-ledger invariants so Open items, Payments, and
Journal have multi-page cardinality. The fixture is validated against representative
Source/Evidence/Reality links and existing business invariants before measurement.
Operational projections are refreshed through the existing projection service; they
are never inserted as benchmark-authored truth.

Sample validation follows:

```text
SourceRecord
  -> sales-order Document -> DocumentLine
       -> customer-delivery Commitment
            -> Reservation
            -> shipment Movement

invoice Document -> balanced LedgerEntries <- payment Evidence/Reality path
```

The control tenant uses overlapping human numbers and unique sentinel content. This
proves that opaque IDs and tenant scope, rather than display numbers, govern isolation.

### Service and adapter flow

```text
fixed-seed dataset setup (excluded from timings)
              |
              v
validated batch fixture + existing projection refresh
              |
              v
versioned benchmark case catalog
              |
              v
existing reality.web.read_models functions
              |
      +-------+---------+
      |                 |
 correctness/page   SQL/plan evidence
      |                 |
      +-------+---------+
              v
validated JSON result -> Markdown review summary
```

The runner owns orchestration only. It does not recreate filtering, counting,
aggregation, or tenant rules. Each case names the production read callable, parameters,
expected total/page identity, and required query-boundary observations.

### Data and migration impact

No schema or migration change is planned. Benchmark Dataset Definition, Case, and Result
are file/command concepts described in `data-model.md`, not business tables. The runner
requires an explicitly supplied PostgreSQL database whose name begins with
`reality_benchmark_`, whose business tables are empty before first setup, and whose use
is confirmed with `--confirm-disposable`. It refuses every target that fails any of
those checks. Dataset setup and measurements are separate stages so setup cost is never
presented as read latency.

### Failure, security, and tenant behavior

- The runner fails closed on missing PostgreSQL configuration, a database name outside
  the `reality_benchmark_` prefix, missing `--confirm-disposable`, non-empty unrelated
  business state, unexpected benchmark state, incomplete cardinality, schema mismatch,
  failed case, missing report field, or control-tenant observation.
- The dataset identity includes definition version, seed, business date and tenant IDs;
  rerun mode validates or explicitly rebuilds rather than silently appending.
- SQL statement capture is bounded to benchmark cases and redacts connection secrets and
  business payloads from evidence.
- Query evidence verifies tenant predicates plus database-side filter/count/order/limit;
  sensitive bind values need not appear in retained reports.
- No mutation confirmation is applicable: this is a repository-side harness targeting an
  explicitly disposable benchmark database, not a chat or product mutation.

## Implementation Phases

### A. Freeze case and result contracts

Add the case catalog and machine-readable result schema first. Map each register family,
filter/count/page/aggregate behavior, tenant sentinel and evidence field to FR/DR/SC.
Add reduced tests that initially fail because the harness does not yet exist.

### B. Build deterministic dataset setup

Create a parameterized fixed-seed setup with reduced and 10,000-order profiles. Use a
batch fixture for tractable setup, validate it against existing domain invariants and
sample traces, reuse projection behavior, and keep setup outside case timings. Never
fabricate unsupported flows or expose the fixture as a product write path.

### C. Execute shared read cases and structural proof

Run all nine families through existing read models. Capture response size, total,
adjacent-page identities, expected filters/aggregates, duration, and bounded SQL/query
plan characteristics. Repeat the catalog against the completed dataset and reject drift.

### D. Remediate only observed failures

If a case exposes Python-side materialization, missing tenant scope, unstable ordering,
an over-limit response, page-derived aggregate, or projection-refresh scan, add the
smallest production read/service correction and a regression test. Do not add speculative
indexes; any index requires failing plan evidence and a proven high-cardinality path.

### E. Produce full evidence for review

Run the explicit 10,000-order benchmark twice on the same dataset, validate its JSON,
render the review summary, and retain the neutral benchmark result with revision,
schema, environment, cases, cardinalities, timings, outcomes and limitations. Generated
evidence is not labelled accepted before product-owner final review.

### F. Close baseline and carry forward

After full evidence, prepare the `016/FR-015` and `016/SC-007` Verified-as-is closure for
review and update the 100,000-orders/day idea with the exact reuse boundary. These
changes and the neutral benchmark result become accepted only when the product owner
approves the final implementation diff.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-002, DR-001–DR-002, DR-004–DR-005 | integration | `test_dataset_is_deterministic_complete_and_traceable` | Dataset profiles and validator do not exist |
| FR-003, FR-010 | contract | `test_case_catalog_covers_every_core_register_and_runs_as_one_gate` | Case catalog/runner absent |
| FR-004–FR-006 | integration | `test_register_pages_are_bounded_filtered_counted_and_stable` | Cross-register proof absent; may expose read defects |
| FR-007 | integration | `test_aggregates_use_complete_filtered_results` | Large multi-page aggregate proof absent |
| FR-008, DR-003 | integration | `test_every_case_excludes_control_tenant_sentinels` | Cross-case sentinel assertion absent |
| FR-009 | SQL contract | `test_case_statements_keep_scope_and_work_in_database` | SQL/plan evidence collector absent |
| FR-011–FR-012 | unit/contract | `test_result_schema_is_complete_redacted_and_repeatable` | Pydantic result model/renderer absent |
| FR-013 | suite/acceptance | reduced pytest plus explicit 10,000-order two-run command | No split fast/full gate |
| FR-014–FR-015 | policy/docs | baseline ledger and capacity-idea assertions | Evidence cannot be cited before acceptance |
| SC-001–SC-008 | acceptance/review | neutral JSON/Markdown result plus final traceability review | Full evidence not yet generated |

Tests use the same case catalog at both profiles. The reduced profile establishes logic
quickly in CI; it must preserve multi-page, equal-sort, beyond-first-page filter, Decimal
boundary, empty-filter and sentinel shapes even with fewer orders. The full profile is
the only evidence allowed to close the 10,000-order baseline.

## Rollout and Rollback

This feature adds no runtime surface, deployment dependency, or migration. The benchmark
harness can be reverted without data rollback. Any production read remediation is
backward-compatible and must be independently covered; reverting it restores the prior
query behavior. Accepted evidence is valid only for its recorded revision and schema and
must not be silently relabeled after later changes.

## Review Risks

- Dataset generation could dominate runtime or accidentally become the measured claim;
  setup and read phases are strictly separated.
- Projection refresh currently occurs on some read paths and may hide unbounded work;
  capture the full case statement set and remediate only if the contract is violated.
- Direct fixture construction could bypass business invariants; limit it to the
  disposable benchmark database and validate representative Source/Evidence/Reality,
  immutable-source, shortest-link, and balanced-ledger invariants before measurement.
- A small catalog would make Inventory look trivially bounded; ensure cardinality and
  filter shapes exercise each register rather than merely the Orders table.
- Timing values vary by environment; record them as observations with no unsupported SLO.
- The future 100,000-order idea could overclaim reuse; document exactly which dataset,
  read cases and reporting pieces transfer and which workload dimensions do not.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
