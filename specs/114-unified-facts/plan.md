# Implementation Plan: Unified Facts

## Architecture
Domain/services unchanged → shared scoped web read model `packages/reality-core/src/reality/web/fact_reads.py` → existing /facts API → typed client and unified/FactsPage.tsx. Reuse page_for semantics, stable SQL sort and explicit column projection joins to SourceRecord and InterpretationRule; source payload/rule configurations stay out of list queries. Count the same filtered relation before paging. Subject types are distinct tenant values ordered/limited101, return100 plus has_more. No new persistence.

Add optional q/subject_type/subject_id/source_record_id parameters to existing API and client defaults. Preserve source/rule nested shapes; add source_version and subject-type choices metadata. Fact Inspector gets a recorded-observation meaning and a new linked context section, retaining technical-row shape. Link only supported subject kinds by exact ID and source FK. Missing source text is explicit. Raw fact values/predicates are marked original content in the register and Inspector value nodes, avoiding localization or HTML interpretation.

Unified /app/facts replaces the old basic Facts view under the feature flag. Sidebar, routing, UnifiedApp and CaseAssistant gain the destination/state. Compact cards show observation/value, subject/time and provenance, with Explain and Related observations. Search and subject filter are server-side. Source rows in DataSourcesPage gain View observations, setting exact source scope. Fact/source Inspector target is reloadable; changing company clears all scopes and selected IDs.

## Constitution Check
| Principle | Result | Evidence |
| --- | --- | --- |
| Source → Evidence → Reality | PASS | Exact source/subject links; no fabricated fact-document relationship. |
| Reality authority | PASS | Recorded observations do not replace typed operational state or select a current winner. |
| Proven schema | PASS | No schema/dependency changes. |
| Tenant/service boundaries | PASS | Existing observation services unchanged; all read joins/filter/count scoped. |
| Tests first | PASS | SQL/API, route and browser failure before implementation. |
| English artifacts | PASS | English code/docs, four UI languages, original recorded strings preserved. |

## Verification and rollback
Plan API tests for equal-time deterministic paging, filters before count, distinct repeated observations, foreign scope, no SourceRecord.payload in list SQL, subject-type bounds and Inspector source/subject links. Browser: search/filter/page, related subject, source→facts, original text under localization, escaped source, reload/focus, empty/retry/company reset and16 screenshots. Run full PostgreSQL, web contracts/i18n/format/build, all unified browsers, docs tests/format/build, spec policy/lint/diff and authenticated synthetic preview.

Rollback: disable unified feature flag or remove Facts route; API changes are additive. No migration/data rollback. Technical completion does not authorize retirement.
