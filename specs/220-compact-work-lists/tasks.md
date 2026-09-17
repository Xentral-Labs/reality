# Tasks: Compact Daily Work Lists

## Setup and Foundation
- [x] T001 Review requirements and Constitution in specs/220-compact-work-lists/spec.md and plan.md.

## US1: Scan more work
- [x] T002 [US1] Extend apps/web/scripts/daily-work-browser.mjs with row geometry and keyboard checks before implementation (FR-001–004).
- [x] T003 [US1] Implement shared compact rows and container-based toolbar layout in apps/web/src/unified/WorkList.tsx and apps/web/src/tailwind.css; adapt CommitmentsPage.tsx, AttentionPage.tsx and DecisionsPage.tsx (FR-001–004).

## Verification and Review
- [x] T004 Run the planned checks, review screenshots and record results in specs/220-compact-work-lists/quickstart.md.
- [x] T005 Review the diff and update docs/WEB_SPEC.md with the shared presentation contract.

## Dependencies and Delivery
T001 → T002 → T003 → T004 → T005. One bounded story is the complete increment. No parallel implementation needed because all pages share the same row.
