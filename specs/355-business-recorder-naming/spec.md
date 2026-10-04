# Business Recorder product naming

## Context and Intent
Replace the user-facing Business Graph product name with Business Recorder. The owner requested consistent application and landing-page naming across both repositories, retaining English product terms and localizing explanations.

### Non-Goals
No schema, route, technical graph identifier, ingestion, authorization, or business-rule changes. Do not rewrite historical specifications or imply complete upstream capture.

## Requirements
- **FR-001**: Navigation, search, diagrams, accessibility labels and marketing use Business Recorder in English, German, Dutch and Spanish.
- **FR-002**: Explain recorded business events, relationships, chronology and source traceability in localized introductory copy, comparing the Business Recorder to a flight recorder for the company.
- **FR-003**: Current onboarding, glossary and human-facing catalog labels agree with the UI. Generated catalogs retain stable tool identifiers.
- **FR-004**: Preserve existing routes, confirmation rules, model terms and capture limits.

## User Scenarios & Testing
In each supported language, the Inspector and site show Business Recorder unchanged, with localized explanatory text. Existing overview and graph links continue to resolve. No former product label remains in active UI copy.

## Assumptions and Dependencies
The existing timeline and record graph remain the same product area. This spec supersedes previous naming requirements only. The linked repository owns its existing surfaces.

## Success Criteria
No former product label remains in active product or marketing copy. Localized descriptions accompany the invariant name. Existing checks pass.

## Requirement Traceability
FR-001: terminology and navigation tests, localization audits. FR-002: localized explanation and builds. FR-003: generated catalog and current docs checks. FR-004: unchanged routing identifiers and diff review.

**Language**: English
