# Verification

## Passed
- `make lint` and `make spec-check`.
- `make web-build`: formatting, TypeScript/Vite build and four-language audit
  (1,843/1,843 strings in each language). Final `npm run test:i18n`: 167 passed.
- `make docs-build`: four generator tests, 67 documentation tests, formatting and
  VitePress build. `make docs-catalog-check`: generated vocabulary remains current.
- Chromium `apps/web/scripts/storyline-browser.mjs`: existing library/scripted flow,
  proposal confirmation, restart, autoplay and pause, plus Free Play draft handoff,
  no automatic writes, exactly one explicit send, lazy reply evidence and reload
  without resending. 32 layouts cover en/de/nl/es, light/dark and 390/1440px.
- Visually inspected Free Play German desktop dark and mobile light screenshots.
  Evidence is readable, the composer remains usable and no horizontal overflow occurs.
- `git diff --check`.

## Full backend suite
`PYTEST_ADDOPTS="-n 4 --dist worksteal --durations=15" make test`: **2,518 passed,
9 skipped, 1 warning**, in 375.67s. This includes all five new chat evidence tests.
The warning is the existing transaction-cleanup warning in
`test_storyline_library_api.py::test_a_chapter_is_prepared_confirmed_and_explained_over_http`.

## Test boundaries
Browser tests use deterministic HTTP fixtures. Backend tests replace only the LLM
provider transport, invoking real application tools and PostgreSQL. They do not call
an external model or mutate a live company. Production needs its existing configured
chat provider and allowance; this change introduces neither credentials nor a provider.

The first endpoint proof failed with 404 before implementation. The focused suite
then exposed a missing test import, which was corrected. An existing browser pause
assertion was moved before chapter navigation so it observes the pause control before
that navigation changes the selected chapter; the complete browser run then passed.
Temporary source-shape checks were replaced by behavioral browser assertions.

Builds report existing bundle-size notices. No schema migration or deployment is
included. Review conclusions are in analysis.md.

## Focus correction (FR-006)
The browser regression first failed waiting for input focus after a failed Enter
send. The shared input now remains read-only while busy, and ChatPage restores
focus after an explicit send settles, including session remounts. Deliberate focus
on another control is preserved. Both `unified-chat-composer-browser.mjs` and the
complete `storyline-browser.mjs` passed on the final code. `make web-build` (167
tests, locale audit, TypeScript/build), spec policy and diff checks passed.
No backend behavior changed, so the recorded full backend result remains applicable.
The built frontend was copied to the local 8080 preview; the served asset hash and
health endpoint were verified. No production deployment.

## Direct library entry (FR-007)
`storyline-browser.mjs` passed with the new card action: absent before a run exists,
opens the correct existing Sandbox directly at Free Play without writes, and returns
to the existing chapter. The complete 32-layout regression also passed.
`make web-build` (167 tests, translation audit, TypeScript/Vite), spec policy and
diff checks passed. No backend change or migration. The new frontend asset was
verified on localhost:8080 with a healthy API.

## Independent Free Play (FR-007–009)
- Full PostgreSQL run: 2,518 passed, 9 skipped, two initial failures in 507.82s.
  The spec-policy failure was a missing traceability section during spec revision;
  it was corrected. The existing 10,000-source benchmark exceeded its 60-second
  threshold under concurrent browser/build/test load. Both gates passed the isolated
  rerun: 2 passed in 13.02s, benchmark call 12.03s. No threshold was relaxed.
- Final focused chat/lifecycle suite: 8 passed, including the final ordinary-company
  collision guard, confirmed/idempotent creation, no story identity and archive.
- `make web-build`: 167 tests, 1,849/1,849 strings in each language, TypeScript and Vite.
- Final browser run: 48 en/de/nl/es light/dark mobile/desktop layouts; separate entry,
  no card buttons, confirmed creation, direct URL/reload, independent chat/session
  creation and retained history without Storyline messages. Existing scripted and
  contextual-chat flows, focus and evidence regressions also passed.
- Visually reviewed the exploration library and German standalone mobile light and
  desktop dark. Inputs remain usable and no horizontal overflow occurs.
- Lint, spec policy and diff checks passed. Public documentation now distinguishes
  contextual Sandbox chat from independent Free Play; generated-doc checks accompany it.
