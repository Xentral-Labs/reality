# Tasks: Guided Fact Rules

## Setup
- [x] T001 Audit historical editor and current service contracts in `research.md`; approve scope in `spec.md`.
- [x] T002 Complete plan, contracts, quality checklist and preimplementation consistency review.

## US1 — Structured authoring
- [x] T003 [US1] Add failing typed conversion/preservation tests in `apps/web/scripts/guided-rule-draft.test.mjs` (FR-001, FR-002, DR-001).
- [x] T004 [US1] Implement `apps/web/src/unified/guidedRuleDraft.ts` and `RuleDraftEditor.tsx`; integrate in `RulesWorkbench.tsx` (FR-001, FR-002).

## US2 — Evidence and decisions
- [x] T005 [US2] Add evidence/recommendation scenarios in `apps/web/scripts/guided-rules-browser.mjs` (FR-003, FR-004, DR-001, DR-002).
- [x] T006 [US2] Implement `apps/web/src/unified/RuleEvidence.tsx` and reviewed integration (FR-003, FR-004).

## US3 — Understand and operate versions
- [x] T007 [US3] Add browser version/simulation/replay/access/context scenarios in `apps/web/scripts/guided-rules-browser.mjs` (FR-005, FR-006, FR-007, FR-008, DR-002).
- [x] T008 [US3] Implement `apps/web/src/unified/RuleResults.tsx`, summary and reviewed replay integration (FR-005, FR-006, FR-007).
- [x] T009 [US3] Complete translations in `apps/web/src/localization.tsx`, keyboard and narrow-screen styles/proof (FR-008).

## Verification and review
- [x] T010 Run required backend/frontend/spec/lint and browser gates; inspect screenshots, record `verification.md`.
- [x] T011 Review requirement coverage and diff; update `docs/WEB_SPEC.md` and local rollout evidence without migrations.

## Dependencies

T001–T002 precede implementation. T003 → T004; T005 → T006; T007 → T008 → T009;
all stories → T010 → T011. Unit and browser checks can execute independently once
components exist; shared workbench edits remain sequential. Deliver the complete
restoration, using US1 as the first independently verified increment.

## Owner-approved usability refinement
- [x] T012 [US1] Add initial draft/sentence/progressive layout regressions (FR-009, FR-010) in guided-rule-draft.test.mjs and guided-rules-browser.mjs.
- [x] T013 [US1] Implement prefilled three-section editor, sentence and persistent reviewed footer in guidedRuleDraft.ts, RuleDraftEditor.tsx and RulesWorkbench.tsx.
- [x] T014 Verify all affected gates, deployed browser layout and preserve lifecycle behavior; update verification.md.

Refinement analysis: FR-009/010 both map to tests and implementation. No clarification,
new domain rule, schema change or critical finding. T012 → T013 → T014.

T014: The initial shared-worktree Finance conflict is superseded by isolated-branch
verification: 75 web tests, production build, translations, formatting, Ruff, spec policy,
deployed browser acceptance and the complete backend suite (1976 passed, 9 skipped).
See verification.md for separate historical integration results.

- [x] T015 Add browser layout regression and implement FR-011 in RulesWorkbench.tsx, preserving saved-version lifecycle; verify isolated PR gates.
