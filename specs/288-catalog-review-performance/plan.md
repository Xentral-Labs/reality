# Implementation Plan: Shared Runtime Catalog

**Branch**: `spec/288-catalog-review-performance` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Reuse the existing validated, process-local application catalog as the single runtime metadata
authority. Add a bounded section accessor so services can copy only the immutable section they
need, migrate every eligible production service/tool that currently invokes the raw catalog
builder, and retain the raw builder for validation, generation and tests. Strengthen initialization
so concurrent first callers cannot publish partial state or perform duplicate successful builds.
No adapter cache, business-response cache, schema or infrastructure is introduced.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: Python standard-library synchronization/caching primitives; existing
catalog loader, FastAPI, Typer and MCP adapters
**Storage**: No persistence; immutable deployment metadata remains source-controlled files
**Testing**: pytest unit/service/HTTP/MCP parity plus a repeatable local service benchmark
**Project Type**: shared backend package consumed by API, MCP, CLI and Web through services/tools
**Constraints**: one validated snapshot per process; isolated returned values; failed builds retry;
mutable business and tenant state never enters the snapshot
**Scale/Scope**: Five eligible production raw-builder call sites plus the canonical builder call;
twenty sequential Proposal Review reads for the acceptance benchmark

## Constitution Check _(blocking gate)_

