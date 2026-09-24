# Feature Specification: MCP Permission Presets

**Feature Branch**: `264-mcp-permission-presets`
**Language**: English
**Created**: 2026-09-24
**Status**: Approved
**Input**: Make broad MCP token permission selection practical without weakening the existing review and confirmation boundary.

## Context and Intent

### Problem

Owners can select all read-only MCP tools with one action, but granting a trusted external agent all currently available change tools requires selecting each tool individually. With a large catalog this is slow and error-prone.

### Scope

Add an explicit full-access selection preset to the existing MCP token form while retaining exact-tool selection, a zero-permission default, and the existing review and confirmation flow.

### Non-Goals

- Do not change token storage, authorization, tool access classifications, or backend APIs.
- Do not grant wildcard access to tools added after token creation.
- Do not remove granular tool selection or the read-only preset.
- Do not create separate presets for individual business domains.

## User Scenarios & Testing

### User Story 1 - Select current full access efficiently (Priority: P1)

As a company owner, I can select every current MCP tool in one action when configuring a trusted external agent, so I do not need to click through the complete catalog.

**Why this priority**: This directly removes the repetitive work reported by owners while preserving explicit token scope.

**Independent Test**: Open token creation, activate the full-access preset, and verify that every current tool is selected and the existing change-capability warning appears during review.

**Acceptance Scenarios**:

1. **Given** no permissions are selected, **When** the owner selects full access, **Then** every tool currently returned by the catalog is selected.
2. **Given** full access is selected, **When** the owner reviews the token, **Then** the review identifies that the token can approve and execute changes and still requires confirmation.
3. **Given** full access is selected, **When** a token is created, **Then** its allowlist contains the explicit current tool names rather than a wildcard.

### User Story 2 - Return to a narrower scope (Priority: P2)

As a company owner, I can switch from full access to read-only access or clear the selection before creating the token.

**Why this priority**: Broad selection must remain easy to reverse before confirmation.

**Independent Test**: Select full access, then select read-only or clear the selection, and verify the selected count and checkboxes reflect the new scope.

**Acceptance Scenarios**:

1. **Given** full access is selected, **When** the owner selects read-only access, **Then** only tools classified as read are selected.
2. **Given** any permissions are selected, **When** the owner clears the selection, **Then** no tools remain selected and review is unavailable.

### Edge Cases

- An empty tool catalog leaves all presets with an empty selection and token review disabled.
- Search and pagination do not limit presets; presets apply to the complete current catalog.
- Duplicate tool names in an invalid catalog response do not create duplicate submitted permissions.

## Requirements

### Functional Requirements

- **FR-001**: The MCP token form MUST offer a single action that selects every tool in the current catalog.
- **FR-002**: Full-access selection MUST submit explicit current tool names and MUST NOT use the wildcard permission.
- **FR-003**: The existing read-only preset MUST replace the selection with only tools classified as read.
- **FR-004**: Owners MUST remain able to clear or individually adjust a preset selection before review.
- **FR-005**: Selecting any change-capable tool MUST retain the existing review warning and explicit confirmation requirement.
- **FR-006**: Preset controls and labels MUST remain usable in all supported UI languages and at mobile and desktop widths.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An owner can select every current MCP permission with one activation.
- **SC-002**: Automated browser evidence proves full-access, read-only replacement, clearing, explicit allowlist submission, and change-warning behavior.
- **SC-003**: The token form introduces no horizontal overflow at the existing supported mobile width.

## Assumptions and Dependencies

- Tool access classifications (`read`, `propose`, and `confirm`) remain authoritative from the existing catalog.
- Existing token review and confirmation behavior remains the security boundary for change-capable permissions.
- The owner approved the full-access preset in the preceding product discussion.

## Requirement Traceability

FR-001, FR-002 and FR-005 → US1. FR-003 and FR-004 → US2. FR-006 → US1 and US2 responsive/localized acceptance coverage.
