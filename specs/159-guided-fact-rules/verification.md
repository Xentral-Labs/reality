# Verification — guided Fact rules

## Original regression and restored scope

Pre-9b8394a App.tsx provided a structured condition/editor and evidence/result journey.
Unified RulesWorkbench had replaced these with JSON fields. The new components restore
that workflow inside the current register/modal; no backend, schema or rule semantics
changed. Existing source/Fact links and shared confirmed services remain in use.

## Test-first and review evidence

- Initial guided-rule-draft test failed because the new module did not exist.
- Typed conversion tests then caught advanced normalization being overwritten by defaults;
  the implementation now preserves the matching saved implementation proposal.
- Unit cases cover false/zero/decimal precision, lists, nested conditions, scope/line ID
  preservation, immutable draft conversion and malformed technical structures.
- Browser cases cover source examples, manual notes, empty search, recommendation,
  alternative destination, cancellation, creation, version editing, read-only simulation,
  activation, explicit replay continuation, member restriction, context reset, uncertain
  writes, keyboard Escape and German narrow-screen layout.
- Desktop and mobile screenshots are inspected under `/private/tmp/guided-rules-screens`.
- Local synthetic browser fixtures never write business data in user companies. Backend
  tests use disposable PostgreSQL databases through the repository test fixtures.

## Final gates

- `make spec-check`: passed.
- `make lint`: passed.
- Complete PostgreSQL suite: `../../.venv/bin/pytest -q -n 4 --tb=short`
  from `packages/reality-core`: **2,046 passed, 9 skipped in 427.00 seconds**.
- `make web-build`: passed, including **73 web tests**, en/de/nl/es i18n audit
  (**1,271/1,271 covered** each), TypeScript and Vite production build.
  Existing bundle-size warning remains.
- Guided browser acceptance passed against both the development build and the
  actual deployed production assets at localhost:8080. The final run includes
  manual evidence, alternative outcomes and reviewed new-question creation.
- `git diff --check`: passed. No new package, backend change, migration or external write.

## Local rollout and review

Only the web image was rebuilt/recreated from the active integration worktree using
root `.env`. API and MCP remain healthy; web is running on port8080. No database
migration, reset or user-company mutation was performed for this feature.
The typed draft, context isolation, exact simulation target, explicit replay cursor,
source references, confirmation lock and four-language layout were reviewed.

Logs: `/private/tmp/guided-rules-backend-all.log`, `guided-rules-web-verified.log`,
`guided-rules-deployed-browser.log`, `guided-rules-compose-build.log` and
`guided-rules-compose-up.log`. Browser screenshots are under
`/private/tmp/guided-rules-screens/`.


## Owner-approved usability refinement

The follow-up user screenshot identified an unintuitive empty Edit form. FR-009/010
now cover prefilled editing, honest setup wording, localized sentence, three sections,
progressive group controls and fixed review actions. Initial-draft tests failed before
implementation. A browser regression caught a one-frame empty value on opening;
layout initialization now populates before paint. Existing advanced definitions,
confirmed service calls, simulation and replay paths remain unchanged.

Refinement results:

- 74 web tests, en/de/nl/es audit (1,285/1,285 each), TypeScript and production build passed.
- Complete suite collected at start: 2,046 passed, 9 skipped in 234.32 seconds.
- Deployed-asset browser proof passed on localhost:8080, including prefilled existing
  fields, initial setup, original lifecycle, collapsed supporting evidence, and footer
  bounds at the top and bottom of the 390px dialog. Screenshots were inspected.
- Spec policy passed after adding the newly introduced Finance test-family coverage row.
- Shared-worktree qualification: while the suite ran, separate Finance opening work
  added test_opening.py and its implementation. A separate early collection check
  failed because the new service module had not yet been written. It now exists, but
  the final global Ruff check reports four I001 formatting errors in the concurrently
  edited Finance/core files. Those are outside this UI change and were not modified.
  The shared final gate remains pending; the UI acceptance checks are complete.

Only the web image was rebuilt/recreated using the root environment file. No migration
or backend deployment was performed. Logs: `/private/tmp/rules-usability-web-final.log`,
`rules-usability-backend.log`, `rules-usability-deployed-browser.log`,
`rules-usability-lint-final.log`, `rules-usability-concurrent-opening.log`.


## Isolated PR branch and unified example step

The PR is isolated from the active integration worktree's Finance changes.
FR-011 places supporting examples and saved-version testing together in step 3,
shows the selected source reference, removes technical rule JSON disclosures, and
keeps supplementary context/history under Further details.

- Production frontend build, all 75 web tests, formatting and four-language audit
  (1221 keys per language) pass.
- Spec policy and Ruff pass in the isolated branch.
- Browser fixture proof passes against the isolated production preview, including
  step-3 evidence containment and absence of technical rule definitions, reviewed
  lifecycle, original-value preservation, roles, stale context and mobile keyboard.
- Complete isolated PostgreSQL suite: **1976 passed, 9 skipped**, 683.33 seconds.
  The feature commit was rebased onto current main; no backend files changed.
- GitHub frontend, docs and spec-policy gates pass. The final documentation-only
  verification commit will trigger the normal CI refresh.
- The active integration web build initially hit a concurrent Finance compile error,
  corrected by the parallel work. The subsequent web-only build and rollout pass.
  The browser acceptance proof also passes against deployed port 8080. No backend
  rollout or migration was performed.
