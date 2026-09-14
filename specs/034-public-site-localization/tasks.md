# Tasks: Public Site Localization

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/public-site-localization.md`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, and resulting repository artifacts are written in English.
Tests precede the behavior they prove. Contract documents change only after the
executable evidence is green.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm product-owner specification approval and zero clarification markers in `specs/034-public-site-localization/spec.md` and `specs/034-public-site-localization/checklists/requirements.md`
- [x] T002 Confirm all Constitution Check rows PASS in `specs/034-public-site-localization/plan.md`
- [x] T003 Record the measured text inventory, German pairing result, and rejected alternatives in `specs/034-public-site-localization/research.md`

## Phase 2: Failing Proofs and Shared Vocabulary

- [x] T004 [US3] [FR-011] [FR-012] Add the failing audit behavior test covering inventory shape, per-language report counts, and injected missing/empty/English-duplicate/dropped-domain-term regressions in `provider-site/scripts/i18n-audit.test.mjs`
- [x] T005 [P] [US1] [FR-002] Add the failing source-structure contract asserting zero language conditionals and zero per-language copy branches in `provider-site/src` in `provider-site/scripts/site-localization.test.mjs`
- [x] T006 [P] [US1] [FR-003] [FR-004] [FR-007] Add failing catalog-lookup, English-fallback, and live-switch translation cases in `provider-site/scripts/site-localization.test.mjs`
- [x] T007 [P] [US1] [FR-006] Add the failing German parity regression asserting pre-existing German sentences verbatim in the German catalog in `provider-site/scripts/site-localization.test.mjs`
- [x] T008 [P] [US1] [FR-009] [FR-010] Add failing protected-term, business-identifier, code-sample, and language-control invariance cases in `provider-site/scripts/site-localization.test.mjs`
- [x] T009 [P] [US2] [FR-015] [FR-016] Extend language-resolution and account-link cases to all four languages plus malformed values in `provider-site/scripts/site-contract.test.mjs`
- [x] T010 [P] [US1] [FR-008] Add the failing runtime-value sentence case for price, capacity, and zero capacity in `provider-site/scripts/site-localization.test.mjs`

**Checkpoint**: Every new proof fails because the site has no catalog, no translation lookup, and no audit.

## Phase 3: User Story 1 — Complete Four-Language Public Site (P1, MVP)

**Goal**: The whole public site reads in English, German, Dutch, and Spanish.

**Independent Test**: Select each language on `/`, `/platform`, and `/why-reality` and
verify all copy, titles, and accessible labels render in that language.

- [x] T011 [US1] [FR-003] [FR-007] Implement `resolveTranslation`, the numeric-placeholder key rule, and the original-content rule in `provider-site/src/localization-core.ts`
- [x] T012 [US1] [FR-003] [FR-004] [FR-005] Implement the translating `LocalizationProvider`, `t()`, document-language handling, and attribute translation in `provider-site/src/localization.tsx`
- [x] T013 [US1] [FR-002] [FR-006] Convert `provider-site/src/LandingPage.tsx` to English source only and remove the `copy.de` branch, preserving the German wording for the catalog
- [x] T014 [US1] [FR-002] [FR-006] [FR-008] Convert `provider-site/src/PlatformPage.tsx` to English source only, including the price and capacity sentences and the localized document title
- [x] T015 [US1] [FR-002] [FR-006] Convert `provider-site/src/WhyRealityPage.tsx` to English source only, including the localized document title
- [x] T016 [US1] [FR-002] [FR-010] Convert `provider-site/src/components/PublicHeader.tsx` to English source only while keeping the language control invariant
- [x] T017 [US1] [FR-006] Add the extracted German catalog covering the complete inventory in `provider-site/src/localization.tsx`
- [x] T018 [US1] [FR-001] Add the Dutch catalog covering the complete inventory in `provider-site/src/localization.tsx`
- [x] T019 [US1] [FR-001] Add the Spanish catalog covering the complete inventory in `provider-site/src/localization.tsx`
- [x] T020 [US1] [FR-009] [FR-013] Declare the site's invariant strings with reasons in `provider-site/scripts/i18n-invariants.mjs`
- [x] T021 [US1] [FR-004] Wire every public route to the translating provider in `provider-site/src/PlatformPage.tsx` and `provider-site/src/WhyRealityPage.tsx`

**Checkpoint**: All four languages render complete copy on all public routes.

## Phase 4: User Story 3 — Durable Coverage Gate (P2)

**Goal**: Incomplete advertised-language coverage fails the site gate.

**Independent Test**: Run the audit against complete catalogs, then against each injected
regression, and confirm the reported language and string.

- [x] T022 [US3] [FR-011] Implement the inventory walk and catalog comparison in `provider-site/scripts/i18n-audit-lib.mjs`
- [x] T023 [US3] [FR-012] Implement missing/invalid classification, protected-term checking, and the per-language report in `provider-site/scripts/i18n-audit-lib.mjs`
- [x] T024 [US3] [FR-014] Add the gate entrypoint with a non-zero exit on failure in `provider-site/scripts/i18n-audit.mjs`
- [x] T025 [US3] [FR-014] Register the audit and new tests in the site gate in `provider-site/package.json`
- [x] T026 [US3] [FR-017] Extend the independence contract to reject product-web imports from site sources and scripts in `provider-site/scripts/site-contract.test.mjs`

**Checkpoint**: `npm test` and `npm run i18n:audit` pass with only site dependencies and fail on injected regressions.

## Phase 5: User Story 2 — Selection Survives Navigation (P1)

**Goal**: A selected language survives route changes, reloads, and account links.

**Independent Test**: Navigate all public routes in each language and follow the account
links.

- [x] T027 [US2] [FR-015] [FR-016] Verify four-language `?lang=` round-trips and account-link preservation in `provider-site/scripts/site-contract.test.mjs`
- [x] T028 [US2] [FR-016] Confirm cross-route language-preserving links on every public route in `provider-site/src/LandingPage.tsx`, `provider-site/src/PlatformPage.tsx`, `provider-site/src/WhyRealityPage.tsx`, and `provider-site/src/components/PublicHeader.tsx`

## Phase 6: Verification and Contract Updates

- [x] T029 [FR-001] Run the complete site gate and record the audit report and build result in `specs/034-public-site-localization/quickstart.md`
- [x] T030 [FR-001] [FR-006] Re-point the existing bilingual copy assertions at the English sources and the German catalog in `provider-site/scripts/site-contract.test.mjs`
- [x] T031 [FR-018] Update the language scope in `specs/022-public-site/spec.md` FR-015 and FR-025
- [x] T032 [FR-018] Update the public-site language contract in `docs/WEB_SPEC.md`
- [x] T033 [FR-018] Update the Public Site evidence row in `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T035 [US1] [FR-019] Add the locale money-format proof, original-content marking, and bare-amount catalog guard in `provider-site/scripts/site-localization.test.mjs`
- [x] T036 [US1] [FR-019] Implement `formatMoney` in `provider-site/src/localization-core.ts` and render the cloud price, self-hosted price, and finance amount through it in `provider-site/src/PlatformPage.tsx` and `provider-site/src/WhyRealityPage.tsx`
- [x] T037 [US1] [FR-020] Remove copy that renders nowhere from `provider-site/src/LandingPage.tsx` and prune its catalog entries in `provider-site/src/localization.tsx`
- [x] T038 [FR-014] Keep the site gate ordered `format:check` → `test` → `i18n:audit` → `build` in `provider-site/package.json`, `Makefile`, and `.github/workflows/quality.yml`
- [x] T034 Review the final diff against `spec.md`, `plan.md`, and the Constitution, and confirm no schema, service, API, or product-web change

## Dependencies

- Phase 2 precedes Phase 3 and Phase 4; the proofs must be observed failing first.
- T011 and T012 precede T013–T016, which precede the catalogs T017–T019.
- T022–T024 depend on T020 for invariant declarations.
- Phase 6 contract updates run only after T029 is green.
