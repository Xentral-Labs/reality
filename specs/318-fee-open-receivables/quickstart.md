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
- The fee browser proof is registered in the CI fixture suite. A registration regression failed first and then passed. Its ten-second estimate adds at most two seconds to the existing seven-shard estimated budget; balancing remains checked, with no change to any runtime/setup deadline.
- `make docs-build`: 11 Python reference tests, 109 Node tests, formatting and VitePress build passed.
- `make lint spec-check`: passed.
- `make docs-catalog-check`: passed after the local implementation commit; regeneration is identical, including Product Advisor artifacts.
- The pre-existing demo-baseline timeout was reproduced on unmodified `590c4d72` and addressed by bounded retained-input batching (see spec 317 evidence). Overall backend verification is still open; draft PR #279 runs CI in parallel with the local suite.
- First CI backend shard 2: 1,616 passed, 1 skipped, 1 failed. The canonical setup projection expected 40 rows but correctly observes 41 after including the existing historical fee. Update that expectation with an explicit one-fee-origin assertion; do not change seeded documents or weaken the gate.
- Updated canonical setup regression: 1 passed in 97.18 seconds, explicitly retaining 40 prior rows plus one fee-origin row. The added assertion reads the stored serialized JSON; no application behavior changed.
- First CI round: all three other backend shards, seven browser-script shards, six live-browser stories, frontend, docs and spec policy passed. Only the stale setup expectation failed; a fresh complete CI run follows the test correction.

## Review

Reviewed reuse of immutable fee/control entries, source links, effective allocations/reversals, tenant/currency/amount guards, cash/credit-only settlement eligibility, absent unstated maturity and unchanged dunning/noncash-reduction eligibility. Projection version 6 invalidates old snapshots for historical fee visibility; no migration/rebooking is performed. `services/exceptions.py` remains untouched.
