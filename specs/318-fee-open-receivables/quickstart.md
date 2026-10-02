# Validation

Run new fee regressions first and record their failures. Verify both fee types, full/partial cash settlement, existing credit allocation, reversal, unchanged posting/source IDs, expense exclusion, maturity/discount exclusion, dunning refusal, tenant/currency/over-allocation and confirmation guards.

Run focused finance, credit exposure, projection and adapter coverage; then full backend, lint/spec, Web and documentation gates. Regenerate references and verify reproducibility. Review no schema expansion, historical rebooking or changes to `services/exceptions.py`.

Verification pending; no completion claim.

## Evidence (2026-10-02)

- Initial regressions: 6 failed; both fee types missing from OP/aging and unsupported by payment settlement context.
- First implementation run: 6 passed, including reviewed partial payment, replay and reversals.
- Extended finance, adapter, projection, Web reads and catalog run: 139 passed.
- Final fee stories, payment-term/discount exclusion, currency/tenant/amount guards, projections and HTTP/MCP confirmation: 14 passed. The added foreign-currency setup changed the finance revision; its test reloads the revision before checking currency compatibility and executing a reviewed allocation.
- Focused fee/settlement/return/dunning/credit-exposure/shared-inventory run: 134 passed.
- Web contract regression: 2 failed before adapter changes, then 2 passed. Full `make web-build`: passed with 453 tests and four translation audits.
- Browser: both fee types open payment without reduction/dunning controls; no writes. General Finance browser smoke passed with filters, paging, freshness, retry and 48 localized screenshots.
- `make docs-build`: 11 Python reference tests, 109 Node tests, formatting and VitePress build passed.
- `make lint spec-check`: passed.
- `make docs-catalog-check`: passed after the local implementation commit; regeneration is identical, including Product Advisor artifacts.
- Overall backend gate remains blocked by the pre-existing demo-baseline timeout, reproduced on unmodified `590c4d72` (see spec 317 evidence). No completion claim and no release/push.

## Review

Reviewed reuse of immutable fee/control entries, source links, effective allocations/reversals, tenant/currency/amount guards, cash/credit-only settlement eligibility, absent unstated maturity and unchanged dunning/noncash-reduction eligibility. Projection version 6 invalidates old snapshots for historical fee visibility; no migration/rebooking is performed. `services/exceptions.py` remains untouched.
