# Implementation Plan: Controlled Fact Observation

**Branch**: `042-observe-facts` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Tighten the existing Fact write service into an atomic, tenant-scoped, source-required and idempotent observation operation. Validate predicate, subject type, subject existence, and canonical value through the machine-readable predicate catalog. Register the operation as a confirmation-required application tool and MCP/Chat proposal while retaining the existing Fact read/Inspector path. Typed domain commands continue emitting their existing Business Events and do not mirror state into Facts.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI application tooling
**Storage**: Existing `fact`, `source_record`, subject tables, `action`, and `business_event`; one additive Fact retry-identity column/index
**Testing**: pytest unit, service, business-story, MCP catalog, PostgreSQL migration, and catalog validation tests
**Project Type**: backend services/API/MCP/Chat with existing independent frontend reader
**Constraints**: UTC; opaque IDs; lossless source; strict tenant scope; append-only Facts; confirmed agent mutations
**Scale/Scope**: One observation per command; bounded predicate vocabulary; no source-specific interpreter or UI mutation form

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Every new Fact requires a same-tenant immutable SourceRecord; optional Document stages are not duplicated. | PASS |
| Reality owns operational state | Facts remain observations; typed operational commands do not write mirror Facts. | PASS |
| Proven schema only | Retry identity is required to prove exactly-once observation; predicate vocabulary starts with the existing Shopify priority scenario. | PASS |
| Tenant + shared service boundaries | Service validates source and subject tenancy; tool, MCP, and Chat share one operation and confirmation boundary. | PASS |
| Spec/test traceability | Every FR/DR maps to service, catalog, proposal, provenance, migration, or regression tests below. | PASS |
| Explainable web behavior | Existing Facts register and Inspector expose the Fact and original Source payload; no browser business rule is added. | PASS |
| Smallest coherent design | Reuses Fact, ChangeProposal, BusinessEvent, catalogs, and Inspector; adds one column and one tool. | PASS |

Planning may proceed: all rows pass and no Constitution exception is requested.

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/          # Fact request fingerprint migration
packages/reality-core/src/reality/db/core.py        # additive retry identity
packages/reality-core/src/reality/services/core.py  # predicate/subject validation and atomic observation
packages/reality-core/src/reality/tools/application.py # shared observe tool
packages/reality-core/src/reality/mcp/catalog.py     # typed proposal schema
packages/reality-core/config/                       # predicate, command, and data-model contracts
packages/reality-core/tests/                        # service/story/catalog/MCP/migration proofs
docs/DATA_MODEL.md                                  # durable Fact boundary
docs/features/chat.md                               # agent proposal behavior
```

**Dependency direction**: Chat/MCP → ChangeProposal → application tool → observation service → Fact + BusinessEvent. Catalog validation is consumed by the service; transports contain no Fact semantics.

## Design

### Reality flow

An existing SourceRecord retains the lossless input. A source-specific parser, human, or agent may propose one cataloged observation about an existing opaque Reality subject. Confirmation invokes the shared tool, which stores one append-only Fact linked directly to SourceRecord and emits `fact.observed` in the same transaction. Creating typed operational Reality from that observation is a separate explicit command.

### Service and adapter flow

- Load and validate the predicate vocabulary from `fact_catalog.yaml`.
- Resolve the declared subject type through a deliberately bounded mapping to existing tenant-scoped model classes.
- Canonicalize the value according to the predicate's `string`, `date`, `datetime`, `integer`, `decimal`, `boolean`, or `enum` contract and serialize it deterministically.
- Compute a request fingerprint from tenant plus caller idempotency key and store it with a tenant-scoped uniqueness constraint.
- A repeated fingerprint with identical canonical content returns the existing Fact; different content raises an idempotency conflict.
- Register `fact_observe` as a mutating application tool and `fact_observe_propose` as its typed MCP/Chat proposal.
- Proposal confirmation uses the existing approval executor; no adapter writes through SQLAlchemy.

### Data and migration impact

Add nullable `request_fingerprint` to `fact` with a unique `(tenant_id, request_fingerprint)` constraint. It remains nullable so historical rows stay readable; the new observation service always supplies it. `source_record_id` remains physically nullable for compatibility but is mandatory in the new-write service. Rollback drops the constraint and column without changing historical Fact contents.

No value column migration is needed. Canonical scalar text is stored in the existing text column, and the catalog describes its logical type. This is smaller, keeps the register readable, and is backward compatible.

### Failure, security, and tenant behavior

- Foreign source and subject IDs behave as not found.
- Validation completes before a Fact or success event is flushed.
- Fact and event share one commit; failure rolls both back.
- Proposal rejection or lack of confirmation never calls the mutation tool.
- Unknown predicates and unsupported subject types fail closed.
- Secrets and model reasoning are never accepted as Fact values by implication; the caller submits only the explicit proposed scalar.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-007 | service/PostgreSQL | `tests/test_fact_observation.py` | Current service allows absent sources, lacks catalog validation and idempotency. |
| FR-008–FR-010 | MCP/story | `tests/test_mcp_fact_observation.py`, `tests/test_mcp_chat.py` | No observation tool or proposal schema exists. |
| FR-011 | API/Inspector | extend `tests/test_master_data_api.py` | Read path exists but new-write trace is unproven. |
| FR-012 | catalog | extend `tests/test_application_catalog.py` | Predicate catalog is empty and command absent. |
| FR-013 | regression | `tests/test_fact_observation.py` | Explicit zero-mirror behavior is unproven. |
| DR-001–DR-005 | story/tenant | provenance, subject, cross-tenant, adapter, and command regression tests | Complete boundary is uncovered. |

Tests are added and observed failing before implementation where practical.

## Rollout and Rollback

Run the additive migration before deploying application code. Existing Facts remain readable. Older application versions ignore the new column. Rollback application code first, then remove the unique constraint and column only if retry evidence is no longer required. No Fact is deleted or rewritten during either direction.

## Review Risks

- A loose subject registry could reintroduce human identifiers or cross-tenant links.
- Catalog/value drift could make an observation unreadable or non-idempotent.
- An inner commit could separate Fact persistence from its Business Event.
- Broad initial predicates could turn Fact into a second operational-state store.
- Existing `record_fact` callers must migrate to the strict contract without silently fabricating provenance.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Post-Design Constitution Re-check

All seven checks remain PASS after design: the single additive field proves retry safety; the SourceRecord and subject remain shortest links; all agent writes cross the existing confirmation boundary; typed Reality remains authoritative.
