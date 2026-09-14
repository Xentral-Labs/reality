# Implementation Plan: Web UX Matrix Completion

**Branch**: `030-web-ux-matrix-completion` | **Date**: 2026-09-02 | **Spec**: [`spec.md`](spec.md)

**Status**: Specification and plan approved by the product owner on 2026-09-02.

## Summary

Close `016/FR-006` with a versioned executable destination-to-UX-matrix inventory and
bounded remediation of surfaces that do not fulfil their approved job. Preserve shared
services and Inspector boundaries, add only the smallest missing authoritative read
contracts, converge on shared responsive patterns, and retain human desktop/mobile review.

## Technical Context

**Language/Version**: TypeScript/React 19; Python 3.12

**Primary Dependencies**: React, Vite, Tailwind/TailAdmin, FastAPI, Pydantic v2,
SQLAlchemy 2, existing services/read models

**Storage**: PostgreSQL through existing models; no schema/migration planned. The UX
coverage manifest is verification metadata only.

**Testing**: Node contracts, localization audit, TypeScript/Vite build, pytest with
PostgreSQL, Spec policy, deterministic desktop/mobile visual review

**Target Platform**: Authenticated Product Web at desktop and representative mobile sizes

**Project Type**: Existing React web application with Python service/API

**Performance Goals**: Preserve bounded server reads; no benchmark claim. `016/FR-015`
remains out of scope.

**Constraints**: No browser-owned truth, duplicate service path, schema expansion, or new
UI framework; page size remains at most 100; Spec 029 owns global Activity.

**Scale/Scope**: 23 top-level routes, seven settings destinations, shared detail/Inspector
states, and 21 authoritative UX-matrix rows.

## Constitution Check

*GATE: Passed before research and re-checked after design.*

| Principle | Plan evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Applicable surfaces retain explanation and raw Source access | PASS |
| Reality authority | UI arranges shared truth and never stores/recalculates business state | PASS |
| Proven schema | No model/migration change; unsupported truth triggers a separate decision | PASS |
| Tenant/service boundaries | Read additions delegate to tenant-scoped services | PASS |
| Spec/test evidence | Tests precede remediation; final owner gate retained | PASS |
| Explainable Web | Answer → Reality → Evidence → Source remains explicit | PASS |
| Simplicity/storage | One non-runtime manifest; no new framework/store | PASS |
| English artifacts | All repository output is English | PASS |

Post-design review remains PASS: no persistence or dependency is added; the manifest is
non-authoritative and any API delta is an additive read over an existing service.

## Baseline and Planned Work

| Family | Current finding | Planned work |
|---|---|---|
| Shell/workspaces | Shared shell exists; Spec 029 owns Activity | Exact topology and ownership proof |
| Home/Facts | Attention flow/onboarding exist | Lock hierarchy and state evidence |
| Exceptions | Queue exists; controls partly decorative | Truthful search/priority controls and Inspect |
| Commitments | Filtering/risk summary exist | Lock risk-first hierarchy and explanation |
| Inventory | State filter exists; location/explanation need proof | Smallest authoritative filter/read delta |
| Reservations/Movements | Opaque IDs lead | Business context first; IDs remain in Inspect |
| Open Items/Payments | Totals/filters exist | Total scope, overdue/unmatched priority, empty guidance |
| Journal | Domain service exists; no Web destination | Read-only destination over existing ledger service |
| Documents/detail | Register/Inspector exist | Business-first columns and required section order |
| Parties/Items/Locations | Detail behavior uneven | Read-first detail, explicit edit, lifecycle separation |
| Commercial/Pricing | Tasks compete | One focused task/workflow at a time |
| Sources & Imports | Setup/test/inspection compete | Configured sources first; separate discovery/test |
| Ask Reality | Spec 028 owns empty state | Preserve evidence/proposal/confirmation flow |
| Explorer/Help | Exist; hierarchy needs proof | Matrix-required search, task entry, and context |
| Activity | Spec 029 | Map separate owner; do not duplicate |

## Implementation Phases

### A. Freeze executable coverage

Add `apps/web/scripts/fixtures/ux-matrix-v1.json` and a Node contract that compares the
actual route union/settings destinations with exact matrix ownership, ordered hierarchy,
states, explanation entries, and responsive cases. Prove named drift categories first.

### B. Converge shared presentation patterns

Minimally consolidate repeated header, control-total, toolbar, table, state, dialog/drawer,
and responsive markup used by three or more surfaces. Preserve accessible shared states.

### C. Complete operational surfaces

Lock Home/Facts, make Exceptions controls truthful, complete Commitments/Inventory
summaries and filtering, add business context to Reservations/Movements, and prove Inspect.

### D. Complete finance and Evidence surfaces

Complete receivable/payable/overdue and allocation hierarchy with server-owned totals;
add read-only Journal; align Documents and document Inspector section order.

### E. Complete configuration and support surfaces

Converge reference registers/details; focus Commercial/Pricing and Sources & Imports;
preserve settings, Spec 028 Ask Reality, Spec 029 Activity, and distinct Explorer/Help jobs.

### F. Validate and close

Run coverage/backend/localization/build gates, desktop/mobile review, full suites, and final
diff review. After owner approval close only `016/FR-006`; retain `016/FR-015`.

## Project Structure

```text
specs/030-web-ux-matrix-completion/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/ux-matrix-coverage.md
├── checklists/requirements.md
└── tasks.md

apps/web/
├── src/{App.tsx,api.ts,localization.tsx,tailwind.css}
└── scripts/{fixtures/ux-matrix-v1.json,ux-matrix-contract.test.mjs}

packages/reality-core/
├── src/reality/{services/core.py,web/api.py}
└── tests/{test_ledger.py,test_master_data_api.py,test_http_boundary.py,test_spec_policy.py}

docs/{WEB_SPEC.md,WEB_UX_MATRIX.md,SPEC_COVERAGE_MATRIX.md,features/web.md}
```

**Structure Decision**: Keep existing client and service/API layout. Verification metadata
sits beside Web tests; authoritative reads stay in services/API.

## Migration and Rollback

- No database migration or backfill.
- Additive reads may deploy before frontend presentation.
- Revert presentation/read deltas together; no business state reversal.
- Rebase after Spec 029 merges and rerun topology proof; never copy its unmerged work.

## Review Risks

1. Scope breadth: implement/review by family and stop at approved hierarchy.
2. Decorative controls: map every control to an authoritative read and proof.
3. Browser calculations: accept server-owned aggregates only.
4. Missing labels: extend bounded read projections, never infer in browser.
5. Visual-only evidence: pair human review with executable topology/state/trace contracts.
6. Concurrent shell ownership: explicit owner, current-main rebase, isolated final diff.

## Complexity Tracking

No Constitution violations or justified exceptions are planned.
