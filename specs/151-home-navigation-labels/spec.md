# Feature Specification: Consistent Home and navigation categories

**Language**: English

## Context and Intent
### Problem
Home counts and navigation name the same work differently and navigation lacks a commitments shortcut.
### Scope
Align category labels and destinations in the existing web UI.
### Non-Goals
No new business counts, routes, schema, service logic or dashboard activity changes.

## User Scenarios & Testing
### US1 — Find the same work from Home and navigation
The user sees Home followed by Commitments, Exceptions and Decisions in daily work.
The three Home cards repeat these labels and show a localized lowercase open qualifier below each count.
Acceptance: English and German labels match across both surfaces, including zero counts;
menu and card selections target the same views after previously filtered navigation.

## Requirements
- **FR-001**: Use Commitments, Exceptions and Decisions for both menu and Home cards. German uses the approved localized obligations, deviations and decisions labels. Show localized open qualifiers below existing counts; retain four-language coverage.
- **FR-002**: Share exact destination selections between menu and cards. Commitments opens existing open customer deliveries; Exceptions opens attention without previous severity/detail filters; Decisions opens decisions without a selected proposal. Reset search/page, preserve company context, and avoid duplicate active menu indicators.

## Assumptions and Dependencies
Owner approved naming and the new navigation entry in conversation on 2026-09-09.
The existing commitments card counts open customer deliveries; this scope remains unchanged.
Use existing shared dashboard reads and selection serialization. This standalone spec
extracts the approved naming refinement from local spec 149 FR-013–014 so it can ship independently.
No unresolved clarifications.

## Success Criteria
- SC-001: The three names match across menu and cards in English and German.
- SC-002: Both entry points open identical filter selections and retain the company.
- SC-003: Existing frontend contracts, production build, localization audit and spec gate pass.

## Requirement Traceability
FR-001 and FR-002 → US1, T001–T003. SC-001–003 → T003.
