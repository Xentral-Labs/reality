# Implementation Plan: Business analysis coverage

## Technical Context
Python 3.12, Pydantic, SQLAlchemy/PostgreSQL, existing declarative reporting graph;
React/TypeScript explorer. No dependency, migration or business write change.
Keep model_version sales.1: all old keys retain meaning; new keys are additive.

## Constitution Check
| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Read existing records and actual identity FKs |
| Operational authority | PASS | No state fields or alternate inventory/finance calculations |
| Proven schema | PASS | No schema expansion |
| Tenant/service boundaries | PASS | Shared traversal compiler and catalog, scoped subqueries |
| Specification/testing | PASS | Approved audit scope, tests before model changes |
| Explainable UI | PASS | Named grouped objects, preserved query traceability |
| Simplicity | PASS | Declarative nodes/edges, two compiler correctness repairs |
| Received values | PASS | Amount columns preserved with signs/units |

## Design and Phases
1. Add regression tests for document-line parent scoping and reverse same-table edges.
2. Correct compile_sql._scope to apply declared parent constraints via tenant-scoped
   EXISTS; validate parent definitions. Select FK carrier by direction/multiplicity.
   Reuse the exact scope for observed filter values.
3. Extend reporting_graph.yaml with precise document subtype nodes, their lines,
   partner/terms/postings edges and recorded amount/count/quantity measures.
4. Declare reservations/holds, lots/serials/handling units, packages and explicitly
   historical shipment events/supersessions; supporting pricing/roles/groups/accounts.
5. Add optional category and search aliases to Node and the shared catalog/API type;
   group explorer navigation and native builder selection without a second vocabulary.
6. Update coverage exclusions and durable docs; run reporting, adapter, UI, catalog,
   lint/build/localization/spec gates and Chrome visual review.

## Files
`packages/reality-core/config/reporting_graph.yaml`, `domain/reporting_graph.py`,
`services/analytics/{graph_model,compile_sql}.py`, reporting tests;
`apps/web/src/{api.ts,localization.tsx,unified/analytics/DataExplorer.tsx}`,
`GraphSteps.tsx`, `AnalysisBuilder.css`; docs/features/analytics.md, docs/WEB_SPEC.md.

## Risks and Mitigation
Same-table subtypes must scope both root and joined lines. Currency and units cannot
be removed by new measure defaults. Preserve original invoice semantics. Shipment
history is not latest shipment state. No fabricated FK from polymorphic string IDs.
Existing declared service measures that are not executable are not new coverage.

## Validation and Rollback
Tests use an isolated PostgreSQL database; mixed-type and neighboring-tenant fixtures,
reverse billed-line traversal, fan-out totals and every declared node query. Full
reporting tests plus web contracts/build/i18n and generated reference checks. Rollback
reverts additive declarations/UI; reports using new keys then refuse explicitly.
No data migration or rollback operation.

Financial detail and evidence scope: include received financial components, opening scopes/items, generic evidence documents/lines, source-version metadata and historical additional facts. Raw payload inspection and mapping/assignment histories stay in the Inspector. These are existing records, not newly computed authorities.
