# Implementation Plan: Guided Analysis Builder

**Branch**: `main` | **Date**: 2026-09-18 | **Spec**: [spec.md](spec.md)

## Summary
Keep Traversal and the existing executor authoritative. Add lossless path formatting and a constrained, metered question interpretation service; build the screenshot presentation over existing catalog/filter/report controls. No migration.

## Technical Context
Python 3.12, Pydantic v2, SQLAlchemy 2/PostgreSQL, existing httpx provider transport; React 19/TypeScript and local CSS. pytest, Node behavior tests and frontend build/i18n gates. Existing execution timeout, path length and result cap remain. UI supports 390px and desktop with docked chat.

## Constitution Check
| Principle | Pre-design | Post-design | Evidence |
|---|---|---|---|
| Source → Evidence → Reality | PASS | PASS | Existing model/SQL explanations and evidence references retained |
| Reality authority | PASS | PASS | No source status treated as settlement; unsupported finance metrics refused |
| Proven schema | PASS | PASS | No schema change; drafts are transient |
| Tenant/service boundary | PASS | PASS | Shared graph tools, current caller, existing tenant/provider policies |
| Specification/test evidence | PASS | PASS | Accepted scope, tests first, no completion with red gates |
| Explainable web | PASS | PASS | One question in sentence, actual links, path and result |
| Storage discipline | PASS | PASS | PostgreSQL and existing query compiler only |
| Received values | PASS | PASS | No new arithmetic authority, no fabricated KPIs |

## Project Structure
- `packages/reality-core/src/reality/services/analytics/cypher_surface.py`: parameterized formatter and complete parse round trip.
- `packages/reality-core/src/reality/services/analytics/interpretation.py`: constrained question interpretation with existing provider credentials, policy and managed question reservation. No general tool loop or writes.
- `packages/reality-core/src/reality/tools/graph.py`, `tools/application.py`, `mcp/catalog.py`: shared formatting/interpreting tools; canonical answer editor metadata.
- `packages/reality-core/src/reality/web/analytics_api.py`: thin adapter additions, preserve unrelated working-tree edits.
- `apps/web/src/unified/analytics/GraphSteps.tsx`: retain tested query helpers, replace Builder presentation and expose reusable controls.
- `apps/web/src/unified/analytics/AnalysisBuilder.css`: scoped reference styling, responsive/theme/accessibility rules.
- `apps/web/src/api.ts`, `localization.tsx`: complete advanced query shapes, API calls and translations.
- `packages/reality-core/tests/test_analysis_builder.py`, `apps/web/scripts/graph-steps.test.mjs`: round trips, provider refusals, lossless advanced state and query controls.

## Implementation order and verification
Tests → services → tools → API → web. Read-only graph analysis is distinct from explicitly saved private reports. Use declared template examples first, with exact labels rather than fake open-invoice/revenue examples. Three summary cards report returned rows, active measures and last read; scalar measure results can be displayed directly without aggregating result rows. Graph badges are not fabricated; show relation multiplicity and actual filters instead of unsupported distinct counts.

Run focused Python/Node tests, full pytest and lint, spec-check, web-build and docs generation/catalog checks. Visual QA uses screenshots when an available browser can render the local page; record a concrete blocker if no browser surface exists. All task markers reflect executed evidence.

## Reference inspection follow-up
Explore data is now verified in signed-in Chrome. Add `DataExplorer.tsx`, an `explore` analytics route, catalog-derived counts and bounded previews; transition using an unsaved initial question. Keep the builder mounted while viewing the catalog to preserve drafts. FR-013 maps to T019, including transition tests. Constitution checks remain PASS.

## Migration, rollback and risks
No migration. Revert the presentation and additive tools to roll back. Preserve existing saved definitions including advanced clauses; unsupported simple-mode shapes remain in expert mode. Provider availability and AI quota errors are explicit. Existing unrelated dirty files are never reverted or staged wholesale. No deployment or push is part of this local implementation request.

## Owner-requested design refinement
Remove the Builder heading/status/question/examples UI and unused input request state. Retain shared interpretation services and template navigation. Align Builder and Explore data with spec225 flat register surfaces and shared theme tokens, compact controls, semantic sentence colors and themed graph/editor. No domain, persistence or API changes. Constitution Check: passed; no new authority or tenant behavior. Validate existing state/contract tests, TypeScript/build, formatting/localization and browser appearance.

## Shared component integration
Owner approved the seven-point consistency review. Replace remaining approximate analytics styling with RegisterWorkbench, RegisterHeader local navigation, RegisterToolbar, PageActionBar and ERP table classes. Keep semantic sentence token colors as an intentional domain affordance. No API/domain/schema changes; Constitution Check PASS. Preserve mounted drafts while gating portalled actions by active view. Verify state/contract tests (including inactive action suppression), build, localization, format and Chrome.

## Three-area navigation and chat integration
Owner approved the concept in conversation. Reuse current routing, global chat open event, shared tools and tenant/owner-checked graph proposal endpoint. Templates resolve periods client-side and open an unsaved question. Use a bounded plain-text context suffix in user chat messages (presentation parsing only, no trusted tool authority) for a snapshot of the checked query; show removable context before sending. Use a dedicated analytics proposal route parameter to avoid unrelated proposal state. The destination reads/validates the proposal through the existing API and executes via GraphSteps; no domain/schema/API changes. Constitution gate PASS. Tests cover default/legacy routing, template no-write behavior, context serialization/bounds/tenant match, drafts, proposal navigation and pre-existing chat guards; run web suite/build/localization and browser review.

## Question hierarchy refinement
Use a single local framed section, shared theme tokens, larger sentence controls and native details/summary for subordinate controls. Move chat adaptation from result navigation to the section heading. Deduplicate only the exact period filter rendered in the sentence and provide explicit whole-period removal in its menu. Show measure names in a sentence selector linked to the advanced controls; retain record/path controls and all aliases/required axes. Constitution Check PASS, no schema/API/domain changes. Tests exercise period visibility/removal without losing other filters; full web checks and available browser review.

## FR-019 implementation and review
Owner approved the compact editable-sentence concept. Update presentation only in
GraphSteps and scoped CSS; derive captions from the existing catalog without changing
Traversal, identity axes, units, filters, execution, saving or chat confirmation.
Tests first: caption abstraction preserves the query, timestamp control remains
accessible, existing snapshot and builder state tests. Verify all web contracts,
format/build/i18n, spec policy, and Chrome. Backend unchanged; full backend rerun is
not required for this presentation-only refinement. Constitution checks remain PASS;
no clarification or critical analysis finding remains.
