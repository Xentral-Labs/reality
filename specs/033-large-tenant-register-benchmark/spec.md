# Feature Specification: Large-Tenant Register Benchmark

**Feature Branch**: `codex/033-large-tenant-register-benchmark`
**Created**: 2026-09-02
**Status**: Approved
**Language**: English
**Input**: "Provide repeatable proof that Reality's core registers remain tenant-scoped and bounded for a tenant processing at least 10,000 orders in one business day, then update the future 100,000-orders/day capacity idea to reuse this established baseline."

## Context and Intent

### Problem

Reality already defines bounded, tenant-scoped reads for its core operational registers,
but the large-tenant contract is supported only by focused query tests and code review.
There is no deterministic, repeatable dataset containing at least 10,000 orders in one
business day and no single evidence run proving that register filtering, counting, and
pagination remain database-bounded at that cardinality. This leaves `016/FR-015` and
`016/SC-007` as the final accepted baseline gap and prevents an honest scale claim.

### Scope

- Provide a deterministic large-tenant benchmark dataset representing at least 10,000
  orders, their lines, and the currently supported related Evidence and Reality records
  within one business day.
- Exercise every core register family named by the Web large-tenant contract through
  the same tenant-scoped read paths used by the product.
- Prove bounded page sizes, filtering and counting before pagination, stable paging,
  complete-result aggregates where applicable, and tenant isolation at benchmark
  cardinality.
- Produce a reproducible, reviewable benchmark result that records its dataset,
  revision, environment, cases, outcomes, durations, and observed limitations.
- Update the future production-shaped ecommerce capacity idea to identify this feature
  as an established read-side baseline and to reuse its dataset and evidence where
  compatible.

### Non-Goals

- Claiming that Reality sustains 10,000 concurrent writes, a particular orders-per-second
  rate, or an end-to-end production workload.
- Proving the separate 100,000-orders/day ingestion, worker, projection, recovery,
  resource-sizing, cloud-cost, or soak-test idea.
- Establishing universal latency service levels or comparing developer machines.
- Adding business behavior, public APIs, UI features, or schema solely for the benchmark.
- Bypassing application read boundaries with benchmark-only business rules.
- Optimizing queries unless this benchmark first exposes a failure against the existing
  large-tenant contract.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Web UI Specification](../../docs/WEB_SPEC.md), especially Core register catalog and
  Large-tenant read contract
