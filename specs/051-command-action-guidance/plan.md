# Implementation Plan: Command Action Guidance

**Branch**: `051-command-action-guidance` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Enrich each validated workspace Action with the canonical `effect` of its referenced Command. Render that description in the complete Action launcher and the shared Action form, keep prerequisites distinct, and localize the resulting guidance without changing mutation services or confirmation behavior.

## Technical Context

**Language/Version**: Python 3.12+ and TypeScript 5  
**Primary Dependencies**: PyYAML, FastAPI, React/Vite, Tailwind CSS  
**Storage**: Existing PostgreSQL application; no schema or persistence changes  
**Testing**: pytest catalog/HTTP tests; Node frontend contracts; strict i18n audit; TypeScript/Vite build  
**Project Type**: Shared Python catalog/API plus independent Product Web  
**Constraints**: Command catalog owns effects; workspace composer validates and enriches; UI presents only; existing explicit mutation confirmation remains intact  
**Scale/Scope**: Thirteen classified Action definitions across five workspaces and four UI languages

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | No domain record or mutation path changes. | PASS |
| Reality owns operational state | Descriptions are presentation metadata and add no document status. | PASS |
| Proven schema only | No table, field, relationship, migration, or backfill is introduced. | PASS |
| Shared service boundaries | Command effects come from the shared application catalog; Web does not define business behavior. | PASS |
| Mutation governance | Existing review and explicit confirmation stay mandatory. | PASS |
| Spec/test traceability | Catalog, API-shape, frontend, localization, build, and visual checks map to the requirements. | PASS |
| Explainable Web behavior | Users see the intended effect before selecting and confirming a mutation. | PASS |

Planning may continue: every row is PASS and no exception is requested.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/catalogs.py
packages/reality-core/tests/test_application_catalog.py
packages/reality-core/tests/test_http_boundary.py
apps/web/src/api.ts
apps/web/src/App.tsx
apps/web/src/localization.tsx
apps/web/src/tailwind.css
apps/web/scripts/workspace-actions-contract.test.mjs
specs/051-command-action-guidance/
```

No domain, service, tool, storage, or migration changes are required. The validated catalog is enriched before the existing application-reference adapter returns it; the browser consumes the typed field.

## Design

### Catalog flow

`Command.effect → validate_workspace_catalog → WorkspaceAction.description → application-reference → Product Web`. Validation rejects absent or blank effects for classified Actions. Workspace YAML does not duplicate command prose.

### Interaction flow

The searchable launcher indexes label, description, and prerequisites. Each result renders label, description, and an optional `Requires: …` line. Selecting either a direct Action or launcher result opens the existing shared form with the same description below its title. Review and confirmation behavior does not change.

### Localization and layout

The existing translation function localizes the catalog description with English fallback. The thirteen currently classified command effects and the `Requires` label receive German, Dutch, and Spanish entries. Shared Tailwind primitives provide wrapping and hierarchy on desktop and mobile.

## Test Strategy and Traceability

| Requirement | Test level | Planned proof |
|---|---|---|
| FR-001-FR-002 | catalog unit | Enrichment equality and missing/blank effect rejection |
| FR-003-FR-008 | frontend contract | Description rendering, separate prerequisites, description search, shared form propagation, confirmation preservation |
| FR-001, FR-006 | HTTP boundary | Application reference exposes the enriched description |
| FR-009 | localization/build | Four-language audit and production build |
| FR-010 | diff/full suite | No schema/service/executor changes and existing suites remain green |

Tests are written and observed failing before implementation where practical.

## Rollout and Rollback

The response field is additive and derived. Older browser clients ignore it. Rollback removes enrichment and presentation with no business-data change.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
