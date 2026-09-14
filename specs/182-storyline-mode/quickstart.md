# Quickstart and evidence: Storyline Mode

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Tasks**: [tasks.md](tasks.md)

This file records what was actually run and what it showed. Nothing here is marked done
without the output that proves it.

## T004 analysis (2026-09-12)

Cross-artifact analysis over spec, plan, research, data-model, contracts and tasks. Findings
and their resolution:

| Finding | Severity | Resolution |
| --- | --- | --- |
| C1 two confirm paths (Playground `confirm_step` vs ordinary action card) | CRITICAL | Confirm and reject go through the storyline routes only; the narrator renders the proposal review itself (plan §2, §5, T023) |
| C2 package contract could not express the planned chapters | CRITICAL | Contract extended: `reads` for read chapters, `context` block with ordered reads, `$exception.<class>.<ref>`, `$company.party`, `requires`, dominator rule for `$chapter`; story recounted to fourteen default chapters and four alternatives; example rewritten (contracts/storyline-package.md, package.py) |
| H1 stale seven-chapter passages | HIGH | spec Screen, US2, US3, US5, SC-003, Assumptions rewritten |
| H2 `command` namespace undefined | HIGH | `command` is the proposal tool name (TOOLS key); validator uses TOOLS and the MCP schema via capability guidance |
| H3 no chapter wrote a Fact | HIGH | chapter `reference` records `order.customer_reference` with `fact_observe`; FR-014 requires a Fact chapter |
| H4 preconditions had no source | HIGH | `requires.findings_present/absent` plus implicit reference resolution; FR-011 reworded |
| H5 refused preparation had no API shape | HIGH | `200 {step_id, refused}` and a `kind: error` trace entry (contracts/storyline-api.md) |
| H6 chapter status derivation undefined | HIGH | derivation table in plan §2; `storyline_state` holds branches only |
| M1 free-play exception snapshot had no home | MEDIUM | `before_exceptions` on the trace entry, captured by the confirm wrapper |
| M2 dependency cannot see the response | MEDIUM | HTTP middleware records GET views (route, params, status); the dispatcher wrappers record reads and mutations with results |
| M3 delta graph would import adapter code | MEDIUM | plan §4 composes from `services/inspector_register.py` and `services/delivery_reads.py` |
| M4 two label mechanisms | MEDIUM | single tenant route `tool-reference`; `application-reference` unchanged; `load_catalog_labels()` is the shared source |
| M5 languages: spec vs contract | MEDIUM | FR-002: English required, four languages for built-ins |
| M6 runtime meaning of `expect` | MEDIUM | shown as expected against observed, never blocking (FR-014, plan §5) |
| M7 stage view on a stored projection | MEDIUM | projections refreshed after seed and confirm for storyline companies (plan §5) |
| M8 SC-003 test vacuous as tasked | MEDIUM | T042 asserts the ordered calls in the browser check |
| M9 free-play state ownership | MEDIUM | browser-only mode; no server flag |
| M10 US6-5 untested | MEDIUM | added to T033 |
| M11 spec example contradicted the contract | MEDIUM | example marked illustrative and corrected |
| LOW items | LOW | schema count, Constitution VIII wording, FR-007 rule, trace `step_id`, `$ref.terms` resolves to the code, version conflict on start, draft route 404, status alignment |

## Phase 1 evidence (2026-09-12)

Environment: worktree `/private/tmp/reality-storyline`, `.venv` of the main checkout,
PostgreSQL at `localhost:54329`, `PYTHONPATH=packages/reality-core/src`.

| Check | Command | Result |
| --- | --- | --- |
| Spec policy | `python3 scripts/check_spec_policy.py` | passed |
| Storyline tests | `pytest tests/test_storyline_package.py tests/test_storyline_delta.py tests/test_storyline_trace.py` | 26 passed |
| Migration 0058 | `pytest tests/test_migrations.py -k "storyline or initial or converge"` | 6 passed (backfill of `recorded_at`, guarded downgrade, clean downgrade and re-upgrade) |
| Regression | `pytest tests/test_playground_steps.py tests/test_playground_runs.py tests/test_playground_api.py tests/test_playground_security.py tests/test_application_tools.py tests/test_http_boundary.py tests/test_application_catalog.py tests/test_unified_app_api.py tests/test_sandbox_read_parity.py` | 744 passed in 119 s |
| Lint | `ruff check src tests migrations`; `ruff format --check` on the changed files | clean (pre-existing formatting drift in `services/core.py`, `web/api.py` and old migrations left untouched) |
| Built-in storyline | `pytest tests/test_storyline_package.py -k built_in` | `order-to-close` validates as a built-in: 18 chapters, four languages, every command, view, class and reference resolved |

