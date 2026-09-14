# Validation Guide

Run the dedicated service/API and route tests first, then the Orders browser harness against Vite5177. Verify explicit order types, exact multi-line delivery drilldown, incoming supplier/unit/revised quantities, all/open status and foreign isolation. In the UI, inspect an order, view its deliveries, open a customer case, inspect a supplier commitment, reload filters, retry an error and switch companies. Run all existing unified browser regressions and the full backend/web/docs gates before checking tasks complete. Preview uses dedicated synthetic data only; no rollout or retirement.


## Local preview

Open `http://localhost:5177/app/orders-deliveries?tenant=ten_7bcf46fd38`.
Vite5177 proxies API8007. In customer/supplier order tabs, search
`SAMPLE-ORDER-113-C` or `SAMPLE-ORDER-113-S`. These two explicit sample agreements
were created through create_manual_order only in the dedicated synthetic preview
database. The customer order has two delivery lines; the supplier order has one.
No live company or external system was modified.

## Test-first and review evidence

- Three new PostgreSQL tests failed before implementation, plus the new route and
  browser entry test. Logs: `/private/tmp/reality-113-{backend-red,route-red,browser-red}.log`.
- A test fixture initially tried to create a second same-type commitment for an
  existing document line. The database correctly rejected it. The final fixture
  uses three distinct service-created lines, with one line-only link, preserving
  the uniqueness rule while testing shortest-link document filtering.
- Focused delivery tests:8 passed. Full suite additionally tests cancelled history.
- No schema or new action tool. The service query selects the appropriate party,
  preserves customer defaults and uses existing effective/fulfillment expressions.
  Exact order criteria apply in SQL before count/page. Supplier case requests
  still fail through the customer-only case endpoint.
- Evidence dates remain recorded calendar values; amounts are received values.
  The remaining quantity column describes unfulfilled quantity, not an assertion
  that a cancelled commitment remains active work. No cross-unit total is shown.
- Technical review found no critical issue in the requirement/Constitution mapping.
  Rollout and retirement are separate; advanced operations remain supporting paths.

## Verified gates — 2026-09-07

- Full PostgreSQL suite: **1496 passed, 7 existing skips**,237.35 seconds.
  `/private/tmp/reality-113-backend.log`.
- Web: **128 contracts passed**, **1509/1509** strings covered in en/de/nl/es,
  formatting and production build passed.
  `/private/tmp/reality-113-{contracts,i18n,web-format,build}.log`.
- Docs: **45 tests**, formatting and production build passed.
  `/private/tmp/reality-113-docs-{test,format,build}.log`.
- Foundation/delivery, Analytics/master data, warehouse/attention, finance, sources
  and Settings browser gates passed, including existing confirmation/recovery,
  scoped investigation and localized screenshot matrices.
  `/private/tmp/reality-113-{foundation,workspaces,operations,finance,sources,settings}.log`.
- Authenticated local read-only browser proof passed: sample customer order → two
  exact commitments → existing case; supplier order → correct supplier → Inspector
  and reload. No business write was sent by navigation.
  `/private/tmp/reality-113-live.log`.
- New workspace's initial complete browser matrix passed48 screenshots with exact
  order drilldown, supplier/customer boundaries, keyboard focus, pagination,
  empty/error/retry, foreign records, company reset and no writes.
  `/private/tmp/reality-113-browser.log`.
- Spec policy, Python lint and diff whitespace checks passed.

Visual review covered light desktop deliveries and dark German mobile order
records. The table scrolls within its own container, preserving readable fields
and right-aligned quantities without overflowing the page.


Final Orders browser rerun also passed all48 screenshots and interaction checks
(`/private/tmp/reality-113-browser-final.log`) after the remaining-quantity label
clarification. All ten tasks are technically complete. Final review found no
critical issue. Facts is the next pending workspace; no rollout or legacy deletion
is claimed. Local preview services remain available for owner review.
