# Tasks: Inbox decision badge

## Setup
- [x] T001 Review scope, Constitution and docs/WEB_SPEC.md; measure the existing pending count; create spec.md and plan.md.
## US1
- [x] T002 [US1] Write apps/web/scripts/inbox-decision-badge-browser.mjs and apps/web/scripts/pending-decisions.test.mjs (FR-001–005).
- [x] T003 [US1] Add apps/web/src/unified/pendingDecisions.ts, the change event in apps/web/src/api.ts and the badge in apps/web/src/unified/Shell.tsx, dailyWork.ts and tailwind.css; document in docs/WEB_SPEC.md (FR-001–005).
## Verification
- [ ] T004 Run frontend and spec gates, check the badge live against the local stack, prepare a separate PR (FR-001–005).

Dependencies: T001 → T002 → T003 → T004.

## Verification record (2026-09-23)
- `npm run format:check`, `npm run test:i18n` (336 pass), `npm run i18n:audit` (4 languages PASS), `npm run build`: green.
- `inbox-decision-badge-browser.mjs` (en/de, expanded/collapsed): pass. `page-title-counts-browser.mjs`: pass.
- `daily-work-browser.mjs` (8 `search/resolve` POSTs counted as writes) and `refined-shell-browser.mjs` (line 181, action menu searchbox) fail identically with this change's `src` reverted; pre-existing on main.
- Count cost on the local stack, largest tenants: pending decisions 0.8–1.1 ms, commitments 60–73 ms, exceptions from stored rows 59–75 ms (the dashboard's live derivation takes 1.1–1.5 s).
