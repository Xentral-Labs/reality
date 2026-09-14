# Feature Specification: Prominent Open-Source Entry

**Feature Branch**: `[066-prominent-open-source]`
**Created**: 2026-09-04
**Status**: Approved
**Language**: English
**Input**: "Make the open-source project substantially more prominent on the public Site so visitors notice it, continue reading, and explore the project."

## Context and Intent

### Problem

Reality is open source, but the public Site does not present that as a meaningful reason to engage. The repository is absent from the main navigation, and the small shared footer offers only Docs, sign-in, and account creation. A visitor who would inspect the code, evaluate the principles, or learn through the documentation can finish the page without discovering that path.

### Scope

- Make the main documentation page discoverable from the shared public navigation on every Site page; keep GitHub in the editorial open-source section rather than the header.
- Keep the landing-page ending focused on its account action without an additional open-source paragraph or editorial section.
- Cover the new public copy in every supported Site language.
- Correct Product Web's Documentation resource so it opens the Docs home page rather than a nested getting-started page.
- Add recognizable Shopify, Xentral, and Odoo marks to the Docs home-page ERP experience section.

### Non-Goals

- Replacing account creation as the primary commercial call to action.
- Adding a route, embedded repository browser, GitHub statistics, contributor profiles, or live repository data.
- Redesigning the footer or repeating the full section on every page.
- Making claims about maturity, adoption, community size, support, or production readiness.
- Changing Product Web, Docs content, domain behavior, persistence, or deployment boundaries.

### Existing Contracts

- [Public Site](../022-public-site/spec.md)
- [Public Site Localization](../034-public-site-localization/spec.md)
- [Site Appearance](../062-site-appearance/spec.md)
- [Shared Site Footer](../063-shared-site-footer/spec.md)
- [Single-Level Site Navigation](../064-single-level-site-navigation/spec.md)
- [Web UI Specification](../../docs/WEB_SPEC.md)

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Discover the source from any page (Priority: P1)

As a technically curious operator or builder, I can see from the main navigation that Reality is open source and open its repository without first reaching the footer.

**Why this priority**: Persistent discoverability directly fixes the current problem regardless of which public page a visitor enters.

**Independent Test**: Open each public page at desktop and mobile widths, locate the source-project entry, and follow it.

**Acceptance Scenarios**:

1. **Given** any public Site page, **When** a visitor reads the shared navigation, **Then** a clearly labelled source-project entry is visible alongside the existing page destinations.
2. **Given** the mobile navigation is closed, **When** a visitor opens it, **Then** the same entry is available without obscuring account or language actions.
3. **Given** the source-project entry, **When** it is followed, **Then** the canonical Reality repository opens.
4. **Given** any supported Site language, **When** the navigation renders, **Then** the entry is understandable in that language while the GitHub brand name remains unchanged.

### User Story 2 - Preserve a focused landing-page ending (Priority: P1)

As an evaluating visitor, I reach a clear final account action without a secondary open-source afterthought competing with the page's conclusion.

**Why this priority**: The shared documentation entry already provides a durable exploration path; repeating code and documentation links after the primary conclusion weakens its hierarchy.

**Independent Test**: Read the landing page through the final call to action and verify that no open-source paragraph or editorial section follows it.

**Acceptance Scenarios**:

1. **Given** a visitor reads the landing page, **When** they reach its final account action, **Then** no open-source paragraph, code link, or repeated documentation link follows it inside the main content.
2. **Given** a visitor wants deeper information, **When** they use the shared navigation, **Then** the prominent documentation entry remains available.

### Edge Cases

