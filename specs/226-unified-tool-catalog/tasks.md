# Tasks: Unified tool catalog
## Setup
- [x] T001 Specify approved scope, review dependencies and Constitution; record plan and compatibility contract.
## Metadata (US1/US3)
- [x] T002 Add tests in tests/test_tool_catalog.py for coverage, explicit merging, variants and MCP contract preservation (FR-003/006).
- [x] T003 Add tool_catalog.py and config/tool_catalog.json; expose additive runtime metadata (FR-002–006).
## Web (US1/US2)
- [x] T004 Add directory filtering/navigation and browser checks (FR-001/002/004/007).
- [x] T005 Implement ToolCatalog.tsx and shared filtering; retain existing form/report access and technical details (FR-001–005/007).
- [x] T006 Localize controls, remove superseded tabs and update route/test expectations (FR-001/007).
## Verification
- [x] T007 Run required frontend, catalog/MCP, spec, lint and documentation gates; inspect browser screenshots (FR-001–007).
- [x] T008 Review diff and compatibility baseline, update docs/WEB_SPEC.md and verification evidence; commit isolated change (FR-001–007).

Dependencies: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008. Metadata tests and UI fixture preparation can be independent; implementation remains sequential in this worktree. Deliver all stories together.
