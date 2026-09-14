# Implementation Plan: Canonical Core Catalogs

**Branch**: `007-core-catalogs` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

## Summary

Split the mixed catalog into four YAML authorities and keep one Python composition
service. Add AST Event completeness, runtime Projection completeness, explicit public
Command registration, and an initially empty Fact-predicate vocabulary. Serve the
composition through the authenticated tenant API and render it in Processing.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React  
**Dependencies**: PyYAML, AST/introspection, SQLAlchemy metadata, FastAPI, React/Vite;
no new dependency  
**Storage**: Reviewed YAML; no database connection required  
**Testing**: pytest unit/API, frontend build, spec policy and lint  
**Constraints**: Offline deterministic validation; catalogs never become business state  
**Scope**: 28 Commands, 37 known literal Events, 13 Projections, explicit Fact predicates

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Catalogs explain existing flow and create no records | PASS |
| Reality owns operational state | Commands retain authoritative reads; Projections are non-authoritative | PASS |
| Proven schema only | No schema or migration change | PASS |
| Tenant + shared service boundaries | Read-only service and authenticated API; no ORM write | PASS |
| Spec/test traceability | FR/DR mapping below; tests precede implementation | PASS |
| Explainable web behavior | Processing consumes canonical Projection explanations | PASS |
| Smallest coherent design | Four YAML files and one loader; no generator framework | PASS |

Post-design review remains PASS with no Constitution exception.

## Repository Structure and Layer Changes

```text
backend/config/{command,business_event,projection,fact}_catalog.yaml
backend/src/reality/catalogs.py
backend/src/reality/web/application_catalog.py
backend/src/reality/web/api.py
backend/tests/test_application_catalog.py
frontend/src/api.ts
frontend/src/App.tsx
docs/ARCHITECTURE.md
docs/features/operational_fields.md
```

The existing web module becomes a compatibility facade; composition moves outside the
transport package.

## Design

### Reality flow

```text
Command → Source/Evidence/Reality transaction → BusinessEvent
                                               ↓ checkpoint progress
                                         Projection rebuild/read
```

Catalogs only describe this flow. Fact definitions describe stable predicate semantics;
individual Facts remain tenant-scoped Reality.

### Service and adapter flow

`load_application_catalog()` loads four resources, enriches Command signatures,
validates category contracts, and returns JSON-safe composition. The tenant API calls
it after membership authorization. The frontend renders Projection explanations.

- Commands: YAML membership explicitly defines the public use-case boundary.
- Events: AST scans literal `emit_business_event(...)` calls and compares types both ways.
- Projections: `materialized_as` values equal `OPERATIONAL_PROJECTIONS`; aliases do not
  create extra canonical entries.
- Facts: stable registered predicates are compared when introduced; empty is valid now.

### Data and migration impact

No schema, migration, or stored data change. The combined YAML is removed after
lossless migration. Rollback restores it and the old facade/frontend list.

### Failure, security, and tenant behavior

Validation fails closed with category and names and needs no network/database. The
endpoint reuses tenant membership but returns only global metadata. It is read-only.

## Test Strategy and Traceability

| Requirement | Test | Expected initial failure |
|---|---|---|
| FR-001–FR-006, FR-014 | composition/category tests in `backend/tests/test_application_catalog.py` | split files absent |
| FR-007 | invalid fixture tests | incomplete coverage accepted |
| FR-008 | AST event coverage | four Events omitted |
| FR-009 | Projection registry coverage | no two-way check |
| FR-010 | explicit Command contract | public boundary implicit |
| FR-011 | offline application/data-model load | database URL currently required |
| FR-012, DR-003 | authenticated API test and frontend build | endpoint/client absent; list hard-coded |
| FR-013 | documentation review | workflow absent |
| DR-001–DR-005 | focused and full regression suites | guardrails not executable |

## Rollout and Rollback

Land split, loader, tests, endpoint, and client atomically. Preserve the Python import
path. Rollback is file-only because no persistence changes.

## Review Risks

- Dynamic Event names require explicit registration instead of silent omission.
- “Public Command” must remain explicit and not be inferred from helpers.
- Existing dirty frontend work requires narrow edits.
- Selective Event-driven workers remain out of scope; current reads may rebuild all
  Projections after any new Event.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