- A visitor enters on another public page; the shared navigation still exposes the repository.
- On mobile, the source-project entry remains readable without displacing language or account actions.
- External destinations remain clearly labelled and keyboard-accessible.
- If GitHub is unavailable, the Site remains fully readable because it uses no live repository data.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The shared public navigation MUST expose one clearly labelled link to the main Reality documentation page on every public Site page; GitHub MUST remain in the editorial open-source section rather than the header.
- **FR-002**: The link MUST be available in desktop and mobile navigation without removing an existing page, account, or language action.
- **FR-003**: The landing page MUST end its main content with the closing account action and MUST NOT append an open-source paragraph or editorial section.
- **FR-004**: The landing page MUST NOT repeat code and documentation links after its closing account action.
- **FR-005**: The shared documentation navigation entry MUST remain the public Site's persistent exploration path.
- **FR-006**: New interface copy MUST be complete in English, German, Dutch, and Spanish.
- **FR-007**: The new entry and section MUST remain keyboard-usable at desktop and mobile widths.
- **FR-008**: The Site MUST NOT depend on repository availability or live repository data to render.
- **FR-009**: Product Web's Documentation resource MUST open the configured Docs root.
- **FR-010**: The Docs home-page ERP experience section MUST show recognizable Shopify, Xentral, and Odoo marks next to its integration message.

### Domain and Traceability Requirements

- **DR-001**: This is a presentation change; Source → Evidence → Reality records are not involved and no business truth is created or interpreted.
- **DR-002**: The change MUST add no table, column, endpoint, domain mutation, authentication state, or alternative business rule.
- **DR-003**: Repository and documentation destinations MUST use their existing canonical public addresses rather than duplicate content in a new route.
- **DR-004**: The section MUST make no unsupported claim about adoption, maturity, community size, support, performance, or production readiness.

### Key Entities _(when data is involved)_

- **Open-source entry**: A persistent public navigation action leading to the canonical Reality repository.
- **Landing-page ending**: The closing account action without a secondary open-source paragraph.

## Success Criteria _(mandatory)_

- **SC-001**: On all three public pages, a visitor can identify and open the repository from the shared navigation without scrolling.
- **SC-002**: The landing page contains no open-source paragraph after its closing account action.
- **SC-003**: The shared navigation continues to provide one direct documentation action.
- **SC-004**: The remaining navigation entry remains readable and operable at representative desktop and mobile widths in both appearances.
- **SC-005**: All four supported languages pass the Site completeness check with no missing new copy.
- **SC-006**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The canonical repository is `https://github.com/Xentral-Labs/reality`.
- The configured public documentation origin is the correct secondary exploration path.
- GitHub is a persistent utility action rather than a fourth Site page, so the three page destinations keep their established meaning.
- The section belongs immediately before the account call to action: visitors first understand the product, then inspect it, then decide whether to start.
- The existing design language and automatic light/dark appearance remain authoritative.

## Open Questions

None.

The scope combines persistent discovery with one explanation. A navigation link alone remains easy to overlook; a large block on every page would compete with each page's purpose.

## Requirement Traceability

| Requirement   | Scenario(s)                    | Planned test/evidence                           |
| ------------- | ------------------------------ | ----------------------------------------------- |
| FR-001        | US1 scenarios 1, 3             | Shared-navigation contract on every public page |
| FR-002        | US1 scenario 2                 | Desktop/mobile structure and visual review      |
| FR-003        | US2 scenario 1                 | Landing-page order contract                     |
| FR-004        | US2 scenario 2                 | Copy contract and content review                |
| FR-005        | US2 scenario 3                 | Repository and Docs destination contract        |
| FR-006        | US1 scenario 4, US2 scenario 5 | Site interface-language audit                   |
| FR-007        | US1 scenario 2, US2 scenario 4 | Keyboard and representative-width review        |
| FR-008        | Edge case 4                    | Static rendering proof with no live request     |
| DR-001-DR-002 | US1-US2                        | Presentation-only diff review                   |
| DR-003        | US1 scenario 3, US2 scenario 3 | Canonical destination contract                  |
| DR-004        | US2 scenario 2                 | Product-claim review                            |
| SC-001-SC-006 | All scenarios                  | Full Site gates and visual review               |