- Local API and frontend were updated on port 8080. Health, direct entry asset and
  authenticated entry route were verified. Existing data/configuration were retained;
  no local user Sandbox was created automatically and no production deploy occurred.

Browser transports remain fixtures; backend provider transport remains stubbed while
real tools run in disposable PostgreSQL. The final collision test was run in the
focused suite after the full suite had collected tests.

## Existing-company chooser amendment (2026-09-15)

The owner requested the current company, another accessible company, or creation of a
Sandbox. The chooser now uses shared bootstrap and presets the current company. It
never redirects based on a dedicated receipt. The explicitly opened company's URL
retains `play=chat`; changing company resets session/context. Ordinary companies are
labeled as working with real data. Existing proposal confirmation remains unchanged.
A 404 evidence read displays the existing unavailable-evidence message; no trace or
Sandbox run is fabricated for ordinary companies.

- Browser regression first failed on the missing company selector, then passed.
- Full Storyline browser passed, including existing-company selection without writes,
  dedicated Sandbox creation/reload, contextual chat/focus and 48 localized layouts.
- Supplemental company browser passed with an ordinary-company saved reply and 404
  evidence, current default, story/company switching, no cross-company history,
  read-only reopening and 390/1440 chooser screenshots. Both screenshots reviewed.
- Web build passed: 167 existing tests, four-language audit (1855/1855), TypeScript
  and Vite. An additional routing/reset regression passed with all 7 tests in its file.
- Lint, spec policy, docs build (4 generator tests, 67 docs tests) and generated
  catalog consistency passed.
- Backend is unchanged by this chooser amendment; the full-suite and focused
  PostgreSQL results above remain applicable.
- Local 8080 preview updated, health returned ok, direct Free Play served
  `index-xye8PTIa.js`. No production deployment.

Final review: shared company access and company selection remain authoritative.
No new schema, business logic, automatic mutation, data conversion or trace scope.

## Narrator exit correction (2026-09-15)

Removed the footer Sandbox chat shortcut. Back to selection uses the shared full-size
button with ArrowLeft and is primary after completion. The existing library callback
opens the exploration chooser without writes. Contextual saved URLs/drafts remain.
The updated contract failed before implementation and passed afterward. Web build
passed (168 tests, four-language audit 1853/1853, TypeScript/Vite). The browser passed
the absent shortcut, clear label and read-only return assertions along with scripted
steps and company-choice coverage. Spec policy and diff check passed. No backend or
generated catalog changes; their previous checks remain applicable. Local 8080 serves
`index-3a5vEx_6.js`. Final review: presentation only, no data or permission changes.

## Storyline-only sidebar entry (2026-09-15)

Removed the separate Free Play sidebar item and retained the single library tile.
Storyline remains highlighted on the Free Play route; its sidebar link opens the
selection. Direct URLs and current-company chat remain unchanged. The browser first
exposed an outdated expectation that sidebar navigation resumes a story immediately.
Updated that proof to open selection and resume through the story card. Final browser
run passed, including absent Free Play sidebar link, active Storyline, retained tile,
read-only return and company choice. Web build passed (168 tests, four-language audit,
TypeScript/Vite), as did spec policy, formatting, docs build and catalog consistency.
Local 8080 serves `index-ByrIIKZD.js`. Final review: navigation only, no backend changes.

## Prominent pending chat status (2026-09-15)

Shared ChatPage now renders an accent status panel with a solid icon tile, rotating
LoaderCircle and strong Reality is working label. It derives only from sending,
exposes role=status and disables decorative rotation for reduced motion. No fabricated
progress or tool claims. The composer browser passed immediate status, success/failure
cleanup, focus/voice/attachment regressions and computed animation checks for normal
and reduced motion. Screenshot reviewed. Web build passed (168 tests, four-language
audit 1853/1853, TypeScript/Vite); spec and diff checks passed. Local 8080 serves
`index-DVzMXZjN.js`. No backend or generated catalog changes.

## Conversation turn styling (2026-09-15)

