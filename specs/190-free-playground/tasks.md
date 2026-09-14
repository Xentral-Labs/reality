# Tasks: Free Playground

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/playground.md
**Gate**: Owner-approved scope; Constitution PASS; requirements checklist 6/6.

## Specification and Design
- [x] T001 Review scope, assumptions and consent in `specs/190-free-playground/spec.md`.
- [x] T002 Complete research and Constitution PASS in `specs/190-free-playground/plan.md`.
- [x] T003 Analyze requirement coverage and boundaries in `specs/190-free-playground/analysis.md`.

## Failing Proof
- [x] T004 [US1] [FR-002] [FR-003] [FR-004] Add entry consent, retry, owner and disabled-policy tests in `packages/reality-core/tests/test_free_playground.py`.
- [x] T005 [US3] [FR-007] [FR-008] Add quota concurrency/reset/provider-boundary tests in `packages/reality-core/tests/test_free_playground.py`.
- [x] T006 [US2] [FR-005] [FR-006] [FR-009] Add task routing/success/dismissal tests in `apps/web/scripts/free-playground.test.mjs` and rendered acceptance in `apps/web/scripts/free-playground-browser.mjs`.
- [x] T007 [US1] [FR-001] [FR-009] Update offer contract tests in `provider-site/scripts/site-contract.test.mjs` and localization audits.

## Services and Adapters
- [x] T008 [US1] [FR-002] [FR-003] [FR-004] Implement consent and idempotent entry in `packages/reality-core/src/reality/services/free_playground.py`, `web/auth.py`, `web/company_setup_api.py`; preserve canonical setup.
- [x] T009 [US3] [FR-007] Implement account-scoped atomic allowance in `services/free_playground.py`, integrate `services/core.py` and `services/playground_chat.py`.
- [x] T010 [US3] [FR-008] Expose allowance in `packages/reality-core/src/reality/web/api.py` and `apps/web/src/api.ts`.

## Web Journeys
- [x] T011 [US1] [FR-001] [FR-002] [FR-003] [FR-004] Implement consent wording and recoverable Home entry in `apps/web/src/Auth.tsx`, `unified/FreePlayground.tsx`, `unified/UnifiedApp.tsx`, `unified/useCompanyContext.ts`.
- [x] T012 [US2] [FR-005] [FR-006] Add starter routing and rendered-result signals in `unified/FreePlayground.tsx`, `HomePage.tsx`, `AttentionPage.tsx`, `FinancePage.tsx`, `DeliveryCase.tsx`.
- [x] T013 [US3] [FR-008] Show allowance/reset and retain draft in `apps/web/src/unified/ChatPage.tsx` and `ChatComposer.tsx`.
- [x] T014 [US1] [FR-001] [FR-009] Align landing/header/platform copy in `provider-site/src/` and both `localization.tsx` catalogs.

## Verification and Review
- [x] T900 Run spec/coverage checks and update `docs/SPEC_COVERAGE_MATRIX.md`.
- [x] T901 Run lint and complete PostgreSQL suite.
- [x] T902 Run web/site/docs builds, localization and applicable UI checks.
- [x] T903 Review no-schema rollback, provider concurrency and tenant boundaries.
- [x] T904 Record verified evidence in `specs/190-free-playground/review.md` and durable feature contracts.

## Requirement Coverage
| Requirement | Test tasks | Implementation tasks |
| --- | --- | --- |
| FR-001 | T007 | T011, T014 |
| FR-002 | T004 | T008, T011 |
| FR-003 | T004 | T008, T011 |
| FR-004 | T004 | T008, T011 |
| FR-005 | T006 | T012 |
| FR-006 | T006 | T012 |
| FR-007 | T005 | T009 |
| FR-008 | T005 | T010, T013 |
| FR-009 | T006, T007, T902 | T014 |

## Loading feedback refinement (FR-010)

- [x] T910 Add delayed-response browser regression checks and observe the current failure.
- [x] T911 Implement localized progress, busy guards and language-preserving navigation.
- [x] T912 Run web gates and browser regressions; rebuild local web and verify live account.

## Hosted offer correction (FR-011)

- [x] T920 Update contract tests for free-only Cloud copy and removed capacity banner; observe failure.
- [x] T921 Update Cloud presentation and translations without altering admission.
- [x] T922 Run site checks, inspect desktop/mobile, update local Docker and open follow-up PR.

## Packages page focus (FR-012)

- [x] T930 Replace architecture-presence assertions with absence checks, then remove the section.
- [x] T931 Verify site checks and local Docker rendering; update PR 266.

## Header design trial (FR-013)

- [x] T940 Update shared header labels/hierarchy, translations and contracts.
- [x] T941 Run site checks and responsive browser review; expose local preview.

## Hero alignment (FR-014)

- [x] T950 Align the hero container and verify equal left edges on desktop/mobile; update local Docker and PR.

## Visual polish (FR-015)

- [x] T960 Apply shared type/spacing/CTA rules and consistent trial labels.
- [x] T961 Verify site gates and desktop/mobile pages; update local preview and PR.

## Product screenshot preview (FR-016)

- [x] T970 Capture actual localized demo details with desktop/mobile variants.
- [x] T971 Add the focused ERP Lite screenshot/story and localized accessible description.
- [x] T972 Verify site gates and responsive rendering; expose local preview.

## Analytics product preview (FR-017)
- [x] T973 Capture and verify actual chart/table demo values and provenance.
- [x] T974 Replace illustrative art with localized responsive product screenshots and accessible text.
- [x] T975 Run site checks and visually review the local preview.

## Shorter How it works (FR-018)
- [x] T976 Reorder the core story and introduce localized, accessible optional depth.
- [x] T977 Verify retained content, responsive disclosures and at least 30% shorter initial page.

## FR-019
- [x] T019 Implement and verify verification-mail return links, fresh-tab recovery and resend controls.
