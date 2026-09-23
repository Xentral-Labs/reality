# Tasks: Welcome exception count from the stored register

## Setup
- [x] T001 Review spec 180, spec 225 FR-018 and docs/WEB_SPEC.md; confirm no existing requirement makes Welcome agree with the register; create spec.md and plan.md.
## US1
- [x] T002 [US1] Add the failing regression test in packages/reality-core/tests/test_attention_reads.py (FR-001–003).
- [x] T003 [US1] Read the dashboard exception total and sample through attention_register in packages/reality-core/src/reality/web/api.py; show a null count as unknown in apps/web/src/api.ts and apps/web/src/unified/HomePage.tsx; record the rule in docs/WEB_SPEC.md (FR-001–003).
## Verification
- [x] T004 Run backend and web gates, time the dashboard before and after, and prepare the PR (FR-001–003).

Dependencies: T001 → T002 → T003 → T004. One small story; sequential.