Removed the CSS flattening of both roles. User turns now fit their content in neutral
right-aligned bubbles (maximum 85%); assistant turns remain unboxed and left-aligned.
Reading width is bounded and turns have more spacing. Author/time metadata remains
accessible without visual clutter, and evidence remains attached to its reply.
Shared composer browser passed role geometry/background assertions, immediate echo,
status/focus/attachment/voice behavior and light/dark mobile/desktop overflow checks.
Reviewed the pending-conversation screenshot. Web build passed (168 tests, four-language
audit, TypeScript/Vite); spec, formatting and diff checks passed. Local 8080 serves
`index-BvZk2txK.js`. No backend or generated catalog change.

## Compact allowance disclosure (2026-09-15)

Available allowance is a compact count pill with an Info icon. A native disclosure
reveals the exact localized reset time. Exhaustion keeps the existing explanation and
reset time visible; send remains disabled. Browser checks passed keyboard expansion,
pointer collapse, hidden reset before expansion, visible reset after exhaustion and
retained draft/disabled sending. Web build passed (168 tests, four-language audit,
TypeScript/Vite), as did spec and diff checks. Updated local 8080 preview. No backend
or catalog changes.

## Header usage and settings (2026-09-15)

Usage now sits in the shared chat header, or the outer Free Play header through a
portal target. Native popover details show actual used/remaining/reset information
and link to Settings → Usage. That read-only view uses the existing authorized
copilot allowance and handles absent allowance explicitly. Personal settings links
to Usage. No unreported plan or nonexistent upgrade target. Only exhaustion remains
near the composer, preserving reset explanation and disabled send.

Web build passed (168 existing tests, four-language audit, TypeScript/Vite). Added
usage routing regression passed with all 8 tests in its file. Free Playground browser
passed header placement, keyboard opening/Escape, usage settings navigation and
exhaustion behavior. Storyline/company browser passed outer-header portal placement,
absence from inner header/composer, chat, reload and tenant isolation. Spec, formatting
and diff checks passed. Local 8080 serves `index-DdUm5kt_.js`. No backend/schema or
generated catalog changes.

## Free Play scroll containment (2026-09-15)

Bound shell/body/main and the company-scoped content wrapper to the available viewport.
Removed the card's competing viewport/minimum height. Chat articles now position their
screen-reader metadata locally so absolute author labels cannot inflate document height.

The new integration assertions first exposed an unbounded content wrapper, then the
metadata overflow. Both were fixed. A dedicated browser path runs those same scroll
assertions with 24 long turns at 1440×900, 390×640 and 1440×500: message scrollTop changes
while header/composer positions and window scrollY remain stable; scroll boundaries
and reload stay contained. Final focused run passed. Computed document/body/viewport
heights matched in all three sizes; screenshots reviewed. Final web build, language
audit, spec policy, formatting and diff checks passed. An intermediate audit mistook
an inline class expression for text; extracting the class constant resolved it.
Other routes retain their scrolling; no backend/catalog change. Updated local 8080.

## Compact notebook toolbar (2026-09-15)

Replaced the two Free Play headers with one 48px toolbar. The company picker truncates,
return-to-selection uses an accessible arrow, and existing Usage/history/new-chat
controls render in the same toolbar. Other chat headers remain unchanged. On desktop
this recovers roughly 90px compared with the former company plus 64px chat headers.
Browser checks passed maximum toolbar height, absence of a second header, control
presence and history toggle operation, mobile overflow, contained long-history scroll
and reload at 1440×900, 390×640 and 1440×500. Screenshots reviewed, including mobile.
Web build, localization audit, spec and diff checks passed. Local 8080 serves
`index-C9mr7rG8.js`. No backend or catalog changes.

## Sessions beside the conversation (2026-09-15)

Company-scoped sessions now render in a left column outside the chat card. Narrow
screens use the history control to open a drawer. The active session is highlighted;
selection closes the drawer, and Escape restores focus. The opened chat no longer
has a Storyline link or an inline conversation selector. Other chat surfaces retain
their existing selector.

Focused browser checks passed session switching, active state, drawer dismissal,
Escape/focus restoration, desktop control visibility, and contained scrolling at
1440×900, 390×640 and 1440×500. Desktop screenshot reviewed; a custom icon display
rule initially overrode responsive hiding and was corrected and regression checked.
Web build, four-language audit, spec policy and diff checks passed. No backend,
schema or catalog changes. Updated local 8080 and PR 15.

