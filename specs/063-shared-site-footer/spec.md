# Feature Specification: Shared Site Footer

**Feature Branch**: `[063-shared-site-footer]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "warum ist der footer bei so funktioniert es und pakete anders? kann man das nicht einheitlich machen?"

## Context and Intent

### Problem

The public Site has three pages. The landing page ends with a footer carrying the product line, the Source → Evidence → Reality principle, and the three ways out: documentation, sign in, create account. The other two pages — the one explaining how Reality works, and the one listing packages — end with their last section and nothing else.

So a reader who follows the navigation into either of those pages reaches the bottom and finds no way onward. The two pages a prospect is most likely to finish reading are exactly the two that drop them. The pricing page in particular ends on the compatibility note, with no account link anywhere below the fold.

The header was extracted into a shared component and stays identical across the three pages. The footer never was: it is markup inside the landing page, holding a link built from a page-local constant. Nothing was decided about the other two pages — they simply never got one.

### Scope

- One footer component, used by every public page.
- The landing page's existing footer becomes that component, unchanged in content.
- The footer's border stops depending on a page-scoped variable so it renders away from the landing page.

### Non-Goals

- Redesigning the footer, or adding links, columns, legal pages or social icons to it. This makes the existing footer consistent; deciding what a fuller footer should contain is a separate question.
- Changing the header.
- Changing any page's own content or sections.
- A footer on the signed-in product, which is a different application with its own shell.

### Existing Contracts

- [Public Site](../022-public-site/spec.md)
- [Site Appearance](../062-site-appearance/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reach the way out from any page (Priority: P1)

As someone who has finished reading any public page, I find the same footer with the same ways onward.

**Why this priority**: This is the request, and the packages page ending without an account link is the sharpest form of it.

**Independent Test**: Scroll to the bottom of each of the three public pages.

**Acceptance Scenarios**:

1. **Given** any public page, **When** it is scrolled to the bottom, **Then** the same footer appears with the product line, the principle, and links to documentation, sign in and create account.
2. **Given** the packages page, **When** it is scrolled to the bottom, **Then** an account link is reachable there.
3. **Given** any page, **When** the footer renders, **Then** it is separated from the content by the same border, in either appearance.
4. **Given** a language other than English, **When** any page's footer renders, **Then** its text is in that language.

### User Story 2 - Keep the two ends of a page a pair (Priority: P2)

As anyone changing the Site later, the footer is one component beside the header, not markup repeated per page.

**Why this priority**: The drift being fixed happened because one end of the page was shared and the other was not; copying the markup three times would set up the same drift again.

**Independent Test**: Read the three page components.

**Acceptance Scenarios**:

1. **Given** the three page components, **When** they are read, **Then** each renders the shared footer and none declares a footer of its own.
2. **Given** the footer, **When** its documentation link is read, **Then** the URL comes from the configured documentation origin, as it did on the landing page.

### Edge Cases

- A page that later wants an extra section below the footer, which must not become a second footer.
- The documentation origin differing per deployment, which the footer must keep reading from configuration.
- The product line, which was previously held in a page-local constant and so escaped the interface-language audit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every public page MUST end with the same footer component.
- **FR-002**: A public page MUST NOT declare a footer of its own beside the shared one.
- **FR-003**: The footer MUST carry the product line, the Source → Evidence → Reality principle, and links to documentation, sign in and create account.
- **FR-004**: The footer's documentation link MUST be built from the configured documentation origin, and that origin MUST NOT appear in the header.
- **FR-005**: The footer MUST render identically away from the landing page, which means it MUST NOT depend on a page-scoped variable.
- **FR-006**: Every string the footer renders MUST be covered in all supported interface languages.

### Domain and Traceability Requirements

- **DR-001**: The change is presentation only; it MUST NOT alter a route, a page's content, or any product claim the Site makes.
- **DR-002**: It MUST add no table, column, endpoint, domain mutation or client-side state.
- **DR-003**: The footer's rendered content MUST be unchanged from the landing page's existing footer.

### Key Entities *(when data is involved)*

- **Public footer**: The single end-of-page component for the Site, beside the public header.

## Success Criteria *(mandatory)*

- **SC-001**: All three public pages end with the same footer, and the packages page offers an account link at its bottom.
- **SC-002**: No page component declares a footer of its own.
- **SC-003**: The footer's border renders on every page in both appearances.
- **SC-004**: Interface-language coverage passes for every supported language with no missing string.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The landing page's footer is the right one to standardise on: it is the only one that exists, and its three links are the ways out a reader needs.
- The header's shared-component shape is the right precedent, so the footer takes the same props and lives beside it.
- The product line is translatable copy rather than a fixed brand string. It was never translated only because holding it in a page-local constant kept it out of the audit's reach.

## Open Questions

None.

Whether the Site eventually wants a fuller footer — legal pages, status, contact — is a separate product question. This specification makes the existing footer consistent and does not decide that.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1-2, US2 scenario 1 | Contract asserting every page renders the shared footer |
| FR-002 | US2 scenario 1 | Contract forbidding a page-local footer |
| FR-003 | US1 scenario 1 | Footer content contract, unchanged from the landing page |
| FR-004 | US2 scenario 2 | Documentation-origin contract, moved to the footer |
| FR-005 | US1 scenario 3 | Border uses a shared token, not the page-scoped alias |
| FR-006 | US1 scenario 4 | Interface-language audit across all supported languages |
| DR-001-DR-003 | US1-US2 | Diff review for presentation-only change with identical content |
| SC-001-SC-005 | All scenarios | Full required quality gates |
