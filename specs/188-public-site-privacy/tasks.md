# Tasks: Public Site Privacy and Legal Information

**Input**: Approved `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/public-site-privacy.md`, `quickstart.md`.
**Gate**: Eight Constitution rows PASS; run analysis before implementation. Technical task status is recorded below; manual review and publication tasks remain pending.
**Language**: English. No business schema or backend feature is justified.

## Format and execution rules

Tasks use `- [ ] Tnnn [P?] [USn?] [requirements] action with exact paths`.
Tests precede the changes they prove; record initial failing evidence where practical.
`[P]` means independent file work after stated prerequisites, not permission to skip dependencies.
This list is an implementation plan, not authorization to publish or obtain legal approval on someone's behalf.
Manual review tasks are explicit evidence requirements, not checks an agent may self-certify.

## Phase 1: Setup and design gates

- [x] T001 Confirm scope approval, eight Constitution PASS rows and absence of blocking analysis findings in `specs/188-public-site-privacy/spec.md`, `plan.md` and `tasks.md`; record the reviewed revision and analysis outcome in `specs/188-public-site-privacy/verification.md` before implementation.
- [x] T002 Inspect the current checkout and isolate implementation from unrelated work; record baseline revision, toolchain/browser availability and required check commands in `specs/188-public-site-privacy/verification.md`; do not switch or overwrite another task's checkout.

## Phase 2: Foundational prerequisites

- [x] T003 [FR-002, FR-003, FR-005, FR-013, FR-015] Define fictional complete/incomplete/stale deployment fixtures in `provider-site/scripts/fixtures/legal/` and a pending dossier structure in `docs/privacy/releases/README.md`; distinguish input review, candidate approval and post-deploy evidence, with no fake human approvals in real records.
- [x] T004 [FR-001, FR-004, FR-006, FR-007, FR-014, DR-003] Add a reusable isolated-context harness in `provider-site/scripts/public-privacy-browser.mjs` using existing Playwright environment inputs; record requests, storage operations and viewport/screenshots, catch unknown destinations, redact personal data, and establish failing baseline observations in `specs/188-public-site-privacy/verification.md`.

## Phase 3: US1 — Identify the operator and understand processing (P1)

**Independent proof**: Eight complete legal documents, footer access, direct/reload/no-script routing and readable localized presentation. Real legal accuracy requires T031–T032 in addition to fixture tests.

- [x] T005 [P] [US1] [FR-001, FR-002, FR-003, FR-004] Add failing fixture-driven validation/render tests in `provider-site/scripts/legal-content.test.mjs` for missing/applicable facts, four-locale completeness, official identifier preservation, escaped text, safe links and complete no-script HTML.
- [x] T006 [US1] [FR-001, FR-004] Add failing footer/route tests in `provider-site/scripts/public-privacy.test.mjs` and legal-page cases in `provider-site/scripts/public-privacy-browser.mjs`: all eight routes, slashless normalization, refresh, missing legal path error, local assets, keyboard/mobile and scripts disabled.
- [x] T007 [US1] [FR-001, FR-002, FR-003, FR-004] Implement pure structured-input validation and escaped localized document rendering in `provider-site/scripts/legal-content.mjs`; use fixture inputs only in tests and prohibit executable/raw HTML content.
- [x] T008 [US1] [FR-001, FR-004] Implement static legal generation in `provider-site/scripts/generate-legal-pages.mjs` and integrate the same renderer with `provider-site/vite.config.ts` and `provider-site/package.json`; emit eight HTML documents with local CSS, native locale/footer/return links, titles and lang attributes.
- [x] T009 [US1] [FR-001, FR-004] Add localized direct legal links in `provider-site/src/components/PublicFooter.tsx`, `provider-site/src/site-routing.ts` and `provider-site/src/localization.tsx`; preserve explicit language on return links and keep legal HTML outside the React translation observer.
- [x] T010 [US1] [FR-001] Configure `provider-site/nginx.conf` to serve legal documents before SPA fallback, normalize legal URLs and return an error for missing legal documents; test the actual built image routing using `provider-site/scripts/public-privacy-browser.mjs` without publishing it.
- [ ] T011 [US1] [FR-001, FR-004] Run independent fixture-based US1 checks and manual keyboard/screen-reader/mobile inspection; record results and any remaining translation-review dependency in `specs/188-public-site-privacy/verification.md`.

