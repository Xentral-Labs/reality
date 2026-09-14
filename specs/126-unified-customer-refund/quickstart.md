# Validation
Use isolated PostgreSQL fixtures, not shared company mutations. Create a posted customer credit of 90, net 20 to its invoice, review a refund of 20: 70 before, 50 after. Confirm once, inspect outgoing cash and allocation. Repeat confirmation and recover an executing outcome: same receipt. Reverse refund: credit returns to 70 while historical receipt verifies.
Run focused tests/test_unified_customer_refund.py then full backend pytest from packages/reality-core. Run web build/contracts/i18n/format and test:refund-entry-browser plus adjacent payment/credit/reversal browser scripts. Run root make lint, make spec-check and git diff --check. Shared localhost:5177/app/finance checks are read-only.

## Verified result — 2026-09-08
- Test-first shared refund preparation failed before routing support; netting after refund failed before the both-endpoint allocation guard. Both regressions now pass.
- 33 focused refund tests passed; complete backend: 1687 passed, 7 existing skips in 328.52s (`/private/tmp/reality-126-backend-full.log`).
- Frontend production build, 131 contracts, 100 i18n tests, 1,680 keys in all four languages, formatting, Ruff and spec policy passed.
- Refund browser: seeded Finance credit, Actions, Chat, Decisions, edit/reject, reload and lost-response recovery; 16 language/viewport/theme views. Adjacent payment, credit, reversal and Finance browser journeys passed.
- German desktop light and mobile dark review screenshots inspected. Shared ports 8080/5177 retain one user and five tenants; credit flow and actual empty refund form verified without financial test writes.
- Final review: canonical refund input/Playground authority/ledger-only receipt preserved; both-endpoint credit capacity enforced; historical proof independent of current reversal observations; all receipt links inspectable and tenant-scoped. No schema, migration, deployment, commit or legacy retirement.
