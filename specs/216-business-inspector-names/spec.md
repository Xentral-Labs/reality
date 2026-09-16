# Feature Specification: Business Inspector area names

**Language**: English
**Status**: Approved scope
**Input**: Rename Context Graph to Business Graph and the Facts navigation area to Business Facts; check related UI names for consistency.

## Context and Intent
Use clearer business-oriented names for the two Inspector areas and the same names wherever a heading or graph reference names that destination.

### Non-Goals
No renaming of the Fact data type, fact filters, storyline fact counts, API/code identifiers, routes or original data. No business behavior or schema changes.

## User Scenarios & Testing
### US1: Recognize destinations (P1)
Navigation, tooltips, accessible names and area headings use Business Graph and Business Facts in every language. Existing overview/graph and facts/views routes remain unchanged. Sub-tabs retain descriptive names such as Timeline, Record graph and All records.
### US2: Follow consistent references (P1)
The standalone facts page heading matches Business Facts; Storyline graph headings, caption and accessible label use Business Graph. Fact/Facts remain canonical names for individual record types, filters and fact counts.

## Requirements
- **FR-001**: Rename Inspector area labels to Business Graph and Business Facts, including shared navigation/title/tooltip uses.
- **FR-002**: Align standalone facts headings and Storyline graph references; retain Fact/Facts for data-type contexts.
- **FR-003**: Treat new area names as invariant product labels in en/de/nl/es; preserve route/filter compatibility, technical identifiers, original content and other terminology policies.

## Success Criteria
Existing navigation tests assert new labels with unchanged destinations and legacy links. Vocabulary checks distinguish area names from Fact/Facts. All language/formatting tests, production build and browser checks pass.

## Assumptions and Dependencies
User approval covers the renamed navigation and directly related headings/references. Both new English product labels remain identical across languages. This updates the Context Graph product-name rule of spec208; spec215 localization of Exceptions/Decisions remains intact. No clarifications needed.

## Requirement Traceability
| Requirement | Tasks | Evidence |
|---|---|---|
| FR-001 | T001,T002 | Inspector navigation regression |
| FR-002 | T002,T003 | Caller review, vocabulary tests and browser |
| FR-003 | T001,T003 | Legacy route tests, language audits and source-value tests |
