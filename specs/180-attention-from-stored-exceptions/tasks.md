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
