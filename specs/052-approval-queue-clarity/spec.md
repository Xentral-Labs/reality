# Feature Specification: Approval Queue Clarity

**Feature Branch**: `[052-approval-queue-clarity]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "Can Exceptions carry a dot badge in the sidebar when something is open, and Pending approvals a counter? And there is both 'pending approval' and 'proposal' — can the application use one word cleanly, or am I wrong?"

## Context and Intent

### Problem

Three separate readings of the same queue make waiting work hard to see and hard to name.

A pending change carries three different names in one product. It is a *proposal* in its buttons and empty states, an *approval* in its badge and tab, and a *decision* in its breadcrumb. The lifecycle **Proposal → Approval → Execution** is correct as a model, but a reader who meets two of those words on one card has to work out that they describe one thing.

The sidebar counts open Exceptions only. A company with zero exceptions and three approvals waiting shows an idle-looking entry, so the work is reachable only by opening the page and switching tabs. The Pending approvals tab itself carries no count, while the Exceptions tab beside it does.

A batch argument repeats one record shape, but every field of every record renders as its own labelled box. Six records of four fields produce twenty-two boxes repeating the same four labels, and the card grows without bound as the batch grows.

### Scope

- Name the object a person acts on once across the authenticated browser product.
- Record the naming rule in the Web specification so it cannot drift back.
- Signal open work on the Exceptions navigation entry for both queues behind it.
- Count pending approvals where the queue is opened, and keep the count true after a decision.
- Render uniform batch arguments as one table with a single header row and a bounded preview.

### Non-Goals

- Renaming `ChangeProposal` in the model, database, API routes, MCP, CLI, or concept documentation; the recorded lifecycle vocabulary is unchanged.
- Changing approval permissions, the execution boundary, or any audit record.
- Adding endpoints, tables, columns, filters, or sorting to the decision queue.
- Pushing live updates; the navigation signal follows navigation rather than a subscription.
- Restyling the Copilot conversation, where a proposal card keeps its narrow measure.

### Existing Contracts

- [Web UI Specification](../../docs/WEB_SPEC.md)
- [Agent Interaction](../014-agent-interaction/spec.md)
- [Web Product](../016-web-product/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read one word for one thing (Priority: P1)

As an operator, I meet a single name for the record I approve, so I never have to reconcile two words for one card.

**Why this priority**: Naming is the cheapest correctness the interface can offer, and every other change in this feature describes the same object.

**Independent Test**: Read every authenticated surface that presents a pending change — decision queue, decision history, Home panels, Copilot dialog, MCP token page — and confirm no user-facing text offers a second word for the card.

**Acceptance Scenarios**:

1. **Given** a card waits for a person, **When** its badge, buttons, and confirmation dialog are read, **Then** each names an approval or the action taken on it, and none says "proposal".
2. **Given** the decision history is open, **When** its empty state and cards are read, **Then** they describe decisions already taken rather than proposals.
3. **Given** the German, Dutch, or Spanish interface is selected, **When** the same surfaces are read, **Then** each translated term matches the single English term and no string falls back to English.

### User Story 2 - See that work is waiting (Priority: P1)

As an operator, I can tell from persistent navigation that something behind Exceptions needs me, whichever of its two queues holds it.

**Why this priority**: A signal that is blind to one of the two queues actively misleads, which is worse than no signal.

**Independent Test**: For companies with only exceptions, only pending approvals, both, and neither, read the sidebar entry and the tab counts without opening a card.

**Acceptance Scenarios**:

1. **Given** a company has zero open exceptions and at least one pending approval, **When** the sidebar renders, **Then** the Exceptions entry carries its open-work mark.
2. **Given** both queues are empty, **When** the sidebar renders, **Then** the entry carries no mark.
3. **Given** the decision queue is open, **When** the tabs render, **Then** the pending tab states its own count beside the count the exceptions tab already states.
4. **Given** the last pending approval is approved or rejected, **When** the queue reloads, **Then** the tab count reaches zero without a manual page reload.

### User Story 3 - Judge a batch without scrolling past it (Priority: P2)

As an approver, I can take in what a batch will create at a glance, and the card stays a comparable size however large the batch is.

**Why this priority**: An approval a person cannot see whole is an approval given blind.

**Independent Test**: Open pending approvals for batches of one, several, and many uniform records, and for an argument whose entries are not uniform.

**Acceptance Scenarios**:

1. **Given** an argument is a list of records sharing one shape, **When** the card renders, **Then** the field labels appear once as a header row and each record is one row.
2. **Given** a batch holds more records than the preview shows, **When** the card renders, **Then** a bounded preview is shown with a control that states the total and reveals the rest in place.
3. **Given** an argument's entries are not uniform records, **When** the card renders, **Then** the existing nested presentation is kept and every value is still rendered rather than stringified.
4. **Given** a record has more columns than the available width, **When** the card renders, **Then** the table scrolls within its own bounds and the page does not scroll sideways.

### Edge Cases

- A record in a batch omits a field that other records carry.
- A batch holds exactly one record.
- An argument is an empty list, a null, or a boolean.
- The pending read is refused for the signed-in member, so no count can be shown.
- Both queues are empty, or the dashboard read fails.
- A translated term is longer than its English source in persistent navigation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The authenticated browser product MUST name the record a person acts on an approval, and MUST NOT present "proposal" as user-facing copy for that record.
- **FR-002**: `ChangeProposal` MUST remain the model, API, and documentation term, and the Web specification MUST record the rule that separates the two so the interface cannot drift back.
- **FR-003**: The Exceptions navigation entry MUST carry a single open-work mark whenever open exceptions or pending approvals exist, and MUST carry none when both are empty.
- **FR-004**: The mark MUST NOT claim which of the two queues holds the work, and MUST carry an accessible label rather than relying on color alone.
- **FR-005**: The counts behind the mark MUST refresh as a person navigates, so a cleared queue clears the mark without a manual page reload.
- **FR-006**: The pending approvals tab MUST state its own count, and that count MUST be reported by the queue it labels so it stays true after an approval or rejection.
- **FR-007**: An argument that is a list of records sharing one shape MUST render as one table whose header states each field label once.
- **FR-008**: Table columns MUST be the union of the fields present across the records, in first-appearance order, so a record that omits a field stays readable in its row.
- **FR-009**: A batch MUST render a bounded preview of at most four records with a control that states the total record count and reveals the remainder in place.
- **FR-010**: Any argument that is not a uniform list of flat records MUST keep the existing nested presentation, and every value MUST continue to be rendered through the shared value renderer rather than stringified.
- **FR-011**: A card in the decision queue MUST use the panel width, a card in a Copilot conversation MUST keep its narrow measure, and a table too wide for either MUST scroll within its own bounds.
- **FR-012**: Every English string added or changed by this feature MUST carry a German, Dutch, and Spanish translation that preserves protected domain terms.

### Domain and Traceability Requirements

- **DR-001**: This feature is presentation only; it MUST NOT change the Proposal → Approval → Execution lifecycle, approval permissions, the execution boundary, or any audit record.
- **DR-002**: It MUST add no endpoint, table, column, or domain mutation, and MUST read only the existing tenant-scoped dashboard totals and change-proposal reads.
- **DR-003**: A refused or failed count read MUST degrade to no count rather than to an error state or a misleading zero.
- **DR-004**: The browser MUST NOT derive business meaning from an argument beyond its shape; column choice MUST follow the record keys as received.

### Key Entities *(when data is involved)*

- **Open-work signal**: A derived boolean over two existing tenant-scoped totals, carried by one navigation entry.
- **Batch argument**: An existing command argument that is a list of records of one shape, presented as rows rather than as labelled boxes.

## Success Criteria *(mandatory)*

- **SC-001**: No authenticated Web surface presents "proposal" as user-facing copy for a card a person acts on, in any of the four supported languages.
- **SC-002**: A company with zero open exceptions and at least one pending approval shows waiting work in persistent navigation without opening a page.
- **SC-003**: A card presenting a uniform batch stops growing beyond its preview, so a batch of twenty-four records occupies the height of a batch of four.
- **SC-004**: The localization audit reports zero missing and zero invalid entries across English, German, Dutch, and Spanish.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The dashboard read continues to expose open exception and pending decision totals for the active company.
- The pending change-proposal read continues to be available to a member who may open the decision queue.
- "Approval" is the term the product owner chose for the interface; the recorded lifecycle keeps "Proposal" for the model.
- Four preview records balance a readable card against a decision made with enough context; the remainder stays one interaction away.

## Open Questions

None. The interface term and the scope of the navigation signal were chosen explicitly by the product owner.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001-FR-002 | US1 scenarios 1-3 | Web specification rule and interface copy review across all surfaces |
| FR-003-FR-006 | US2 scenarios 1-4 | Navigation signal and queue-count behavior across empty, single-queue, and both-queue companies |
| FR-007-FR-011 | US3 scenarios 1-4 | Frontend batch-argument contracts, including the existing nested-value guarantee |
| FR-012 | US1 scenario 3 | Localization audit across English, German, Dutch, and Spanish |
| DR-001-DR-004 | US1-US3 | Diff review for absent schema, endpoint, and permission change; degraded-read behavior |
| SC-001-SC-005 | All scenarios | Full required quality gates |
