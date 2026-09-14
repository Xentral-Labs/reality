# Verification and local use

Open `http://localhost:5177/app/warehouse` and choose Record opening stock. Select a
stocked item without lot/serial tracking, a stock-capable location and a positive
quantity. Review the additive before/after effect before confirming. No shared
company stock was changed by validation.

## Evidence — 2026-09-08

- Red-first new opening tests observed the unsupported review path before implementation.
- Final focused opening suite: **26 passed**. Earlier adjacent correction/application
  suite also passed after the generic raw-opening compatibility guard was completed.
- Complete backend run: **1,730 passed, 7 existing skips, one documentation-contract
  failure**, in 339.80 seconds. The failure was the literal phrase `backend/schema`
  in the Spec 131 WEB_SPEC paragraph, interpreted as a retired directory name by the
  repository layout test. Rewording that documentation was the only subsequent
  repository change relevant to backend tests; **all 8 repository-layout tests passed**
  on the corrected tree. No remaining failure; the unchanged business suites were not
  repeated for this wording-only correction.
- Web: **131 contract tests**, **100 localization tests**, **1,808 audited keys per
  language**, production build and full Prettier check passed. The existing bundle-size
  advisory remains.
- New opening-stock browser passed: Warehouse/launcher/Chat/Decisions, raw proposal
  review, bounded/empty search, optional device-time conversion, lost preparation and
  persisted same-request recovery, explicit approval, committed-result recovery after
  lost confirmation without replay, historical reload, Inspector, reject, company
  isolation, Escape/focus return, and 16 localized light/dark desktop/mobile reviews.
- Existing correction browser (16 layouts) and workspace browser (64 layouts) passed.
- Root Ruff, spec policy and diff whitespace checks passed.
- Visual inspection: desktop German light review, mobile German dark review and mobile
  English dark form. Shared primary-button base classes restored after initial visual
  review; final browser run includes the corrected styling. Item SKU accompanies name
  in the review when supplied by the real service.
- API restarted on port 8007 with existing shared company/user configuration; Vite
  remains on 5177. No production deployment, shared stock test mutation or credential
  change.

Logs: `/private/tmp/reality-132-{backend,focused,layout,browser,corrections,warehouse,web-build,contracts,i18n,i18n-tests,format,lint,spec,diff}.log`.
Screenshots: `/private/tmp/reality-132-browser/`.

## Final review

No schema changes. Shared canonical movement execution and tenant locks remain the
business boundary. Explicit review snapshots are guards, not new stock authorities.
Manual proposal/event provenance does not fabricate external evidence. Receipt checks
remain independent of current stock and preserve history after correction. No direct
browser business arithmetic or general CLI/MCP narrowing. A2 remains partial and
legacy/practice retirement is not claimed.
