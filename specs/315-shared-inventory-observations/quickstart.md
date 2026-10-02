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
- Full backend suite and browser smoke test: pending; no completion claim until their required results are green.

## Review

Reviewed tenant predicates on every aggregate, same-tenant outer query, corrected receipt contributions, cancellation, transfer conservation, unchanged Page re-export, SQL pagination and movement provenance. No business arithmetic remains in the Web inventory forwarding function. The existing company-wide projection consumes `core.inventory_rows`; its calculation remains equivalent, so no projection version bump or stored-data rewrite is needed.
