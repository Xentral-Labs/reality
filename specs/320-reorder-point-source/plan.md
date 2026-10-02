# Implementation Plan: Reorder Points Name Their Statement

**Branch**: `320-reorder-point-source` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

`set_reorder_point` and `remove_reorder_point` store each statement through `core.store_source_record` as the next version of the stream `internal_reorder_point` / `reorder_point` / `<item>@<location>`. The payload carries the stated values (or `removed: true`) and a statement id, which is the confirmation id or a fresh id. The row gains a required `source_record_id`, and reads, results and events carry it.

Migration `0111` adds the column and writes a marked source version for each existing point. It sets the stream's current version, makes the column NOT NULL and indexes it.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | This is the change: each statement is a source version and the row points to it. |
| II. Reality is the operational authority | PASS | No document fields. |
| III. Proven schema only | PASS | One column. The Inspector traces through it and the review compares against the row as before. |
| IV. Tenant and service boundaries | PASS | Composite tenant FK. Same reviewed tools. |
| V. Specification and test evidence | PASS | The new tests failed without the change (5 failed), then passed. |
| VI. Explainable Web product | PASS | Reads expose the statement in force. |
| VII. Simplicity and storage discipline | PASS | No new table. The history uses the existing source versioning. |
| VIII. Received values are recorded, never recomputed | PASS | Values are stored as stated, in the payload and in the row. |

## Design

1. `db/core.py`: `ItemReorderPoint.source_record_id` with a composite FK and index.
2. `services/reorder_points.py`:
   - `_state()` stores a statement.
   - `set` points the row at its statement. A replay of the same confirmation returns without a second version or event.
   - `remove` stores a removal version before deleting the row.
   - Both events carry `source_record_id`.
3. Migration `0111_reorder_point_source`: backfills, reusing an equal version if one exists. The downgrade drops the column and keeps the sources.
4. Docs: `config/data_model.yaml`, `docs/SPEC_COVERAGE_MATRIX.md`, `make docs-generate`.

## Rollback

The downgrade drops the column. The source records stay, as evidence is never deleted.

## Complexity Tracking

None.
