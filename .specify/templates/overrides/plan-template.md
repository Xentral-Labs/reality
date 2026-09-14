# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Language**: English for all repository artifacts and review evidence.

## Summary

[Requirement and smallest coherent technical approach]

## Technical Context

**Language/Version**: Python 3.12+; TypeScript where frontend is in scope
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite as applicable
**Storage**: PostgreSQL; immutable object storage only for proven source binaries
**Testing**: pytest business stories/integration/unit; frontend build and focused UI tests
**Project Type**: backend services/API/CLI plus independent frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope
**Scale/Scope**: [Bounded feature scope]

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | [links/flow or N/A reason] | PASS/FAIL |
| Reality owns operational state | [derivation, no document status] | PASS/FAIL |
| Proven schema only | [business calculation/use case or no schema change] | PASS/FAIL |
| Tenant + shared service boundaries | [query and adapter path] | PASS/FAIL |
| Spec/test traceability | [FR → scenario → test] | PASS/FAIL |
| Explainable web behavior | [inspect/trace path or N/A] | PASS/FAIL |
| Received values not recomputed | [values taken as received, or why a derivation is an observation] | PASS/FAIL |
| Smallest coherent design | [simpler alternatives considered] | PASS/FAIL |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/domain/       # pure rules, if needed
packages/reality-core/src/reality/services/     # application behavior
packages/reality-core/src/reality/tools/        # shared agent/CLI tools
packages/reality-core/src/reality/web/          # transport only
packages/reality-core/tests/                    # unit, service, story, adapter proof
apps/web/src/                     # presentation only
```

**Files/layers affected**: [Exact paths and dependency direction]

## Design

### Reality flow

[Source → Evidence → Reality records and shortest links]

### Service and adapter flow

[Shared application service and all callers]

### Data and migration impact

[No schema change, or proven fields/constraints/backfill/rollback]

### Failure, security, and tenant behavior

[Not-found behavior, rollback, idempotency, confirmation]

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story/service/unit | [path/name] | [reason] |

## Rollout and Rollback

[Compatibility, migration order, observability, rollback]

## Review Risks

- [Highest semantic, tenancy, data, or UI risk]

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
