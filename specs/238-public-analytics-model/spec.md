# Feature Specification: Public analytics model explorer

**Language**: English
**Status**: Approved scope from owner request, 2026-09-19

## Context and Intent
Expose the complete declared analytics model beside the existing Data model in the
public Tool Usage explorer so business readers and engineers can discover questions.

### Non-Goals
No live tenant data, query execution, graph database, runtime schema or catalog changes.
No manual duplicate of the analytics declaration and no redesign of existing tabs.

## User Scenarios & Testing
US1: A reader opens Analytics model, searches a business concept, selects an object
and sees its fields, relationships, measures and applicable starting templates.
US2: A reader follows a relationship or a permalink and can return with browser Back.
US3: A German reader sees localized model labels and explanatory UI; stable technical
keys and original technical declaration text remain unchanged.
Acceptance includes empty search, unknown object hashes, small screens and no data.

## Requirements
- **FR-001**: Add Analytics model next to Data model, with a direct link from both guides.
- **FR-002**: Generate all declared nodes, properties, incoming/outgoing edges, measures,
  templates and limits from the executable reporting model with no tenant reads.
- **FR-003**: Search names/keys/fields/measures and filter categories; show full object
  meaning, grain, source/derivation, coverage, correction rules and technical definition.
- **FR-004**: Explain measure units, additive restrictions and differences, allow related
  object navigation, and show template definitions without implying query execution.
- **FR-005**: Preserve existing explorer behavior; support stable analytics:key hashes,
  browser history, keyboard-operable controls, responsive wrapping and EN/DE UI.

## Success Criteria
Every declared model object and template is represented; no invented runtime value is
published. Generated-data tests, docs contracts and production build pass.

## Assumptions and Dependencies
Use the existing graph catalog service without a session and the current docs generator.
The user approved placement and scope. Technical declaration prose may remain English.

## Requirement Traceability
FR-001/005 → T002/T003; FR-002 → T001/T002; FR-003/004 → T002/T003;
all → T004 verification.

## Canonical explorer terminology (owner refinement)

- **FR-006**: All explorer entry names remain English in every UI language: resources,
  processes and steps, technical entries, business-area groups, data-model actions,
  analytics objects/fields/relationships/measures/templates. Explanations, descriptions
  and controls remain localized. Existing German search terms remain discoverable.
  This supersedes FR-005 localized model-label wording, not localized explanations.
Acceptance: German shows Business partner and English Analytics names while retaining
German instructions and purposes; English and German searches still find the entries.
