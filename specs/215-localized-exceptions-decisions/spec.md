# Feature Specification: Localized Exceptions and Decisions

**Language**: English
**Status**: Approved scope
**Input**: User approves translating these two concepts consistently across screens in a separate PR.

## Context and Intent
Spec208 kept all model nouns in English. The user now prefers localized Exceptions and Decisions for readability, while retaining the other canonical terms.

### Non-Goals
No technical identifier, API, schema, route, source-payload, English-language or business-rule changes. Do not translate the remaining canonical model nouns.

## User Scenarios & Testing
### US1: Recognize the two work areas (P1)
Navigation, Home, page titles and Inspector singular/plural labels use Ausnahme/Ausnahmen and Entscheidung/Entscheidungen (de), Uitzondering/Uitzonderingen and Beslissing/Beslissingen (nl), Incidencia/Incidencias and Decisión/Decisiones (es).
### US2: Follow consistent references (P1)
Search, links, catalog/rule headings, empty states, queue/history and helper text use the same vocabulary. Spanish object references currently using excepción/excepciones are made consistent with incidencia/incidencias. Shipping-specific delivery exceptions retain their existing natural wording.

## Requirements
- **FR-001**: Localize both object names, singular/plural, in de/nl/es throughout visible UI labels.
- **FR-002**: Align related navigation/search/catalog/rule/history/help wording, preserving grammar and action meaning.
- **FR-003**: Preserve other canonical terms, original content, English output, routes/identifiers and business behavior; amend the spec208 exception and vocabulary checks explicitly.

## Success Criteria
All three languages pass explicit noun and related-label checks. No English Exception/Decision tokens remain in localized catalog values referring to these objects. Existing formatting/source-content tests and language audit pass; production build passes.

## Assumptions and Dependencies
The user's approval supersedes spec208 only for these two objects. Existing shared translation keys reach all relevant surfaces. No clarification remains.

## Requirement Traceability
| Requirement | Tasks | Proof |
|---|---|---|
| FR-001 | T001,T002 | Updated terminology tests |
| FR-002 | T001,T002 | Related-label tests and catalog review |
| FR-003 | T001,T003 | Remaining canonical tests, source/format checks, diff review |
