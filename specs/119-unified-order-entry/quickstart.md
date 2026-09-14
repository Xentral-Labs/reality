# Validation

## Scope and environment

Multi-line sales/purchase order entry shares canonical service validation and the
existing reviewed proposal lifecycle. No stock or ledger effects at entry. Original
header/line totals and untyped line metadata remain in manual source evidence. No
schema, deployment or retirement.

Local preview: `http://localhost:5177/app/orders-deliveries`. API 8007 shares the same
users, sessions, tenants and database as 8080. Only authentication and form/reference
reads are used for live verification. Mutation proofs use isolated PostgreSQL or
intercepted HTTP browser fixtures.

## Evidence

- Test-first: four backend failures before implementation; browser failed at the
  missing New order button. Logs: `/private/tmp/reality-119-red.log` and
  `/private/tmp/reality-119-browser-red.log`.
- Final focused tests: 30 passed, covering all diagnosed regressions, sales/purchase,
  source totals/metadata, malformed/stale/foreign inputs, directed snapshots, exact
  receipt, duplicate-payload rejection, same-number different agreements, concurrent
  prepared orders, current authorization, HTTP/practice and historical fulfillment.
  Log: `/private/tmp/reality-119-targeted-final.log`.
- Full final backend suite: 1559 passed, 7 existing skips
  (`/private/tmp/reality-119-backend-final.log`). Earlier intermediate runs identified
  source Decimal serialization, catalog count expectations and preserved raw line
  metadata; those are repaired and included in the focused proof. An obsolete run
  was stopped to avoid interpreting mixed implementation states.
- Frontend contracts: 131 passed; build, format and all four language audits pass
  (1583/1583). Logs: `/private/tmp/reality-119-{contracts,build,format,i18n}.log`.
- New browser proof passes multi-line add/remove/edit, sales/purchase forms, stated
  totals, richer canonical intent preservation, four entry points, reload/reject,
  response-loss recovery without repeat execution, unverified-result warning and
  direct delivery-work links. Log: `/private/tmp/reality-119-browser-final.log`.
- Existing shell/delivery, receipt/release, hold and correction browser journeys pass.
  Logs: `/private/tmp/reality-119-{delivery,receipt,holds,corrections}-browser.log`.
- 16 localized 390/1440 px light/dark review screenshots and a purchase-entry screenshot
  are under `/private/tmp/reality-119-browser/`. Desktop light and mobile dark inspected.
- Spec policy, Ruff and diff checks pass before final documentation closure.

## Shared preview check

API 8007 restarted using the shared runtime launcher. Existing owner login works on
both 8080 and 5177, with the same session identity and five tenants. The order form
loads existing company/party/item/location choices. No proposal or order was created
in the shared database. Log: `/private/tmp/reality-119-shared-check.log`; screenshot:
`/private/tmp/reality-119-shared-form.png`. The local Chrome harness was used because
the integrated browser connection is unavailable.

## Review

FR-001/006/007 map to the browser proof; FR-002–FR-005 map to isolated backend stories
and existing canonical service tests. Immutable action-attributed order creation
snapshots prove directed commitments and exact receipt identities without trusting
human numbers. Later fulfillment changes only current observations. Source/type
uniqueness is handled before writing an identical agreement. Extra raw line metadata
is retained rather than inventing typed fields or new validation restrictions.
