# Feature Specification: Human-readable decision review

**Feature Branch**: `276-human-readable-decision-review`  
**Created**: 2026-09-26  
**Status**: Approved  
**Language**: English  
**Input**: Make proposed changes unmistakable in Chat, replace the broken-looking review loading state, and make order decisions business-readable with an obvious action hierarchy.

All repository artifacts and recorded decisions for this feature are written in English.

## Context and Intent

### Problem

Chat currently renders most pending proposals as a plain button whose label exposes a
technical review name. It does not look like a decision or explain that no change has happened.
Opening a common proposal before its read completes produces a tiny, apparently empty modal.
The order review contains useful business data, but its title, status copy and equal-weight
left-aligned actions make the required decision difficult to scan.

### Scope

- Present every ordinary Chat proposal as a distinct pending-decision card.
- Keep pending-decision cards compact in both the main conversation and the narrower global
  Chat dock, with a bounded reading width and without a large, separate status banner.
- Give proposal review loading and failure states the same usable dialog frame as loaded content.
- Lead the order review with the decision, business effect and summary; keep trace data secondary.
- Preserve all proposal identities, review tokens, permissions, confirmation paths and receipts.
- Provide one reusable decision-review frame, structured value renderer and action bar for
  common and action-specific reviews; domain adapters supply content instead of rebuilding the
  interaction.

### Non-Goals

- Changing proposal creation, approval, rejection, execution or authorization semantics.
- Replacing the Decisions register or redesigning every action-specific review card.
- Adding inferred business summaries that are not present in the proposal response.
- Removing exact technical details required for traceability.

## User Scenarios & Testing

### User Story 1 - Recognize a decision in Chat (Priority: P1)

An operator sees a visually distinct card with a business action title, terse pending-state copy
and one clear review action. Repeated decision, origin and purpose copy does not compete with the
action.

**Independent Test**: Render a Chat response with a proposal and assert the localized business
action, terse pending-state copy and review action; assert repeated decision/origin/purpose copy
and the raw tool name are absent from the primary card.

**Acceptance Scenarios**:

1. **Given** a pending ordinary proposal, **When** Chat renders it, **Then** it is presented as
   a decision card rather than a generic button.
2. **Given** the proposal has a known action tool, **When** its card is rendered, **Then** the
   localized business action leads and the technical tool name remains hidden.
3. **Given** a user activates the review action, **When** routing occurs, **Then** the existing
   proposal identity opens the canonical review overlay without replacing the current Chat or
   underlying workspace route.
4. **Given** pending proposals appear in the main conversation or global Chat dock, **When** the
   cards render, **Then** they use a compact information hierarchy and remain visually
   subordinate to the conversation rather than filling the available width as large panels.
5. **Given** the surrounding Chat and review action already establish that a decision is pending,
   **When** the compact card renders, **Then** it does not repeat a decision label, proposal
   purpose or agent origin and states only that the action is not yet executed.
6. **Given** multiple ordinary proposals are pending in one conversation, **When** Chat renders
   them, **Then** one bounded list groups them as compact rows with a count, dividers and one
   independently routed review action per proposal; it does not imply batch approval.

### User Story 2 - Understand loading and read failures (Priority: P1)

An operator who opens a decision sees a correctly sized review dialog with a meaningful title
and answer-shaped placeholder. A failure explains that the decision could not be loaded and
offers retry without closing the dialog.

**Independent Test**: Render the common proposal dialog with pending and failed reads and
assert its labelled frame, loading skeleton, retry action and close control.

**Acceptance Scenarios**:

1. **Given** no proposal answer is held yet, **When** review opens, **Then** the full dialog
   frame is visible and carries an accessible busy state.
2. **Given** the read fails, **When** the dialog remains open, **Then** it shows an error card
   and a retry action in addition to close.

### User Story 3 - Decide on an order confidently (Priority: P1)

An operator sees a decision-specific title, the proposed order summary, what confirmation will
change and will not change, and a separated action footer with one primary confirmation action.

**Independent Test**: Render a proposed order review and assert the decision heading, effect
section, business summary, secondary trace disclosure and action ordering/hierarchy.

**Acceptance Scenarios**:

1. **Given** a pending customer order proposal, **When** review is displayed, **Then** the title
   asks the operator to confirm the customer order and the total is prominent.
2. **Given** the review is pending, **When** actions are displayed, **Then** close and rejection
   are secondary, editing is described as requesting a correction, and confirmation is the sole
   primary action at the end of the footer.
3. **Given** an operator needs implementation detail, **When** they expand System details,
   **Then** the proposal identity, exact review and receipt remain available.

### Edge Cases

- Unknown tools use the server-provided review label without exposing an internal tool key.
- Settled proposals retain their outcome controls and do not claim a decision is still required.
- Narrow viewports stack card content and actions without horizontal overflow.
- A review failure never appears as an empty modal and never causes an automatic mutation retry.

## Requirements

### Functional Requirements

- **FR-001**: Chat MUST render each non-report proposal in a distinct decision card with a
  localized business action title, a terse statement that the action is not yet executed, and a
  single localized review action. It MUST NOT repeat a decision-required label, proposal origin
  or proposal purpose in the compact card.
