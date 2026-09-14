# Implementation Plan: Data Model Explorer

**Branch**: `175-docs-data-model` | **Date**: 2026-09-12 | **Spec**: [spec.md](spec.md)

## Summary
Extend the static documentation explorer with a Data Model tab. Generate complete field metadata from SQLAlchemy models; keep bilingual business annotations in docs-owned data. Reuse existing tool contracts and navigation.

## Technical Context
Python 3.12, SQLAlchemy 2, Vue 3 and VitePress already exist. No dependencies, database connections or business writes. Scope: nine records and their relationships. Tests: Python schema parity and Node docs contracts, rendering checks, full docs build.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Examples explain the chain and shortest actual links | PASS |
| Reality owns operational state | Derived values separate; no document fulfilment fields | PASS |
| Proven schema only | No business schema changes | PASS |
| Tenant + shared services | Offline metadata only; actions link to shared tools | PASS |
| Spec/test traceability | FR mapping below; owner accepted scope | PASS |
| Explainable web behavior | Fields, actual relationships and action contracts | PASS |
| Received values not recomputed | Illustrative received quantities; derived observations labeled | PASS |
| Smallest coherent design | Static metadata and one focused Vue component | PASS |

## Repository Structure and Layer Changes
- `apps/docs/scripts/data_model_reference.py`: inspect Base.metadata and annotate descriptions, examples and semantic guidance.
- `apps/docs/scripts/generate-catalog-reference.py`: integrate metadata into generated tool-usage.json.
- `apps/docs/.vitepress/theme/components/DataModelExplorer.vue`: searchable responsive object and field reference.
- `apps/docs/.vitepress/theme/components/ToolUsage.vue`: tab, hashes and history integration.
- `apps/docs/content/{de/,}concepts/business-reality-guide.md`: entry link.
- `apps/docs/scripts/data-model.test.mjs` and `test_data_model_reference.py`: contract and schema parity tests.
- `apps/docs/Dockerfile`: copy generator helper.
- `apps/docs/.vitepress/theme/custom.css`: constrain code-block margins to narrow document padding.
- `.github/workflows/quality.yml`, `Makefile`: run schema parity in existing docs gates.

## Design
### Reality flow
Read actual SourceRecord, Document, DocumentLine, Commitment, CommitmentRevision, Reservation, Movement, LedgerEntry and Fact metadata without any tenant query. Model defaults are documented as persistence defaults, never promises about every tool. Follow exact foreign keys; external related tables link to existing table-map reference.
### Service and adapter flow
No domain/service/tool changes. Commands writing an object are obtained from existing catalog entries; descriptions distinguish correction/revision from direct edits. New model hashes use `model:<table>`; tool navigation reuses existing selection history. Static metadata is loaded with the existing JSON.
### Data and migration impact
No business changes or migration. Type, nullable and default come from SQLAlchemy; field meanings use reviewed annotations with existing data_model.yaml as fallback. Examples validate field names and are marked incomplete illustrative excerpts.
### Failure, security and tenant behavior
Unknown object hashes return a usable object list. Missing fields/commands in curated annotations fail generation. No user input reaches SQL, no connections, no live data.

## Test Strategy and Traceability
| Requirement | Tests | Initial failure |
|---|---|---|
| FR-001 | Node: all nine objects, bilingual purpose/example | Missing data model |
| FR-002 | Python: exact column/type/nullability/default parity; Node: field details | Missing generator |
| FR-003 | Node: action and relation targets; revision guidance | Missing links |
| FR-004 | Node: source/fact/derived semantic boundaries | Missing explanatory content |
| FR-005 | Component render/navigation checks, responsive CSS and build | Missing tab |
| FR-006 | Bilingual handbook links; deterministic regeneration; Docker build | Missing links/helper |

## Rollout and Rollback
Build the static docs image and preview on 8083 from this isolated worktree. Revert the docs commit to roll back; no backend coordination. Preserve existing handbook changes.

## Review Risks
Storage nullability is not input requiredness; scalar defaults differ from command defaults. SQLAlchemy imports must remain offline. Old YAML meanings can be stale; review every covered column. Narrow layouts must wrap all text.

## Complexity Tracking
No exceptions. Post-design Constitution Check: all PASS.

## ERP expansion plan and review

Keep the same generated metadata contract, adding group and bilingual group label. Extend existing curated definitions after inspecting current SQLAlchemy fields; fail on missing descriptions, invalid examples or unknown related record keys. Add all stored fields through the existing generator. No new helper module, dependency, migration or service.

Group buttons limit the visible object picker; global search overrides the active group. A selected record switches to its group. Explain empty action lists as catalog coverage, not lack of application support. Extend existing Python/Node tests before implementation and the versioned browser check for Party/Item/Shipment and cross-group search/history. Regenerate, build, inspect narrow/desktop views and replace the same local docs preview.

Constitution re-check: all eight rows remain PASS. Scope was explicitly accepted by the owner. Analysis before implementation: FR-007/008 are fully covered by T010–T013; no unresolved ambiguity or critical inconsistency.

## Field table presentation

FR-009 keeps the generated data unchanged. Replace field cards/details with a native table and scoped overflow wrapper in DataModelExplorer.vue. Use row/column headers, wrapped content and visible values; update browser selectors and semantic table assertion first. No business/schema changes. Constitution check remains all PASS. Analysis: T014–T016 cover the accepted table requirement and existing navigation regression; no unresolved or critical findings.

## Unified visual design

Add a feature-scoped `apps/docs/.vitepress/theme/tool-usage.css` with shared spacing, border, surface, radius and typography tokens; use shared classes in both explorer components and remove their duplicate visual rules. Keep layout-specific grid/table/navigation rules local. Introduce the same compact title/description header above search for all tabs. Retain model guidance in a native disclosure. No new dependencies or business changes. Existing field-table assertion will target the table region instead of forbidding unrelated disclosures.

Constitution check: all PASS. FR-010 maps to T017–T019 and existing regression checks; no unresolved clarification or critical analysis issue. Test before implementation, then build and inspect all tabs at mobile/desktop sizes in both themes.

## Compact header and search

FR-011 uses existing VitePress navigation and search components. Shorten only button text, preserve accessible names, hide the keyboard hint on tablets, and use scoped CSS to display the three primary links alongside the existing complete menu below 1280px. Exclude only the local search input from the global focus outline, since its parent already uses focus-within. No new dependency, route, business rule or storage change. Constitution check: all PASS. Requirements review: the owner requested these presentation changes; no unresolved clarification. Analysis: T020–T021 cover FR-011; no critical findings. Verify rendered layout and keyboard interaction before recording completion; no redundant source-string tests for CSS. Rollback by reverting the presentation changes.
