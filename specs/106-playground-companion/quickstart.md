# Verification
Run pytest tests/test_playground_chat.py and existing provider/Playground tests.
Run frontend contracts, build and localization audit.
Check attention disclosure, suggestions, retained chat across central tabs, reset
on run switch, long conversation, narrow viewport and both themes.

## Evidence — 2026-09-07
- Test-first: three backend tests and two frontend contracts failed before implementation.
- Targeted API/provider/companion tests: 68 passed, including rejected mutation dispatch.
- Complete backend invocation from repository root: 1375 passed, 7 skipped, 11 migration
  failures because their relative alembic.ini requires the package working directory.
  Reran all 11 migration tests from packages/reality-core: 11 passed (14.14 seconds).
  No product changes were made for this invocation error.
- Frontend: 110 contracts passed; build, format, four-language audit (1214 keys) passed.
- Browser fixtures: full Playground journey and focused companion journey passed;
  question/answer, retained history across tabs, desktop light/dark and mobile composer.
  Screenshots: /private/tmp/reality-workspace-qa/companion-{light,dark,mobile}.png.
- Ruff, spec policy and diff checks passed. Local API healthy and web running after rebuild.
- Live model output was not used as test evidence: browser replies and provider failure
  are controlled fixtures. Deployment-managed key presence was checked without disclosure.
- Final review: no schema or business writes, no tenant supplied by the client, scope
  resets in finally; both tool discovery and dispatch enforce read access.

## Central chat and Markdown refinement
Owner-approved change: chat now occupies the central Ask Reality tab; attention
remains right. It stays mounted across tab changes. Speaker labels, headings, lists
and GFM tables render separately; overflow stays inside the table. Suggestions
collapse after the first answer. No backend changes or live provider replay.
Regression observed failing before implementation. Final verification: 111 contracts,
build, 1215-key localization audit, spec/diff checks and synthetic browser journey
passed, including two table rows, list items, retained conversation and mobile width.

## Compact timeline and chat focus
FR-007 verified with 112 frontend contracts, production build, four-language audit
(1216 keys), formatting and spec/diff checks. Both the focused companion browser
fixture and the full Playground journey passed with synthetic data. Browser checks
cover the default 44px recorder, explicit expansion, increased chat width, hidden
side columns, return button and Escape, retained messages, themes and mobile composer.
The full journey checks anchored action buttons with the default collapsed timeline
across reloads and expands the timeline before inspecting its events. Local web
deployment rebuilt successfully; no backend or business-record changes were needed.

## Worklist and conversation refinement
FR-008/009 supersede the focus-mode experiment. Test-first companion contracts failed
before changes, then all 113 frontend contracts passed. Build, formatting, spec/diff
and four-language audit (1218 scanned keys) passed. Full synthetic Playground journey
and final focused browser run passed. Browser covers grouped known/unknown classes,
formatted unreserved quantity, missing context, center record inspection, immediate
user message, spinner, provider failure, explicit retry without duplicate turns or
failed history, retained conversation, themes and mobile composer. Screenshots include
attention-worklist.png, companion-pending.png and companion-{light,dark,mobile}.png.
Final review: presentation labels do not derive business state; inspector reads remain
tenant-scoped; no complete/dismiss mutation, provider call or backend change introduced.

FR-005 duplicate-navigation cleanup: regression failed before removing the companion
links, then 114 contracts, production build and spec/diff checks passed. Central
register tabs and attention-detail navigation remain unchanged; unused callback removed.

FR-006 sender-label refinement: observed regression failure before replacing visible
You/Reality headings with article accessible names, including pending/error replies.
116 frontend contracts, production build and spec/diff checks passed. Message
alignment and content remain unchanged; no backend change.
