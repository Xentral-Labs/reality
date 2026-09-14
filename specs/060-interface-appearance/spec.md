# Feature Specification: Interface Appearance

**Feature Branch**: `[060-interface-appearance]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "kann man die app einfach in darkmode auch anbieten?"

## Context and Intent

### Problem

The Product Web can only be read on a light ground. Someone working in a dark room, on a dark-configured operating system, or across a long shift has no way to ask for anything else, and every other application they keep open already offers the choice.

The reason it was never offered is that the palette was never in one place. Colour was fixed in two independent layers at once: colour literals spread through the hand-written stylesheets, and Tailwind utilities naming a single-theme scale inside the `@apply` rules that compose the shared primitives. A third layer re-declared five shared variables against light-only scales, silently overriding the first. Nothing in the product could change ground without every one of those layers being edited, so the question was not a preference the product could answer.

This is a readability and comfort concern, not a decorative one. The same work that makes the ground switchable also makes contrast measurable, because a named token can be checked where a literal repeated hundreds of times cannot.

### Scope

- Give the interface a single semantic colour vocabulary that both stylesheets and Tailwind utilities read.
- Offer light, dark and follow-the-system as a personal preference.
- Resolve the preference before the first paint so no wrong-theme flash occurs.
- Hold dark to the contrast standard the product should meet.

### Non-Goals

- Redesigning the light appearance. Its existing contrast shortfalls are recorded here, not corrected, because fixing them changes the established look rather than adding a theme.
- Moving feature markup from its hand-written class names to Tailwind utilities. The token vocabulary is the groundwork for that; it is not that migration.
- Storing the preference on the account or synchronising it across devices.
- A per-company or per-workspace appearance; this is personal to the reader.
- Theming anything outside the Product Web.

### Existing Contracts

- [Web Product](../016-web-product/spec.md)
- [Complete Workspace Navigation](../056-complete-workspace-navigation/spec.md)
- [Web UI Specification](../../docs/WEB_SPEC.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the interface on a dark ground (Priority: P1)

As someone who works in a dark environment, I set the interface to dark and every surface follows.

**Why this priority**: This is the request. A theme that reaches some surfaces and not others is worse than none, because the reader cannot trust what they see.

**Independent Test**: Set the preference to dark and walk the authenticated surfaces, including menus, dialogs, tables, forms, charts and the sign-in screen.

**Acceptance Scenarios**:

1. **Given** the dark preference, **When** any authenticated surface renders, **Then** its grounds, text, borders, shadows and status colours are the dark palette.
2. **Given** the dark preference, **When** a surface composed from shared primitives renders, **Then** it follows the same palette as surfaces composed from hand-written rules.
3. **Given** the dark preference, **When** a native scrollbar, select popup or focus ring is drawn, **Then** the browser paints it to match rather than leaving light furniture on a dark page.
4. **Given** the dark preference, **When** text sits on a saturated fill such as a danger control, **Then** it stays light and legible rather than inverting into the fill.

### User Story 2 - Choose, and be remembered (Priority: P1)

As any user, I choose light, dark or follow-the-system among my other personal preferences, and the choice holds.

**Why this priority**: A theme that is not remembered is a demonstration, not a preference.

**Independent Test**: Set each of the three choices in Profile, reload, and change the operating system setting while the tab is open.

**Acceptance Scenarios**:

1. **Given** Profile, **When** the personal preferences are read, **Then** appearance sits with language, format and timezone and states that it applies immediately to this device.
2. **Given** a chosen preference, **When** the application is reloaded, **Then** the same appearance is applied.
3. **Given** the follow-the-system choice, **When** the operating system changes between light and dark, **Then** the interface follows without a reload.
4. **Given** any preference, **When** the application first paints, **Then** it paints in the resolved appearance with no flash of the other one.
5. **Given** an explicit light or dark choice, **When** the operating system changes, **Then** the explicit choice is kept.

### User Story 3 - Trust the text to be readable (Priority: P2)

As anyone reading on the dark ground, secondary and quiet text is legible rather than merely present.

**Why this priority**: A dark theme is easy to make look right in a screenshot and hard to make readable; the standard is the point.

**Independent Test**: Measure contrast for every foreground and ground pairing the stylesheets actually put together.

**Acceptance Scenarios**:

1. **Given** the dark palette, **When** every such pairing is measured, **Then** each meets at least 4.5:1.
2. **Given** the quiet text level, **When** it is measured on the dark ground, **Then** it meets the standard while staying visibly lighter than the muted level above it.
3. **Given** the light palette, **When** it is measured, **Then** it is unchanged from before this feature.

### Edge Cases

- Storage that is unavailable or holds an unrecognised value, which falls back to following the system.
- A surface deliberately dark in both appearances, such as a code block, whose light text must not be inverted.
- Elements whose colour must not follow the ground: brand fills, saturated status fills, focus rings and modal scrims.
- The unauthenticated sign-in screen, which renders before any account preference is known.
- Charts, whose gridlines and bands are drawn as strokes and fills rather than as text and grounds.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The interface MUST offer light, dark and follow-the-system as a personal appearance preference.
- **FR-002**: The preference MUST be presented in Profile alongside the other personal preferences, and MUST state that it applies immediately and is held on the device.
- **FR-003**: The preference MUST persist across reloads on the same device.
- **FR-004**: The follow-the-system choice MUST track operating-system changes while the application is open; an explicit choice MUST NOT be overridden by them.
- **FR-005**: The resolved appearance MUST be applied before the first paint, with no flash of the other appearance.
- **FR-006**: Every colour that distinguishes the two appearances MUST be expressed as a semantic token, so that one definition serves both hand-written rules and Tailwind utilities.
- **FR-007**: A colour that must not follow the ground — brand fill, saturated status fill, focus ring, scrim, or text on a saturated fill — MUST be held outside the switching vocabulary.
- **FR-008**: The browser MUST be told which appearance is active, so that native scrollbars, select popups and focus rings are painted to match.
- **FR-009**: Every string the preference control introduces MUST be covered in all supported interface languages.

### Domain and Traceability Requirements

- **DR-001**: The change is presentation only; it MUST NOT add or alter a route, command, projection, permission or Reality state.
- **DR-002**: It MUST add no table, column, endpoint or domain mutation.
- **DR-003**: The appearance preference MUST remain on the device and MUST NOT enter tenant-scoped or account-scoped storage.
- **DR-004**: A semantic token MUST have exactly one definition per appearance; a second declaration that shadows it MUST NOT exist.
- **DR-005**: Every foreground and ground pairing the stylesheets compose MUST meet 4.5:1 in the dark appearance.
- **DR-006**: The light appearance MUST be unchanged by this feature.

### Key Entities *(when data is involved)*

- **Appearance preference**: One of light, dark or follow-the-system, held per device for the reader.
- **Semantic token**: A named role — ground, surface, border, text level, status pair — whose value is defined once per appearance and read everywhere.

## Success Criteria *(mandatory)*

- **SC-001**: A reader sets dark in Profile and every authenticated surface, plus the sign-in screen, renders dark.
- **SC-002**: The choice survives a reload, and follow-the-system tracks the operating system without one.
- **SC-003**: No wrong-appearance flash is observable on first paint.
- **SC-004**: Every foreground and ground pairing composed by the stylesheets meets 4.5:1 in dark.
- **SC-005**: The light appearance renders as it did before this feature.
- **SC-006**: Interface-language coverage passes for every supported language with no missing string.
- **SC-007**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The device is the right scope for this preference: it describes the screen being read, not the person, and a reader on two machines may reasonably want two answers.
- The existing light palette is the intended appearance and stays the reference; the dark palette is derived to match its structure rather than to restate it.
- The reader's operating system exposes a colour-scheme preference; where it does not, follow-the-system resolves to light.
- Tailwind's theme layer can hold a token whose value is a reference resolved at the point of use, which is what lets one definition serve utilities and stylesheets alike.
- The hand-written class names stay as they are; the tokens sit underneath them and do not require markup to change.

## Open Questions

None.

The light appearance carries three foreground and ground pairings below 4.5:1 that predate this feature, the widest being quiet text on white at 2.58:1. They are recorded rather than corrected: the quiet level cannot be lifted on its own, because the muted level above it already sits near the threshold and the two would become indistinguishable. Correcting them means darkening the muted level across the interface, which changes the established light appearance and is a design decision rather than part of offering a second one.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001-FR-002 | US2 scenario 1 | Profile preference control rendered with the personal preferences |
| FR-003 | US2 scenario 2 | Reload retains the stored choice |
| FR-004 | US2 scenarios 3, 5 | Operating-system change tracked when following, ignored when explicit |
| FR-005 | US2 scenario 4 | Appearance resolved before first paint |
| FR-006 | US1 scenarios 1-2 | Single token vocabulary read by both stylesheets and utilities |
| FR-007 | US1 scenario 4, Edge cases | Fills, rings, scrims and text on fills held outside the switch |
| FR-008 | US1 scenario 3 | Colour scheme declared per appearance |
| FR-009 | US2 scenario 1 | Interface-language audit across all supported languages |
| DR-001-DR-003 | US1-US2 | Diff review for presentation-only, device-scoped change |
| DR-004 | US1 scenario 2 | No shadowing declaration of any token |
| DR-005 | US3 scenarios 1-2 | Contrast measured over every pairing the stylesheets compose |
| DR-006 | US3 scenario 3 | Light palette unchanged |
| SC-001-SC-007 | All scenarios | Full required quality gates |
