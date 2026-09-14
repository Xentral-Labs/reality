# Validation
Use isolated pytest PostgreSQL data: `pytest -q tests/test_unified_invoice_entry.py` from the core
package. Run full suite and web build/contracts/i18n/format. Run the invoice browser fixture.
Open Finance → New invoice; select customer/supplier order and line, enter stated invoice values,
review and confirm in a disposable test company. Inspect source and postings. Reload or simulate a
lost response; recovery must not repeat the business action. Shared local company smoke is read-only.

## Verification finding
The initial full suite exposed a pre-existing random short-ID collision in the 100,000-entry
PostgreSQL benchmark. Its committed tenant survived the failure and polluted two later lifecycle
tests. Spec impact: none for the fixture repair; use unique deterministic benchmark IDs and
finally cleanup with rollback. This changes test isolation only, not production identity behavior.

## Completed verification — 2026-09-08
- 1,572 core tests passed; seven existing environment-dependent skips. Full run:
  `/private/tmp/reality-120-backend-final.log`. Focused invoice/practice checks: 90 passed.
- 131 frontend contracts, build, formatting and 1,600/1,600 localization keys passed in
  English, German, Dutch and Spanish.
- Invoice fixture covers sales/supplier entry, retained stated values, edit/reject,
  reload, Finance/Actions/Chat/Decisions and lost-response recovery; 16 responsive/theme reviews.
- Existing order, finance (48 screenshots), receipt/release, holds and correction browser
  journeys passed. No duplicate local business actions were used for verification.
- Shared preview login on 8080 and 5177 uses the same user/session and five tenants.
  Finance form reads pass; no invoice was prepared or confirmed in the shared database.
- Spec policy, Ruff and diff whitespace checks passed. No schema migration, deployment,
  old-UI retirement or expansion to payment/credit/repeated partial invoice semantics.

## Final review
All seven requirements are implemented through shared services and exact proposal review.
The source-stated amount remains independent of order totals. Invoice line links directly
 to its order line, and the invoice's source and posting IDs are attributable to the action.
Historical proof excludes later reversal/settlement state; the invoice Inspector provides
current financial context. Unverified or unknown outcomes do not expose a success link.
Optional effective time defaults at execution without a time-varying review token.
The benchmark fixture repair changes tests only; production identifier generation is unchanged.
