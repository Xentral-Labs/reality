# Validation guide

Baseline 141: 1491 backend passes, 7 existing skips; 124 frontend contracts.

Run `PYTHONPATH=src ../../.venv/bin/pytest -q -n 2 --dist loadscope` from packages/reality-core against disposable PostgreSQL. Run make lint/spec-check, frontend format/contracts/i18n/build and unified/operations/workspace/finance browser harnesses. Run docs format/tests/build. Finance browser must cover three tabs × four languages × two themes × two widths, per-currency complete controls beyond first page, no payment total claims, reference-ID filters, Inspector reload/focus, company reset, errors and no mutation requests. Review the actual isolated 5177 preview.

Research found the payment row/aggregate search mismatch before implementation; spec and design explicitly omit those aggregate headlines. Requirements quality passes 8/8 with no unresolved clarification. No extension hooks configured.

## Implementation review

No backend business logic changed. The API client adds optional page arguments
for Payments and Journal without changing existing call defaults. The initial
route test failed before implementation, then passed. The Finance browser
proves complete open-item/journal currency controls across page changes and
explicit absence of payment aggregate headlines. A response-listener race in
the harness was corrected by installing the listener before clicking Next.

Runtime inspection confirmed the existing account interaction is exact journal
filtering, so the contract preserves that interaction rather than claiming an
unavailable separate account-sheet screen. Dutch `Credit` is an intentional
accounting-language equivalent, documented in the audit's locale allowlist.

The authenticated isolated preview passed invoice 600 / payment 200 / open 400,
all three views and native evidence inspection/reload. The labeled synthetic
fixture is confined to `reality_unified_preview_107` and its sample tenant; it
uses shared application services. Log: `/private/tmp/reality-142-live.log`.

Visual review covered desktop open items and mobile currency controls. Tables
scroll inside their own container on narrow screens. Advanced financial actions
remain in supporting workspaces; there is no new financial mutation or posting
UI. Remaining legacy/Playground retirement is outside this increment.

## Verified checks — 2026-09-07

- Full PostgreSQL suite: **1491 passed, 7 existing skips**, 228.86 seconds with
  two load-scope workers. `/private/tmp/reality-142-backend.log`.
- Frontend contracts: **125 passed**; localization **1421/1421** in all four
  languages; formatting and production build passed. Logs use
  `/private/tmp/reality-142-{contracts-final,i18n-final,format,web-final}.log`.
- Docs formatting, **45 tests** and build passed; Python lint and spec policy
  passed, with no whitespace errors.
- Final Finance browser: three tabs, complete filtered currency controls across
  pages, state/direction presentation, reversal history, Inspector reload/focus,
  empty/retry/company reset, no writes and **48 localized screenshots** passed.
  `/private/tmp/reality-142-browser-final.log`.
- Foundation/delivery regression passed its complete action and visual matrix;
  Analytics/master-data regression passed all four families, recovery and
  **64 localized screenshots**. Logs: `/private/tmp/reality-142-foundation.log`
  and `/private/tmp/reality-142-workspace.log`.

Final dark desktop review confirmed compact filters and readable currency
controls; mobile review confirmed that only the table scrolls horizontally.
No runtime data from fixtures is presented as ordinary company truth outside
the dedicated sample preview.

The warehouse/attention regression also passed traversal, exact-item views,
Inspector recovery, error/resolved states, company switching, no writes and
64 localized screenshots (`/private/tmp/reality-142-operations.log`).

All nine tasks are technically complete. Final review found no remaining critical
issue. The local preview remains on 5177/8007 for product-owner review. No merge,
deployment or legacy/Playground retirement is claimed.
