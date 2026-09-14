# Tasks: Playground Companion

## Setup
- [x] T001 Review approved spec, plan and Constitution; no unresolved clarifications.

## US1 — Ask about this sandbox
- [x] T002 [US1] [FR-003] [FR-004] Add failing regressions in packages/reality-core/tests/test_playground_chat.py.
- [x] T003 [US1] [FR-003] [FR-004] Add narrow scope in services/tenant_policy.py, shared read-only loop in agent/mcp_chat.py, companion service and web/playground.py endpoint.
- [x] T004 [US1] [FR-001] [FR-005] Add PlaygroundChat.tsx and integrate right column in PlaygroundWorkspace.tsx/css; translate in localization.tsx.

## US2 — Discover questions
- [x] T005 [US2] [FR-002] Add contextual suggestions and retained conversation tests in apps/web/scripts/playground-companion.test.mjs and PlaygroundChat.tsx.

## Verification
- [x] T011 [FR-006] Remove visible sender headings while retaining accessible sender names; verify regression contracts and build.
- [x] T010 [FR-005] Remove duplicate chat register links and unused callback after a regression contract; verify frontend contracts, build and spec policy.
- [x] T009 [FR-008] [FR-009] Add attention and pending/retry regressions; implement compact AttentionList and central inspection, simplify PlaygroundChat and remove focus state; verify contracts, browser, localization, build, format and spec checks.
- [x] T008 [FR-007] Test compact timeline and reversible focus in frontend contracts/browser; implement workspace/companion state and scoped CSS; verify build, localization and responsive behavior.
- [x] T007 [FR-006] Add Markdown regression in playground-companion.test.mjs and browser fixture; refine PlaygroundChat.tsx/CSS; verify contracts/build and themed responsive rendering.
- [x] T006 Verify backend, contracts, build, localization and browser; record evidence in quickstart.md and docs/WEB_SPEC.md.

## Dependencies
T001 → T002 → T003 → T004/T005 → T006. Tests precede implementation.
UI contract tests can be written independently of backend regressions.
Coverage: FR-001 T004; FR-002 T005; FR-003/004 T002/T003; FR-005 T004/T006.
