# Implementation Plan: Repeating Form Groups

## Summary

Replace the manual-order `lines_json` textarea with declarative action-form metadata and one reusable React repeating-group renderer. Keep serialization in the presentation layer and all validation/mutation authority in existing services.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | The existing `create_manual_order` endpoint and service are unchanged. | PASS |
| Reality authority | The renderer performs no fulfillment or pricing calculation. | PASS |
| Proven schema | No persistence change. | PASS |
| Tenant/service boundary | Item selectors remain tenant-scoped and the explicit endpoint remains authoritative. | PASS |
| Test evidence | Component/source contracts precede implementation and existing suites remain required. | PASS |
| Explainable Web | Business rows and review summaries replace transport JSON. | PASS |
| Simplicity | One small renderer extends the existing form system without a form-builder dependency. | PASS |

## Technical Design

- Introduce typed field definitions for scalar, select, reference, and repeating-group controls in `App.tsx`.
- Store form values as recursively serializable values rather than strings only.
- Extract one reusable field renderer and repeated-row editor.
- Declare `order.lines` with item reference, quantity, unit, unit price, optional description, and optional promised date.
- Preserve existing confirmation and endpoint orchestration.

## Testing and Rollback

Add frontend contracts for absence of `lines_json`, presence of repeated-row controls, minimum-row enforcement, and direct `lines` submission. Run frontend contracts, i18n, build, lint, spec policy, and backend smoke coverage. Rollback restores the JSON field without data migration.

## Complexity Tracking

No constitutional exceptions.
