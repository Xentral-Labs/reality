# Implementation Plan

## Technical Context

React/TypeScript frontend, FastAPI and Python shared services, PostgreSQL. Delete
exclusive code; no new dependencies. Keep existing AnalyticsExplorer/ReportLibrary.

## Constitution Check

| Principle | Result |
|---|---|
| Source → Evidence → Reality | PASS: no record changes |
| Reality authority | PASS: delete redundant presentation/read only |
| Proven schema | PASS: no schema changes |
| Tenant/service boundaries | PASS: retained services and authorization unchanged |
| Spec and test evidence | PASS: explicit removal request, tests before implementation |
| Explainable Web | PASS: Explore/Inspector traceability retained |
| Simplicity/storage | PASS: remove exclusive service without replacement business rules |
| Received values | PASS: no value computation added |

## Design and implementation order

First add routing/render and HTTP retirement tests. Remove
packages/reality-core/src/reality/services/company_insights.py, then its two GET
adapters and AnalyticsMetric in web/api.py. Remove exclusive API types/methods in
apps/web/src/api.ts. Simplify AnalyticsPage.tsx and HomePage.tsx; update routing.ts
and browser fixtures. Replace Sandbox tests using retired reads with retained
analytics catalog/query reads. Delete service tests specific to the retired feature.
Update docs/WEB_SPEC.md and docs/features/analytics.md.

## Verification

Run make spec-check, make lint, full backend pytest, frontend contracts/i18n/build,
retirement browser scenarios and docs catalog generation/check. Record failures
without marking affected tasks complete. No migration is needed; rollback restores
removed code and routes. Review scope against existing dirty files.

## Complexity Tracking

None. Domain, persistence and tool registry need no edits.

## Sidebar refinement

The follow-up user request approves FR-005. Move the existing link within
apps/web/src/unified/Shell.tsx after Master data, retaining its handler and icon.
Use invariant Analytics for visible label, accessible name and collapsed tooltip.
Update analytics-browser.mjs and unified-shell-chat-browser.mjs expectations first.
No backend, data, route or dependency changes. All Constitution checks remain PASS.
Run frontend contract/i18n/build, spec policy and targeted browser verification;
backend results above remain applicable because this refinement is presentation only.
Rollback restores the link's former group and label.

Use the existing localization dictionaries and invariant-term catalog for Analytics
so runtime translation preserves its accessible label and portal tooltip too.
