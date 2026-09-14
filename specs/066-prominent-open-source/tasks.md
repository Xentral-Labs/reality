---
description: "Requirement-traceable prominent open-source Site tasks"
---

# Tasks: Prominent Open-Source Entry

**Input**: `spec.md`, `plan.md`, and supporting artifacts
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and artifacts MUST be written in English.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner approval and absence of clarification markers in `specs/066-prominent-open-source/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/066-prominent-open-source/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings across `specs/066-prominent-open-source/`

## Phase 2: Failing Proof

- [x] T004 [US1] [FR-001] [FR-002] [FR-007] [DR-003] Add a failing shared-navigation repository contract in `provider-site/scripts/site-contract.test.mjs`
- [x] T005 [US2] [FR-003] [FR-004] [FR-005] [FR-008] [DR-001] [DR-002] [DR-003] [DR-004] Add a failing static landing-section contract in `provider-site/scripts/site-contract.test.mjs`
- [x] T006 [P] [US2] [FR-006] Add expected German, Dutch, and Spanish open-source copy to the contract in `provider-site/scripts/site-contract.test.mjs`

## Phase 3: User Story 1 — Discover the source from any page

- [x] T007 [US1] [FR-001] [FR-002] [DR-003] Add the canonical GitHub utility action to `provider-site/src/components/PublicHeader.tsx`
- [x] T008 [US1] [FR-006] Add localized header copy in `provider-site/src/localization.tsx`
- [x] T009 [US1] [FR-007] Refine shared responsive navigation presentation in `provider-site/src/landing.css`
- [x] T010 [US1] Run the independent shared-navigation contract in `provider-site/scripts/site-contract.test.mjs`

## Phase 4: User Story 2 — Understand why the open project matters

- [x] T011 [US2] [FR-003] [FR-004] [FR-005] [FR-008] [DR-001] [DR-002] [DR-003] [DR-004] Add the static open-source section and canonical destinations in `provider-site/src/LandingPage.tsx`
- [x] T012 [US2] [FR-006] Add German, Dutch, and Spanish section copy in `provider-site/src/localization.tsx`
- [x] T013 [US2] [FR-007] Add responsive light/dark token-based section styling in `provider-site/src/landing.css`
- [x] T014 [US2] Run the independent section contract and language audit in `provider-site/`

## Final Phase: Cross-Cutting Review

- [x] T015 Run `make spec-check` and review requirement/task coverage in `specs/066-prominent-open-source/`
- [x] T016 Run the complete Site tests, i18n audit, format check, and production build in `provider-site/`
- [ ] T017 Perform desktop/mobile and light/dark visual review of `/`, `/why-reality`, and `/platform`
- [x] T018 Review the final diff against the Constitution and every FR/DR, then record results in `specs/066-prominent-open-source/quickstart.md`
- [x] T019 [US1] [FR-009] Correct and prove the Product Web Documentation resource root in `apps/web/src/App.tsx` and `apps/web/scripts/product-boundary.test.mjs`
- [x] T020 [US2] [FR-010] Add and prove Shopify, Xentral, and Odoo marks in `apps/docs/content/index.md`, `apps/docs/content/de/index.md`, `apps/docs/.vitepress/theme/custom.css`, and `apps/docs/scripts/docs-contract.test.mjs`
- [x] T021 Run complete Product Web and Docs quality gates with `make web-build` and `make docs-build`

## Amendment: Focused Landing Ending

- [x] T022 [US2] [FR-003] [FR-004] Replace the open-source paragraph contract with an absence regression in `provider-site/scripts/site-contract.test.mjs`
- [x] T023 [US2] [FR-003] [FR-004] Remove the paragraph and dead copy from `provider-site/src/LandingPage.tsx`
- [x] T024 [US2] [FR-003] Remove the unused paragraph styles from `provider-site/src/landing.css`
- [x] T025 Run the complete Site test, localization, formatting, build, and spec gates

## Dependencies

- Phase 1 gates all implementation.
- Phase 2 precedes the code it proves.
- User Story 1 and User Story 2 share localization and CSS files, so execute them sequentially.
- Final review follows both user stories.

## Requirement Coverage

| Requirement   | Test task(s)          | Implementation/review task(s) | Status  |
| ------------- | --------------------- | ----------------------------- | ------- |
| FR-001–FR-002 | T004, T010            | T007, T009                    | Complete |
| FR-003–FR-005 | T005, T014            | T011, T013                    | Complete |
| FR-006        | T006, T014, T016      | T008, T012                    | Complete |
| FR-007        | T004, T014, T016–T017 | T009, T013                    | Automated proof complete; visual review pending |
| FR-008        | T005, T014            | T011                          | Complete |
| DR-001–DR-002 | T005, T018            | T011, T018                    | Complete |
| DR-003        | T004–T005, T018       | T007, T011                    | Complete |
| DR-004        | T005, T018            | T011, T018                    | Complete |
| FR-009        | T019                  | T019                          | Complete |
| FR-010        | T020–T021             | T020                          | Complete |

## Implementation Strategy

Implement the persistent navigation entry first as an independently useful discovery improvement. Then add the explanatory landing section. Keep all behavior static and reuse existing Site primitives and tokens.
