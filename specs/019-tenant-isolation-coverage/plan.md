# Implementation Plan: Complete Tenant Isolation Coverage

**Branch**: `[019-tenant-isolation-coverage]` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Close `003/FR-012` with one checked-in tenant-isolation catalog mapping the complete
public business surface to stable families, classifications, and named executable
proof. Add deterministic discovery for public tenant-aware callables and existing
projection/tool registries. Reuse and strengthen PostgreSQL stories through an
asymmetric two-tenant graph and behavior-specific read, collection, aggregate,
mutation, relationship, and adapter checks. Correct only defects proven by those tests;
add no schema or alternate business path.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML, pytest; existing FastAPI,
Typer, and application-tool boundaries for representative adapter evidence
**Storage**: Existing PostgreSQL schema; one source-controlled YAML evidence catalog;
no persisted runtime data or migration
**Testing**: PostgreSQL pytest service/business stories, deterministic catalog/discovery
tests, focused adapter tenant-context regressions, full backend suite and Ruff
**Project Type**: Backend business services with CLI, Web/API, Chat, and MCP adapters;
frontend is outside implementation scope
**Constraints**: Foreign reads indistinguishable from unknown IDs; atomic foreign-write
failure; opaque IDs; lossless SourceRecords; shared services; no schema expansion;
global tenant administration explicitly classified
**Scale/Scope**: Public business callables in `services/core.py`, `artifacts.py`,
`file_interpreters.py`, and `projections.py`; 13 registered projections; 13 application
tools; canonical catalog services; representative tenant-context adapters

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Two-tenant fixtures cover complete lineage; foreign traversal and relationships fail without rewriting source content. | PASS |
| Reality owns operational state | Existing Reality records and derived aggregates are tested; no operational state is added to Documents. | PASS |
| Proven schema only | No model, field, table, relationship, or migration; the catalog is evidence metadata only. | PASS |
| Tenant + shared service boundaries | Canonical proof targets tenant-explicit services; adapter checks prove context propagation without replacing service assertions. | PASS |
| Spec/test traceability | Each catalog family has classification and named pytest evidence; FR/DR mapping is validated by drift tests. | PASS |
| Explainable web behavior | Inspect/trace behavior is unchanged; foreign records remain non-disclosing and local lineage remains available. | PASS |
| Smallest coherent design | Existing services, registries, fixtures, and tests are reused; endpoint duplication and a runtime authorization framework are rejected. | PASS |

Post-design re-evaluation: PASS. The catalog contract, evidence model, and test harness
introduce no Constitution exception.

## Repository Structure and Layer Changes

```text
backend/
├── config/tenant_isolation_catalog.yaml       # family/classification/evidence authority
├── src/reality/
│   ├── catalogs.py                            # load and validate isolation catalog
│   └── services/*.py                          # only if failing proof finds a defect
└── tests/
    ├── tenant_isolation/
    │   ├── conftest.py                        # asymmetric two-tenant graph
    │   ├── coverage.py                        # catalog/discovery helpers
    │   └── test_families.py                   # behavior-specific family proof
    ├── test_application_catalog.py            # catalog validation/drift
    ├── test_application_tools.py              # tool registry/context proof
    └── test_master_data_api.py                # representative adapter propagation

specs/003-tenant-access/spec.md                 # close FR-012 last
docs/SPEC_COVERAGE_MATRIX.md                    # remove one accepted gap last
specs/019-tenant-isolation-coverage/            # design, tasks, evidence
```

**Files/layers affected**: Evidence metadata, catalog validation, and tests are planned.
Existing services may change only after a new failing scenario proves a violation of
`003/FR-010` or `003/FR-012`. No frontend, model, migration, generated artifact, or
adapter-specific business rule is planned.

## Design

### Reality flow

The fixture creates two complete but asymmetric graphs:

```text
Tenant A → Source A → Evidence A → Reality A → Ledger/Projection A
Tenant B → Source B → Evidence B → Reality B → Ledger/Projection B
```

