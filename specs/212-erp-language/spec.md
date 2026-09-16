# Feature Specification: ERP language for operational screens

**Language**: English
**Created**: 2026-09-16
**Status**: Approved scope
**Input**: The user requests a PR improving awkward German wording and reviewing the other non-English languages from an ERP clerk's perspective.

## Context and Intent
Preview actions currently describe an explanation rather than opening record details. Some master-data headings translate English abstractions literally; some status labels risk confusing recording with completion.

### Scope
Review German, Dutch and Spanish labels in operational previews, master data and adjacent Sales, Purchasing, Warehouse and Finance actions. Apply concrete wording corrections consistently through existing catalog keys. Preserve useful established ERP terms.

### Non-Goals
No general English copy rewrite (one context-specific delivery heading is allowed), model noun renaming (spec 208), source text translation, quantity layout redesign, new business fields, routes, permissions or business calculations. No wholesale rewrite of marketing, developer tooling or every historical catalog entry.

## User Scenarios & Testing
### User Story 1 - Recognize actions and data (Priority: P1)
An ERP clerk using de/nl/es can identify the detail action and understand master-data and preview headings without interpreting literal English constructions.
Acceptance: The full-explanation action names viewing all details in each language; the matching overflow message uses the same destination wording. Master-data identity and inventory headings use ordinary business vocabulary. Context-sensitive labels retain their meaning across every caller.
Independent test: Review the before/after language table and run catalog and formatting checks.

### User Story 2 - Trust the wording (Priority: P1)
A clerk can distinguish data being recorded from an operation being completed, and tracking of items from shipment updates.
Acceptance: Recording does not claim completion; no wording implies shipment receipt/payment that is not recorded. Canonical English model names and original business values remain unchanged. Existing actions still use the same keys and routes.
Independent test: Existing model terminology and original-value/formatting tests, plus manual review of key usage.

## Requirements
- **FR-001**: Replace awkward detail-action/overflow wording consistently in de/nl/es.
- **FR-002**: Use natural business vocabulary for reviewed master-data and operational labels in all three languages, recording the decisions and retained terms.
- **FR-003**: Preserve recording/completion, reservation/availability and shipping/tracking distinctions; preserve canonical model nouns, source values, English and business behavior.

## Success Criteria
All three supported non-English languages have a recorded review. No reviewed detail action calls itself a complete explanation. Localization audits, canonical terminology checks, original-value formatting tests and production build pass.

## Assumptions and Dependencies
User approval covers this wording-only follow-up PR. Scope follows the screens discussed in specs 165, 208 and 209. Shared keys require inspection of their callers before editing. No unresolved clarifications.

## Requirement Traceability
| Requirement | Tasks | Verification |
|---|---|---|
| FR-001 | T002,T003 | Before/after review and catalog audit |
| FR-002 | T002,T003 | Three-language review and web build |
| FR-003 | T001,T002,T004 | Existing model terminology, formatting and source-value tests; key-only diff review |
