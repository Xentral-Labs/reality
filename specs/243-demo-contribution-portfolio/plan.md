# Implementation Plan: Demo Contribution Portfolio

**Branch**: `243-demo-contribution-portfolio` | **Date**: 2026-09-20 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Extend the versioned canonical demo profile from international-v2 to international-v3 with five additional complete, source-backed invoice-line contribution cases. Together with existing fixture A, the profile exposes six reviewed outcomes. One bounded acquisition lot and five ordinary sales/issue/invoice paths provide exact consumed cost; a single supplier invoice supplies scenario-specific direct and allocated selling costs. Existing costing services create all reviews and continue to derive DB1/DB2 only at read time.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript where frontend is in scope
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite as applicable
**Storage**: PostgreSQL; immutable object storage only for proven source binaries
**Testing**: pytest business stories/integration/unit; frontend build and focused UI tests
**Project Type**: backend services/API/CLI plus independent frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope
**Scale/Scope**: Five additional complete EUR invoice-line cases in the canonical demo profile; no change to empty companies, execution fixtures, continuous Demo Data, public APIs, or schema

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Each acquisition, order, movement, sales invoice, and selling-cost invoice begins as a lossless `demo_profile` SourceRecord and enters the ordinary document/movement/ledger/cost-review path. | PASS |
| Reality owns operational state | Documents receive no fulfillment or costing status; movements, postings, assignments, and reviews remain authoritative inputs to read-time derivation. | PASS |
| Proven schema only | The existing profile manifest accepts named costing-case references; no table, column, or migration is added. | PASS |
| Tenant + shared service boundaries | Initialization uses the existing run/owner-bound profile authority and ordinary tenant-scoped costing services; adapters remain unchanged. | PASS |
| Spec/test traceability | FR/DR mappings below name business-story tests before implementation; quickstart proves end-to-end outcomes and replay. | PASS |
| Explainable web behavior | The existing shared contribution explanation reads the new cases, including source and evidence trace; no browser calculation changes. | PASS |
| Received values not recomputed | Revenue, acquisition cost, and selling costs are authored source inputs; only DB1, DB2, and rate are read-time observations. | PASS |
| Smallest coherent design | Reuse one bounded acquisition lot, existing services, and manifest vocabulary; reject auto-costing unrelated historical or live invoices. | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/demo/international.py       # profile version only
packages/reality-core/src/reality/playground/catalog.py       # recognize canonical profile version 3
packages/reality-core/src/reality/services/demo_data.py       # preserve continuous-data eligibility for version 3
packages/reality-core/src/reality/services/demo_profile.py     # authored portfolio sources and ordinary service orchestration
packages/reality-core/tests/test_demo_costing_profile.py       # business-story and replay proof
docs/features/company-setup-demo.md                            # durable behavior contract
specs/146-company-setup-demo/contracts/demo-profile.md         # profile-version contract
apps/docs/content/{,de/}concepts/business-reality-guide/
  08-inventory-cost-and-contribution.md                        # business-facing worked portfolio
apps/docs/content/{,de/}agent-playbooks/contribution-margin.md # operational DB1/DB2 situations and tools
apps/docs/.vitepress/config.mts                                # bilingual playbook navigation
docs/SPEC_COVERAGE_MATRIX.md                                   # executable evidence mapping
```

**Files/layers affected**: Demo vocabulary → profile initialization service → existing shared costing services. No domain, tool, API, CLI, MCP, database, scheduler, or frontend behavior changes.

## Design

### Reality flow

For each new scenario, one immutable acquisition source creates an opening movement and each authored sale creates an order/commitment, issue movement, sales invoice/document line, and revenue posting. One inventory review covers the exact company-owned opening and five issue movements. Each invoice line receives a reviewed commercial match to its exact inventory member. A supplier-invoice source records scenario-specific selling costs; ordinary selling assignments connect those source lines to the target invoice lines. Contribution reviews confirm revenue completeness and all selling categories. DB1/DB2 remain read-time observations linked to those reviews.

### Service and adapter flow

`services.demo_profile.initialize` remains the sole orchestrator. Its narrow `_cost_action` path creates confirmed profile proposals through `execute_cost_change`, exactly as fixture A does. Existing `cost_query`, `reviewed_contribution`, Finance/Orders previews, Inspector, analytics, CLI, MCP, and Chat consume the resulting records without changes.

### Data and migration impact

No schema or migration change. Increment `PROFILE_VERSION` to 3 so new companies and compatible profile checks identify the expanded immutable baseline. Existing version-2 companies are not mutated or silently reseeded. The manifest retains `costing_cases` and adds five stable named complete-case entries.

### Failure, security, and tenant behavior

All work runs inside the existing profile initialization transaction and run/owner authority. A failure rolls back the portfolio with the rest of initialization. Replaying a completed request returns the existing initialized run; source namespaces and external references remain stable. Tenant isolation and cross-tenant behavior are unchanged. Continuous Demo Data remains outside this authority and keeps missing-cost semantics.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-002, FR-005, FR-008 | business story | `packages/reality-core/tests/test_demo_costing_profile.py::test_complete_portfolio_has_varied_exact_outcomes` | Existing manifest contains only one complete contribution outcome. |
| FR-003, FR-004, DR-001-DR-004 | business story | `packages/reality-core/tests/test_demo_costing_profile.py::test_portfolio_selling_costs_reconcile_and_remain_source_backed` | Existing fixture exposes only one selling-cost composition. |
| FR-006, FR-007, FR-011 | regression story | Extend `test_missing_and_late_return_cases_remain_truthful` and add continuous-profile boundary assertions | New portfolio could accidentally blur intentional gaps without explicit coverage. |
| FR-009, DR-004 | service/replay | Extend `test_canonical_profile_versions_and_replays_one_costing_baseline` with source/review/assignment counts | Version and expanded identities do not yet exist. |
| FR-010, DR-005 | service/security | Existing profile authority tests plus cross-tenant contribution reads in cost service suite | No service-boundary code changes; focused regression demonstrates reuse. |
| FR-012 | documentation contract | `apps/docs/scripts/docs-contract.test.mjs` and spec/docs checks | Portfolio wording and examples are absent. |

## Rollout and Rollback

Deploying version 3 affects only newly initialized canonical demo companies. No migration or backfill runs. Existing version-2 companies remain readable and keep their original manifest. Rollback reverts the profile version and authored cases before new version-3 companies are created; already-created demo evidence remains ordinary valid business data and needs no destructive cleanup.

## Review Risks

- Inventory ownership must isolate the bounded portfolio lot from pre-existing movements of the reused demo item.
- The inventory review must include all five issue movements with exact member matching and no cross-scenario quantity reuse.
- Selling-cost assignments must reconcile exactly and explicitly review every category, especially the zero-cost scenario.
- Profile-version change must not make existing version-2 companies appear eligible for mutation or replay under version 3.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
