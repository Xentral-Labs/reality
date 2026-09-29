# Implementation Plan: Journey Proof Stories, Round Two

**Branch**: `294-journey-proof-stories-2` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

## Summary

Eleven business stories in the scenario catalog modules, one per journey. Each drives the shared services and reviewed tools. Passing journeys are promoted in the Business Journey Guide, with English and German keywords. Failing journeys keep an honest limitation. One defect found in research is fixed with a regression test: a reviewed shipment movement ignores payment readiness, against spec 275 FR-005. See [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: SQLAlchemy 2, pytest; existing services and reviewed tools

**Storage**: PostgreSQL test fixtures; no schema change

**Testing**: pytest business stories, catalog tests, Guide question checks; the full backend suite runs in the CI shards

**Target Platform**: Backend suite and the generated Docs payload

**Project Type**: Evidence and catalog content, plus one defect fix

**Performance Goals**: The stories add under 15 s to the suite and seed no demo data

**Constraints**: No ORM writes in stories; stated values asserted as recorded; every "no finding" assertion has a positive control; every refusal asserts its code

**Scale/Scope**: Four story modules (one new), one service fix, catalog, coverage and generated Guide

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Stories create sources, documents and promises through services; P04 and P07 use stored Shopify payloads. |
| II. Reality is the operational authority | PASS | Assertions read derived fulfilment, billing and findings, not document status. |
| III. Proven schema only | PASS | No schema change. |
| IV. Tenant and service boundaries | PASS | Reviewed tools and tenant-scoped services only. The fix makes one tool honour the shared readiness decision (spec 275 FR-008). |
| V. Specification and test evidence | PASS | Stories, and the regression test for the defect, are written before catalog changes and before the fix. |
| VI. Explainable Web product | PASS | The Guide status follows executable evidence; no UI change. |
| VII. Simplicity and storage discipline | PASS | Stories reuse catalog helpers; the fix reuses `fulfillment_readiness`. |
| VIII. Received values are recorded, never recomputed | PASS | G07 and I06 assert stated prices and amounts as recorded. |

## Design

### Outcome rule

As in spec 292:
- A passing story promotes its journey.
- A story that reveals a defect against an existing requirement leads to a regression-tested fix, and the journey may then be promoted.
- A story that reveals a missing capability is renamed to pin today's behavior. The journey stays `partial`, its limitation names the finding, and `docs/scenarios/coverage.md` records it.

### The readiness fix

When `movement_create` prepares a `shipment` against a `customer_delivery` commitment, its review and its execution consult `fulfillment_readiness` for the proposed quantity. On a blocker, they refuse with `shipment_blocked_readiness` and the same values as `shipment_dispatch`. Service-level `record_movement` stays unchanged, because the stories and the importers use it as the recording primitive. The rule belongs to the reviewed person-facing path, as it does for dispatch.

### Catalog and Guide

- `config/business_journey_catalog.yaml`: status, evidence level, `internal_evidence` (story first), limitations, `keywords` and `question_examples` in English and German.
- `tests/test_business_journey_catalog.py`: `PROVEN_BY_STORY` grows by the promoted journeys. A new check requires every journey in `PROVEN_BY_STORY` to carry at least one keyword or extra question example.
- `docs/scenarios/coverage.md`: rows and summary counts, plus the findings of failed stories.
- `make docs-generate` regenerates the Guide payload and the product advisor knowledge.

## Project Structure

```text
specs/294-journey-proof-stories-2/{spec,plan,research,quickstart,tasks}.md, checklists/requirements.md

packages/reality-core/
├── src/reality/services/delivery_actions.py            # movement_create shipment honours readiness
├── config/business_journey_catalog.yaml
└── tests/
    ├── test_business_journey_catalog.py
    ├── test_movement_create_readiness.py                # new: regression for spec 275 FR-005
    └── scenarios/
        ├── test_catalog_purchasing.py                   # G07, H03, I06, I07, K05
        ├── test_catalog_orders_and_shipments.py         # D16, L06, O01
        ├── test_catalog_sources.py                      # new: P04, P07
        └── test_catalog_finance.py                      # R01

docs/scenarios/coverage.md, docs/SPEC_COVERAGE_MATRIX.md, generated Docs payload
```

**Structure Decision**: Extend the catalog modules. The source stories get their own module, because they need Shopify payload helpers and clock control that the other modules do not use.

## Rollback

Revert the commit. Statuses return to `partial`. Reverting the fix restores the bypass.

## Complexity Tracking

No Constitution violations.