## Phase 4: US2 — Browse with minimum processing (P1)

**Independent proof**: No optional/external asset traffic, no durable language preference, narrow legacy cleanup and preserved explicit Site/Docs/App handoff.

- [x] T012 [P] [US2] [FR-007, DR-003] Add failing pure-language tests in `provider-site/scripts/shared-language.test.mjs`: URL/in-memory precedence, explicit English, preserved query/hash, no inferred persistence, no legacy value reads, only targeted deletion, blocked storage and known-domain cookie scope.
- [x] T013 [P] [US2] [FR-007, DR-003] Add failing entry/redirect tests in `apps/web/scripts/entry-routing.test.mjs` for validated lang preservation and unchanged auth destinations; add account-load versus explicit-save coverage to `provider-site/scripts/shared-language-browser.mjs` using synthetic account responses.
- [x] T014 [US2] [FR-006, FR-007, FR-008, FR-014] Extend `provider-site/scripts/public-privacy.test.mjs` and `public-privacy-browser.mjs` with fresh/returning/default/blocked-storage journeys, zero external asset/preconnect requests, no-banner behavior and preservation of unrelated storage; update `provider-site/scripts/shared-language-browser.mjs` for Docs internal topics/reload, nl/es fallback, explicit en/de switches and bare-URL defaults.
- [x] T015 [US2] [FR-007, DR-003] Replace durable reads/writes in `apps/shared/language.ts` with explicit URL/current-page language, surgical URL updates and best-effort deletion only of `reality.language` and host/known-parent `reality_language` cookies; preserve server profile fallback and unrelated storage.
- [x] T016 [US2] [FR-007] Remove mount persistence and duplicate destructive URL rewriting in `provider-site/src/localization.tsx`, `LandingPage.tsx`, `PlatformPage.tsx`, `WhyRealityPage.tsx` and `components/PublicHeader.tsx`; carry explicit lang through internal navigation including English.
- [x] T017 [US2] [FR-007, DR-003] Update `apps/docs/.vitepress/theme/components/LanguageBridge.vue` and `ProductLink.vue` to preserve URL language through internal Docs links, nl/es English fallback and external handoff; replace storage-based readiness in `apps/docs/scripts/header-browser-check.mjs` with rendered-state readiness.
- [x] T018 [US2] [FR-007, DR-003] Update `apps/web/src/Auth.tsx` and `entryRouting.ts` to preserve explicit language through entry aliases and profile redirects without automatic preference writes; keep explicit profile saves on existing services and update legacy-language setup in `apps/web/scripts/company-danger-zone-browser.mjs`.
- [x] T019 [US2] [FR-006] Remove remote font requests/preconnects in `provider-site/index.html`, use system font stacks in `provider-site/src/site.css` and `landing.css`, and replace the remote Xentral logo with text in `provider-site/src/LandingPage.tsx`; record asset provenance/remaining local-asset rights in `specs/188-public-site-privacy/verification.md`.
- [x] T020 [US2] [FR-007, DR-001, DR-002, DR-003] Update `specs/176-shared-language/spec.md` and `docs/WEB_SPEC.md` to state navigation-only anonymous language retention, preserved authenticated profile preference and unchanged business/service boundaries; explicitly qualify the old bare-URL reopen scenario.
- [x] T021 [US2] [FR-006, FR-007, FR-008, FR-014, DR-003] Run US2 language and network/storage proofs across Site/Docs/App, including known production-like subdomains and unavailable storage; record no unexpected account mutations or preference recreation in `specs/188-public-site-privacy/verification.md`.

## Phase 5: US3 — Optional-service boundary (P1, conditional)

**Independent proof**: Empty optional inventory and absent banner; a nonempty optional configuration fails before public release. This does not claim implementation of consent controls.

