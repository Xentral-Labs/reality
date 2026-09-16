# Feature Specification: Canonical Reality model terms

**Language**: English

**Created**: 2026-09-16
**Status**: Approved scope
**Input**: Use English Reality model keywords in every non-English interface for technical operators learning the model.

## Context and Intent

### Problem
Translated object names obscure the shared vocabulary between the technical product, model and API.

### Scope
Navigation, Home categories, Inspector type selectors, object headings and related navigation/search labels in German, Dutch and Spanish use canonical English model names. Surrounding controls and explanations remain localized.

### Non-Goals
No new simpler operational product, model changes, API changes, source payload rewriting, or translation of general business objects into English. No rewrite of historical documentation or externally managed marketing pages.

## User Scenarios & Testing

### User Story 1 - Learn one model vocabulary (Priority: P1)
As a technical operator, I recognize the same model objects regardless of UI language.

**Independent Test**: Compare navigation and Inspector object categories in en/de/nl/es.

**Acceptance Scenarios**:
1. Given de/nl/es, when navigating Home and object registers, then Commitments, Exceptions, Decisions and Facts retain their English names.
2. Given de/nl/es, when filtering Inspector records, then Facts, Source Records, Documents, Document Lines, Commitments, Reservations, Movements, Ledger Entries and Business Events use canonical names; Context Graph stays invariant.
3. Given a localized object search or navigation link, then its model noun is canonical and its control wording remains localized.

### User Story 2 - Keep localized operation (Priority: P2)
As an operator, I retain localized controls, business vocabulary and formatting.

**Independent Test**: Confirm Save, business partners, items and locations remain translated, and English output and original-content boundaries remain unchanged.

**Acceptance Scenarios**:
1. Given each non-English language, when viewing controls and general business categories, then existing translations remain.
2. Given English, then existing copy remains unchanged, including Additional facts.
3. Given original source data, then its content remains untouched.

### Edge Cases
Singular object names and compound navigation labels retain the same model noun. The Additional facts type denotes Fact records and is displayed as Facts in non-English languages. Explanatory prose may explain concepts in ordinary local language; generic decisions or exceptions in prose are not blindly rewritten.

## Requirements

### Functional Requirements
- **FR-001**: Use canonical English model nouns in all non-English navigation, Home categories, object headings and Inspector type labels, including singular forms.
- **FR-002**: Related object search, navigation links and category labels MUST retain the same model noun with localized control wording.
- **FR-003**: Preserve English copy, localized general business objects/controls, formatting, original payloads and all operational behavior.

## Success Criteria
- **SC-001**: All three non-English languages show the canonical vocabulary for every listed model type.
- **SC-002**: No related tested navigation/search label uses an alternative translated model noun.
- **SC-003**: Existing localization, formatting and original-content checks pass.

## Assumptions and Dependencies
The user approved this terminology and audience explicitly before implementation. Current non-English languages are de/nl/es. Existing catalog lookup and localization boundaries remain authoritative. This supersedes localized category naming in spec 151 and the corresponding Web contract; historical feature records remain historical.

## Requirement Traceability

| Requirement | Acceptance | Test | Implementation |
|---|---|---|---|
| FR-001 | US1 scenarios 1–2 | T003 | T004 |
| FR-002 | US1 scenario 3 | T003 | T004 |
| FR-003 | US2 scenarios 1–3 | T005 | T006 |
