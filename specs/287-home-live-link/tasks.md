# Tasks: Home Live Link Placement

**Input**: Design documents from `/specs/287-home-live-link/`

## Phase 1: Specification and design

- [x] T001 Record approved scope and acceptance scenarios in `specs/287-home-live-link/spec.md`
- [x] T002 Complete the Constitution Check and presentation design in `specs/287-home-live-link/plan.md`, `research.md`, `data-model.md`, `contracts/ui.md` and `quickstart.md`
- [x] T003 Validate requirements quality in `specs/287-home-live-link/checklists/requirements.md`

## Phase 2: User Story 1 - Recognize the live action in context (P1)

**Goal**: Group the live-monitor action with the graph's Live status while keeping range filtering separate.

**Independent Test**: The focused contract proves structure, styling, conditional display and callback preservation; the build proves component integration.

- [x] T004 [US1] Add a failing placement and interaction contract in `apps/web/scripts/home-live-link-contract.test.mjs`
- [x] T005 [US1] Separate the range selector and live action in `apps/web/src/unified/HomePulse.tsx`
- [x] T006 [US1] Render the supplied action beside the Live status in `apps/web/src/unified/ActivityGraph.tsx`
- [x] T007 [US1] Update the durable Welcome layout contract in `docs/features/home-live-status.md`

## Phase 3: Verification and review

- [x] T008 Run the focused contract, Web build, localization audit, formatting check and `make spec-check`
- [x] T009 Review the final diff against FR-001–FR-006, the Constitution and existing authorization/navigation behavior

## Dependencies and Execution Order

T004 precedes T005–T006 so the behavior is proved failing first. T005 and T006 are sequential because they change the same component interface. T007 may proceed independently. T008–T009 follow implementation.