- [x] T022 [US3] [FR-008, FR-009, FR-010, FR-011, FR-012] Add failing empty/nonempty optional-inventory tests in `provider-site/scripts/legal-content.test.mjs` and absence-of-banner/settings tests in `provider-site/scripts/public-privacy.test.mjs`; demonstrate that an optional service cannot inherit release eligibility merely from operator approval.
- [x] T023 [US3] [FR-008, FR-009, FR-010, FR-011, FR-012] Enforce empty optional inventory in `provider-site/scripts/legal-content.mjs` and document the conditional status and required future consent test matrix in `docs/features/public-site-privacy.md`; do not add a consent manager or runtime storage.
- [x] T024 [US3] [FR-008, FR-009, FR-010, FR-011, FR-012] Run US3 baseline checks and record in `specs/188-public-site-privacy/verification.md` that runtime consent scenarios are inapplicable only while the verified optional inventory is empty; if a service must be retained, stop that activation and revise plan/tasks/analyze before implementing it.

## Phase 6: US4 — Release evidence and maintenance (P1)

**Independent proof**: Missing, stale or fixture evidence cannot authorize publication; deployment observations match reviewed inputs and changes reopen approval. Technical checks run with fixtures; real reviews remain manual dependencies.

- [x] T025 [US4] [FR-005, FR-013, FR-014, FR-015] Add failing release-gate cases in `provider-site/scripts/legal-content.test.mjs` and `public-privacy.test.mjs` for unknown inventory, fixture artifacts, missing reviewer/evidence, changed digests, other-operator deployment mismatch and absent candidate approval; distinguish input validation from post-build candidate promotion and post-deploy verification.
- [x] T026 [US4] [FR-005, FR-013, FR-014, FR-015] Implement input completeness/version checks and post-build artifact eligibility validation in `provider-site/scripts/legal-content.mjs` with command entrypoints in `generate-legal-pages.mjs` and `provider-site/package.json`; candidate digest/approval must remain outside the hashed candidate artifact to avoid self-reference or rebuilding after approval.
- [x] T027 [US4] [FR-013, FR-014] Wire `provider-site/Dockerfile`, `.github/workflows/quality.yml`, `.github/workflows/deploy-testing.yml` and `scripts/deploy_railway_demo.sh` to separate non-publishable fixture builds from release candidates and require the same artifact's approval before public promotion; fail closed for unknown operator/preview mode and test workflow guards without pushing or deploying.
- [x] T028 [US4] [FR-005, FR-013, FR-015] Create a clearly pending public deployment input in `provider-site/legal/deployment.json` and an input/ownership guide in `docs/privacy/releases/README.md`; inventory hosting/CDN/security logs and Site/Docs/App boundaries, leaving unverified facts blocked and linking private evidence outside public assets.
- [x] T029 [US4] [FR-014, FR-015] Add deployed/candidate audit modes to `provider-site/scripts/public-privacy-browser.mjs` and document canonical/www, host-added processing, logging review, coordinated Site/Docs/App rollout, compliant rollback and six-month review in `docs/features/public-site-privacy.md`; no scheduler or automatic provider mutation.
- [x] T030 [US4] [FR-005, FR-013, FR-014, FR-015] Exercise gate failures, preview rejection, change invalidation and remediation ownership using fixtures; record results in `specs/188-public-site-privacy/verification.md` and a pending real-deployment dossier under `docs/privacy/releases/` without claiming publication approval.
- [ ] T031 [US4] [FR-002, FR-003, FR-004, FR-005, FR-013] Obtain verified operator facts and qualified review of actual inventory, provider/transfer arrangements, jurisdiction and legal translations; populate `provider-site/legal/deployment.json` and `provider-site/legal/content/en.json`, `de.json`, `nl.json`, `es.json` only from reviewed inputs, and record reviewer/date/evidence under `docs/privacy/releases/`; this task remains blocked until real inputs and review exist.
- [ ] T032 [US4] [FR-002, FR-003, FR-004, FR-005, FR-013, FR-015] Compare generated real legal pages against supplied facts and all four approved translations; record manual operator, privacy/legal, screen-reader and hosting review evidence and outside-scope follow-up owners under `docs/privacy/releases/`; do not replace human approvals with automated validation.

## Phase 7: Cross-cutting verification and review

