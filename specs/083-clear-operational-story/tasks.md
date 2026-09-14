# Tasks: Clear Operational Story

## Phase 1: Specification and Design Gates

- [x] T001 Record approved scope and requirements review in specs/083-clear-operational-story/spec.md.
- [x] T002 Pass Constitution Check in specs/083-clear-operational-story/plan.md.
- [x] T003 Analyze specs/083-clear-operational-story/{spec,plan,tasks}.md before implementation. Nine requirements covered; no critical findings, unmapped tasks or unresolved ambiguities.

## Phase 2: Failing Proof

- [x] T004 [US1] [FR-001] [FR-002] [FR-004] [FR-005] Add case and semantic tests in provider-site/scripts/site-contract.test.mjs.
- [x] T005 [US2] [FR-003] [FR-006] [FR-009] Add readiness tests in provider-site/scripts/site-contract.test.mjs; retain locale and routing tests.
- [x] T006 [US3] [FR-007] [FR-008] [FR-009] Add journey and rule guidance tests in apps/docs/scripts/docs-contract.test.mjs; retain locale/link gates.

## Phase 3: Business Outcome

- [x] T007 [US1] [FR-001] [FR-002] [FR-004] [FR-005] Update provider-site/src/{LandingPage,WhyRealityPage}.tsx and components/OperationalStory.tsx, with responsive styles in landing.css.

## Phase 4: Honest Entry

- [x] T008 [US2] [FR-003] [FR-006] [FR-009] Update provider-site/src/{LandingPage,PlatformPage,localization}.tsx and docs/WEB_SPEC.md.
- [x] T009 [US2] [FR-002] [FR-003] [FR-004] [FR-006] Update apps/docs/content/{index.md,getting-started/,product-guides/,integrations/} and matching de/ editions.

## Phase 5: Model and Extension

- [x] T010 [US3] [FR-005] [FR-007] [FR-008] [FR-009] Update apps/docs/content/concepts/ and matching de/ guidance, add product-guides/missing-information.md and navigation in apps/docs/.vitepress/config.mts.

## Final Phase

- [x] T011 Run site/docs tests, localization, builds, make spec-check and make lint; record evidence in specs/083-clear-operational-story/quickstart.md.
- [ ] T012 Review routes, links, semantics, translations, responsive presentation and final diff; report any unavailable visual check in specs/083-clear-operational-story/quickstart.md. Source/diff review completed; desktop/mobile visual acceptance remains pending because no browser is connected.

## Dependencies and Strategy

## Owner revision: preserve core-technology positioning

The owner approved targeted refinement, not a dashboard-first redesign. Earlier tasks record
the first iteration; these tasks supersede its site presentation. Docs improvements remain.

- [x] T013 [US1] [FR-001] [FR-002] Add original hero/diagram/brand/context tests in provider-site/scripts/site-contract.test.mjs before restoration.
- [x] T014 [US1] [FR-001] [FR-002] [FR-004] [FR-005] Restore provider-site/src/{LandingPage,WhyRealityPage}.tsx and landing.css from the pre-PR baseline with targeted semantic corrections.
- [x] T015 [US2] [FR-003] [FR-006] [FR-009] Maintain readiness/action boundaries and translations in provider-site/src/localization.tsx.
- [x] T016 Run site/docs quality gates and record revision evidence in specs/083-clear-operational-story/quickstart.md.

Revision review: all nine requirements remain covered by existing tasks plus T013–T016.
Constitution Check remains PASS; no unresolved clarification or critical inconsistency remains.

Gates → failing proof → US1 → US2 → US3 → verification. No parallel agents required.
After shared case wording is fixed, site translations and documentation editions can be reviewed independently.
Each story has its independent test in spec.md. No backend or migration changes.

## Requirement Coverage

## Owner revision: discreet open-source closing note

- [x] T017 [US1] [FR-010] Replace the banner contract with a failing end-of-page paragraph and inline-link contract.
- [x] T018 [US1] [FR-010] Replace the banner and its styles with a restrained closing paragraph; translate it in every public locale.
- [x] T019 [FR-010] Run site quality gates, spec policy and final diff review; record evidence.

Review: owner explicitly requested this placement and treatment. Constitution Check: PASS;
no backend, schema, source handling or action behavior changes. Test precedes implementation;
existing presentation and readiness contracts remain in force. No unresolved clarification.

## Owner revision: focused autonomy and landing-page ending

- [x] T020 [US1] [FR-002] [FR-010] Add absence contracts for the autonomy disclaimer, repeated walkthrough card and open-source paragraph in `provider-site/scripts/site-contract.test.mjs`.
- [x] T021 [US1] [FR-002] [FR-010] Remove all three redundant blocks and their unused styles/copy from `provider-site/src/LandingPage.tsx` and `provider-site/src/landing.css`.
- [x] T022 [FR-009] Run the complete Site quality gates and spec policy, then review the final diff.

Review: the owner explicitly removed both autonomy-section boxes and the closing paragraph. The
existing temporal context visual continues to carry the lamp example, the four-step progression
continues to explain bounded autonomy, and shared navigation continues to expose Docs.
Constitution Check remains PASS; no runtime, data, localization, or business behavior changes.

| Requirement | Test tasks | Implementation tasks |
|---|---|---|
| FR-001 | T004 | T007 |
| FR-002 | T004 | T007, T009 |
| FR-003 | T005 | T008, T009 |
| FR-004 | T004 | T007, T009 |
| FR-005 | T004 | T007, T010 |
| FR-006 | T005 | T008, T009 |
| FR-007 | T006 | T010 |
| FR-008 | T006 | T010 |
| FR-009 | T005, T006 | T008, T010 |
| FR-010 | T017 | T018, T019 |
