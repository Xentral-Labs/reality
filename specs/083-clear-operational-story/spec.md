# Feature Specification: Clear Operational Story

**Created**: 2026-09-05
**Status**: Approved scope
**Language**: English for repository artifacts; localized public presentation follows existing language contracts.
**Input**: Implement the reviewed landing-page and documentation clarity improvements.

## Context and Intent

### Problem

The original technology-led positioning is valuable, but examples and readiness claims need
precision. The first rewrite oversimplified the product into an operations dashboard; the owner
explicitly requests restoration with selective improvements.

### Scope

Public landing, explanatory and package pages; documentation entry, first journey,
operational guidance, Facts and customization. Preserve routes and advertised languages.

### Non-Goals

No connectors, business operations, database changes, pricing changes, deployment or new
automation. No claim that a static example is an executable, preloaded demo.

## User Scenarios & Testing

### User Story 1 - Understand the business outcome (Priority: P1)

A prospective customer understands the operational core for agents through the original
technology-led narrative, supported by a concrete delivery example.

**Independent Test**: Read the technology-led hero and core diagram, then follow the refined order example.

**Acceptance Scenarios**:
1. Given a first visit, the original hero, core diagram, brands, context graphics and capability
   progression remain, with refined explanations rather than a dashboard-first redesign.
2. Given the illustrative lamp order, ten promised and four shipped leave six open; two active
   reservations cover two of those six. Four unreserved units do not prove a stock shortage.

### User Story 2 - Choose an honest starting point (Priority: P1)

A prospective user distinguishes sample learning, a bounded own-data pilot and live integration.

**Independent Test**: Follow landing links to the documentation journey and readiness table.

**Acceptance Scenarios**:
1. Given vendor logos, adjacent copy says they are not ready-to-connect integrations.
2. Given missing stock or due-date data, guidance states what cannot be concluded.
3. Given a proposed action, guidance distinguishes changes in Reality from external execution.

### User Story 3 - Learn and extend the model (Priority: P2)

An operator learns the model through the same case and can find the bounded Fact-rule path.

**Independent Test**: Follow the first trace, then the missing-information guidance.

**Acceptance Scenarios**:
1. Given a pending pick, it is not presented as an actual Movement.
2. Given a Shopify update, guidance explains review rather than automatic replacement.
3. Given a missing observation, owners can learn simulation, activation and separate replay;
   a Fact rule is not a custom Exception or permission to act.

### Edge Cases

No exceptions does not prove completeness. Payment authorization is not settled payment.
Historical source retention does not imply all rows are immutable or arbitrary as-of reconstruction.
Existing translated routes and section anchors remain usable.

## Requirements

### Functional Requirements

- **FR-001**: Preserve the original technology-led hero, core diagram, system brands, agent-context
  graphics and capability progression. Refine copy without redesigning the public pages.
- **FR-002**: Use the illustrative ten-lamp case once in the landing page's agent-context timeline
  rather than repeating it in a separate walkthrough card. Preserve the deeper fulfillment and
  finance graphs on the explanation page, label conceptual behavior and correct misleading typed
  labels without flattening the visuals.
- **FR-003**: Distinguish demo, own-data pilot and live integration in documentation. Owner refinement on 2026-09-12 removes the Connections readiness paragraph and its link from the landing page (spec022 FR-028); do not imply new live integration availability.
- **FR-004**: Explain known, open and unknown; distinguish missing evidence from missing execution.
- **FR-005**: Preserve Source → Evidence → Reality, typed financial authority and qualified history claims.
- **FR-006**: Explain read, propose, approve and verify without implying automatic autonomy or external writes.
- **FR-007**: Give business users, operators and integrators distinct documentation entry paths.
- **FR-008**: Explain owner-controlled Fact rules, simulation, activation, replay and fixed Exception classes.
- **FR-009**: Preserve published routes, configured origins, language selection, keyboard and narrow-screen usability.
- **FR-010**: Keep the autonomy progression visually focused. Do not append a separate autonomy disclaimer box or repeated walkthrough card, and end the landing page's main content with the final signup call to action without an open-source paragraph.

## Success Criteria

- **SC-001**: All three entry paths are reachable from public guidance.
- **SC-002**: Every presentation of the shared case uses consistent quantities and an explicit evidence boundary.
- **SC-003**: No changed entry page promises turnkey vendor connections or autonomous external execution.
- **SC-004**: Content contracts, localization completeness, documentation links and both builds pass.

## Assumptions and Dependencies

The owner's subsequent review supersedes the dashboard-first interpretation: restore the original
public pages with targeted improvements. Preserve the useful documentation changes. Existing
English source content remains canonical; localized public copy is maintained through the existing
language catalogs and translated editions required by the public-surface contract. Technical
artifacts remain English. The current Shopify guard and Fact-rule services are authoritative.
Automated content regression tests are required before implementation, with visual checks where available.

## Requirement Traceability

| Requirements | Stories | Planned evidence |
|---|---|---|
| FR-001, FR-002, FR-004 | US1 | Original hero/visual preservation and refined example tests; docs journey tests |
| FR-003, FR-006 | US2 | Readiness and governed action content tests |
| FR-005 | US1, US3 | Domain vocabulary, history and financial authority tests |
| FR-007, FR-008 | US3 | Docs entry, Fact rules and navigation tests |
| FR-009 | US2, US3 | Routing, localization, appearance, links and build gates |
| FR-010 | US1 | End-of-page placement, inline links and localization contract |
