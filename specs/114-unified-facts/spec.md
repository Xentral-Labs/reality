# Feature Specification: Unified Facts

**Created**: 2026-09-07
**Language**: English
**Status**: Owner-authorized continuation; second explicitly missing workspace after Orders & deliveries.
**Revised**: 2026-09-10 — the Workspaces sidebar link to `/app/facts` was removed (FR-001); the register itself is unchanged.

## Context and Intent
### Problem
Facts remain outside the unified sidebar. Operators need understandable recorded observations with exact subject/source context, without mistaking a past observation for guaranteed current truth.
### Scope
A read-only Facts register in the unified shell: search, subject-type filtering, related observations for one exact subject, exact-source drilldown, observed timestamps, stored values and shared Inspector provenance.
### Non-Goals
No validity/active/superseded classification, latest-value winner, conflict resolution, business status replacement, fact editing/creation, new predicates, AI decisions, schema, deployment, merge or legacy/Playground retirement.

## User Scenarios & Testing
### US1 — Find recorded observations (P1)
An operator searches recorded fact identity, predicate, subject type/ID, stored value or source metadata; filters by a subject type present in the company; and pages a stable newest-observed register. Each observation remains separate, including differing values at the same timestamp.
Acceptance: count and filters precede paging; timestamp ties sort by opaque ID; values/predicates remain as stored text. Missing source is shown as no linked source recorded, not inferred manual input. No status claims imply expiry or validity.
### US2 — Follow evidence and context (P1)
Explain an observation to see its stored value, time, exact supported subject and source links. Related observations shows all held observations for the exact type/subject ID. Data & sources can open observations for one exact source version.
Acceptance: foreign selected facts/sources remain inaccessible. Facts link directly to their source and subject; documents appear only through actual subject/evidence relationships. Unsupported legacy subject kinds remain plain recorded identities. Rule provenance is metadata, not a fabricated Inspector link.
### US3 — Work comfortably (P2)
Filters and selected Inspector survive reload; a company switch clears old context. Loading, empty and retry states are explicit. Keyboard operation and en/de/nl/es in light/dark at390/1440px work without page overflow.

## Requirements
- **FR-001**: `/app/facts` is the unified Facts register when the existing feature flag is enabled. It is reached from Data & sources (View observations) and from the Reality Inspector Facts group, which embeds the same register; the Workspaces sidebar group does not list it separately (revised 2026-09-10: the earlier Workspaces link duplicated the Inspector Facts group without adding content). The route stays valid for deep links. URL state contains q/page, exact subject type/ID, exact source ID and fact/source Inspector target; unsupported target kinds normalize safely.
- **FR-002**: Extend the existing tenant facts read with scoped SQL search and exact subject/source filters before count/paging; stable observed_at DESC/id DESC ordering and page clamping. Keep default response fields and source/rule metadata compatibility. Lists must not select original source payload or rule configuration.
- **FR-003**: Show recorded value, exact predicate, subject identity, observed time, source identity/version when held and optional interpretation rule/version. Keep repeated/differing observations separate. No source/validity inference or browser business calculation. Stored content must not be translated or executed as markup.
- **FR-004**: Related observations filters exact subject type+ID across held sources. Data & sources → Facts filters one exact source_record_id, not external reference. Both scopes have explicit clear controls and reset pagination.
- **FR-005**: Fact Inspector describes recorded observation semantics, exposes exact supported subject/source links and preserves existing technical metadata. No direct fact→document relationship is invented. Unsupported subject kinds and absent sources retain honest text.
- **FR-006**: Expose subject types from the current tenant, at most100 plus truncation indication, independent of current page/search. Preserve a selected value even if outside the bounded choice list. Empty/error/retry, foreign404 and company reset are covered. Register/Inspector navigation has no business writes.
- **FR-007**: New structural copy is localized in four languages, recorded values/predicates remain original and observed timestamps use account formatting. Keyboard Inspector focus/reload and16 language/theme/viewport combinations pass.

## Success Criteria
Service/API tests prove stable paging, exact scope, retained contradictory observations, source metadata without payload loading and shared Inspector links. Browser tests prove subject/source traversal, original-text preservation, safe payload rendering and16 screenshots. All required regression gates pass.

## Assumptions and Dependencies
The owner explicitly requested Facts after Orders & deliveries. The current catalog contains order.shipping_priority, while held legacy/rule observations may contain other types. Fact has only observed_at, no validity interval or supersession link. Existing observe_fact and rule persistence remain unchanged. Source metadata absence does not establish origin. Human rollout acceptance and remaining advanced-flow migration are separate.

## Requirement Traceability
| Requirements | Stories | Planned evidence |
| --- | --- | --- |
| FR-001 FR-006 | US1 US3 | Route/URL normalization, paging/reset/error/empty browser |
| FR-002 FR-003 | US1 | SQL filters/count/order, metadata-only queries, repeated/raw-value observations |
| FR-004 FR-005 | US2 | Exact source/subject traversal, Inspector links and foreign scope |
| FR-007 | US3 | Four-language original-content, keyboard, theme and viewport browser proof |
