# Implementation Plan: Operational quick previews

**Date**: 2026-09-16 | **Spec**: [spec.md](spec.md)

## Summary
Add an optional, server-owned preview section contract to the existing Inspector read. A shared service composes existing scoped document, delivery, inventory, shipment and settlement reads. Only inline requests ask for preview content; full Inspector sections and actions remain compatible. No domain/storage changes.

## Technical Context
Python 3.12+, SQLAlchemy 2/PostgreSQL, FastAPI; React/TypeScript and existing localization. pytest service/API proofs and Playwright browser checks. No dependencies. Bound preview rows to 20 per section with an explicit overflow notice; batch identity lookups. Avoid tenant-wide financial registers for single-record reads.

## Constitution Check
Pre-design and post-design: PASS for all eight principles.
- Source → Evidence → Reality: existing opaque links preserved.
- Operational authority: shared reads calculate fulfillment/settlement, no document statuses added.
- Proven schema: no migrations or business fields.
- Tenant/service boundaries: all lookups scoped; presentation calls shared service; reads only.
- Specification/test evidence: approved conversational scope; tests precede implementation; completion gated on checks.
- Explainability: keep full explanation and named record links.
- Simplicity/storage: existing stack; one presentation composition service.
- Received values: retain source-stated descriptions/amounts; distinguish current-name fallback.

## Project Structure
- `packages/reality-core/src/reality/services/operational_previews.py`: shared composition.
- `packages/reality-core/src/reality/web/api.py`: optional preview query delegation.
- `apps/web/src/api.ts`, `unified/InlinePreview.tsx`, `unified/Inspector.tsx`, `unified/ShipmentsRegister.tsx`: contract/rendering; remove duplicate shipment details now supplied by the shared preview.
- `apps/web/src/localization.tsx`: four-language labels; `apps/web/scripts/operational-preview-labels.test.mjs` also checks server-produced vocabulary.
- `packages/reality-core/tests/test_operational_previews.py`: service/story/adapter regression.
- `apps/web/scripts/operational-previews-browser.mjs`: responsive read-only browser acceptance.
- `docs/WEB_SPEC.md`, `docs/SPEC_COVERAGE_MATRIX.md`: durable contract/traceability.

## Verification and Rollback
Run targeted PostgreSQL tests first, then full pytest, ruff, spec-check, web-build (format/contracts/i18n/build), docs-catalog-check and preview browser checks. Rollback code; no data migration. Do not overwrite unrelated working changes. Main risks: label history, financial reversal semantics, missing values, foreign links and localization. Existing business-service tests remain authoritative.

## Complexity Tracking
No exceptions.

## Approved master-data extension
Reuse `reference_workspace.py` for page-bounded list enrichment and tenant-scoped named references. Add transient grouped preview sections to `reference_detail` without changing the raw fields or revision fingerprint. Render through shared Inspector presentation in `MasterDataPage.tsx`; update register column profiles in `RegisterTable.tsx`. Move only the Master data link in `Shell.tsx`. Test existing editing/revision behavior alongside list/preview values and all four browser families. No schema expansion; all Constitution gates remain PASS.
