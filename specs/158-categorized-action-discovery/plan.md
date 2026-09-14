# Implementation Plan: Categorized Action Discovery

**Date**: 2026-09-10 | **Spec**: [spec.md](spec.md)
**Language**: English. Existing integration worktree, no branch replacement.

## Summary

Add a validated presentation catalog to the application reference. It owns category
paths for Commands, inherited paths for Actions, explicit form variants, navigation
destinations and page/record placements. Render one searchable disclosure directory
and reuse the same entries in global and contextual menus. Existing action cards
and application services remain the only execution paths.

## Technical Context

Python 3.12, existing YAML catalog loader, TypeScript/React/Vite. No dependencies,
SQL queries, tables, migrations or service mutations are added. Native disclosure
controls and buttons avoid introducing a tree-widget dependency or incorrect ARIA
keyboard contracts. PostgreSQL remains the only business database.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Browsing writes no business records; existing forms retained | PASS |
| Reality owns operational state | No state or calculation moves to documents | PASS |
| Proven schema only | Presentation configuration only, no schema change | PASS |
| Tenant + shared services | Existing authorized reference endpoint and form services | PASS |
| Spec/test traceability | Approved spec; tests precede implementation; tasks map all FR/DR | PASS |
| Explainable web | Existing catalog details and Inspect paths preserved | PASS |
| Received values | No amount/quantity computations changed | PASS |
| Smallest coherent design | One metadata file; no generic executor or new UI framework | PASS |

## Repository Structure and Layer Changes

- `packages/reality-core/config/action_discovery.json`: categories, primary command
  paths, explicit supported form variants/placements and management destinations.
- `packages/reality-core/src/reality/action_discovery.py`: pure metadata validation.
- `packages/reality-core/src/reality/catalogs.py`: compose validated discovery metadata.
- `apps/web/src/api.ts`: additive reference type.
- `apps/web/src/unified/actionDiscovery.ts`: pure grouping/search/placement helpers.
- `apps/web/src/unified/ActionDirectory.tsx`: accessible hierarchical catalog.
- `apps/web/src/unified/ActionLauncher.tsx`: global and contextual launchers using
  shared metadata; typed dispatch to existing ActionCard variants only.
- `RealityInspectorPage.tsx`, `WarehousePage.tsx`, `FinancePage.tsx`,
  `UnifiedApp.tsx`, `Shell.tsx`: integrate directory and contextual launchers.
- Existing Sales/Purchasing/Commitments detail actions remain intact and are checked
  against explicit placements; management destinations navigate to existing pages.
- `apps/web/src/localization.tsx`: translations for new chrome/category labels.

## Design

Command primary paths are exhaustive; Actions inherit the path of their Command.
Form identity is separate from Command identity: record_movement offers opening,
receipt and shipment choices, never a generic execution button. Menu candidates
match explicit contexts; Finance matches tab and flow. A provider shares the
reference read across launchers. Form dispatch is allowlisted in TypeScript.
Category-first rendering retains Action/Command badges and detail components.
Search reveals matching entries and ancestors without changing manual expansion.
Unknown entries display Unclassified; configuration validation rejects drift.

## Failure, Security and Tenant Behavior

No business writes during reads, search or navigation. Reset the provider on company
change. Loading/error states offer retry, never stale-company launch candidates.
Navigation targets are internal selection objects. Existing forms enforce permission,
preview, confirmation, idempotency and server-side applicability. Empty business
registers do not disable the page menu. No mutation endpoint changes.

## Test Strategy and Traceability

- `tests/test_action_discovery.py`: complete classification, malformed metadata,
  unknown service/group/form references and inheritance (FR-001/006, DR-001).
- `scripts/action-discovery.test.mjs`: grouping, search, unique counts, unknown fallback,
  form completeness and placement matrix (FR-001–004/006–011).
- `scripts/action-discovery-browser.mjs`: real React DOM with synthetic reference and
  empty registers; tree keyboard/search/reset/mobile/locales, catalog availability,
  Warehouse menus, Finance supplier exclusions, no writes (FR-002–012, DR-001–003).
- Existing frontend contract suite, i18n audit, build, backend full pytest, Ruff,
  spec policy and relevant existing action browser regressions.

Expected initial failures: missing discovery module/metadata, flat catalog DOM and
missing contextual page actions. Keep proof of the failing baseline.

## Rollout and Rollback

Additive application-reference field; old consumers ignore it. Build matching core
and web from the active worktree, using the root .env, without migrations or volume
changes. Local web/API update only after verification; no remote deployment.
Rollback matching application images/assets; no data rollback needed.

## Review Risks

- Confusing adapter support with form availability.
- Losing direction or record context; supplier customer-credit leakage.
- Counts duplicating shared Actions or related service aliases.
- Search hiding matches in collapsed branches or disrupting manual state.
- Existing dirty integration changes require focused diff review.

## Complexity Tracking

No Constitution exceptions. No schema or execution-service changes.