| Principle                          | Evidence in this plan                                                                                               | Result |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------ |
| Source → Evidence → Reality        | Metadata reuse creates no record and changes no evidence or Reality link.                                           | PASS   |
| Reality owns operational state     | Proposal, attribution and all business state remain fresh service reads; metadata never becomes operational state.  | PASS   |
| Proven schema only                 | No schema, migration, backfill or persisted cache.                                                                  | PASS   |
| Tenant + shared service boundaries | The snapshot contains deployment metadata only; API/MCP/Web/CLI keep calling tenant-scoped shared services/tools.   | PASS   |
| Spec/test traceability             | [Spec traceability](spec.md#requirement-traceability) maps every FR/DR; this plan names executable proof below.     | PASS   |
| Explainable web behavior           | Review fields and trace remain unchanged; only metadata acquisition is accelerated beneath the service boundary.    | PASS   |
| Received values not recomputed     | No received or derived business value changes; only descriptive deployment metadata is reused.                      | PASS   |
| Smallest coherent design           | Extend the existing runtime snapshot and migrate five callers; reject transport caches and external infrastructure. | PASS   |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/catalogs.py
packages/reality-core/src/reality/services/core.py
packages/reality-core/src/reality/services/proposal_reviews.py
packages/reality-core/src/reality/storyline/package.py
packages/reality-core/src/reality/tools/application.py
packages/reality-core/tests/test_application_catalog.py
packages/reality-core/tests/test_proposal_review_parity.py
packages/reality-core/tests/test_capability_guidance.py
packages/reality-core/tests/test_http_boundary.py
packages/reality-core/tests/test_ai_mcp.py
packages/reality-core/src/reality/benchmarks/proposal_review.py
docs/ARCHITECTURE.md
```

**Files/layers affected**: `reality.catalogs` owns raw construction, validation, the process-local
snapshot, bounded copied reads and explicit clearing. Services and tools depend inward on that
catalog boundary. Web/API/MCP/CLI adapters receive the benefit through existing services/tools and
gain no cache implementation. Tests cover the boundary, representative consumers and adapters.

## Design

### Reality flow

No Source, Evidence or Reality record is created or modified. `ChangeProposal` remains the shortest
true record for decision review. Application-reference metadata describes executable vocabulary
and never becomes a second authority for tenant or business state.

### Service and adapter flow

`load_application_catalog()` remains the explicit fresh builder used by validation, generators and
tests. The existing runtime catalog boundary becomes concurrency-safe and remains failure-retryable.
`runtime_application_catalog()` continues returning an isolated full copy for external reference
reads. A bounded section accessor returns an isolated copy of only the requested section for
services/tools, avoiding a deep copy of unrelated sections.

Eligible production consumers migrate as follows:

1. `catalogs.catalog_code()` reads runtime `commands`, `projections` and `workspaces` sections.
2. `services.core._fact_contract()` reads runtime `fact_predicates`.
3. `storyline.package.catalog_index()` derives its own cached index from runtime sections rather
   than invoking the raw builder again.
4. `tools.application._capability_describe()` reads runtime `capability_guidance`.
5. `services.proposal_reviews.proposal_next_step()` reads runtime `capability_guidance`.

The only production call to the raw builder after migration is the canonical runtime snapshot
initializer. Direct test and generation calls remain intentional and are covered by the caller
inventory.

### Data and migration impact

No database table, field, migration, payload, public API or stored value changes. The process-local
snapshot is rebuilt naturally at process restart and may be explicitly cleared by the existing
development/test reset function.

### Failure, security, and tenant behavior

Initialization completes under one process-local synchronization boundary. A snapshot becomes
visible only after full validation and enrichment. Exceptions leave no successful snapshot, so a
later call retries. Callers receive deep-copied full catalogs or sections and cannot corrupt shared
state. Proposal not-found, cross-tenant behavior, authorization, confirmation and rejection are
unchanged because they remain outside the cache.

## Test Strategy and Traceability

| Requirement                   | Test level             | Planned test                                                                                                                        | Expected initial failure                                                                         |
| ----------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| FR-001, FR-006–FR-008, FR-012 | unit                   | Extend `test_application_catalog.py` for one concurrent successful build, isolated section copies, failure retry and clear/rebuild. | Current `lru_cache` can perform duplicate concurrent builds and has no bounded section accessor. |
| FR-002, DR-004                | source/service/adapter | Add a production caller inventory assertion and representative HTTP/MCP/direct-tool parity assertions.                              | Eligible services currently import the raw builder directly.                                     |
| FR-003, FR-005                | service                | Extend `test_proposal_review_parity.py` across proposed, decided, malformed, retired and changed-state reads.                       | `proposal_next_step()` currently reconstructs the catalog.                                       |
| FR-003, FR-009                | unit                   | Preserve raw-builder validation tests and prove explicit fresh builds remain independent of the runtime snapshot.                   | A broad replacement could accidentally force validators through cached data.                     |
| FR-003, FR-010                | unit/service           | Cover fact contract, capability description, catalog code and storyline index against runtime sections.                             | These production paths currently use raw builds or independent catalog caching.                  |
| FR-011, SC-001                | benchmark              | Add and run `python -m reality.benchmarks.proposal_review` for 20 warmed service reads and p95 ≤ 200 ms.                            | Current measured review is approximately 1.54 s.                                                 |
| DR-001–DR-003                 | architecture/service   | Review no-schema diff, tenant-isolation tests and unchanged proposal relationships.                                                 | A wrongly scoped cache could retain tenant or business state.                                    |

## Rollout and Rollback

Land tests first, then the central concurrency-safe runtime accessor, then migrate consumers one by
one. Startup already initializes the runtime catalog for the API, so deployment behavior remains
compatible. Other processes initialize lazily on their first catalog-backed call. The benchmark
prints build count, individual durations and p95 for review evidence. Rollback is a code revert;
there is no persisted state or migration to undo.

## Review Risks

- Returning a shared mutable object would let one consumer corrupt metadata for all others; every
  public accessor must preserve copy isolation.
- A naive lock around an `lru_cache` miss can still serialize two duplicate builds because both
  calls have already missed; the design must publish and re-check state inside one boundary.
- Replacing raw builds indiscriminately would weaken catalog validation and generator tests; the
  caller inventory must distinguish runtime reads from explicit fresh builds.
- Copying the full catalog for narrow service reads could meet correctness but miss the latency
  goal; bounded section copies are required and benchmarked.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
| ---------------------- | ---------- | ---------------------------- | -------- |
| None                   | —          | —                            | —        |