- [Web Product Baseline](../016-web-product/spec.md), especially FR-015 and SC-007
- [Test Strategy](../../docs/TEST_STRATEGY.md)
- [Production-shaped ecommerce capacity idea](../../docs/ideas/ecommerce-capacity-baseline.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproduce the Large-Tenant Read Proof (Priority: P1)

As a maintainer, I can create the same large-tenant business-day dataset and run one
documented benchmark command so I can determine whether all core registers honor the
large-tenant contract on the tested revision.

**Why this priority**: A repeatable executable proof is the missing acceptance evidence;
without it, boundedness remains an unverified claim at the stated scale.

**Independent Test**: From a clean supported environment, generate the fixed-seed
dataset, run the benchmark twice, and verify that both runs cover the same register
cases and report the same cardinalities and pass/fail outcomes.

**Acceptance Scenarios**:

1. **Given** an empty benchmark tenant, **When** the documented dataset setup runs with
   its default seed, **Then** it creates at least 10,000 orders dated within one business
   day plus deterministic lines and supported related records, and reports the created
   cardinalities.
2. **Given** the completed dataset, **When** the benchmark runs, **Then** it exercises
   Orders, Commitments, Inventory, Reservations, Movements, Open items, Payments,
   Journal, and Documents with representative search, filter, count, sort, and paging
   cases through product read boundaries.
3. **Given** the same revision, dataset definition, seed, and environment, **When** the
   benchmark is repeated, **Then** the result contains the same cases, expected counts,
   and contract outcomes while reporting timing observations separately.
4. **Given** setup or a benchmark case fails, **When** the run completes, **Then** it
   exits unsuccessfully and identifies the failed stage or register without presenting
   partial evidence as a pass.

---

### User Story 2 - Trust Bounded and Isolated Results (Priority: P2)

As a product owner or reviewer, I can inspect evidence that large-tenant register reads
are complete where they count or aggregate, small where they return rows, and isolated
from another tenant.

**Why this priority**: A quick response is not useful if it silently counts only the
visible page, scans in application memory, returns unstable pages, or leaks tenant data.

**Independent Test**: Add distinguishable records to a control tenant, execute
selective and non-selective cases across the benchmark tenant, and verify result
cardinality, stable page identity, aggregate truth, query boundary evidence, and the
absence of control-tenant records.

**Acceptance Scenarios**:

1. **Given** more matches than one page, **When** any core register is read, **Then** the
   response contains 50 rows by default and never more than 100 rows, while its total
   count represents the complete filtered tenant result.
2. **Given** a filter matching records beyond the first unfiltered page, **When** that
   filter is applied, **Then** matching and counting occur before pagination and the
   expected records are returned.
3. **Given** records with equal primary sort values, **When** adjacent pages are read
   repeatedly, **Then** stable ordering prevents duplicate or missing records across
   those pages.
4. **Given** a second tenant containing unique sentinel records, **When** every benchmark
   case runs for the large tenant, **Then** no row, count, aggregate, or search result
   includes the sentinel data. Option and inspector endpoints remain outside this
   nine-register benchmark because none is invoked by its catalog.
5. **Given** a register exposes an aggregate or dashboard value, **When** its filtered
   result exceeds one page, **Then** the value reflects the complete filtered set rather
   than the visible page.

---

### User Story 3 - Carry the Baseline Forward Honestly (Priority: P3)

As a maintainer planning the later production-shaped capacity initiative, I can see
which 10,000-orders/day read proof already exists, what it does not prove, and which
artifacts may be reused.

**Why this priority**: The narrow baseline should reduce future work without being
misrepresented as the larger ingestion and operational-capacity result.

**Independent Test**: Review the benchmark result and the updated capacity idea and
verify that both name the reusable artifacts, distinguish 10,000-order read cardinality
from the 100,000-order mixed workload, and retain the larger idea's unresolved targets.

**Acceptance Scenarios**:

1. **Given** an accepted benchmark run, **When** a reviewer opens its report, **Then**
   they can identify the tested revision, schema revision, environment, dataset seed and
   cardinalities, covered register cases, durations, outcome, and limitations.
2. **Given** the production-shaped ecommerce capacity idea, **When** this feature is
   complete, **Then** the idea references the established 10,000-order read baseline,
   names compatible reusable artifacts, and explicitly states that ingestion throughput,
   concurrent mixed traffic, resource saturation, backlog recovery, and cloud sizing
   remain unproven.

### Edge Cases

- A partially populated benchmark tenant must not be treated as a valid completed
  dataset or produce passing evidence.
- Re-running setup for the same benchmark identity must be deterministic and must not
  silently double the measured cardinality.
- A requested page size of zero, a negative value, or more than 100 must follow the
  product's defined validation or clamping behavior without creating an unbounded read.
- Filters with no matches, matches only after the first page, equal sort values,
  boundary dates, and Decimal amount/quantity boundaries must remain correct.
- The control tenant may have overlapping human-readable order or document numbers;
  isolation must rely on tenant scope and opaque identity rather than those numbers.
- Timing variance may change observed durations but must not change dataset cardinality,
  coverage, correctness, or boundedness outcomes.
- Unsupported future business flows must be omitted and reported, never fabricated to
  make the dataset appear production-complete.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The benchmark MUST provide a deterministic dataset with at least 10,000
  distinct orders dated within one business day, a recorded non-trivial line
  distribution, and currently supported related Evidence and Reality records sufficient
  to exercise every core register family.
- **FR-002**: Dataset setup MUST report its seed, business date, tenant identity,
  cardinality by relevant record type, and completion state, and repeated setup MUST
  neither silently duplicate nor ambiguously reuse partial data.
- **FR-003**: The benchmark MUST exercise Orders, Commitments, Inventory, Reservations,
  Movements, Open items, Payments, Journal, and Documents through their product read
  boundaries with representative unfiltered, searched, filtered, sorted, counted, and
  multi-page cases wherever the register supports those operations.
- **FR-004**: Every measured register response MUST return 50 rows by default and MUST
  not return more than 100 rows. Option and inspector endpoints are not exercised by
  this nine-register catalog and retain their separate Web contract coverage.
- **FR-005**: Every tested search and filter MUST be applied to the tenant-scoped result
  before pagination, and every reported total MUST count the complete filtered result.
- **FR-006**: Every tested register MUST use stable ordering that produces repeatable,
  non-overlapping adjacent pages when primary sort values are equal.
- **FR-007**: Aggregates and dashboard values included in benchmark coverage MUST be
  computed from the complete tenant-scoped filtered set and MUST NOT be derived from the
  visible page length or sum.
- **FR-008**: The benchmark MUST include a separately populated control tenant and MUST
  fail if any covered large-tenant row, count, aggregate, or search result contains
  control-tenant data. Option and inspector endpoints are outside this catalog.
- **FR-009**: The evidence MUST demonstrate that high-cardinality filtering, counting,
  sorting, aggregation, and pagination occur in the data-store query rather than after
  unbounded business-record materialization.
- **FR-010**: One documented benchmark entrypoint MUST perform prerequisite validation,
  dataset validation, all required cases, and report generation, and MUST return a
  failing outcome if any required stage or assertion fails.
- **FR-011**: Each result MUST record the tested git revision, schema revision,
  environment description, dataset definition and seed, record cardinalities, covered
  cases, per-case durations, pass/fail outcome, and explicit limitations.
- **FR-012**: Repeat runs with the same revision, dataset definition, seed, and
  environment MUST retain identical required cases, cardinalities, expected counts, and
  correctness outcomes; timing is observational and may vary.
- **FR-013**: Normal fast quality gates MUST verify benchmark correctness on a reduced
  dataset, while the full 10,000-order proof MUST be explicitly runnable and retained as
  reviewable acceptance evidence without making every fast test generate the full set.
- **FR-014**: Completion MUST update `016/FR-015` and `016/SC-007` from documented gap to
  verified evidence and cite the accepted benchmark result.
- **FR-015**: Completion MUST update the production-shaped ecommerce capacity idea to
  reference this baseline, identify reusable dataset/runner/reporting artifacts, and
  preserve an explicit boundary between proven large-cardinality reads and the unproven
  100,000-orders/day mixed operational workload.

### Domain and Traceability Requirements

- **DR-001**: Generated business data MUST preserve SourceRecord → Document/DocumentLine
  → applicable Fact/Commitment/Reservation/Movement/LedgerEntry traceability; flows that
  are not currently supported MUST remain absent and documented.
- **DR-002**: Benchmark records MUST use opaque identity and the shortest true
  relationships, and operational state MUST remain derived from Reality rather than
  duplicated onto Documents.
- **DR-003**: All benchmarked reads MUST call the same tenant-scoped application
  services or query boundaries used by Web and other product interfaces; benchmark-only
  direct business reads MUST NOT establish a separate truth path.
- **DR-004**: Benchmark setup MUST not expand the business schema or type upstream data
  solely to make dataset generation or measurement convenient.
- **DR-005**: SourceRecords used by the dataset MUST remain immutable and deterministic
  retries or changed external input MUST retain the established versioning semantics.

### Key Entities *(when data is involved)*

- **Benchmark Dataset Definition**: The versioned description of seed, business date,
  order/line distribution, supported flow mix, control-tenant sentinels, and expected
  record cardinalities.
- **Benchmark Case**: One named register operation with inputs, expected count/page or
  aggregate, required query-boundary properties, and an observed duration.
- **Benchmark Result**: The immutable review artifact that binds a tested revision and
  environment to its dataset, executed cases, outcomes, timings, and limitations.
- **Benchmark Tenant**: The isolated company context containing the large-cardinality
  dataset; it has no privileged business behavior.
- **Control Tenant**: A second company context containing distinguishable sentinel data
  used only to prove isolation of all benchmark outcomes.

## Success Criteria *(mandatory)*

- **SC-001**: A clean supported environment can produce a validated dataset containing
  at least 10,000 distinct orders on one business date and execute all required cases
  from one documented benchmark entrypoint.
- **SC-002**: Two consecutive runs against the same completed dataset report identical
  case coverage, record cardinalities, expected totals, page identities, and pass/fail
  outcomes.
- **SC-003**: One accepted full run covers all nine core register families and reports
  zero responses above 100 rows, zero unstable adjacent-page results, zero incorrect
  filtered totals or covered aggregates, and zero control-tenant observations.
- **SC-004**: Every high-cardinality benchmark case has reviewable evidence that tenant
  restriction, search/filter, count or aggregate, stable ordering, and page bound are
  applied before result materialization as applicable.
- **SC-005**: The benchmark report contains 100% of the required reproducibility fields
  and clearly states that its durations are observations rather than universal latency
  guarantees.
- **SC-006**: Reduced-dataset contract tests pass in the normal fast suite, and the full
  acceptance run is separately reproducible without changing business behavior.
- **SC-007**: `016/FR-015` and `016/SC-007` cite the accepted result as verified, while
  the 100,000-orders/day capacity idea explicitly retains all throughput, concurrency,
  recovery, resource, soak, and cloud-sizing work not proven here.
- **SC-008**: Every FR and DR has an acceptance scenario and executable proof or an
  explicitly reviewed evidence rationale in the plan and tasks.

## Assumptions and Dependencies

- The 10,000-orders/day contract is a data-cardinality and bounded-read contract; it is
  not an order-ingestion throughput promise.
- PostgreSQL is the only supported database and is required for the accepted full run.
- Existing core-register behavior and `docs/WEB_SPEC.md` define the expected filters,
  counts, page bounds, ordering, and complete-result aggregates.
- The benchmark may use supported deterministic setup fixtures outside the measured
  read cases when their method and exclusion from timings are explicit.
- A reduced dataset is sufficient for fast contract regression; only the separately
  documented acceptance run must contain at least 10,000 orders.
- Per-case durations are recorded to expose regressions and inform later targets, but
  this feature has no owner-approved hardware-independent latency threshold.
- The later production-shaped capacity idea remains a brainstorming document rather
  than an approved implementation specification.

## Open Questions

No unresolved product questions remain. The authoritative Web contract defines the
register catalog and bounds, and the distinction between this read-cardinality proof
and the later 100,000-orders/day production-shaped capacity initiative is explicit.
The product owner approved this specification on 2026-09-02.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-002, DR-001–DR-002, DR-004–DR-005 | US1.1, edge cases | Deterministic dataset contract and cardinality validation |
| FR-003, FR-010, FR-012–FR-013 | US1.2–US1.4 | Reduced regression plus two-run full benchmark evidence |
| FR-004–FR-009, DR-003 | US2.1–US2.5 | Register result assertions, control tenant, and query-boundary evidence |
| FR-011 | US3.1 | Benchmark result schema and accepted report inspection |
| FR-014–FR-015 | US3.2 | Baseline evidence ledger and capacity-idea boundary review |
| SC-001–SC-008 | US1–US3 | Automated contracts, accepted full run, and final traceability review |