- [x] T033 [FR-001, FR-004, FR-006, FR-007, FR-014, DR-003] Run `make site-build`, `make web-build`, `make docs-build` and all privacy/language/browser proofs from `specs/188-public-site-privacy/quickstart.md`; record actual commands, candidate identity, results and screenshots in `specs/188-public-site-privacy/verification.md`.
- [x] T034 [DR-001, DR-002, DR-003] Run `make lint`, complete required PostgreSQL `make test`, `make spec-check` and `make docs-catalog-check`; verify no schema/migration or catalog behavior changed and record results in `specs/188-public-site-privacy/verification.md`.
- [x] T035 [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, DR-001, DR-002, DR-003] Review final diff, requirement coverage, no-schema decision, static route contract and rollout/rollback against `specs/188-public-site-privacy/spec.md` and `plan.md`; record unresolved checks and reviewer in `verification.md`, never marking conditional or manual work falsely complete.
- [ ] T036 [FR-013, FR-014, FR-015] After T031–T035 pass, assemble pre-publication approval bound to the tested candidate artifact in `docs/privacy/releases/`; retain pending publication status until the operator authorizes actual deployment. This task prepares evidence and does not deploy.
- [ ] T037 [FR-001, FR-005, FR-014, FR-015] After separately authorized publication of the approved artifact, audit canonical/www hosts and actual hosting/logging configuration using `provider-site/scripts/public-privacy-browser.mjs`; record post-deploy results under `docs/privacy/releases/` and disable/remediate or roll back failures through the authorized operator process.
- [ ] T038 [FR-014, FR-015] Update `docs/features/public-site-privacy.md`, `specs/188-public-site-privacy/quickstart.md`, `verification.md` and task checkboxes with verified evidence only; keep pending legal/publication/deployment items visible and do not mark the feature or `docs/V0_CHECKLIST.md` complete while required checks remain open.

## Dependencies and parallel opportunities

- T001 → T002 → T003 → T004 precede story work. Analysis is a pre-implementation gate,
  not a self-dependency requiring completion of implementation tasks.
- US1: T005/T006 tests → T007 → T008 → T009/T010 → T011. T006 follows T004's harness.
- US2: T012/T013 may run independently after foundations; T014 follows T006 because
  they share browser files. T015 follows T012; T016–T018 follow relevant tests and T015.
  T019 follows T014. T020 and T021 follow the implemented shared behavior.
- US3: T022 → T023 → T024 after US1's validator and US2's essential-only baseline.
- US4 technical lane: T025 → T026 → T027 → T028 → T029 → T030. The input guide T028
  can be drafted early, but unknown facts must never be made up to unblock a task.
- T031–T032 are manual-input/review dependencies; they do not block fixture-based coding
  or T033–T035. They do block real-release completion and T036.
- T033–T035 follow all technical story work. T036 requires both review and test lanes.
  T037 needs real publication, not just a completed local implementation. T038 can record
  partial evidence at any time, but its completion requires the whole required dossier.

Parallel examples: US1 renderer test work T005 can run beside US2 pure-language tests T012
and App routing tests T013 after foundations. Later Site, Docs and App adapters may be
worked independently once the shared helper contract is fixed; coordinate shared test-file
edits. US3 shares the validator and must not race US1/US4 edits. US4 operator evidence can
be collected while technical tests run. These are scheduling opportunities, not a request
to spawn agents for this task generation.

## Implementation strategy

The first reviewable increment is US1 with fictional local preview inputs. It is not a
publicly releasable MVP. A public release needs all four stories' applicable requirements,
real reviewed information, all verification gates and deployment evidence. Deliver helper
rules before adapters and deployment integration; domain/services/tools stay unchanged.
If operator facts are unavailable, complete and review the technical work with fixtures,
then report T031–T032/T036–T037 as pending rather than inventing legal content or approval.

## Requirement coverage

All statuses are Pending. Conditional rows map to enforced inapplicability, not implemented consent UI.

