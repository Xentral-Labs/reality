# Verification: Refined workspace shell

## Environment and scope

Worktree `/private/tmp/reality-225`, branch `225-refined-workspace-shell`, based on
`origin/main` at `5130b476`. Original checkout changes were not imported or modified.
Local Vite preview used port 5225. Browser fixtures contain synthetic records and
make no real business writes. Chromium only; Safari/Firefox are not claimed.

## Test-first evidence

The new acceptance script failed before implementation at `60 !== 48` for the
content header. Final acceptance checks verify actual geometry and interactions,
not only source text.

## Required checks

- Spec policy and Ruff: PASS.
- Web formatting, 232 Node contract tests, four-language audit (1896 strings per
  language), TypeScript and production bundle: PASS, including the final rerun.
- Generated documentation catalog check: PASS, no generated diffs. Initially the
  isolated checkout lacked the docs formatter dependency; linking the installed
  dependencies restored the generator's normal formatting step.
- `git diff --check`: PASS.
- `scripts/ci_backend_changes.py`: `changed=false`, matching the web-only scope.

## Browser acceptance

- Refined shell: company placement, 48px aligned headers, description Escape/focus,
  chat draft retention, company isolation, Activity, populated action popover,
  profile theme toggle, standalone chat, short-height profile and 32 combinations
  of four languages, four widths and two themes. Touch targets cover collapsed
  navigation, utilities, company/status controls, chat controls and action entries.
  Final mobile action-dismissal and touch-menu rerun: PASS.
- Collapsible navigation: PASS; keyboard, tooltips, profile/company access, stored
  preference, blocked-storage fallback, draft preservation and mobile behavior.
- Live simulation: PASS; eligibility, all non-running/error states, timeout/recovery,
  hidden-page behavior, reduced motion and stale-company response suppression.
- Page introductions: PASS; 46 desktop/mobile route layouts and three translations,
  with unavailable business reads and accessible description disclosures.
- Title counts: PASS; 18 registers, zero/filter/error recovery, nested catalog,
  navigation and mobile actions. Lower technical disclosure is exercised by keyboard
  because the existing fixed footer can intercept a pointer click there.
- Action discovery with `LAUNCHER_ONLY=1`: PASS; catalog navigation/search, launcher
  dispatch, failed-catalog recovery and mobile bounds; zero business writes. Old
  finance toolbar assertions remain available in the full script, outside this scope.

## Optional backend diagnostic

An additional parallel PostgreSQL run was interrupted after the first failure to
inspect it: **1448 passed, 1 failed, 2 skipped** in 597 seconds. The failure was
`tests/scenarios/test_international_demo.py::test_canonical_profile_counts_and_cases`
with `JobError("handler_timeout")`. The unchanged test then passed alone in 12.35s.
This supports a load-related timeout but does not prove the entire backend suite
passes. No backend implementation, fixture or timeout was changed. The full backend
suite is neither required by the CI changed-path gate nor claimed complete here.

## Visual review

Inspected German desktop light/dark, 1024px dark, mobile dark and collapsed-rail
screenshots. Shell headers align, company/global controls have separate homes and
long company names truncate without page overflow. Theme screenshots disable CSS
transitions to capture the settled appearance. Artifacts are in
`/private/tmp/reality-225-browser/`. No production deployment or merge performed.