Hand-play of the chapters against the real services: research R8.

## Phase 2 evidence, user story 1 (2026-09-13)

| Check | Command | Result |
| --- | --- | --- |
| Run and chapter tests | `pytest tests/test_storyline_runs.py` | 11 passed |
| HTTP surface | `pytest tests/test_storyline_library_api.py` | 4 passed |
| Regression | playground, tools, HTTP boundary, catalog, unified app API, sandbox parity, tenant isolation and all storyline suites | 805 passed in 117 s |
| Web typecheck | `tsc -b` | clean |
| Web contract tests | `node --test scripts/*.test.mjs` | 129 passed (4 new in `storyline-contract.test.mjs`) |
| i18n audit | `node scripts/i18n-audit.mjs` | passed; `Storyline` added to the invariant terms |
| Web build | `vite build` | built |
| Browser | `node scripts/storyline-browser.mjs` against Vite on 127.0.0.1:5177 with fixtures | passed: library start opens the practice company; prepare shows the preview with no write outside `/storyline`; confirm goes through the storyline route and no change-proposal route; protocol lists propose and confirm; delta shows the raised finding and the graph; the new row is marked in the stage; a call expands to its catalog entry with a Tool Usage link; a record opens the Inspector; Next moves to the next chapter; 4 languages × 2 themes × 390/1440 px without horizontal overflow and without page errors |

Decisions taken while implementing:

- Storyline runs are practice runs and their chapters run through the ordinary
  proposal path that practice companies already admit; the Playground lesson
  scopes (bounded input models, decision scope) are not used. `tenant_policy`
  admits storyline steps to the practice decision path and gains a storyline seed
  scope bound to the current transaction.
- The seed replays the package history through the tool handlers on a
  savepoint-joined session inside the run's savepoint, so handler commits release
  savepoints and a failure rolls the company back as one unit.
- The delivery review runs at preparation for eligible commands, so a held customer
  refuses the dispatch chapter at prepare (no proposal), as in a business company.
- The stage renders the chapter's view through the shared live reads with the added
  rows marked and a link to the full page; embedding whole pages was dropped because
  their headers portal into the shell header.
- After a chapter runs the page stays on it until "Next chapter" is chosen.

## Phase 3 evidence, user stories 2 and 3 (2026-09-13)

| Check | Command | Result |
| --- | --- | --- |
| Story end to end | `pytest tests/scenarios/test_storyline_order_to_close.py` | 3 passed: default path (14 chapters), alternatives call / refund / wait, alternatives keep / reorder-20; expected against observed findings per chapter; refused dispatch at prepare; read chapters write nothing; every event after the seed in exactly one chapter's delta and every Fact listed (SC-002); month-end lists exactly the remaining findings |
| Resume | `pytest tests/test_storyline_runs.py -k resumes` | passed: start again resumes the run at the first chapter not done, earlier chapters keep trace and delta, a done chapter cannot be prepared again |
| All storyline suites | package, delta, trace, runs, HTTP, scenario | 45 passed |
| Browser | `storyline-browser.mjs` section 5b | passed: reload resumes at the current chapter, an earlier chapter is read-only with its protocol, a finding of the delta opens the Exceptions page |

Finding recorded in research R8 addendum: a refund of a credit clears the unmatched finding
on the incoming payment and raises one on the refund's outgoing cash entry; the refund
chapter says so.

## Phase 5 evidence, user story 6 (2026-09-13)

| Check | Command | Result |
| --- | --- | --- |
| Library HTTP | `pytest tests/test_storyline_library_api.py` | 6 passed: built-in download verbatim and as JSON, import under another key round-trips unchanged and is private to the account, same key and version asks and replaces on request keeping the old row, built-in key cannot be shadowed, built-ins cannot be deleted, imports can; bad packages refused with every error and nothing stored, list body, oversize and non-UTF-8 bodies refused, membership command warned |
| Round trip | `pytest tests/scenarios/test_storyline_order_to_close.py -k reimported` | passed: an exported, re-imported and replayed package ends in the same events, findings and Facts (SC-007) |
| All storyline suites | package, delta, trace, runs, HTTP, scenario | 48 passed |
| Docs | generator, reference unittests, prettier, 57 docs contracts, `npm run build` | generated `content/storylines/index.md` in EN and DE, `content/public/storylines/order-to-close.storyline.yaml` and `storyline.schema.json`; the process page links the storyline; sidebar entry; CI stale-output guard and Makefile extended |
| Web | tsc, i18n audit, 129 contract tests, vite build, `storyline-browser.mjs` | passed; browser section 1 imports a broken file and reads both errors, imports a good one, removes it, and the download is a plain link to the export route |

