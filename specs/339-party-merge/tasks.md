# Tasks: Merging Duplicate Business Partners

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [x] T001 Clarify the spec (decisions delegated to the recommended options, 2026-10-03)
- [x] T002 Plan
- [x] T003 Tasks

## Phase 2: Merge (FR-001, FR-004)

- [x] T004 Tests in `tests/test_party_merges.py`: merge and lifecycle; every refusal with a positive control; another company.
- [x] T005 `PartyMerge` model and migration `0131_party_merges`.
- [x] T006 `services/party_merges.py`: validate, review, merge, reads.

## Phase 3: Merged reads and intake (FR-002, FR-003)

- [x] T007 Tests: detail, balances, exposure and intake resolve to the survivor; the statement-count bound.
- [x] T008 `party_detail`, `party_balance_rows`, `credit_exposures`, Shopify and file interpretation.

## Phase 4: Surfaces (FR-005)

- [x] T009 Tests in `tests/test_party_merge_adapters.py`: MCP strict schema, CLI, web API.
- [x] T010 Tools, MCP, CLI, web API, the partner page's merge action.
- [x] T011 Catalogs, refusals, i18n, data model, docs.

## Phase 5: Journeys (FR-006)

- [x] T012 Stories L10 and O02 in `tests/scenarios/test_catalog_party_merges.py`; promote both.
- [ ] T013 Full suite, spec policy, PR.
