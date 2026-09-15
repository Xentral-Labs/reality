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