| Requirement | Test/review tasks                        | Implementation/documentation tasks |
| ----------- | ---------------------------------------- | ---------------------------------- |
| FR-001      | T006, T010, T011, T033, T037             | T007–T010                          |
| FR-002      | T005, T031–T032                          | T007, T028, T031                   |
| FR-003      | T005, T031–T032                          | T007, T028, T031                   |
| FR-004      | T005–T006, T011, T032–T033               | T007–T009, T031                    |
| FR-005      | T025, T030–T032, T037                    | T026, T028–T029                    |
| FR-006      | T014, T021, T033                         | T019                               |
| FR-007      | T012–T014, T021, T033                    | T015–T020                          |
| FR-008      | T014, T022, T024                         | T023                               |
| FR-009      | T022, T024                               | T023 (conditional)                 |
| FR-010      | T022, T024                               | T023 (conditional)                 |
| FR-011      | T022, T024                               | T023 (conditional)                 |
| FR-012      | T022, T024                               | T023 (conditional)                 |
| FR-013      | T025, T030–T032, T036                    | T026–T028, T031                    |
| FR-014      | T004, T014, T025, T030, T033, T035, T037 | T026–T029, T038                    |
| FR-015      | T025, T030, T032, T035–T037              | T026, T028–T029, T038              |
| DR-001      | T034–T035                                | T020                               |
| DR-002      | T034–T035                                | T020                               |
| DR-003      | T012–T013, T021, T033–T035               | T015, T018, T020                   |
| SC-001      | T006, T011, T033, T037                   | T007–T010                          |
| SC-002      | T014, T021, T033                         | T015–T019, T023                    |
| SC-003      | T025, T030–T032, T037                    | T026, T028, T031                   |
| SC-004      | T022, T024                               | T023 (conditional)                 |
| SC-005      | T030, T032, T036–T037                    | T026–T029                          |
| SC-006      | T033–T035, T038                          | T020, T029, T038                   |

## Implementation status (2026-09-13)

32 technical tasks are complete. T011 remains partially complete because actual human
screen-reader review is pending. T031/T032 require verified operator/provider facts and
qualified legal/translation review; T036/T037 require real publication approval and a
post-deploy audit. T038 cannot certify full completion until those checks exist.
See [verification.md](verification.md); no public deployment was performed.

## Hosting extension tasks (FR-016–FR-018)

- [x] T039 Record approved hosting scope, design, test plan and analysis.
- [x] T040 Add and observe failing infrastructure safety/verification tests.
- [x] T041 Implement private S3 prerequisite, Helm overlay and duplicate-log suppression.
- [x] T042 Implement metadata-only live verifier and ordered operational runbook.
- [x] T043 Run local checks and record actual results; review against FR-016–FR-018.
- [ ] T044 Apply AWS prerequisites with supplied administrator roles and authenticated access.
- [ ] T045 Enable ALB logging, roll out server changes and set all error/application collector retention.
- [ ] T046 Verify real delivery, permissions, retention and effective logging; update final inventory before legal publication.

Dependency order: T039 → T040 → T041/T042 → T043 → T044 → T045 → T046.
T044–T046 require live access. No task or hosting requirement is complete solely because
configuration files exist. FR-016 maps T040–T044/T046; FR-017 maps T040–T046; FR-018 maps
T040/T042/T043/T046. Existing legal review and publication tasks remain pending.

## Real-operator draft tasks (FR-019)

- [x] T047 Review request, source discrepancies, draft-mode design and traceability; no critical analysis findings.
- [x] T048 Add failing draft-mode tests, including candidate rejection and indexing protection.
- [x] T049 Implement explicit draft mode and four real-operator legal review drafts.
- [x] T050 Run tests/build and verify all eight local Docker URLs; retain publication blockers.

Order: T047 → T048 → T049 → T050. Unanswered legal/hosting questions continue to block
T031/T032/T036/T037; they do not block local draft review.

## Railway release-gate regression tasks (FR-014)

- [x] T051 Add a failing contract test proving Railway uses an explicit non-canonical
      draft, requires provider URL inputs and cannot enter the AWS production release path.
- [x] T052 Add the Railway-specific demo image and document its URL and publication
      boundary without changing the approved AWS release path.

This bug fix restores FR-014 for the already documented Railway deployment boundary.
T051 precedes T052. It does not itself complete the pending legal/publication evidence.

## Final Railway demo legal-page tasks (FR-020)

- [x] T053 Verify Railway provider, transfer and Hobby log-retention facts against
      Railway's official privacy, DPA and logging documentation.
- [x] T054 Add failing generation and Docker contract tests for localized final demo
      pages, no AWS/draft wording, noindex and required Railway URL inputs.
- [x] T055 Implement the explicit Railway demo input overlay and legal generation mode
      without weakening preview, draft or canonical candidate validation.
- [x] T056 Run the complete Site suite, Docker build and deployed no-script smoke checks;
      record the resulting Railway deployment evidence.

Order: T053 → T054 → T055 → T056. No critical specification/plan/task inconsistency
remains; every FR-020 outcome has test and implementation coverage.
