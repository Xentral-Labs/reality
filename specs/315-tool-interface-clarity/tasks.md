# Tasks: Tool interface clarity

## Phase 1: Specification and Design Gates

- [x] T001 Record accepted scope and requirements review in `specs/315-tool-interface-clarity/spec.md` and `checklists/requirements.md`.
- [x] T002 Complete Constitution PASS design and three-operation audit in `specs/315-tool-interface-clarity/plan.md` and `research.md`.
- [x] T003 Analyze spec/plan/tasks and record coverage evidence in `specs/315-tool-interface-clarity/verification.md` before implementation.

## Phase 2: User Story 1 - Category clarity

- [x] T004 [US1] [FR-001, FR-002, FR-005] Add failing shared-guide tests in `apps/docs/scripts/test_interface_guide_reference.py` and `apps/docs/scripts/docs-contract.test.mjs`.
- [x] T005 [US1] [FR-001, FR-002, FR-005] Define guide metadata and render shared manual terminology in `apps/docs/scripts/generate-catalog-reference.py`; consume it in `apps/docs/.vitepress/theme/components/ToolUsage.vue`.

## Phase 3: User Story 2 - Follow the operation

- [x] T006 [US2] [FR-003, FR-004, DR-001] Add example identity, optional quantity and relationship tests in `apps/docs/scripts/test_interface_guide_reference.py`, `apps/docs/scripts/docs-contract.test.mjs` and `apps/docs/scripts/tool-interface-render.test.mjs`.
- [x] T007 [US2] [FR-003, FR-004, DR-001] Render catalog-resolved example links and explicit operation relationships in `apps/docs/scripts/generate-catalog-reference.py` and `apps/docs/.vitepress/theme/components/ToolUsage.vue`.

## Phase 4: User Story 3 - Consolidation and audit

- [x] T008 [US3] [FR-005, FR-006, DR-001] Review shared terminology proof and audit against source paths; record outcome in `specs/315-tool-interface-clarity/verification.md`; retain deliberate adapter differences documented in `research.md`.

## Final Phase: Verification and Review

- [x] T009 Generate all catalog output with `make docs-generate` and verify repeatability for `apps/docs/content/tool-usage/`, `apps/docs/content/de/tool-usage/` and `apps/docs/.vitepress/data/tool-usage.json`.
- [x] T010 Run spec gate, lint, complete documentation Python/Node tests, format and production build; record results and scoped gate rationale in `specs/315-tool-interface-clarity/verification.md`.
- [x] T011 Review final diff against FR/DR and stable registry identifiers; update `specs/315-tool-interface-clarity/tasks.md` only after required checks pass.

## Dependencies and Implementation Strategy

T001–T003 gate all implementation. Tests precede their changes. US2 follows shared guide metadata from US1; US3 reviews both. The Python and Node test authoring can run independently; edits to shared generator/Vue files remain sequential. Deliver the guide first, then relationship presentation, then generation and review. No domain/service/tool behavior changes are necessary.

## Requirement Coverage

| Requirement | Test/review tasks | Implementation/documentation tasks |
|---|---|---|
| FR-001, FR-002 | T004, T010 | T005, T009 |
| FR-003, FR-004 | T006, T010 | T007, T009 |
| FR-005 | T004, T008 | T005, T009 |
| FR-006 | T008, T011 | T002, T008 |
| DR-001 | T006, T008, T011 | T002, T007 |
