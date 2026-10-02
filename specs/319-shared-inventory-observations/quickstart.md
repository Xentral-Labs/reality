# Validation

On isolated PostgreSQL run `pytest tests/test_shared_inventory_observations.py tests/test_stock_block_readers.py tests/test_inventory_and_fulfillment.py` from `packages/reality-core` with this checkout on PYTHONPATH.

Confirm a revised supplier promise with a partial receipt contributes only its remaining quantity, location filters isolate every quantity, and inventory projections match the service.

Then run `make test`, `make lint spec-check`, `make web-build`, `make docs-generate` and reproducibility checks. Review generated inventory and fulfillment reference entries. No migrations or data rewrites are necessary.

## Verification evidence (2026-10-02)

- Before implementation: 5 failed, 1 passed. Web reported incoming 12 instead of the service's 7; four projection entries omitted stock blocks.
- Final targeted inventory, correction and query-count run: 15 passed (`test_shared_inventory_observations.py`, `test_chat_latency.py`, `test_movement_corrections.py`). Includes correction-aware incoming, transfer conservation and SQL filtering/sorting before pagination.
- `make lint spec-check`: passed. Tenant-isolation catalog validates, including the paginated service's dedicated evidence family.
- `make web-build`: passed; 451 frontend contract tests and all four translation audits passed.
- Documentation reference unit tests: 11 passed; Docs formatting check passed. Regeneration changes only three generated Tool Usage files.
- Inventory browser smoke: passed in English and German, including location navigation and scope.
- Documentation: 109 Node tests and VitePress build passed; `make docs-catalog-check` passed for the inventory commit.
- Full backend attempt: 1,357 passed, 3 skipped, then demo-baseline setup raised `JobError("handler_timeout")`. The same `test_demo_costing_profile.py` module fails with 12 setup errors both here (127.56 seconds) and on unmodified base `590c4d72` (169.44 seconds) against isolated PostgreSQL. No scheduler timeout or application policy was changed to bypass the failure. Overall verification remains incomplete; required final tasks are not marked complete.

## Review

### Main integration (2026-10-02)

Rebased onto `cd009334`, retaining main's immutable stock-block declarations and resolution records. The shared query consumes `_open_stock_blocks`, so partial release/scrap is subtracted once and no removed status field is read. Projection metadata names `stock_block_resolution`. Spec 317 is now occupied by main's reservation measurement; this inventory spec moved to free number 319, with authority and documentation references updated. Focused shared inventory, stock-block readers/operations, multi-warehouse reservation and catalog tests: 95 passed. Lint/spec passed; generated references updated. Fresh post-rebase full CI remains pending and prior complete-CI evidence below is historical, not evidence for this new base.

### Final verification

Full CI on `f9ccedc1`, run [36974152614](https://github.com/Xentral-Labs/reality/actions/runs/36974152614): all four backend shards passed (1,249 + 1,299 + 1,617 + 1,177 = 5,342 passed; 10 skipped). Spec policy, frontend, documentation, seven browser-script shards and six live-browser stories passed. The local full attempt started before the setup expectation correction and stopped at that same stale assertion after 3,318 passed and 3 skipped; the corrected setup regression separately passed. The complete current-commit CI is the full-suite evidence, not the interrupted local run. Lint/spec and catalog reproducibility also passed locally after rebasing onto `7b0c41f6`.

Final diff self-review found no schema expansion, changed deadlines, historical rewrite or change to `services/exceptions.py`. Temporary PostgreSQL test data was removed after local checks. Human PR review and merge authorization remain pending in PR #279. No deployment or merge is claimed.

### Verification-blocker remediation

Profiling reproduced the timeout: 26,000 SQL round-trips, 166.9 seconds in profile creation, 89.6 seconds cumulatively in 79 cost decisions, and only 5.7 seconds rebuilding projections. Batch retained input identities within `_inputs`; retain all tenant predicates, validation order, hashes and source values, with no cross-call cache or changed deadline. The new query-count test failed before the refactor (2 movement-basis reads instead of 1). Final inventory-cost integrity and canonical demo module run: 65 passed in 191.55 seconds, including completed setup under the unchanged 120-second limit. Full backend verification still follows.

Reviewed tenant predicates on every aggregate, same-tenant outer query, corrected receipt contributions, cancellation, transfer conservation, unchanged Page re-export, SQL pagination and movement provenance. No business arithmetic remains in the Web inventory forwarding function. The existing company-wide projection consumes `core.inventory_rows`; its calculation remains equivalent, so no projection version bump or stored-data rewrite is needed.
