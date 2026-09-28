# Implementation Plan: Journey Proof Stories

**Branch**: `292-journey-proof-stories` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

## Summary

Add twelve business-story tests to the existing scenario catalog files, one per journey, driven through the shared services and reviewed proposals that CLI, Web and Chat use. Promote every journey whose story passes to `supported` with the story as executable evidence, keep the others `partial` with the story's finding as their public limitation, and regenerate the Business Journey Guide. No production code changes unless a story exposes a defect against an existing requirement (FR-005).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: SQLAlchemy 2, pytest, existing `reality.services` and `reality.tools.application`

**Storage**: PostgreSQL through the existing test fixtures; no schema change

**Testing**: pytest against disposable PostgreSQL (`session`, `business` fixtures); catalog tests; Docs generator freshness

**Target Platform**: Backend test suite and generated Docs payload

**Project Type**: Evidence and catalog content

**Performance Goals**: The twelve stories add under 10 s to the backend suite; no demo seeding (see `reality-ci-suite-cost`)

**Constraints**: No ORM writes in stories; tenant-scoped services only; stated values asserted, never recomputed

**Scale/Scope**: Three test modules, one catalog file, two generated JSON files, coverage documents

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Stories create orders, invoices and payments through the services that record source, evidence and reality; no shortcut writes. |
| II. Reality is the operational authority | PASS | Stories assert fulfilment, reservations and open items derived from Reality, never document status fields (DR-001). |
| III. Proven schema only | PASS | No schema, table or typed field (FR-008). |
| IV. Tenant and service boundaries | PASS | Every call is tenant-scoped through services or reviewed proposals (DR-003). |
| V. Specification and test evidence | PASS | Approved spec; stories are the evidence and are written before any catalog promotion. |
| VI. Explainable Web product | PASS | The Guide status follows executable evidence; no UI change. |
| VII. Simplicity and storage discipline | PASS | Stories join the existing catalog modules and reuse their helpers. |
| VIII. Received values are recorded, never recomputed | PASS | Tax stories assert stated net, tax and gross as given (DR-002). |

Post-design check: PASS. No data model, contract or service change is planned.

## Design

### Story placement

| Module | Journeys |
|---|---|
| `packages/reality-core/tests/scenarios/test_catalog_orders_and_shipments.py` | A04, A06, A07, A19 |
| `packages/reality-core/tests/scenarios/test_catalog_stock_and_returns.py` | F01, F05, F07 |
| `packages/reality-core/tests/scenarios/test_catalog_finance.py` | C04, M08, N06, N01, N02 |

Each story is named for its business outcome and its docstring starts with the catalog ID, as in the existing catalog stories. The services per journey and the expected outcome are in [research.md](research.md).

### Outcome rule

1. **Story passes**: set the journey to `supported` / `executable`, put the story first in `internal_evidence`, and replace its public limitation with only what lies outside the journey question (for example, no order-level cancel for A07), or none.
2. **Story fails on a defect against an existing requirement**: fix it with a regression test that names the requirement, then apply rule 1.
3. **Story fails on a missing capability**: rename the story to pin today's behavior as a limitation, keep the journey `partial`, write the finding as its public limitation and record it in `docs/scenarios/coverage.md`.

A19 and F07 are expected to reach rule 3 (research). N02 is expected to pass for "stated tax recorded" with its limitation naming the missing self-assessed reverse-charge tax.

### Catalog and generated output

- `packages/reality-core/config/business_journey_catalog.yaml`: status, evidence level, `internal_evidence` and `limitations` of the twelve entries.
- `make docs-generate` regenerates `apps/docs/.vitepress/data/business-journeys.json` and `apps/docs/public/generated/business-journeys.json`.
- `packages/reality-core/tests/test_business_journey_catalog.py`: a pinned test that every entry in this feature's scope whose status is `supported` cites a story in `tests/scenarios/test_catalog_*`, and every one still `partial` has a limitation other than "not yet proven".
- `docs/scenarios/coverage.md` and `docs/scenarios/catalog.md`: status and evidence rows for the twelve IDs, gap findings for rule-3 journeys.
- `docs/SPEC_COVERAGE_MATRIX.md`: the three catalog module rows list the new IDs and spec 292.

### Dependency

PR #243 (spec 290 FR-002a) rewrites the limitation texts this feature edits. Implementation starts after it merges and rebases onto `origin/main`; the spec, plan and tasks do not depend on it.

## Project Structure

```text
specs/292-journey-proof-stories/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
├── checklists/requirements.md
└── tasks.md

packages/reality-core/
├── config/business_journey_catalog.yaml
└── tests/
    ├── test_business_journey_catalog.py
    └── scenarios/
        ├── test_catalog_orders_and_shipments.py
        ├── test_catalog_stock_and_returns.py
        └── test_catalog_finance.py

apps/docs/.vitepress/data/business-journeys.json
apps/docs/public/generated/business-journeys.json
docs/scenarios/coverage.md
docs/scenarios/catalog.md
docs/SPEC_COVERAGE_MATRIX.md
```

**Structure Decision**: Extend the three existing catalog modules and their helpers; add no fixture module, service or tool.

## Rollback

Revert the commit. Statuses return to `partial`; no data or schema is affected.

## Complexity Tracking

No Constitution violations or exceptions.
