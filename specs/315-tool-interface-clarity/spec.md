# Feature Specification: Tool interface clarity

**Created**: 2026-10-02
**Status**: Approved scope
**Language**: English
**Input**: Implement the session's accepted plan to distinguish commands, agent tools and Web actions, show their relationships, and reduce demonstrated duplicate definitions.

## Context and Intent

### Problem

Readers mistake three access layers for independent features. The technical label Actions does not explain its Web workspace scope. Independently maintained terminology can drift between the interactive reference and generated manual pages.

### Scope

Explain the three categories in both documentation languages, show a real reservation example and command relationships, audit reservation/order/payment definitions, and consolidate proven presentation duplication.

### Non-Goals

No new business operations, database fields, MCP contract changes, automatic command execution, universal form generator, or speculative input-validation refactor.

### Existing Contracts

- `AGENTS.md`, `.specify/memory/constitution.md`, `docs/SPEC_DRIVEN_WORKFLOW.md`
- `docs/WEB_SPEC.md`; `specs/226-unified-tool-catalog/spec.md`

## User Scenarios & Testing

### User Story 1 - Understand the categories (Priority: P1)

A reader opens the technical Tool Usage overview and understands the shared operation and its agent and Web entrypoints.

**Independent Test**: Both languages explain all three categories, overlapping counts and registered Web action scope.

**Acceptance Scenarios**:

1. **Given** the technical overview, **When** a reader views its category guide, **Then** commands include reads, agent tools describe callable interfaces, and Web actions describe registered workspace interactions.
2. **Given** the category counts, **When** reading their explanation, **Then** the reader learns they are overlapping definitions and Web actions do not count every button.
3. **Given** either documentation language, **When** reading the manual pages or overview, **Then** the same category terminology is used.

### User Story 2 - Follow the shared operation (Priority: P1)

A reader follows the reservation example or a technical entry to its actual command.

**Independent Test**: Existing catalog identities drive navigable relationships and the reservation example.

**Acceptance Scenarios**:

1. **Given** the reservation example, **When** following its links, **Then** `reserve_stock`, `reservation_propose`, and `reserve` open their respective entries and proposal approval is explained.
2. **Given** a mapped tool or Web action, **When** opening its details, **Then** its command relationship is explicitly labeled.
3. **Given** a tool without a mapped business command, **When** reading its details, **Then** its registered description remains visible and the guide explains that reads and governance need not map to one command.

### User Story 3 - Maintain one definition where appropriate (Priority: P2)

A maintainer can change category terminology once and regenerate both presentations while preserving business interfaces.

**Independent Test**: Shared category metadata feeds the manual renderer and overview; audit evidence distinguishes real duplication from deliberate adapter differences.

**Acceptance Scenarios**:

1. **Given** the category metadata, **When** documentation is generated, **Then** the interactive model and manuals share labels, explanations and reservation identities.
2. **Given** reservation, manual order and customer payment, **When** reviewing their paths, **Then** the audit records schemas, service authority, confirmation and justified adapter differences without introducing another business rule.

### Edge Cases

- Commands can be reads; a command can have several tools or none.
- Unmapped tools retain their descriptions; mapping absence does not imply unsupported functionality.
- Reservation quantity is optional; the proposal tool alone does not allocate stock.
- Technical identifiers and existing anchors remain stable; business-resource Actions labels remain general.

## Requirements

### Functional Requirements

- **FR-001**: Use Web actions/Web-Aktionen for technical workspace actions, preserving general business Actions terminology.
- **FR-002**: Explain the categories, overlapping counts, extra read/governance tools, and registered-action count scope in both languages.
- **FR-003**: Show a reservation example linked to real entries and explain proposal followed by explicit confirmation before execution.
- **FR-004**: Explicitly label existing command/agent/Web relationships in entry details and retain explanations for unmapped tools.
- **FR-005**: Reuse one category definition and catalog-derived example across interactive and generated documentation.
- **FR-006**: Record the three-operation duplication audit and consolidate only demonstrated duplication without changing business validation or public interfaces.

### Domain and Traceability Requirements

- **DR-001**: Preserve existing shared services, tenant boundaries, confirmation, source/evidence/reality relationships and all MCP identities, schemas and handlers. This feature reads catalog metadata only.

## Success Criteria

- **SC-001**: Both documentation languages explain all three categories and offer three valid reservation links.
- **SC-002**: Every existing mapped technical entry retains its relationship; all existing entries and identifiers remain present.
- **SC-003**: One category definition supplies both presentations; audit evidence covers all three selected operations.

## Assumptions and Dependencies

The user's “ja mach” approves the session's proposed product scope. Existing catalog mappings and registry schemas are authoritative. Additional runtime consolidation is warranted only by demonstrated duplication. No unresolved clarifications remain.

## Requirement Traceability

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-001, FR-002 | US1.1–3 | Documentation contract tests and build |
| FR-003, FR-004 | US2.1–3 | Catalog relationship/example tests and build |
| FR-005 | US3.1 | Generator/renderer shared-definition tests |
| FR-006 | US3.2 | `research.md` audit and final diff review |
| DR-001 | US2, US3 | Registry schema preservation tests and scoped diff review |
