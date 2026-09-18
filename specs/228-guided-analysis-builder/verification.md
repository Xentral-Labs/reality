# Verification: Guided Analysis Builder

## Scope and review

Spec impact: implements spec228 FR-001–FR-013. No migration or new business authority.
The reference was inspected in signed-in native Chrome, including Explore data. The
visual hierarchy is adopted; unsupported mock KPIs and example meanings are deliberately
replaced with the declared reporting model and explicitly scoped result metadata.

Code review covered tenant checks, shared service/tool/API use, provider eligibility and
managed reservation, exact bound values, branch origins, required currency/unit axes,
private report ownership/revisions, stale-request rejection and unexecuted editor drafts.
The existing analytics resource match already assigns both new graph tools; there are
no new commands, views or projections requiring additional German resource labels.

## Automated evidence

- The new formatter/interpretation tests were introduced before the corresponding code;
  missing formatter and parser preservation failures were observed before correction.
- Additional malformed HAVING and silently discarded measure-alias tests failed before
  their parser fixes and passed afterward.
- Focused graph suite: 174 passed (declaration, coverage, isolation, lifecycle, traversal,
  syntax and tool execution plus initial builder tests).
- Final focused builder/syntax suite: 51 passed, including expert private save/reopen,
  provider output validation, missing provider, reservation before dispatch, record-value
  omission and foreign membership refusal.
- Frontend query/state suite: 27 passed, including late responses, abort on unmount,
  failed expert execution, draft retention, explicit same-report reopening, save definition and branching transitions.
- Complete backend suite: 2,806 passed, 9 skipped; the single failure was the catalog
  cardinality assertion still expecting 485 rather than 487 registered operations.
  After updating that assertion, the complete catalog file passed (35 tests).
- After transferring only this feature to current main, the affected builder, graph,
  isolation, private-report lifecycle and catalog suites passed together (135 tests).
- Final web contract suite on main: 256 passed.
- Web formatting: PASS. TypeScript/Vite build: PASS (existing large-bundle warning).
- Localization audit: PASS in en/de/nl/es, 1,935 statically detected strings covered.
- Backend Ruff: PASS. Spec policy: PASS.
- Catalog reference generation: PASS; regeneration produced byte-identical reference artifacts.

Commands and logs were run locally; the complete backend suite uses
`cd packages/reality-core && ../../.venv/bin/pytest -q -n 2 --dist worksteal tests`.
An initial run from the repository root failed migration tests because their relative
`alembic.ini` was absent; this was corrected rather than modifying migration behavior.
The new tool registrations also exposed missing capability/topic/isolation catalog entries;
those entries and the catalog cardinality expectations were updated.

## Visual evidence

Native Chrome displayed the temporary isolated review page with the actual GraphSteps
and DataExplorer components, real catalog/templates and synthetic responses used only
for presentation review. Invalid parameter input showed an error and blocked saving,
while tab switching retained the draft. Temporary review files were then removed.

Final review used the actual application at localhost:8080 and its real demo-company
reads, after transfer to main:

- Desktop builder with the existing docked chat: live example, consistent sentence,
  real table, read state and generated parameterized Cypher.
- Executed the generated Cypher through the actual API; the result stayed successful.
- Connections: actual outgoing and incoming directions; catalog Open path created an
  unsaved party-to-order question. Long German node labels fit without word fragmentation.
- Keyboard ArrowRight moved focus and selection from Connections to Cypher.
- Chrome responsive mode at 390px: question/examples and sentence wrap, tabs fit,
  editor stays within its card, catalog stacks vertically and its sidebar scrolls;
  wide preview tables scroll inside the card without widening the page.
- At 1440px: catalog uses the reference's searchable left column, counts banner and
  field/relationship/preview detail. A five-record preview was fetched through graph.ask.
- Browser review exposed lowercase boolean copy in previews; it now uses the shared
  Yes/No translations and preserves false values, with a regression test.
- Browser device emulation and DevTools were closed after review.

A transient CUA output issue was resolved by explicitly reading/emitting returned state
and screenshot data. It is not an outstanding blocker. No live AI-provider dispatch was
performed; provider integration boundaries use deterministic mocks.

## Completion boundary

All implementation and review tasks are complete. The working tree is on current main
(d94e8cbf); the separate proposal-fix branch and its commits were preserved unchanged.
No migration, deployment or remote push was performed. Supported business concepts and
truthful metadata replace the reference's unavailable mock financial KPIs by design.

## Owner-requested application design refinement

Removed the Builder title/subtitle/status hero and question/examples panel, including unused local input/template interpretation state. Preserved template entry, sentence, results, graph, expert query and private saving. Builder and Explore data now inherit application theme/semantic tokens, flat register surfaces, compact typography and shared primary buttons; the catalog summary is neutral. No backend behavior changed.

