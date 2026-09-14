# Implementation Plan: Unified Data and Sources

Branch: `139-unified-app-foundation` | 2026-09-07 | [Spec](spec.md)

## Technical Context and Summary
Existing Python/SQLAlchemy/PostgreSQL/FastAPI and React/TypeScript. No schema or dependencies. Presentation-only metadata read composition in web/source_reads.py: scoped column selections, SQL counts, stable server pagination via existing page_for. No alternative business calculations. Original payload available only through existing selected-record Inspector.

## Constitution Check
| Principle | Result | Proof |
| --- | --- | --- |
| I Source → Evidence → Reality | PASS | Exact source version → existing evidence → Inspector |
| II Reality authority | PASS | No operational document status added |
| III Proven schema | PASS | No schema |
| IV Tenant/services | PASS | Tenant criteria on counts, joins and records; read-only adapter |
| V Spec/tests | PASS | Authorized continuation, tests before implementation, full gates |
| VI Explainability | PASS | Existing source/document Inspectors |
| VII Simplicity | PASS | Existing stack/pager, no infrastructure |
| VIII Received values | PASS | Source unchanged; document amounts displayed, never recomputed |

All PASS before/after design; no complexity exception.

## Design / Project Structure
- `packages/reality-core/src/reality/web/source_reads.py`: source-system register with SQL source-version count; source metadata register with scoped ImportJob outer join. Source payload and job input/error never selected.
- `web/api.py`: GET data-sources/systems and data-sources/records, q max500, source_system max200, page >=1, size 1..100; ordinary-company guard. Existing evidence-documents gains optional exact source_record_id.
- `web/read_models.py`: optional exact-source criterion inside document_page before count/page; all existing callers preserved.
- `apps/web/src/api.ts`: source metadata clients and additive document source-system/source-ID parameters.
- `apps/web/src/unified/DataSourcesPage.tsx`: three tabs, server search/pager, source/version labels, literal job state, exact evidence navigation, existing Inspector, supporting setup/import/Explorer links.
- `routing.ts`, `Shell.tsx`, `UnifiedApp.tsx`, `CaseAssistant.tsx`: data-sources route and data_view/source_system/source_record/evidence_type/entry state; company clears context.
- `localization.tsx`: all controls in four languages.

## Order / Verification
No domain/service/tool mutation needed. Add failing metadata API and route tests first, then read composition and adapter, then frontend and browser. `tests/test_unified_source_api.py` proves payload exclusion, SQL column selection, counts/paging/versions, exact-source evidence, tenant scope and no writes. Existing source ingestion/interpretation tests retained. Browser source → evidence → Inspector, company switch/reload, search/paging, empty/retry and original-content safety, 48 localized screenshots. Full backend/frontend/docs/lint/spec and all unified browser regressions.

## Limits and Rollback
Source system counts are held versions, not connections or external objects. Document search does not claim party-name matching; direct link counts are omitted. Selected Inspector loads one full original without a byte-size cap; no lazy payload-fetch claim. No full registry preload or full-source client filtering. Unregistered system records stay visible. Supporting legacy paths retain advanced actions. Opt-in switch remains rollback; no migration, deployment or retirement.
