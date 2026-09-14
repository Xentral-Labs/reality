# Feature Specification: Single-Level Site Navigation

**Feature Branch**: `[064-single-level-site-navigation]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "die ersten drei seiten sind eh eine seite könnte man da auch ein punkt in der nav draus machen"

## Context and Intent

### Problem

The public navigation lists five entries. Three of them — Connect, Agent core, Delegate — are anchors into sections of the landing page. The other two are the site's other pages.

So the navigation mixes two levels. Three of its five entries answer "where on this page", the remaining two answer "which page", and nothing distinguishes them. A reader choosing between them cannot tell that picking one of the first three keeps them where they already are while picking one of the last two takes them somewhere else. On the landing page itself, three of the five entries do nothing but scroll.

It also makes the site look larger than it is. Five navigation entries suggest five destinations; there are three.

### Scope

- Replace the three section anchors with one entry for the landing page.
- Leave the sections themselves, and their ids, exactly as they are.

### Non-Goals

- A dropdown holding the three sections. That keeps the deep links but adds a second layer of opening to a navigation with three destinations, and on mobile a disclosure inside the already-disclosed menu.
- Changing the landing page's sections, their order, or their content.
- Changing the footer, the language menu or the account actions.
- Adding or removing a page.

### Existing Contracts

- [Public Site](../022-public-site/spec.md)
- [Shared Site Footer](../063-shared-site-footer/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the navigation as a list of destinations (Priority: P1)

As a reader, every navigation entry takes me to a page, and there are as many entries as there are pages.

**Why this priority**: This is the request. A navigation whose entries mean two different things cannot be read at a glance.

**Independent Test**: Open any public page and read the navigation.

**Acceptance Scenarios**:

1. **Given** any public page, **When** the navigation is read, **Then** it lists exactly three entries, one per public page.
2. **Given** the navigation, **When** any entry is followed, **Then** a page opens rather than the current page scrolling.
3. **Given** a page other than the landing page, **When** the overview entry is followed, **Then** the landing page opens.
4. **Given** a language other than English, **When** the navigation renders, **Then** the overview entry is in that language.

### User Story 2 - Keep links already published working (Priority: P2)

As someone following a link to a landing-page section from an email, a post or a search result, I still land on that section.

**Why this priority**: Removing an entry from the navigation is a presentation decision; silently breaking an address that has been shared is not.

**Independent Test**: Open the landing page with each section anchor appended.

**Acceptance Scenarios**:

1. **Given** a link to a landing-page section anchor, **When** it is opened, **Then** the page scrolls to that section as before.
2. **Given** the landing page, **When** its markup is read, **Then** every section that previously had an id still has it.

### Edge Cases

- The landing page itself, where the overview entry points at the page already open.
- A non-English language, where the entry carries a query parameter that must survive.
- The mobile menu, which holds the same entries and now has two fewer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The navigation MUST list exactly one entry per public page and no entry for a section of a page.
- **FR-002**: The entry for the landing page MUST be labelled as an overview and MUST open the landing page.
- **FR-003**: Navigation links MUST keep the language query parameter for a language other than English.
- **FR-004**: The landing page's section ids MUST remain, so addresses already published still resolve.
- **FR-005**: Every string the navigation renders MUST be covered in all supported interface languages.

### Domain and Traceability Requirements

- **DR-001**: The change is presentation only; it MUST NOT alter a route, a page's content, or any product claim the Site makes.
- **DR-002**: It MUST add no table, column, endpoint, domain mutation or client-side state.
- **DR-003**: No page that was reachable MUST become unreachable.

### Key Entities *(when data is involved)*

- **Navigation entry**: One public page, named and linked. Not a position within a page.

## Success Criteria *(mandatory)*

- **SC-001**: The navigation shows three entries, and each opens a different page.
- **SC-002**: Every previously published section anchor still resolves on the landing page.
- **SC-003**: Interface-language coverage passes for every supported language with no missing string.
- **SC-004**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The landing page's sections remain reachable by reading the page, which is what a landing page is for; they do not need a navigation entry each.
- "Overview" is the right name for the landing page in the navigation. "Platform" would collide with the packages entry, which already points at the platform route.
- The section ids are addresses that may have been shared, so they are kept even though nothing in the Site links to them any more.

## Open Questions

None.

A dropdown was considered and rejected: it preserves the three deep links, but adds a layer of disclosure to a navigation with three destinations, and nests a menu inside the mobile menu. The sections stay reachable by scrolling, which is the ordinary way to read a landing page.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1-2 | Contract asserting three entries and no section anchor in the navigation |
| FR-002 | US1 scenario 3 | Overview entry present and pointing at the landing route |
| FR-003 | US1 scenario 4 | Language query retained on navigation links |
| FR-004 | US2 scenarios 1-2 | Contract asserting every section id survives |
| FR-005 | US1 scenario 4 | Interface-language audit across all supported languages |
| DR-001-DR-003 | US1-US2 | Diff review for presentation-only change and reachability of every page |
| SC-001-SC-004 | All scenarios | Full required quality gates |
