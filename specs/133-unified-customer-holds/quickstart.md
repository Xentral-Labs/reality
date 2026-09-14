# Verification and local use

Open `http://localhost:5177/app/master-data`, select a customer and choose Customer
delivery holds. Alternatively use a customer delivery case or Actions. Placement
reviews a supported reason and optional note; release reviews the complete active
customer hold set. Reservations remain allowed and individual delivery holds remain
after customer-wide release.

## Evidence — 2026-09-08

- Red-first: all 14 initial new cases failed on the missing reviewed customer-hold path.
- Final focused new plus existing party/delivery-hold suite: **29 passed**, including
  19 new cases. Independent PostgreSQL sessions prove concurrent placement has one
  effect. Actual HTTP tests cover the context read, customer/practice/actor boundary,
  prepare and explicit token confirmation.
- Complete backend: **1,750 passed, 7 existing skips**, in **322.63 seconds**. No core
  source or test changes followed that completed run.
- Web: **131 contract tests**, **100 localization tests**, **1,826 audited keys per
  language**, production build and full Prettier check passed. The existing bundle-size
  advisory remains.
- New customer-hold browser: five entries, empty/paged customer selection, persistent
  lost-preparation recovery, exact placement and release, lost release confirmation
  with explicit reconciliation and no replay, historical result versus current holds,
  retained individual hold, raw Chat review, rejection, company isolation and keyboard
  focus. **32 localized desktop/mobile light/dark placement/release reviews** passed.
- Adjacent delivery-hold browser (16 layouts), opening-stock browser (16 layouts) and
  delivery browser (case/launcher/Chat, full layout matrix, fulfillment and unknown
  outcome recovery) passed.
- Manual visual review: German mobile dark placement, German desktop light release;
  primary buttons, wider scope copy, escaped note and customer identity are visible.
  A missing accessible select name found by the initial browser test was corrected
  before the successful final run. Ordinary reservation wording avoids accidentally
  treating a translated word as a protected domain identifier in the localization audit.
- Root Ruff, specification policy and diff whitespace checks passed.
- Local API restarted on port 8007 and `/healthz` returned `status: ok`; unified master
  data on port 5177 returned HTTP 200. Existing shared users/tenants are retained.

All business writes used isolated PostgreSQL databases or intercepted browser fixtures.
No shared company holds/stock/financial data, credentials, provider calls or mail changed.
No production deployment or old-app retirement.

Logs: `/private/tmp/reality-133-{red,focused,backend,browser,holds,opening,delivery,web-build,contracts,i18n,i18n-tests,format,lint,spec,diff}.log`.
Screenshots: `/private/tmp/reality-133-browser/`.

## Final review

Canonical party-hold tools and tenant locks remain authoritative. The new wrapper is
customer-specific, while raw party tool compatibility remains intact. Optional event
action attribution and exact snapshots require no schema change. Historical receipt
proof is independent of current holds and does not manufacture source evidence.
Current/future shipment scope and continued reservation permission are explicit.
Document-wide hold controls and overall legacy/practice retirement remain open.
