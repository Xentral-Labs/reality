# Validation

## Scope and environment

Spec 118 adds movement reversal and quantity replacement through the shared action
review. Existing source and supported tracking/commitment references are retained;
unsupported newer return relationships prevent the form's quantity shortcut.
Consumed reservations are not restored. No schema change or legacy retirement.

Active preview: `http://localhost:5177/app/warehouse?warehouse_view=movements`.
API 8007 uses the same users, tenants and database as 8080. Only authentication,
register/snapshot reads and opening the form are allowed for live verification;
correction execution tests use isolated PostgreSQL databases or HTTP browser fixtures.

## Test-first and regression evidence

- Initial backend proof: five failures before implementation (`/private/tmp/reality-118-red.log`).
- Initial browser proof: missing correction entry (`/private/tmp/reality-118-browser-red.log`).
- Targeted correction/core/application tools: 26 passed; expanded identity/fulfillment
  stories: 23 passed. Final correction-specific set: 13 passed, including cached
  master-reference refresh across sessions (`/private/tmp/reality-118-final-targeted.log`).
- Final full backend: 1543 passed, 7 existing skips
  (`/private/tmp/reality-118-backend-final.log`).
- Frontend contracts: 131 passed; build, format and all four language audits pass
  (1568/1568 covered). Logs: `/private/tmp/reality-118-{contracts,build,i18n,format}-final.log`.
- New correction browser journey passes Warehouse, launcher, Chat, Decisions,
  preserved intent, reverse/replace, no preparation effect, reload/edit/reject,
  exact review and response-loss recovery without repeat execution. Separate
  observation failure remains visible after successful proof.
- Existing delivery, receipt/release and hold browser journeys pass unchanged.
- Screenshots cover 390/1440 px, light/dark and English/German/Dutch/Spanish under
  `/private/tmp/reality-118-browser/`; desktop light and mobile dark inspected.
- Spec policy, Ruff and diff checks pass before final documentation closure.

## Shared preview verification

Restarted API 8007 with the shared runtime launcher. Existing owner login passes
on both 8080 and 5177, with the same session identity and five tenants. Opened a
real Warehouse movement correction form and waited for its snapshot; no business
proposal was prepared or executed. Live screenshot:
`/private/tmp/reality-118-shared-form.png`; proof log:
`/private/tmp/reality-118-shared-check.log`. Browser connection was unavailable;
used the existing local Chrome test harness for this check.

## Review

All seven requirements map to executable evidence in `docs/SPEC_COVERAGE_MATRIX.md`.
Projected validation remains in the core service; transport layers do not introduce
business rules. Corrections reuse the existing proposal lock, actor checks and
explicit confirmation. Receipt proof is attributable and historical; observation
is separate. No migration or source rewrite. Broader stock entry, document-line and
financial corrections, rollout and retirement remain separate increments.
