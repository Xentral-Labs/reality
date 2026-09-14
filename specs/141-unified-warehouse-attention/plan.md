# Implementation Plan: Unified Warehouse and Attention

**Language**: English
**Scope**: Existing ordinary-company investigation in the unified App; no schema or new mutation tool.

## Technical Context
Python 3.12, SQLAlchemy 2/PostgreSQL, FastAPI, React/TypeScript and existing semantic Tailwind controls. Work stays in `/private/tmp/reality-139`; preserve the uncommitted 139/140 implementation. No dependencies added.

## Constitution Check
| Principle | Result | Proof |
| --- | --- | --- |
| Source → Evidence → Reality | PASS | Existing Inspector follows exact original records and source links |
| Reality operational authority | PASS | Reuse inventory reads, reservations, movements and exception derivations |
| Proven schema only | PASS | No persistence or schema change |
| Shared services and tenant scope | PASS | Existing read models and canonical exception/correction services; scoped reference joins |
| Tests and spec before implementation | PASS | Tests precede service/adapter work; executable browser and full suite gates |
| Explainable UI | PASS | Quantities/findings link to exact records; existing delivery actions remain shared |
| Simplicity | PASS | Add two focused pages and thin read adapters; no workflow/command engine |
| Received values | PASS | Display recorded quantities; no monetary or cross-unit sums |

## Architecture and Implementation Order
1. Add regression/acceptance tests for exact-item filtering, corrections, tenant isolation, exception matching before paging, resolved findings and no read effects.
2. Add optional exact `item_id` filter to existing `inventory_page`, `reservation_page`, `movement_page` in `web/read_models.py`. Defaults preserve callers. Continue using their existing stock arithmetic, joins and ordering.
3. Add `services/attention_reads.py` wrapping canonical exception derivation/explanation with bounded response paging, search/severity filtering and exact delivery targets. Canonical severity ordering and resolution remain unchanged.
4. Add `web/warehouse_reads.py` to compose existing register output into JSON-safe rows, resolve bounded commitment types, and call the canonical movement correction relationship helper. No alternate correction rule or stock calculator. Default 50, cap 100. Known cost: correction-role checks are bounded per selected page; exception derivation still evaluates the company before slicing.
5. Add strict GET endpoints in `web/api.py`: `/warehouse/{view}`, `/attention`, `/attention/{id}`. Ordinary-company guard reused from 140; no new write endpoint.
6. Add typed API helpers, `WarehousePage.tsx`, `AttentionPage.tsx`, route/selection fields, sidebar entries, Home attention link, delivery inventory link and item-to-warehouse navigation. `/app/attention` deliberately leaves `/app/exceptions` available for existing unsupported proposal/correction workflows.
7. Verify four languages/themes/widths, saved URLs, keyboard Inspector, failures and existing shared delivery action paths.

## Legacy Capability Decisions
Keep company-wide item stock, reservations, recorded movements, canonical findings and explanation. Redesign their presentation. Keep specialist receiving, transfers, release and correction controls in supporting workspaces; no new mutation card is justified by this investigation increment. Defer Finance and integrated practice. Do not remove old routes.

## Migration and Rollback
No database change. New destinations are under the existing opt-in frontend flag. Existing API response shapes stay unchanged; optional read-model arguments default to absent. Disabling the flag restores the old presentation without altering records or histories.

## Validation
`test_unified_operations_api.py`, `test_attention_reads.py`; existing inventory/correction/exception tests plus full PostgreSQL suite. Frontend route contracts, `unified-operations-browser.mjs`, full existing unified browser regressions, format/contracts/i18n/build. Docs checks, Ruff, Spec policy and diff review. Record actual evidence in quickstart.md; owner visual acceptance and rollout stay separate.

FR-009 refinement: Constitution PASS. Reuse ExceptionCatalog with an optional company context for introductory copy. Add a separate Attention card and modal state; preserve all existing finding logic. The existing authenticated catalog returns global metadata only. Verify operations browser, frontend contracts/build/localization/format/spec; no backend changes.