- Web contract/state suite: 256 passed (`/tmp/reality-analysis-refine-tests.log`).
- TypeScript and production build: passed (`/tmp/reality-analysis-refine-build.log`); existing large-chunk advisory remains.
- Localization audit: passed (`/tmp/reality-analysis-refine-i18n.log`).
- Native Chrome: inspected real local tenant Builder results, graph and Cypher, and Explore data. At 390px, sentence controls wrap, catalog stacks, and scrolling stays inside the graph/table surfaces. Checked desktop with docked chat.
- Themes: CSS reviewed against shared light/dark variables; dark rendering was not separately switched in the user's preferences.
- Independent designer final code review: no blocking findings.
- Final formatting check, spec policy and whitespace validation: passed. Changes remain local on `main`.

## Shared workspace integration (FR-014)

All four views now use RegisterWorkbench. Primary tab labels replace duplicate internal page titles. Builder saving and catalog Use in analysis use PageActionBar; Builder passes active-view state so its mounted draft cannot leak actions into other views. Local tabs use RegisterHeader local placement, catalog/report search uses RegisterToolbar, inputs/actions use shared controls, and result/catalog tables use ERP geometry. Templates and reports are flat compact lists. Numeric result columns retain explicit right alignment.

Verification: 256 web tests pass, including active-view state assertions and preserved draft/reopen behavior. Updated the render harness to provide the newly reused RegisterWorkbench. TypeScript/build, localization (all four languages), formatting, spec policy and git whitespace checks pass. Logs: `/tmp/reality-analysis-shared-{tests,build,i18n,format}.log`. Existing build chunk advisory remains. No backend changes in this refinement.

Native Chrome review: desktop Templates, Builder results, Explore data and private report list; Save analysis opens its naming form from the shared header menu without writing data. Switching to reports removes Builder/catalog header actions. Mobile 390px: report actions wrap and Builder sentence, local tabs, summary and table remain usable without page-wide overflow. Returned Chrome to desktop. Final code review confirmed current action visibility and disabled-save guards.

## Three-area workflow completion
261 web tests, TypeScript/build, format, localization (four languages), spec policy and diff checks passed. Logs `/tmp/reality-analysis-workflow-final-*.log`. Native Chrome verified three-tab navigation, integrated template adoption, Create with chat and Adapt with chat prefilling removable context without sending. Automated real-component tests verify composer preservation, cross-tenant rejection, failed-send restoration/retry, and proposal opening without saving. No paid/live provider turn was sent. The final mobile recheck was unavailable because native Chrome stopped returning window content/screenshots; prior mobile layout verification predates this navigation change.


## Clear question hierarchy (FR-018)

Implemented the local question frame, heading/chat action, larger sentence tokens,
labeled conditions, single period representation and initially collapsed measures,
columns, paths and sorting. Aggregate sentences show the selected measures without
changing currency or identity axes. Regression tests cover strict time-range detection
and removal of both bounds while preserving unrelated filters and dimensions.

263 web tests pass; TypeScript/production build, four-language localization audit,
formatting, spec policy and whitespace checks pass. Logs:
`/tmp/reality-question-{test-contracts,build,i18n-audit,format-check}.log`.
The existing bundle-size advisory remains. Native Chrome desktop with docked chat:
opened the real order-intake template, confirmed 40 result rows, framed heading,
readable aggregate sentence and single period display. Clicking the measure token
opened the disclosure and exposed record path, both measures, identity/name/currency
axes and sorting; collapsed it again afterward. No report saved or chat sent.
Mobile and dark mode were not separately rendered for this refinement. Responsive
wrapping and shared theme variables were reviewed in CSS. Final code/spec review
found no blocking issue; no domain, API or schema changes in this refinement.

## FR-019 compact sentence refinement
- Owner-approved presentation update; no backend or query contract change.
- Web contracts: 269 passed. Final focused sentence/snapshot regressions passed after
  preserving meaningful catalog labels for ordinary name fields.
- TypeScript/Vite build, Prettier, all four language audits and spec policy passed.
- Native Chrome with docked chat: the historical stock question displays one compact
  line with physical stock, Article · Location and the selected date; no technical
  identity/+N caption. Neutral controls, secondary chat action and unrestricted filter
  state are visible. Result remains 16 rows; identity/unit axes remain in the query.
- Existing responsive flex wrapping and mobile menu placement retained. No schema,
  data write, saved-report mutation, commit, push or deployment.
- Final review: query preservation regression passes; no outstanding finding.
