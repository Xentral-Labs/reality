# Tasks: Payment Returns Store No Forward Links

- [x] T001 [FR-001, FR-002, FR-003] Tests in `packages/reality-core/tests/finance/test_payment_returns.py`: the columns are gone; two returns each name their own derived links; no fee names no fee documents; the migration refuses a link it cannot confirm, drops agreeing links and restores them on downgrade.
- [x] T002 [FR-001] Drop the columns from the `PaymentReturn` model in `src/reality/db/core.py`; migration `migrations/versions/0110_payment_return_links.py`.
- [x] T003 [FR-002] `_caused()` and `return_detail` in `src/reality/services/payment_returns.py`.
- [x] T004 Docs: `config/data_model.yaml`, `docs/SPEC_COVERAGE_MATRIX.md`, `make docs-generate`.
- [ ] T005 Full suite in CI. Done locally: the finance, finance-scenario, operational-exception, catalog, isolation, index and migration suites (641 tests), ruff.
