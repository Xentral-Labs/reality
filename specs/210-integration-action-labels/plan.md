# Implementation Plan: Visible integration actions

Date: 2026-09-16 | Spec: [spec.md](spec.md)

## Summary
Add an opt-in labeled action presentation to RegisterTable and enable it for source systems and received records. Reuse all handlers. No domain/service/tool changes; implementation is confined to the Web adapter.

## Technical Context
TypeScript, React, shared CSS, existing localization and Playwright HTTP fixtures. No dependencies, database or schema changes. Four localized labels and two tables.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Existing exact-source Inspector and Facts links retained | PASS |
| Reality owns operational state | No operational state changed | PASS |
| Proven schema only | No schema change | PASS |
| Tenant + shared services | Existing scoped handlers/reads retained | PASS |
| Spec/test traceability | FR-001–004 covered by browser proof below | PASS |
| Explainable web | Outcome labels expose existing trace paths | PASS |
| Received values | No value calculation | PASS |
| Smallest coherent design | One optional presentation prop, no new component or dependency | PASS |

Pre-design and post-design checks pass. User approved product scope; no constitutional exception.

## Repository Structure and Design
- `apps/web/src/unified/RegisterTable.tsx`: optional `actionPresentation` with default icons; labeled mode preserves button children and adds a scoped class. No clone-to-icon conversion for labeled actions.
- `apps/web/src/tailwind.css`: scoped labeled-action sizes override 24px/zero-font icon styling. On narrow screens labeled tables release the sticky first column so it cannot cover the actions. Fixed readable action-column widths keep labels usable under stored preferences and horizontal scrolling.
- `apps/web/src/unified/DataSourcesPage.tsx`: enable labels for systems and records with 300px/320px action columns; reuse Settings and Received data strings, add Open details; retain View observations. Evidence-document actions stay compact.
- `apps/web/src/localization.tsx`: translate Open details for all supported non-English languages.
- `apps/web/scripts/unified-sources-browser.mjs`: first add failing visible-text proof, then cover all four destinations, keyboard/focus, languages/themes/widths/densities and zero mutations.
- `apps/web/scripts/unified-source-configuration-browser.mjs`: update row settings label selectors.
- `docs/WEB_SPEC.md`: document the bounded labeled-action exception.

Source records, source configuration and Facts keep existing opaque identity, tenant context, filters and recovery. No migration or backend test additions are justified for this presentation-only change.

## Test Strategy and Traceability

| Requirement | Proof | Initial failure |
|---|---|---|
| FR-001 | sources browser: two visible source labels, dialog and filtered records | hidden icon children / old label |
| FR-002 | sources browser: visible record labels, Inspector and exact-source Facts | hidden icon children / old label |
| FR-003 | sources browser: rendered label bounds, four languages, both densities, 390/1440px and both themes | icon-only buttons |
| FR-004 | sources and source-configuration browser tests; existing contracts and table browser regression | destinations already pass; presentation regression protected |

Required focused gates: sources, source-configuration and table browser scripts; `make web-build`, `make spec-check`, `make lint`, `make test`, documentation catalog check. Record environmental or unrelated failures without claiming completion.

## Rollout and Rollback
Ordinary frontend deployment; no migration. Revert the new prop usage, styling and labels to roll back. Other pending workspace edits must remain untouched.

## Review Risks
CSS specificity, localization width, and modifying a shared table with unrelated pending edits. Review scoped diffs and browser screenshots.

## Complexity Tracking
None.
