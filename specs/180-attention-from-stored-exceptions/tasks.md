# Tasks: Attention Reads from the Stored Exceptions Projection

**Language**: English

Feature 179 (#229) and PR #227 merged on 2026-09-12; implemented the same day.

- [x] T001 Service tests: stored register and summary with builders and derivations forbidden; filters; refusals; uninitialized company; metadata present and consistent.
- [x] T002 `attention_register` and `attention_summary` read the `exceptions` projection rows and metadata of one generation; no refresh, enqueue, commit or cache write.
- [x] T003 `attention_detail`: distinct cleared-since-last-calculation classification when a stored finding no longer derives; service test that clears a finding before refresh.
- [x] T004 HTTP boundary: existing fields unchanged, `metadata` added, cleared case safe and distinguishable.
- [x] T005 `AttentionPage`: `ProjectionFreshness` line, prior rows kept while pending, uninitialized wording, cleared case in the preview, read-only refresh.
- [x] T006 `ExceptionRulesRegister`: counts and preview from the stored path, same freshness line.
- [x] T007 Localization (de, nl, es) and i18n audit.
- [x] T008 Browser fixtures for the four states in the operations and inspector suites.
- [x] T009 Measure register and summary on the local stack company; record before/after in the PR.
- [x] T010 Ruff, targeted pytest modules, prettier, tsc, contract tests, spec policy check.

## Phase 8: Refresh feedback (FR-009)
- [x] T030 [FR-009] Assert the in-flight state, both outcomes, the backlog and four languages in `apps/web/scripts/projection-freshness-browser.mjs`; it fails against the notice as shipped, which exposes no busy state.
- [x] T031 [FR-009] Report the outcome in `apps/web/src/unified/ProjectionFreshness.tsx`, pass the read's loading state from `AttentionPage.tsx`, `FinancePage.tsx`, `ExceptionRulesRegister.tsx`, `PaymentCard.tsx` and `ProjectionDataDialog.tsx`, and localize in `localization.tsx`.


## Stable refresh feedback (FR-009 refinement)
- [x] T032 [FR-009] Add browser regressions for stable button/notice geometry on repeated fast/slow reads, explanatory outcomes, read failures, four languages and mobile/desktop; observe failure before implementation.
- [x] T033 [FR-009] Update ProjectionFreshness.tsx and localization.tsx; pass read error from AttentionPage, FinancePage, ExceptionRulesRegister, PaymentCard and ProjectionDataDialog.
- [x] T034 [FR-007, FR-009] Run required frontend/spec checks and review the diff; record verification.

## Minimum spinner feedback (owner refinement)
- [x] T035 [FR-009] Extend browser regression for immediate spinner, minimum one-second visibility on fast reads, long-read coverage, stable geometry and reduced motion.
- [x] T036 [FR-009] Add a cleaned-up minimum feedback timer and reserved spinner slot in ProjectionFreshness.tsx; preserve error and read-only semantics.
- [x] T037 [FR-009] Run browser, build, frontend contracts, localization, formatting and spec checks; record review evidence.

## Compact timestamp and action (owner refinement)
- [x] T038 [FR-009] Verify screen-reader-only outcome feedback and adjacent timestamp/button geometry; remove the visible feedback row while preserving spinner, failure and backlog semantics.

## Persistent refresh affordance (owner refinement)
- [x] T039 [FR-009] Assert visible static idle/completed icon, rotating busy icon and keyboard activation in projection-freshness-browser.mjs; preserve minimum-duration, geometry and reduced-motion checks.
- [x] T040 [FR-009] Replace the hidden LoaderCircle with persistent RefreshCw in ProjectionFreshness.tsx; run required frontend checks and record review.
