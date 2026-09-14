# Feature Specification: Site Appearance

**Feature Branch**: `[062-site-appearance]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "kannst du die webseite auch noch dark mode ready machen" / "mit auto umschaltung"

## Context and Intent

### Problem

The Product Web now follows a light or dark preference. The public Site does not, so a reader whose system is set to dark meets a bright page on the way in and a dark one once signed in. The product contradicts itself at its own front door.

The Site could not follow anything, for the same reason the Product Web could not: colour was written where it was used. 890 colour literals sat across three page stylesheets, 390 of them distinct — the same border grey written eleven ways, the same brand tint written five. Nothing named a role, so nothing could be given a second value.

Unlike the Product Web, the Site has no account. There is nobody to hold a preference for, and asking a first-time reader to choose an appearance before they have read anything is a question about the wrong thing. The operating system already carries the answer.

### Scope

- Give the Site one semantic colour vocabulary, stated in a single file.
- Follow the operating system's colour-scheme preference, with no control and no stored state.
- Keep the light appearance as it is.
- Hold dark to the contrast standard.

### Non-Goals

- A manual override on the Site. There is no account to hold one, and the system preference is the reader's own standing answer.
- Redesigning the light appearance. Its existing contrast shortfalls are recorded here, not corrected.
- Changing copy, layout, imagery or routing.
- Sharing a stylesheet or token file with the Product Web. The two are separate deployables and keep separate vocabularies, even where the role names match.

### Existing Contracts

- [Public Site](../022-public-site/spec.md)
- [Interface Appearance](../060-interface-appearance/spec.md)
- [Web UI Specification](../../docs/WEB_SPEC.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Arrive in the appearance already chosen (Priority: P1)

As someone whose system is set to dark, the Site is dark when I open it, without my asking.

**Why this priority**: This is the request, and the inconsistency with the signed-in product is what makes it visible.

**Independent Test**: Set the operating system to dark and open each Site page.

**Acceptance Scenarios**:

1. **Given** a system set to dark, **When** any Site page is opened, **Then** its grounds, text, borders, shadows and accents are the dark palette.
2. **Given** a system set to light, **When** any Site page is opened, **Then** it renders as it did before this feature.
3. **Given** the Site is open, **When** the system preference changes, **Then** the page follows without a reload.
4. **Given** either appearance, **When** the page first paints, **Then** it paints in that appearance with no flash of the other.

### User Story 2 - Read the dark bands as bands (Priority: P2)

As any reader, the sections that are deliberately dark still read as deliberate rather than merging into the page.

**Why this priority**: A dark feature band on a light page carries emphasis; on a dark page it disappears unless it is given its own ground.

**Independent Test**: Open the pages carrying dark bands in both appearances.

**Acceptance Scenarios**:

1. **Given** the dark appearance, **When** a dark band renders, **Then** it remains distinguishable from the page ground around it.
2. **Given** either appearance, **When** text sits on a dark band, **Then** it stays light rather than inverting into the band.
3. **Given** either appearance, **When** the banded section carrying a gradient renders, **Then** the gradient keeps its depth rather than flattening to one tone.

### User Story 3 - Trust the text to be readable (Priority: P2)

As anyone reading on the dark ground, every foreground the Site composes is legible.

**Why this priority**: A palette derived by hand is easy to get subtly wrong, and nobody reports low contrast — they just leave.

**Independent Test**: Measure contrast for every foreground and ground pairing the Site composes.

**Acceptance Scenarios**:

1. **Given** the dark palette, **When** every such pairing is measured, **Then** each meets at least 4.5:1.
2. **Given** the light palette, **When** it is measured, **Then** it is no worse than before this feature.

### Edge Cases

- A browser or system that expresses no colour-scheme preference, which resolves to light.
- A page stylesheet gaining a new colour later, which would silently not follow the reader.
- Colour that must not follow the ground: brand fills, the dark bands, and text on either.
- Gradients, whose stops must stay distinct after being named.
- Shadows, whose base colour changes while each rule keeps its own alpha.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Site MUST render in the appearance the operating system reports, and MUST follow a change to it without a reload.
- **FR-002**: The Site MUST NOT present an appearance control and MUST NOT store an appearance preference.
- **FR-003**: Every colour that distinguishes the two appearances MUST be a semantic token, stated once for each appearance in a single file.
- **FR-004**: A page stylesheet MUST NOT contain a colour of its own.
- **FR-005**: A colour that must not follow the ground — brand fill, dark band, or text on either — MUST be held in its own token rather than the switching one.
- **FR-006**: A dark band MUST remain distinguishable from the page ground in both appearances, and a banded gradient MUST keep distinct stops.
- **FR-007**: The browser MUST be told which appearance is active, so native scrollbars, form controls and focus rings are painted to match.
- **FR-008**: The light appearance MUST be no worse than before this feature at any pairing.

### Domain and Traceability Requirements

- **DR-001**: The change is presentation only; it MUST NOT alter copy, layout, routing or any product claim the Site makes.
- **DR-002**: It MUST add no table, column, endpoint, domain mutation or client-side state.
- **DR-003**: A token MUST have exactly one definition per appearance; a second declaration that shadows it MUST NOT exist.
- **DR-004**: Every foreground and ground pairing the Site composes MUST meet 4.5:1 in the dark appearance.
- **DR-005**: The Site MUST keep its own vocabulary; it MUST NOT import the Product Web's stylesheets or tokens.

### Key Entities *(when data is involved)*

- **Semantic token**: A named role — ground, surface, border, text level, accent, status pair, dark band — defined once per appearance and read everywhere.
- **Dark band**: A section deliberately dark in both appearances, with its own ground, border and text roles.

## Success Criteria *(mandatory)*

- **SC-001**: A reader whose system is dark sees every Site page dark, with no control and nothing stored.
- **SC-002**: Changing the system preference switches the open page without a reload.
- **SC-003**: No page stylesheet holds a colour literal.
- **SC-004**: Every foreground and ground pairing the Site composes meets 4.5:1 in dark.
- **SC-005**: The light appearance renders as it did, at no worse contrast than before.
- **SC-006**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The operating system preference is the right and only answer for a public page: the reader has already given it once, and the Site has nowhere to keep a second one.
- The existing light appearance is the intended design and stays the reference; dark is derived to match its structure.
- Values that differed imperceptibly in the original — the same border grey written eleven ways — represent one intent and may be named once. The palette is consolidated, not redesigned.
- The Site and the Product Web stay separate deployables with separate vocabularies, even where role names coincide.

## Open Questions

None.

Five foreground and ground pairings in the light appearance sit below 4.5:1, and are recorded rather than corrected: quiet text on white, brand on brand tint, positive and caution on white and on their own tints. Each is the Site's existing colour, measured unchanged — brand on brand tint at 4.36:1 and caution on white at 4.26:1 are the values the Site already shipped. The consolidated quiet-text token is better than every value it replaces, which ranged from 2.86:1 to 3.47:1, and still does not reach the standard. Lifting it means darkening the muted level above it, which changes the established light appearance and is a design decision rather than part of following the reader's system.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1-3 | Colour-scheme media query drives the palette |
| FR-002 | US1 scenario 1 | No control and no stored state in the Site |
| FR-003 | US1 scenarios 1-2 | Token vocabulary stated once per appearance |
| FR-004 | US1 scenario 1 | Contract asserting no colour literal in a page stylesheet |
| FR-005 | US2 scenario 2 | Contract asserting band text does not invert |
| FR-006 | US2 scenarios 1, 3 | Band ground distinct per appearance; gradient stops distinct |
| FR-007 | US1 scenario 4 | Colour scheme declared for both appearances |
| FR-008 | US3 scenario 2 | Light pairings measured against the previous values |
| DR-001-DR-002 | US1-US3 | Diff review for presentation-only change |
| DR-003 | US1 scenario 1 | Contract asserting no shadowing declaration |
| DR-004 | US3 scenario 1 | Contrast measured over every pairing the Site composes |
| DR-005 | US1 scenario 1 | No cross-application stylesheet import |
| SC-001-SC-006 | All scenarios | Full required quality gates |
