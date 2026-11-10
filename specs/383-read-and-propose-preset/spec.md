# Feature Specification: Read-and-Prepare Preset for Manual MCP Tokens

**Feature Branch**: `383-read-and-propose-preset`
**Language**: English
**Created**: 2026-10-11
**Status**: Draft
**Input**: The manual MCP token form offers read-only and full-access presets. An owner who wants an agent to read and prepare changes, but never approve them, must deselect every approval tool by hand.

## Context and Intent

### Problem

Spec 264 gave the manual token form two presets: every read tool, and every tool. The
common setup for an external agent sits between them: it reads and prepares proposals, and
a person approves. An agent that refuses to run with a credential able to approve its own
proposals cannot use the full-access preset. Producing the right token today means
selecting full access and then finding and clearing every approval tool in a catalog of
about 180, which is the repetitive, error-prone work spec 264 set out to remove.

### Scope

Add one preset to the manual token form that selects every current tool whose access class
is not `confirm`, that is every read and every propose tool.

### Non-Goals

- Do not change the default empty selection, the existing presets, review, warning or
  confirmation.
- Do not change access classes, token storage, authorization or any backend API.
- Do not add the preset to the interactive consent screen.
- Do not grant tools added after the token is created.

## User Scenarios & Testing

### User Story 1 - Create a token that can prepare but not approve (Priority: P1)

As a company owner, I can select every read and prepare-change tool in one action, so the
token I give an agent can propose changes and cannot approve them.

**Why this priority**: It is the recommended way to connect an agent, and it currently takes
the most clicks to set up.

**Independent Test**: Open token creation, select full access, then activate the new preset;
verify read and propose tools are selected, confirm tools are not, and review shows no
approval warning.

**Acceptance Scenarios**:

1. **Given** any selection, **When** the owner activates the read-and-prepare preset,
   **Then** exactly the current tools classified `read` or `propose` are selected.
2. **Given** that selection, **When** the owner reviews the token, **Then** the warning that
   the token may approve and execute changes is absent.
3. **Given** that selection, **When** the owner adjusts a single tool or clears the
   selection, **Then** the form behaves as for any other preset.

### Edge Cases

- Search and pagination do not limit the preset; it applies to the whole current catalog.
- Duplicate names in an invalid catalog response are submitted once.
- A catalog with only `confirm` tools leaves the selection empty and review disabled.

## Requirements

### Functional Requirements

- **FR-001**: The manual MCP token form MUST offer one action that replaces the selection
  with every current tool whose access class is `read` or `propose`.
- **FR-002**: The preset MUST submit explicit tool names, never the wildcard, and MUST NOT
  select any `confirm` tool.
- **FR-003**: The preset's label MUST exist in every supported UI language.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An owner can create a read-and-prepare token with one preset activation.
- **SC-002**: Browser evidence proves the selection and the absent approval warning.

## Assumptions and Dependencies

- Access classes remain authoritative from the existing catalog (spec 264).
- The existing review and confirmation flow remains the security boundary.

## Requirement Traceability

FR-001, FR-002 → US1. FR-003 → US1 localized coverage.
