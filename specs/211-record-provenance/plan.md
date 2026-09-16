# Implementation Plan: Visible record provenance and source addressing

**Date**: 2026-09-16 | **Spec**: [spec.md](spec.md)

## Summary
One shared provenance service resolves record origin from the `source_record_id` that operational tables already carry, joining the retained textual source system code to the tenant's configured `SourceSystem`. Registers and details render that single contract; the existing inline and full Inspector gain the retained payload, the terminal interpretation outcome and the produced-record links they were missing. Two nullable columns on `SourceSystem` — an external base address and the connector shell it was installed from — plus an optional per-source-type address template in the connector catalog compose an external link at read time. No ingestion, interpretation, payload or received value changes.

## Technical Context
Python 3.12+, SQLAlchemy 2/PostgreSQL, FastAPI, Alembic; React/TypeScript with existing localization and table preferences. pytest service/API proofs and Playwright browser acceptance. No new dependencies. Bound payload presentation and produced-record lists explicitly; resolve origin per displayed page in batched statements keyed by `source_record_id`, never per row.

## Constitution Check
Pre-design: PASS for all eight principles.
- **I. Source → Evidence → Reality**: the feature exposes the existing chain and adds no new link. `SourceRecord` stays immutable and lossless; the textual source-system snapshot stays authoritative for what was received.
- **II. Reality is the operational authority**: origin is presentation over existing opaque links. No state moves to Documents, and no human-readable number becomes identity; the external reference is displayed, never joined on.
- **III. Proven schema only**: two nullable columns on `SourceSystem`. `base_url` is proven by US3 — without it no link can exist, and the user has decided it belongs to the instance. `connector_code` is proven twice over: it is joined on to resolve address templates and filtered on to group instances under their connector, and the inference it replaces is demonstrably wrong today, associating one `shopify_payments` instance with both the `shopify_payments` and `shopify` shells. Rejected simpler alternatives are recorded in `research.md`. No column is added to `SourceRecord` or to any operational table.
- **IV. Tenant and service boundaries**: every resolution is tenant-scoped, including the code join; configuration goes through an application service and the existing business-operation policy; web, MCP and CLI read the same service.
- **V. Specification and test evidence**: scope approved in conversation on 2026-09-16 and recorded here; every FR maps to a test and an implementation task; tests precede implementation.
- **VI. Explainable web product**: this is that principle applied to the one path the workspace was missing — from an operational row to the payload that produced it.
- **VII. Simplicity and storage discipline**: one new service module, one migration, no new infrastructure. Address templates are data in the existing catalog file, not code.
- **VIII. Received values are recorded, never recomputed**: the payload is displayed verbatim and bounded; nothing is normalized, reformatted or re-derived for display.

Post-design: to be re-recorded in `verification.md` before implementation tasks are accepted.

## Project Structure
- `packages/reality-core/migrations/versions/0061_source_system_addressing.py`: two nullable columns plus a one-time unambiguous backfill of `connector_code`.
- `packages/reality-core/src/reality/db/core.py`: `SourceSystem.base_url`, `SourceSystem.connector_code`.
- `packages/reality-core/src/reality/services/provenance.py`: new shared module — origin resolution for a bounded set of `source_record_id` values, manual-origin fallback from `ChangeProposal`, contributing-source disclosure from Facts, and external link composition.
- `packages/reality-core/src/reality/services/core.py`: `install_connector_shell` records the shell; `connector_shells` groups instances by the recorded shell instead of the description prefix; `set_source_system_base_url` validates and stores the address.
- `packages/reality-core/src/reality/services/delivery_reads.py`: `source_record` inspection gains payload, interpretation outcome and the resolved link.
- `packages/reality-core/src/reality/services/reference_workspace.py` and the operational register reads in `core.py`: bounded origin enrichment per displayed page.
- `packages/reality-core/config/connector_catalog.yaml` and `src/reality/integrations/catalog.py`: optional `deep_links` per connector plus the validator that currently pins the connector key set to exactly four keys.
- `packages/reality-core/config/tenant_isolation_catalog.yaml` and `tests/test_application_catalog.py`: classify each new public function and bump the pinned discovered-operation count (486 on main at planning time).
- `packages/reality-core/src/reality/web/api.py`: origin in existing read payloads; base-address configuration route.
- `apps/web/src/api.ts`, new `apps/web/src/unified/SourceBadge.tsx`, `unified/RegisterTable.tsx` column profiles, `unified/MasterDataPage.tsx`, `unified/OrdersPage.tsx`, `unified/CommitmentsPage.tsx`, `unified/ShipmentsRegister.tsx`, `unified/FinancePage.tsx`, `unified/InlinePreview.tsx`, `unified/SourceConfiguration.tsx`, `src/localization.tsx`.
- `packages/reality-core/tests/test_provenance.py`, `tests/test_source_system_addressing_migration.py`.
- `apps/web/scripts/record-provenance-browser.mjs`, `apps/web/scripts/provenance-labels.test.mjs`.
- `docs/features/source_ingestion.md`, `docs/DATA_MODEL.md`, `docs/WEB_SPEC.md`, `docs/SPEC_COVERAGE_MATRIX.md`.

## Verification and Rollback
Run the targeted PostgreSQL tests first, then the migration test, then full pytest, ruff, spec-check, web-build (format/contracts/i18n/build), docs-catalog-check and the provenance browser script. Rollback is code plus one downgrade dropping two nullable columns; no data is written by the migration, so rollback loses only configured addresses. Do not overwrite the unrelated changes present in the shared working tree; prepare the branch from a clean checkout of `origin/main`.

Main risks: a register read that resolves origin per row instead of per page; a link composed from payload text; a payload rendered unbounded; the pinned isolation-catalog count conflicting with a parallel branch; and a backfill that resolves an instance the existing rules leave ambiguous. The backfill must accept a single match only, and the description-prefix test must be removed in the same change so two answers to the association question never coexist.

## Complexity Tracking
No open exception. FR-007 adds a second column beyond the address the user asked for; it was reviewed as a product-scope decision and approved on 2026-09-16 after the present double association in `connector_shells` was demonstrated. It is recorded here because the approval, not the column, is what the Constitution requires to be explicit. Should a later review reverse it, FR-007, SC-006 and acceptance scenarios US3.5 and US3.6 are dropped together, links resolve only for source systems whose code equals a catalog connector code, and every other requirement stands unchanged.
