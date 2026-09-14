# Tasks: First-Time Fact Rule Wizard

## Phase 1: Specification and design gates

- [x] T001 Record owner scope approval in `specs/177-fact-rule-wizard/spec.md` and Constitution PASS in `plan.md`.
- [x] T002 Analyze `specs/177-fact-rule-wizard/spec.md`, `plan.md`, `tasks.md` before implementation.

## Phase 2: User Story 1 — Understand and start

- [x] T003 [US1] [FR-001, FR-002, FR-003, FR-010] Add failing entry, starter, validation and navigation checks in `apps/web/scripts/fact-rule-wizard-browser.mjs`.
- [x] T004 [US1] [FR-001, FR-002, FR-003, FR-010] Implement wizard shell, goal guidance and localized starters in `apps/web/src/unified/FactRuleWizard.tsx`, `ruleWizardState.ts`, `RulesWorkbench.tsx` and `apps/web/src/localization.tsx`.

## Phase 3: User Story 2 — Source-backed configuration

- [x] T005 [US2] [FR-004, FR-005, FR-011, DR-001] Extend browser source, fallback and editor regression tests in `apps/web/scripts/fact-rule-wizard-browser.mjs` and `guided-rules-browser.mjs`.
- [x] T006 [US2] [FR-004, FR-005, FR-011, DR-001] Integrate evidence and structured configuration in `apps/web/src/unified/FactRuleWizard.tsx`, `RuleEvidence.tsx`, `RuleDraftEditor.tsx`; preserve legacy workbench.

## Phase 4: User Story 3 — Test and activate deliberately

- [x] T007 [US3] [FR-006, FR-007, FR-008, FR-009, DR-002] Add milestone unit and complete lifecycle browser tests in `apps/web/scripts/fact-rule-wizard.test.mjs` and `fact-rule-wizard-browser.mjs`.
- [x] T008 [US3] [FR-006, FR-007, FR-008, FR-009, DR-002] Implement save/test/review/activation, resume and async guards in `apps/web/src/unified/FactRuleWizard.tsx`, `ruleWizardState.ts` and `RulesWorkbench.tsx`.

## Final phase: Verification and review

- [x] T009 [FR-001–011, DR-001, DR-002] Update `docs/WEB_SPEC.md` with wizard and lifecycle boundaries.
- [x] T010 Run spec policy, Ruff, complete pytest including migrations, web/site builds, web contracts, localization, focused wizard/legacy browser and catalog freshness gates; record exact results in `specs/177-fact-rule-wizard/verification.md`.
- [x] T011 Review complete diff against all requirements, desktop/mobile screenshots and rollback; update task status in `specs/177-fact-rule-wizard/tasks.md` only with green evidence.

## Dependencies and implementation strategy

T001 → T002 → test tasks T003/T005/T007 → T004 → T006 → T008 → T009–T011.
Deliver the full approved journey. Tests are written first. No domain/service/tool
changes: existing layers are reviewed before adapter implementation. Independent
contract tests and backend verification may run concurrently; edits to shared files
remain sequential. US1 entry and US2 source/configuration each have independent fixture
proofs; US3 adds saved lifecycle coverage. No parallel implementation agents required.

## Requirement coverage

| Requirements | Test tasks | Implementation tasks |
|---|---|---|
| FR-001–003, FR-010 | T003, T010 | T004 |
| FR-004, FR-005, FR-011, DR-001 | T005, T010 | T006 |
| FR-006–009, DR-002 | T007, T010 | T008 |

Completion evidence: [verification.md](verification.md), 2026-09-12.
