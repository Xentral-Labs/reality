# Implementation Plan: CEO Contribution Analytics Templates

**Branch**: `244-ceo-contribution-templates-refresh` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

## Summary

Declare four localized contribution questions in the existing reporting graph and validate context-dependent templates with a non-runnable placeholder only during model loading. The browser already refuses to execute a contribution question without a selected review/capture/company context and exposes the existing selector; preserve and test that boundary.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React in the existing adapter
**Primary Dependencies**: Pydantic v2, SQLAlchemy 2, React/Vite
**Storage**: PostgreSQL; no schema or stored-data change
**Testing**: pytest graph tests; focused Node web test; frontend build
**Project Type**: shared reporting service plus React frontend
**Constraints**: Decimal; explicit cost context; currency/base-unit axes; tenant scope; no browser business rules
**Scale/Scope**: Four static templates and one load-time validation allowance

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Templates read the existing retained contribution relation; no lineage changes. | PASS |
| Reality owns operational state | Questions expose derived observations only. | PASS |
| Proven schema only | No schema or persistence is added. | PASS |
| Tenant + shared service boundaries | Execution remains tenant-scoped `graph.ask`. | PASS |
| Spec/test traceability | FR/DR mappings have declaration, execution, and browser tests. | PASS |
| Explainable web behavior | Coverage and the explicit cost-basis selector remain visible. | PASS |
| Received values not recomputed | Canonical contribution service retains all calculations. | PASS |
| Smallest coherent design | Reuses one catalog and selector; no dashboard, endpoint, or calculation. | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/config/reporting_graph.yaml
packages/reality-core/src/reality/services/analytics/graph_model.py
packages/reality-core/tests/test_reporting_graph_declaration.py
packages/reality-core/tests/test_reporting_graph_traversal.py
apps/web/scripts/analysis-chat-workflow.test.mjs
specs/244-ceo-contribution-templates/
```

No domain calculation, database, MCP schema, command, view, projection, exception, or event changes.

## Design

### Reality flow

The selected confirmed population pins reviewed revenue, inventory consumption, and selling-cost evidence. A template contributes only grouping, measures, ordering, and period meaning. Execution reads the existing contribution relation and creates no authority.

### Service and adapter flow

`reporting_templates()` publishes the declarations. Model loading validates a contribution template by supplying a sentinel context to the pure planner only; the published question remains context-free. `GraphTemplates` adopts it. `GraphSteps.execute()` stops before the API while context is absent and renders the existing selector. Selection adds explicit context and triggers the normal query.

### Data and migration impact

None. No migration, backfill, fixture version, or persisted template record.

### Failure, security, and tenant behavior

The sentinel exists only during model validation and is never returned or executed. Runtime still rejects missing, foreign, and unavailable contexts. Removing the declarations and validation allowance is a data-free rollback.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-010 | declaration | exact keys and EN/DE copy | keys absent |
| FR-002, FR-005-FR-009, DR-001-DR-004 | service/story | execute each shape with confirmed fixture | declarations absent |
| FR-003, FR-004 | browser contract | no ask before selector choice | contract absent |
| FR-011 | graph validation | context-dependent template resolves | context-required refusal |
| FR-012 | regression | existing graph/web suites and build | drift if introduced |

## Rollout and Rollback

Backward-compatible catalog addition. Existing consumers receive four entries. Saved reports remain valid because templates are not persisted answers.

## Review Risks

- Load-time accommodation accidentally weakens runtime context enforcement.
- Required axes are omitted.
- Leakage ordering implies unknown DB2 is zero.
- Trend copy overstates history beyond the selected retained population.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
