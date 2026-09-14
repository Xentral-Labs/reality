# Implementation Plan: Inline Row Previews

**Branch**: `164-inline-row-previews` | **Date**: 2026-09-10 | **Spec**: [spec.md](spec.md)

## Summary

Replace overlay-based read-only inspection in the eight approved workspaces with one shared inline preview presentation. Extract the existing Inspector's read-only body so it can render inline without duplicating interpretation. Keep editors, confirmation dialogs, focused delivery work, and the full Inspector as separate destinations. Add one semantic icon vocabulary for disclosure, navigation, filtering, editing, and operational work.

## Technical Context

**Language/Version**: TypeScript 5.8, React 19; Python 3.12 backend unchanged
**Primary Dependencies**: existing React/Vite/Tailwind and Lucide dependencies
**Storage**: N/A; no persistence or schema change
**Testing**: Node contract tests, TypeScript build, localization audit, focused Playwright browser journey
**Project Type**: independent React frontend over existing tenant-scoped API
**Constraints**: reuse existing read models; no browser business rules; preserve confirmations; accessible keyboard disclosure
**Scale/Scope**: three daily-work lists and five operational workspace families; one open preview per register

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Existing Inspector data and links are reused; presentation location alone changes. | PASS |
| Reality owns operational state | No document or frontend workflow state is introduced. | PASS |
| Proven schema only | No schema or stored field changes. | PASS |
| Tenant + shared service boundaries | Existing tenant-scoped API clients remain the only data source. | PASS |
| Spec/test traceability | The test table and tasks map every FR/DR to contract, build, browser, or review evidence. | PASS |
| Explainable web behavior | Row previews retain a labelled route to the full trace and original-source path. | PASS |
| Received values not recomputed | Preview renders returned values; no amount or quantity is recomputed. | PASS |
| Smallest coherent design | One extracted preview body and two layout primitives avoid page-specific inspectors or new endpoints. | PASS |

Planning may continue: every gate passes and no exception is requested.

## Repository Structure and Layer Changes

```text
apps/web/src/unified/Inspector.tsx
apps/web/src/unified/InlinePreview.tsx
apps/web/src/unified/WorkList.tsx
apps/web/src/unified/{AttentionPage,CommitmentsPage,DecisionsPage}.tsx
apps/web/src/unified/{OrdersPage,WarehousePage,FinancePage,MasterDataPage}.tsx
apps/web/scripts/inline-row-previews.test.mjs
apps/web/scripts/inline-row-previews-browser.mjs
docs/WEB_SPEC.md
docs/WEB_UX_MATRIX.md
```

**Files/layers affected**: frontend presentation and frontend test artifacts only. No domain, service, tool, API, migration, or database file changes are planned.

## Design

### Reality flow

The existing SourceRecord → Document/DocumentLine → Reality chain is unchanged. Inline preview requests the same tenant-scoped Inspector representation and renders the same returned fields and links. It does not infer or store state.

### Service and adapter flow

`page row → disclosure state → existing api.inspector(tenant, kind, opaque id) → shared Inspector content`. Proposal and exception summaries already loaded by their pages may render returned fields directly; deeper explanation continues through the existing Inspector route. Mutating buttons continue to open their existing cards/dialogs and confirmation flows.

### Data and migration impact

No schema, migration, endpoint, payload, fixture, or persisted-preference changes. Rollback is a frontend revert.

### Failure, security, and tenant behavior

Inline reads retain the active tenant and existing cross-tenant not-found semantics. Loading, retry, and error content stays inside the selected row. Context changes clear preview identity. Preview activation never invokes a mutation.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–003, FR-008–010, FR-012 | contract/browser | `inline-row-previews.test.mjs`; focused browser journey | overlays remain and no expanded-row contract exists |
| FR-004, FR-011, FR-017 | regression/static review | existing action-card tests plus handler assertions | daily-work drawer combines preview and work |
| FR-005–007, FR-016, FR-018 | contract/visual | semantic icon assertions and browser screenshots | chevrons conflate navigation and disclosure |
| FR-013–015 | component/browser | shared Inspector-content assertions and responsive journey | Inspector body only renders inside a dialog |
| DR-001–005 | static/CI | diff review and existing tenant/Inspector tests | no failure expected; invariants must remain unchanged |

## Rollout and Rollback

Ship as a frontend-only bundle after contract, build, localization, desktop, mobile, and existing action-flow checks pass. No feature flag or migration is required. Roll back the frontend image without touching stored data.

## Review Risks

- A broad RegisterTable change could affect out-of-scope pages, so expansion remains explicit per page.
- Row click handlers can conflict with links and actions.
- Inspector content can be long; previews must remain concise by default.
- Master Data editing must stay distinct from preview.
- The active deploy integration worktree has conflicts; work remains isolated here.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
