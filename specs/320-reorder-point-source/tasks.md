# Tasks: Reorder Points Name Their Statement

- [x] T001 [FR-001, FR-002, FR-003] Tests first in `packages/reality-core/tests/test_reorder_points.py` (5 failed before the change).
- [x] T002 [FR-002] `ItemReorderPoint.source_record_id` in `src/reality/db/core.py`; migration `migrations/versions/0111_reorder_point_source.py`.
- [x] T003 [FR-001, FR-002] `src/reality/services/reorder_points.py`: statements as source versions, replay, events.
- [x] T004 Docs: `config/data_model.yaml`, `docs/SPEC_COVERAGE_MATRIX.md`, `make docs-generate`.
- [ ] T005 Full suite in CI. Done locally: the reorder-point, operational-exception, payment-return, catalog, isolation, index and migration suites (415 tests), ruff.
