# Feature Specification: Clear inspector navigation

**Language**: English

## Context and Intent
### Problem
Rules and Actions do not explain the content behind the navigation entries.
### Scope
Place rules beside their results and expose history and available actions separately.
### Non-Goals
No business logic, catalog, authorization, schema or action execution changes.

## User Scenarios & Testing
### US1 — Find facts and their rules (P1)
Given Business Facts, users can switch among All records, Calculated views and Fact rules.
### US2 — Find exceptions and their rules (P1)
Given Exceptions, users can switch among Open exceptions and Exception rules and open a finding from a rule.
### US3 — Understand inspector destinations (P1)
Given the sidebar, Event history and Available actions are separate destinations with appropriate headings and icons.

## Requirements
- **FR-001**: Business Facts contains All records, Calculated views and Fact rules; no separate Rules navigation entry remains.
- **FR-002**: Exceptions contains Open exceptions and Exception rules, reusing existing rule and finding views without changing their behavior.
- **FR-003**: Event history and Available actions have separate sidebar entries and no unrelated sibling tabs.
- **FR-004**: Old inspector rules, exceptions, history and commands links remain usable; company, search and finding context survive canonicalization. Back/forward and reload retain the selected Exceptions tab.
- **FR-005**: Navigation, tabs and headings use consistent English, German, Dutch and Spanish terminology and remain usable at desktop and mobile widths.

## Assumptions and Dependencies
The owner approved this exact structure in conversation on 2026-09-16. Existing services and catalogs remain authoritative. Available actions retains current permission and confirmation checks.

## Success Criteria
- SC-001: All five requirements have passing navigation/routing and browser evidence.
- SC-002: Frontend build, localization audit and spec check pass.

## Requirement Traceability
| Requirement | Tasks | Proof |
|---|---|---|
| FR-001 | T001,T002,T004 | Navigation contract and browser |
| FR-002 | T001,T003,T004 | Rules/finding browser transition |
| FR-003 | T001,T002,T004 | Sidebar and isolated destination checks |
| FR-004 | T001,T003,T004 | Routing regression, reload/back browser |
| FR-005 | T002,T004 | Four-language browser and responsive checks |