## Phases 6 to 8 evidence, user stories 4, 5 and 7 (2026-09-13)

| Check | Command | Result |
| --- | --- | --- |
| Free play and preconditions | `pytest tests/test_storyline_runs.py -k "free_play or precondition"` | 2 passed: a reserve confirmed outside the story is recorded with actor `person`, no step, its own marker; the delta by ordinal lists its events and the cleared finding; the propose entry has no marker (404); a chapter whose finding no longer exists names `finding_present: overdue_receivable`, cannot be prepared, and restart opens a fresh company |
| Draft export | `pytest tests/test_storyline_export.py` | 4 passed: offsets; three free-play commands become `$ref`, `$company.party`, `$chapter.step-1.output.…`, `0d`/`+5d` and texts marked missing; the draft validates except for `missing_text` and `draft`; filled in, it imports and plays to the same event types (SC-009); story chapters keep their texts, an unknown command and an unknown identity stay in place as `unsupported`; the route downloads YAML or JSON and refuses other formats and foreign runs |
| All storyline suites | package, delta, trace, runs, HTTP, export, scenario | 54 passed |
| Web | `tsc -b`, `i18n-audit`, `node --test scripts/*.test.mjs` | clean; 131 contract tests (presentation step machine, free play as a page mode) |
| Browser | `storyline-browser.mjs` sections 7 to 10 | passed: free play lists the two calls outside the story, a picked confirmation loads `delta?ordinal=8`, "Back to the story" returns to the current chapter; a blocked chapter shows `overdue_receivable` and no prepare button, restart opens `tenant=story-2`; the presentation run issues exactly the chapter calls the run by hand issued (`order/prepare`, `order/confirm`) and then `reference/prepare`, a click on the chapter list pauses it before any call, the language switch while paused renders German titles without a new call, the fixture's failing prepare pauses it; the library links the run to `/api/storyline/runs/run-1/draft?format=yaml`; 16 layouts with the language explicit in the URL |

## Second built-in storyline, Purchase to pay (2026-09-13)

| Check | Command | Result |
| --- | --- | --- |
| Built-in validation | `pytest tests/test_storyline_package.py -k built` | both built-ins validate: 19 chapters, four languages, every command, view, class and reference resolved |
| Story end to end | `pytest tests/scenarios/test_storyline_purchase_to_pay.py` | 2 passed: default path (14 chapters) and the credit branch; expected against observed findings per chapter; duplicate booked and reversed through the posting group in the output; discount accepted on the record; month-end lists exactly `invoice_price_differs` (plus `billed_not_received` on the credit branch); every event after the seed in exactly one chapter's delta |
| Docs | generator, prettier, docs contracts, build | storylines page lists both, public copy of the new file written |

Hand-play findings are in research R9.

## Final gates (2026-09-13)

| Check | Command | Result |
| --- | --- | --- |
| Backend | `pytest tests` from `packages/reality-core` on PostgreSQL 54329 (includes `test_migrations.py`) | 2377 passed, 9 skipped in 11:35 |
| Lint | `ruff check src tests migrations`; `ruff format --check` on the storyline files | clean |
| Spec policy | `make spec-check` | passed |
| Web | `tsc -b`, `i18n-audit` (4 languages), `node --test scripts/*.test.mjs`, `vite build` | clean, 131 passed, built |
| Storyline browser | `storyline-browser.mjs` (10 sections) | passed |
| Other browser scripts | `retirement`, `unified-inspector`, `unified-activity` | fail on this branch at the same steps as on `origin/main` 7693136 (baseline worktree, Vite on 5178): retirement waits for the "Orders & deliveries" link, activity for the "Activity" button, inspector for the exception catalog freshness marker; not regressions of this change |
| Docs | generator (no drift), prettier, 57 docs contracts, `npm run build` | passed |

Branching note: PR #234 was squash-merged while user story 6 was in progress; the commits
pushed after the merge were stranded on that branch and are carried again by the second PR
together with user stories 4, 5 and 7.

## Open

- Nothing. T049 review done with the second PR.
- The full verification gates (T046 to T048) run again at the end; the docs gate ran after Phase 1 and must run again once the docs page lands.
