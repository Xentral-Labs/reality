# Verification: Visible integration actions

## Pre-implementation review
User confirmation approved the scoped design. Spec Kit analysis: four functional requirements, six tasks, 100% coverage, zero ambiguities, duplicates, unmapped tasks, Constitution conflicts or critical findings. Checklist passed. No extension hooks configured.

## Regression evidence
The source browser test initially failed at the missing Settings control after stale header selectors were repaired. Before implementation both action pairs used hidden text and identical fallback icons.

## Development-workspace checks
- Frontend contracts: 203 passed.
- Localization audit: en/de/nl/es all covered, zero missing or invalid entries.
- Final TypeScript/Vite build passed (existing bundle-size advisory only).
- Shared table browser regression passed: density, sorting, selection/export, widths, keyboard/row navigation, sticky scrolling and 24 localized screenshots.
- First source browser run passed all four destinations, focus return, source filters, retry/company reset, zero writes and 48 screenshots. Visual review found sticky-column occlusion on mobile; scoped responsive fix and stronger hit-target assertion added. Final run passed, including rendered text bounds and hit-target checks in both densities, all four languages, both themes and both viewport widths. German desktop and mobile screenshots visually reviewed.
- Ruff passed from packages/reality-core.
- Spec policy passed.
- Generated documentation catalog has no diff.
- Full frontend formatting passed.

## Review and environment
Only Web presentation and test selectors change. Existing source/record click handlers remain exact; no domain, service, schema, commands, MCP or catalog changes. Existing unrelated working-tree edits were preserved. The shared table defaults to its existing compact icon presentation. Labeled tables release the sticky first column below 640px so controls remain reachable.

The system make command is blocked by an unaccepted Xcode license. Equivalent commands were executed directly. Chromium and PostgreSQL tests require execution outside the filesystem sandbox. The full backend suite was attempted with eight isolated test databases. `tests/scenarios/test_international_demo.py::test_canonical_profile_counts_and_cases` failed with `JobError("handler_timeout")` during demo profile seeding; the run was interrupted after 440 passed, two skipped and one failed (140 seconds). No backend files were changed by this feature. The isolated recheck passed in 6.47 seconds, consistent with load sensitivity. The final full-suite run without concurrent browser/build load passed: **2621 passed, 9 skipped**, one SQLAlchemy transaction warning, in 393.98 seconds (`pytest -n 8 -x`). T006 is complete. Source-settings browser regression passed, including review/cancel, duplicate handling, uncertain response recovery, company boundaries, pagination and eight localized screenshots.

## Final review

All planned gates passed through their direct command equivalents in the original development workspace. Final source/configuration/table browser checks, frontend contract tests, localization, formatting, build, Ruff, spec policy, generated catalog parity and full backend suite are green. `git diff --check` passed. No migration or catalog change is needed. Source-setting writes retain existing review/confirmation; the four table actions only navigate or open a dialog. Existing unrelated workspace changes remain untouched. No deployment performed.

## Isolated PR branch

Prepared on `origin/main` at `f8d73f74` in a separate worktree. Only the feature's eight source/test/documentation files and spec 210 are included; unrelated local edits were not copied. Rechecked frontend formatting, **211 contract tests**, all-language localization audit (1,889 entries), TypeScript/Vite build, source-configuration and shared-table browser regressions, specification policy and whitespace. The earlier backend result above belongs to the development workspace; no backend changes are included, and remote CI validates the PR commit. The source-browser rerun also passed all four destinations, both densities, accessibility/hit-target assertions, all-language mobile/desktop layouts, and zero mutations (48 screenshots).
