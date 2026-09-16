# Feature Specification: Consistent Source labels

**Language**: English
**Status**: Approved scope
**Input**: User approves Source instead of Origin/Ursprung for data-source labels, with related filters and details consistent across languages.

## Context and Intent
Register provenance columns use Origin while other data-source labels use Source/Quelle/Bron/Fuente. Use Source consistently for the data source; keep Source Record as the name of an individual received record.

### Non-Goals
No global replacement of spatial origin, stock locations, software source code, original business values, API/schema identifiers or business logic. No rewrite of every explanatory paragraph using the ordinary word source.

## User Scenarios & Testing
### US1: Recognize the source (P1)
Orders, master-data and document register origin columns are named Source in all languages. Source/Sources and direct source-system/type/name/reference labels use the same vocabulary.
### US2: Inspect the original record (P1)
Related source actions/metadata keep the distinction between the source system and the Source Record being inspected. Provenance groups containing source-system/external-ID fields use Source. Existing payload/record inspection and external links remain unchanged.

## Requirements
- **FR-001**: Replace data-source Origin column labels with Source using existing shared localization.
- **FR-002**: Use Source/Sources and consistent localized compounds in direct data-source labels/actions/settings; name links/details for the individual received payload Source Record.
- **FR-003**: Preserve Source Record vocabulary, technical identifiers, routes, original data, geographical origins and source-code terminology.

## Success Criteria
Existing provenance label tests assert the new shared names and record distinction. Reviewed catalog values agree in de/nl/es. Existing frontend tests, audits, build, spec policy and provenance browser checks pass.

## Assumptions and Dependencies
User approved Source in every UI language. Existing metadata contracts and SourceBadge remain authoritative. Scope is UI labels and direct source metadata/actions, not technical vocabulary or all prose. No unresolved clarifications.

## Requirement Traceability
| Requirement | Tasks | Proof |
|---|---|---|
| FR-001 | T001,T002 | Provenance label regression and browser |
| FR-002 | T001,T002 | Catalog review and vocabulary assertions |
| FR-003 | T003 | Original-value tests, caller/diff review, provenance browser |
