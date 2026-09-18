# Implementation review: Order journey timeline

## Scope and authorization
The owner accepted the proposed order-focused concept on 2026-09-18. Spec233 records that authorization, the explicit supersession of spec162, and the first sales-order scope. Requirements quality was checked before implementation; Constitution Check is PASS without exceptions. The custom UX/domain checklist remains reviewer-owned for the eventual PR review; it does not replace the owner's existing implementation authorization.

## Pre-implementation analysis
Eleven functional requirements and four success criteria have task/test coverage. No unresolved clarification or critical consistency finding. The plan uses existing typed links, event projection and Inspector; no schema, source mutation, document operational status or inferred process identity. Mandatory extension hooks were absent.

## Implementation review
- Authoritative membership is filtered in SQL before pagination and constrained to the tenant at every stage. Source, item, party and correlation do not expand membership.
- Reservation and movement links use their commitment. Commitment uses its line when present; document-level commitments remain supported.
- Posting-group events retain their true identity and expose held ledger-entry references, bounded to 250 with explicit truncation. No per-entry events are invented.
- The browser owns only presentation, selection and viewport layout. It never calculates fulfillment, balances or state.
- Requests abort on scope changes. Backward pages preserve the range; forward pages prevent burst loss. The shared 30-second visible-tab cadence remains.
- CSS responds to available container width, including an open chat dock. Lane labels remain visible during local horizontal scrolling. Light/dark and all four languages were reviewed with screenshots.
- The original recorder helpers remain unmodified; the active Inspector page mounts the new timeline. The legacy browser's recorder-specific segment is updated to the new handoff.

## Verification evidence
- Initial service proof failed at collection because order_journey did not exist; the initial layout proof failed because its module did not exist. Posting-group layout regression failed before support was added.
- Six new PostgreSQL service/API tests pass, including bounded ledger links. The earlier combined journey/timeline/Storyline regression run passed 14 tests.
- New browser acceptance passes: order selection, grouping/member drill-down, record Inspector, older pages, retry preserving data, a 101-event forward burst preserving the pinned range, stale order/company reads, keyboard activation, 390px/1440px, sticky lane labels, English/German/Dutch/Spanish and dark mode.
- Browser screenshots: `/tmp/reality-233-browser/desktop.png`, `mobile.png`, `de-dark.png`, `nl-dark.png`, `es-dark.png`. These use test fixtures, not production data.
- Lint and spec policy pass. Documentation catalog generation/check passes with no generated changes.
- Frontend gate passes: 274 contract/localization tests, four-language audit, formatting, TypeScript and production build. Final standalone build also passes after the last adapter/UI guard review. The existing Vite chunk-size notice remains unchanged.
- The baseline Inspector failure is supplemental evidence; the dedicated journey browser suite is the spec233 acceptance gate.

## Existing regression-suite limitation
`apps/web/scripts/unified-inspector-browser.mjs` stops in the exception-catalog scenario at line 1003, waiting for `[data-inline-exception-catalog] [data-projection-freshness="ready"]`, before reaching the Timeline. Reproduced the identical failure on an unchanged `HEAD` archive served separately at port 5179. This is a pre-existing fixture/suite mismatch, not a new timeline failure. Evidence: `/tmp/reality-233-existing-inspector.log` and `/tmp/reality-233-baseline-inspector.log`. No exception-catalog implementation or fixture was changed to conceal it. The dedicated journey suite is the executable acceptance proof for spec233.

## Full-suite execution
The sequential backend run was intentionally interrupted after completed files to accelerate remaining work. `/tmp/reality-233-finished-tests.json` retains the 87 fully completed passing files. The remaining collection runs with four isolated PostgreSQL workers; partially completed files run again. An AdminShutdown during interrupted-run cleanup is not counted as a passed test or product failure. A final collection proves exact disjoint coverage: 2,893 total tests = 952 tests in the completed-file set + 1,941 in the worker set. No test belongs to both sets. The worker run finished with 1,934 passed, 7 skipped and one transaction-cleanup warning in 326.04 seconds. Together with the 952 tests from the completed-file set, full-suite coverage is 2,886 passed and 7 skipped, with no failures. The final six service/API regressions were also rerun after unknown-tenant HTTP handling was added and all pass.

## Final state
All spec233 implementation tasks and its required verification gates are complete. The implementation is prepared for a feature pull request. No deployment or merge was performed. Human PR review remains outstanding. The existing unrelated Inspector browser mismatch is explicitly documented above. The working tree contains only the planned feature, tests and documentation changes.