- **FR-002**: Chat MUST NOT expose the internal proposal tool name in the card's primary content.
- **FR-003**: The card's single primary action MUST route to the existing canonical review
  overlay with the exact proposal ID while preserving the current route. Chat MUST NOT use the
  workspace-destination mapper for this action; the global review host MAY delegate to the
  existing specialized review component inside the overlay.
- **FR-004**: Common proposal review MUST use a stable, labelled dialog frame while loading,
  loaded or failed.
- **FR-005**: A failed common review read MUST retain the error, offer explicit retry and close,
  and MUST NOT approve, reject or otherwise mutate the proposal.
- **FR-006**: A pending order review MUST lead with a decision-specific title, concise business
  summary and explicit effect statement before status, controls or technical detail.
- **FR-007**: A pending order review MUST expose exactly one visually primary action; secondary
  close, rejection and correction actions MUST remain distinct and accurately named.
- **FR-008**: Proposal identity, exact review, receipt, verification and links MUST remain
  available in a collapsed System details disclosure.
- **FR-009**: All new user-facing text MUST be complete in English, German, Dutch and Spanish.
- **FR-010**: Keyboard cancellation, focus restoration, permission checks, proposal review
  tokens, canonical execution and uncertain-outcome recovery MUST retain existing behavior.
- **FR-011**: A shared decision-review kit MUST own the category/title header, close control,
  decision status/effect hierarchy and action footer used by common, order and master-data
  reviews.
- **FR-012**: A shared business-value renderer MUST display scalar values, flags, arrays and
  nested objects as readable labelled content; primary review content MUST NOT serialize an
  object or array as JSON text.
- **FR-013**: All pending reviews using the shared kit MUST use one action hierarchy and wording:
  secondary non-approval, optional correction, and a single business-specific primary confirm
  action at the end of the footer.
- **FR-014**: Domain-specific reviews MAY provide purpose-built summaries and sections, but MUST
  NOT independently implement dialog chrome or pending-decision action styling.
- **FR-015**: Chat pending-decision cards MUST use one compact surface with a bounded 680 px
  reading width in the main conversation and tighter spacing in compact or dock presentation;
  status MUST remain visible without a separate full-width header band.
- **FR-016**: Known Item, Location and Payment Term creation proposals MUST use localized
  business action titles instead of server review labels such as `Item create` or
  `Payment term create` in both Chat and the review dialog; unknown proposal types MAY fall back
  to the server review label.
- **FR-017**: Chat MUST group ordinary pending proposals into one labelled, counted list surface.
  Each proposal MUST remain a separate row with its own proposal ID, review destination and
  action. Rows MUST keep title and status together on the left, align the review action at the
  right on supported desktop and dock widths, and use dividers instead of separate card margins.
- **FR-018**: Closing a review opened from Chat MUST reveal the same Chat and underlying workspace
  context. Confirmation, rejection, permissions, review tokens and uncertain-outcome recovery
  MUST continue through the existing canonical review services and components.
- **FR-019**: Chat, Decisions and the common review dialog MUST use one proposal business-label
  mapping. Known master-data creation purposes and structured Payment Term field labels MUST be
  translated in English, German, Dutch and Spanish; received business values remain unchanged.
- **FR-020**: Concurrent identical Proposal Review reads for the same tenant and proposal MUST
  share one in-flight request. The entry MUST be discarded after either success or failure so a
  later open performs a fresh authoritative read. Mutation requests MUST NOT be cached or
  deduplicated by this mechanism.

## Requirement Traceability

| Requirements                 | Stories | Acceptance and test evidence                                                                                 |
| ---------------------------- | ------- | ------------------------------------------------------------------------------------------------------------ |
| FR-001–FR-003, FR-015–FR-020 | US1     | Chat decision-list semantics, overlay routing, localization, read deduplication and compact layout assertion |
| FR-004–FR-005                | US2     | Common review loading, failure, retry and no-mutation contract                                               |
| FR-006–FR-008                | US3     | Order review hierarchy, action and System details contract                                                   |
| FR-009                       | US1–US3 | Four-language localization audit                                                                             |
| FR-010                       | US1–US3 | TypeScript build and existing proposal review contracts                                                      |
| FR-011–FR-014                | US2–US3 | Shared-kit ownership, structured-value and action-parity contracts                                           |

## Success Criteria

- **SC-001**: Contract tests identify the Chat proposal as a decision card and find no raw tool
  key in its primary label.
- **SC-002**: Loading and failed common reviews always retain a dialog at least as wide as the
  loaded review on supported desktop and mobile viewports.
- **SC-003**: The pending order review has one and only one primary action and its accessible
  name describes the business change being confirmed.
- **SC-004**: Web build, localization audit and focused decision UX tests pass.
- **SC-005**: The focused Chat contract proves the shared 680 px maximum card width and the
  compact/dock spacing variant without weakening decision semantics.
- **SC-006**: The focused Chat contract proves one list surface for ordinary proposals, separate
  row actions and no per-proposal card wrapper.
- **SC-007**: A focused async test proves that two simultaneous reads make one load call and that
  success and failure both allow a later fresh load.

## Assumptions and Dependencies

- Existing `review_label`, `review_purpose`, actor type and action-specific review payloads are
  the authoritative inputs; the browser does not invent business effects.
- The current proposal routing and action-specific review components remain authoritative.
- The owner approved the product scope in the 2026-09-26 conversation before planning.