## Free Play visual refinement (FR-016, 2026-09-15)

Removed the outer chat card frame/width cap, widened and separated the session
column, moved the labeled new-conversation action above sessions and outlined the
company picker. Zero allowance now replaces the composer with a compact reset status.
Normal chat surfaces and the authoritative allowance/session APIs remain unchanged.

Web build passed: 169 contract tests, TypeScript/Vite and four-language audit.
Focused browser passed responsive scrolling, drawer/session selection, labeled action
placement and its session-creation POST, zero-allowance input removal, reset display
and positive-allowance composer recovery. Reviewed desktop and mobile screenshots.
Fixture assertions were adjusted to include hidden mobile drawer controls and await
the session creation endpoint. Spec policy and diff checks passed; local 8080 updated.

## Main company context only (FR-017, 2026-09-15)

Free Play now opens directly using the shared company prop. Removed its chooser,
company button, Sandbox creation/read actions and redundant play-state flag. Legacy
play=chat URLs still work; companySelection clears session/draft/evidence and keeps
the route. Updated library/page introduction in four languages. No backend changes.

Browser checks passed direct library entry, global company switching, no writes,
real-company evidence fallback, draft/session isolation, reload and responsive layout.
The existing long-history session/scroll checks passed desktop/mobile/short viewports.
169 web tests, TypeScript/Vite, localization audit, spec policy and diff checks passed.
Reviewed desktop screenshot; local 8080 updated. Changes remain locally committed;
GitHub publication awaits the explicit approval requested in the previous turn.

## Standalone Chat feature (FR-018, 2026-09-15)

Promoted the company conversation to Chat at /app/chat, directly after Home in
primary navigation. Removed the Storyline library entry and its shared active state.
Renamed the adapter to CompanyChatPage. Former /app/free-play and /chat links
resolve to the canonical chat route with company/session context preserved.
The global company remains authoritative; tools, confirmations and usage are unchanged.

All 170 web tests, TypeScript/Vite build, four-language audit, spec policy and diff
checks passed. Browser checks verified navigation order/active state, absence of the
Storyline tile, global company switching with cleared draft/session/evidence, reload,
no company creation writes and responsive layout. Long-history checks passed on desktop,
mobile and short viewports, including session selection and composer recovery.
Reviewed desktop/mobile screenshots. Local 8080 serves index-DBAITsw3.js.
Review found no remaining issue for this adapter-only change; no backend/schema/catalog
changes. GitHub publication still awaits the previously requested explicit approval.

## Chat spacing (FR-019, 2026-09-15)
Removed page gutters, column gap and inner Chat title/desktop toolbar. Usage is
in the session footer; its popover is clamped within the viewport. Mobile keeps
the history control. The standalone empty greeting centers in the message area.

170 web tests passed; formatting, four-language audit, TypeScript/Vite, spec policy
and diff checks passed. The make wrapper was blocked by the host Xcode license;
its exact npm verification commands and spec checker were run directly instead.
Browser checks passed desktop/mobile/short-height scrolling, composer bounds,
empty-state centering, zero outer padding, zero desktop toolbar height and Usage
popover visibility within the viewport. Reviewed the desktop empty screenshot.
Synthetic new-session fixture reuses an ID, so the empty-state proof reloads its
cleared message data. Local 8080 updated. Review: no remaining issue.

## Learning introduction (FR-020, 2026-09-15)
Updated Storyline library heading, explanation and learning-path label in English,
German, Dutch and Spanish. Formatting, four-language audit, TypeScript/Vite build,
spec policy and diff checks passed. Local 8080 updated. Copy-only review confirms
existing story controls and Sandbox behavior are unchanged.

## Cross-company session recovery (FR-021)
Navigation now applies companySelection before merging destination fields when the
tenant changes. This fixes Storyline start/restart inheriting a previous-company
chat ID. Failed selected-session reads offer Back to chats without creating records.
The routing regression failed before implementation and passes afterwards; all 171
web contract tests passed. Browser proved invalid-session recovery, cleared URL and
company context isolation. Formatting, four-language audit, TypeScript/Vite, spec
policy and diff checks passed. Local 8080 updated. No server or data change.