Human-facing values overlap while opaque IDs and quantities/amounts differ. Local
traversal remains intact. Supplying B records under A must return not found, omit B from
lists/totals, or reject the relationship atomically. Source payloads remain unchanged.

### Service and adapter flow

The catalog groups public operations by shared behavior. Each entry has a stable key,
classification (`record_read`, `collection`, `aggregate`, `mutation_relationship`,
`boundary`, or `global_admin`), covered operation names, evidence, and authority/reason.

Discovery parses an explicit module set for top-level public callables with tenant
context. It also compares the catalog with `OPERATIONAL_PROJECTIONS`, `TOOLS`, and
services referenced by canonical command/projection catalogs. Indirect boundaries such
as demo seeding are explicitly listed. Private helpers stay private; excluded public-
looking operations need a catalog reason.

Behavior-specific tests exercise catalog families through shared services:

- record reads compare foreign-ID and unknown-ID failure type/message;
- collections/searches use foreign sentinels and overlapping human values;
- aggregates use asymmetric values so contamination cannot cancel out;
- mutations snapshot relevant rows, events, quantities, and balances in both tenants;
- tool and representative API checks prove selected tenant propagation.

Existing tests count only when their named scenario explicitly asserts the required
foreign behavior. Otherwise they are strengthened or a focused scenario is added.

### Data and migration impact

No business data or migration change. The YAML catalog is an evidence contract, not
tenant-owned runtime state. Fixtures use disposable PostgreSQL test databases.

Rollback reverts catalog, tests, any narrowly proven service correction, and baseline
evidence together. No data reversal is needed.

### Failure, security, and tenant behavior

- Foreign and random unknown IDs produce equivalent non-disclosing outcomes.
- Foreign records contribute zero to local rows, counts, balances, or projections.
- Cross-tenant writes fail before commit and leave both event streams unchanged.
- Global lifecycle/access operations require explicit authority and classification.
- Confirmation, membership, idempotency, immutability, and error semantics remain.
- Uncovered operations, stale entries, empty evidence, or broad exemptions fail with
  exact stable identifiers.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-003 | catalog/unit | discover configured modules/registries and require family, class, authority, and proof | No exhaustive catalog or discovery gate exists. |
| FR-004 | service | foreign ID equals unknown-ID `NotFound` behavior for record reads | Many families lack explicit foreign/unknown comparison. |
| FR-005 | story | two populated tenants prove collections, searches, projections, and totals | Current proof covers selected registers and sometimes an empty foreign tenant. |
| FR-006 | service | foreign mutations snapshot both graphs and prove zero side effects | Only selected commitment, handling-unit, ledger, proposal, and API writes have proof. |
| FR-007 | adapter | tools and representative API operations preserve shared-service tenant context | Existing adapter evidence is not mapped to exhaustive service authority. |
| FR-008–FR-010 | catalog/unit | uncovered, stale, invalid, and exempt fixtures fail deterministically | No drift validator exists. |
| FR-011 | regression | each discovered defect receives a failing test before shared-boundary correction | Unknown until the family suite runs. |
| FR-012 | documentation | baseline changes only after all gates and owner review | `003/FR-012` remains a gap. |
| DR-001–DR-006 | review/story | lineage, opaque IDs, no schema, shared service, and lossless payload review | No single cross-cutting evidence review joins these assertions. |

## Rollout and Rollback

Ship as one evidence/test change plus any narrowly required tenant fixes. The gate runs
in the normal PostgreSQL suite; no deployment ordering or runtime configuration exists.
Close the baseline gap last. A revert restores the catalog, tests, corrections, and
`003/FR-012` gap together.

## Review Risks

- Signature discovery can include helper-like functions or miss indirect tenant context.
- Broad grouping can claim evidence for an operation not actually exercised.
- Symmetric fixtures can hide aggregate leakage; measures must be non-cancelling.
- Safe adapters can hide leaking services; service evidence remains canonical.
- A universal parameterized test can become unreadable; use focused family factories.
- Closing `003/FR-012` early would overstate the baseline.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
