# Tasks: Email-only account menu

## Setup
- [x] T001 Review approved scope, Constitution and docs/WEB_SPEC.md; create spec.md and plan.md.
## US1
- [x] T002 [US1] Inspect existing shell/profile checks in apps/web/scripts and update obsolete label expectations before presentation changes (FR-001–003).
- [x] T003 [US1] Update apps/web/src/unified/ProfileMenu.tsx and apps/web/src/localization.tsx; document the account control in docs/WEB_SPEC.md (FR-001–003).
## Verification
- [x] T004 Run frontend and spec gates, inspect long-email desktop/mobile behavior, record verification.md and prepare separate PR (FR-001–003).

Dependencies: T001 → T002 → T003 → T004. One small story; sequential implementation. Localization and documentation can be prepared independently after scope review, but no parallel agents are needed.
