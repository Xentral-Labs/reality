# Feature Specification: Email-only account menu

**Feature Branch**: `feat/account-menu-label`
**Language**: English
**Created**: 2026-09-18
**Status**: Approved
**Input**: Use My account in the sidebar, show the full email in the menu, and label the settings link Account settings.

## Context and Intent
### Problem
A truncated email above a redundant Profile subtitle makes the sidebar account control hard to recognize.
### Scope
A single account label and a readable account identity in the existing menu.
### Non-Goals
No new name field, inferred identity, authentication changes, settings redesign, menu actions or API changes.

## User Scenarios & Testing
### User Story 1 — Recognize and open my account (P1)
An email-only user sees My account in the sidebar and opens it to identify the signed-in account.
Acceptance: the expanded sidebar shows avatar, My account and chevron without an email or subtitle. The menu shows the complete email without a redundant Profile heading. Long emails wrap within the menu. Account settings opens the existing personal settings route. Collapsed navigation retains an accessible localized label and tooltip. All four supported languages and narrow screens remain usable.

## Requirements
- **FR-001**: Use localized My account as the single sidebar account label and accessible menu name; do not infer or require a personal name.
- **FR-002**: Show the unchanged full account email in the menu header, wrapping long addresses without ellipsis or horizontal overflow; omit the Profile heading.
- **FR-003**: Label the existing personal-settings menu entry Account settings; preserve navigation, appearance, external links, dismissal and sign-out behavior.

## Assumptions and Dependencies
The user approved this exact scope and requested a separate PR. Existing accounts are email-based. No clarification remains. Existing ProfileMenu and supported language dictionaries remain authoritative.

## Success Criteria
The sidebar no longer displays a truncated account identifier. The complete email is readable in the open menu at desktop and mobile widths. Existing account actions remain reachable.

## Requirement Traceability
FR-001–003 → US1 → T002–T004. Verify through existing shell/browser checks, localization audit, production build and explicit long-email visual inspection; no new unit tests for this presentation-only change.
