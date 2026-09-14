# Feature Specification: Command Action Guidance

**Feature Branch**: `051-command-action-guidance`

**Created**: 2026-09-03

**Status**: Approved

**Language**: English

**Input**: User description: "Show the existing business description for every workspace command in All actions and in its Web action form, while keeping prerequisites understandable and separate."

## Context and Intent

### Problem

Workspace Views already explain their purpose, but Actions currently show only a label and prerequisite record types. Users therefore cannot understand a mutation's business effect until after selecting it, and even the form does not explain the intended change.

### Scope

- Reuse every classified Command's canonical business effect as its Workspace Action description.
- Show the description in the complete Action launcher and shared Action form.
- Keep prerequisites visible as distinct supporting guidance and make descriptions searchable.
- Localize the complete visible experience in every supported Product Web language.

### Non-Goals

- Changing Action membership, ordering, permissions, adapters, fields, mutation services, or confirmation behavior.
- Adding new Commands, generic command execution, domain state, storage, or schema.
- Adding field-level help or replacing remaining opaque-identity inputs beyond the existing reference selectors.

### Existing Contracts

- [Web UI Specification](../../docs/WEB_SPEC.md)
- [Workspace Views and Actions](../046-workspace-views-actions/spec.md)
- [Specialized Workspace Views](../049-specialized-workspace-views/spec.md)
- [Repeating Form Groups](../053-repeating-form-groups/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand actions before selecting them (Priority: P1)

As an operations user, I can read what every available action does in the complete action launcher before I choose it.

**Why this priority**: A label and technical prerequisites alone do not explain the business effect of a mutation.

**Independent Test**: Open All actions in any actionable workspace and verify every result shows its catalog-owned business description and, where applicable, separate prerequisites.

**Acceptance Scenarios**:

1. **Given** a workspace with actions, **When** the user opens All actions, **Then** every action shows its label and business effect.
2. **Given** an action has prerequisites, **When** it is shown in the launcher, **Then** the prerequisites appear separately from the business effect.
3. **Given** the user searches with words from an action description, **When** results are filtered, **Then** the matching action remains discoverable.

---

### User Story 2 - Understand an action while completing it (Priority: P1)

As an operations user, I can see the selected action's business effect above its form so that I understand the intended mutation before entering or reviewing values.

**Why this priority**: Mutating workflows must be understandable before confirmation, especially when their fields contain opaque identities.

**Independent Test**: Select any direct or launcher action and verify the same description appears below the title throughout entry and review.

**Acceptance Scenarios**:

1. **Given** an action selected directly or through All actions, **When** its form opens, **Then** the catalog-owned description appears below the title.
2. **Given** the form enters its review step, **When** the user reviews values, **Then** the description remains visible and the existing explicit confirmation remains required.
3. **Given** a supported non-English UI language, **When** the launcher or form renders, **Then** the action description is localized with the normal English fallback.

### Edge Cases

- A workspace action referencing a command without a non-empty effect is rejected during catalog validation rather than exposed without guidance.
- An action with no prerequisites shows no empty prerequisite label.
- Long descriptions wrap without hiding the action label, navigation arrow, fields, or confirmation controls.
- Search with no matches retains the existing localized empty result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every validated workspace Action MUST expose a non-empty business description derived from its referenced Command's canonical effect.
- **FR-002**: Workspace catalog validation MUST reject any classified Action whose referenced Command lacks a non-empty effect.
- **FR-003**: All actions MUST show the Action label and business description for every result.
- **FR-004**: All actions MUST show non-empty prerequisites separately with a localized `Requires` label and MUST omit that row when none exist.
- **FR-005**: Action search MUST match label, description, and prerequisites case-insensitively.
- **FR-006**: The Action form MUST show the same business description below its title during both entry and review.
- **FR-007**: Direct and launcher-selected Actions MUST use the same form and description behavior.
- **FR-008**: Existing explicit review and confirmation behavior MUST remain unchanged.
- **FR-009**: New visible guidance and all catalog Action descriptions MUST support English, German, Dutch, and Spanish through the existing localization fallback contract.
- **FR-010**: The change MUST NOT add business state, persistence schema, generic command execution, or alternate service logic.

### Key Entities

- **Command effect**: The canonical business explanation of what one shared application command changes.
- **Workspace Action**: Validated presentation metadata that references one Web-enabled command and receives its description from that command.
- **Prerequisite**: A concise business record type that must already exist before an action can be completed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of classified workspace Actions display a non-empty description in All actions.
- **SC-002**: 100% of Action forms display the same description returned for their launcher entry.
- **SC-003**: Users can distinguish what an action does from what it requires without opening the form.
- **SC-004**: Description words successfully find matching actions in the launcher.
- **SC-005**: Existing action execution, review, and confirmation acceptance tests remain green in all four supported languages.

## Assumptions and Dependencies

- The Command catalog's `effect` is the canonical short business description; no second Action-specific prose field is required.
- Existing prerequisites remain valid concise classifications and are presentation metadata, not permission or validation rules.
- Field-level explanations and additional reference selectors are outside this focused change.
- No database migration or application-service mutation is required.

## Open Questions

None. The user approved the generic catalog-owned behavior and the existing Command effect provides the required canonical description.

## Requirement Traceability

| Requirement | Acceptance scenario(s) | Planned proof |
|---|---|---|
| FR-001-FR-002 | US1-1, edge case 1 | Catalog enrichment and rejection unit tests |
| FR-003-FR-005 | US1-1 to US1-3 | Product Web launcher contract and search tests |
| FR-006-FR-008 | US2-1 to US2-2 | Shared Action form and confirmation contract tests |
| FR-009 | US2-3 | Strict localization audit and four-language visual review |
| FR-010 | All scenarios | Architecture diff review and complete regression suite |