## Automatic missing-session recovery (FR-022)
The specific selected ChatSession 404 is classified with its selection identity.
Generation-guarded reads and an effect replace the invalid URL selection and load
the current company's chat without showing an error or requiring a click. Other
failures keep the existing visible error and retry controls. No mutation is added.
171 contract tests, formatting, localization audit, TypeScript/Vite, spec policy
and diff checks passed. Browser checks prove no-click recovery, cleared URL, reload
and preserved 503 errors, followed by company isolation checks. Local 8080 updated.

## Compact session rows (FR-023, 2026-09-15)
- Scope review: owner requested a separate PR for denser session rows. FR-023 maps
  to T029 and measured browser geometry; no unresolved clarifications, uncovered
  requirements or critical analysis findings. Constitution Check: PASS.
- Test-first: the existing composer browser failed with button height 40 != 36
  before the responsive class change. It now passes: desktop button/row pitch
  36/36 px at 1440 px; mobile button/row pitch 40/44 px at 390 px.
- Existing selection/options, removal-dialog cancellation and composer checks pass.
  Desktop and mobile screenshots were visually reviewed.
- All 191 frontend contracts, TypeScript/Vite build, formatting, spec policy and
  diff whitespace checks pass. The existing bundle-size warning remains.
- Final review: only desktop padding and inter-row spacing change. No backend,
  schema, translations or executable catalog changes; their gates do not apply.

## Steady pending chat status (2026-09-15)

The streaming work bound the status to `sending && !visibleReply?.text`, so the first
streamed token hid it and the `reset` event that opens every tool round in
`mcp_chat.py` brought it back: one tool call made it blink. It derives only from the
pending send again, as FR-010 states. Because it is now on screen for the whole answer,
the accent panel with its 40px icon tile became a quiet status line aligned to the
composer's width, which is what FR-010 now asks for. Role, live region, reduced-motion
rotation and removal on success or failure are unchanged.

- `chat-stream-browser` asserts the indicator is present while text streams and gone
  after the recorded answer arrives; it passed, including reset, stale reload and the
  390px viewport.
- `unified-chat-composer-browser` passed its status, reduced-motion and failure-cleanup
  checks; its later session-history assertions belong to concurrent work in the shared
  checkout and were not run against this change.
- TypeScript build and the four-language audit (1878/1878) pass. No backend, schema or
  catalog change.

## Comfortable conversation navigation (FR-024, 2026-09-15)
- Owner approved wider history, one-line action labels and contextual options.
  Increment analysis: FR-024 maps to T030 and browser acceptance; no unresolved
  clarification or critical finding; Constitution Check PASS. The prerequisite
  helper resolved the active spec 207, so this review used the explicit spec 195
  artifacts without changing active feature state.
- Test-first browser failure: history width 240 != 288. After implementation, the
  full composer browser passes desktop/mobile geometry, idle/hover/focus/open-menu
  visibility, emulated touch visibility, actual German archive-label line count
  and overflow, existing selection and confirmation-dialog cancellation.
  Screenshot /private/tmp/reality-chat-history-room.png visually reviewed.
- TypeScript/Vite build, changed-file Prettier, diff whitespace and spec policy pass.
  Spec policy ran directly with python3 scripts/check_spec_policy.py because the
  local make launcher requires Xcode license acceptance.
- Frontend contracts: 190/191 pass. The existing shell-header layout regex at
  apps/web/scripts/unified-app-contract.test.mjs:452 fails against concurrent
  Shell.tsx/HeaderControls changes outside this increment. T030 remains unchecked
  until the complete gate is green. No backend/schema/catalog change.
- Final review: only sidebar widths, menu sizing and scoped option visibility were
  changed for this increment. Concurrent working-tree edits were preserved.

### Isolated PR verification
On origin/main (1d549ae9) with only FR-024 applied, all 191 frontend contracts
pass, including the previously affected header test. The complete composer browser
passes against the isolated preview on port 5188. TypeScript/Vite build, i18n audit,
changed-file Prettier, spec policy and diff whitespace checks pass. T030 is complete.
The existing bundle-size warning is unchanged. No concurrent work is included.
