# Tasks: Work counts on workspace tabs

## Setup
- [x] T001 Inventory every tab of every main page, measure each candidate count on the local stack, record owner decisions in spec.md; write plan.md.
## US1
- [x] T002 [US1] Write apps/web/scripts/workspace-tab-counts-browser.mjs (FR-001–008).
- [x] T003 [US1] Generalize apps/web/src/unified/workCounts.ts, add TabWorkCount.tsx, wire Shell.tsx, OrdersPage.tsx, WarehousePage.tsx, FinancePage.tsx and tailwind.css; document in docs/WEB_SPEC.md (FR-001–008).
- [x] T005 [US1] Reorder `dailyWork` (Decisions, Exceptions, Commitments), accent the Decisions counts and the Welcome tile; update daily-work-browser shortcut order (FR-008).
## Verification
- [x] T004 Run frontend and spec gates, check live against the local stack, prepare a separate PR (FR-001–008).

Dependencies: T001 → T002 → T003 → T004. Depends on spec 253 (PR #145).

## Verification record (2026-09-23)
- `workspace-tab-counts-browser.mjs` (en/light, de/dark): pass. `inbox-decision-badge-browser.mjs` (en/de, expanded/collapsed): pass.
- `page-title-counts-browser.mjs` (18 registers): pass; it caught a shared `.shell-tab-count` class that would have misled the tab scroll-into-view measurement, fixed with a separate `.shell-tab-work-count` class.
- `npm run format:check`, `npm run test:i18n` (336 pass), `npm run i18n:audit` (4 × PASS), `npm run build`: green.
- Costs re-measured with the default filters: open receivables 7–13 ms, customer commitments 60–73 ms, findings 59–75 ms, overallocated stock 6–8 ms.
