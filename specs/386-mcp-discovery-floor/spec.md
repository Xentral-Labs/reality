# Feature Specification: A Discovery Floor Every MCP Grant Holds

**Feature Branch**: `386-mcp-discovery-floor`
**Language**: English
**Created**: 2026-10-11
**Status**: Proposal — needs the owner's decision before planning continues
**Input**: A person can deselect `capability_catalog` or `company_context` at consent, and the connection then fails at run time in a way neither the person nor the client can explain.

## Context and Intent

### Problem

The MCP server tells every client to call `capability_catalog` first. It is how an agent
learns which business areas the company covers and which tools its credential may use.
`company_context` is how a client learns which company a credential belongs to, and it is
the only way a client holding two credentials can confirm that both belong to the same
company. A client needs both before it can do anything else.

At `/oauth/authorize` every eligible tool is preselected, and the person may deselect any of
them, these two included. Manual tokens start from an empty selection, so a token without
them is the default unless the owner picks a preset. Such a connection is accepted and
looks healthy in Connected clients. It fails on the client's first call, with a refusal
that names a tool the person never thought of as a permission.

A client cannot fix this. It can refuse the connection after the fact and ask the person to
consent again, which is what happens today, but it cannot make the consent screen keep the
two tools. A client-supplied "required tools" hint would move the decision to every client
and would let a client declare any tool required, including change-capable ones.

### Proposal

Reality defines a small, fixed **discovery floor**: read tools that every credential holds
because no connection works without them, and that disclose nothing beyond what the
credential's holder may already know. Proposed members:

- `capability_catalog`: lists the company's capability areas and which tools *this
  credential* may call.
- `company_context`: the company's id, name and purpose.

The consent screen shows them as always included rather than as checkboxes. Manual token
creation adds them to any selection. A credential's effective tools are its selection plus
the floor.

### Non-Goals

- Do not accept client-declared required tools.
- Do not put any `propose` or `confirm` tool in the floor; the floor never widens what a
  credential can change.
- Do not grant the wildcard or any tool added to the catalog later, other than a future
  floor member that the owner approves through a spec change.
- Do not change scopes; this assumes spec 382's invariant that every grant holds
  `reality:read`.

## User Scenarios & Testing

### User Story 1 - A connection cannot be left unable to start (Priority: P1)

As a person connecting an MCP client, I cannot deselect the tools the client needs to start,
so the connection I approve works.

**Independent Test**: Approve a consent with every tool deselected except one proposal tool;
the client can still call `capability_catalog` and `company_context`.

**Acceptance Scenarios**:

1. **Given** a consent screen, **When** it renders, **Then** the floor tools are shown as
   always included and cannot be deselected.
2. **Given** an approval whose selection omits the floor, **When** the grant is created,
   **Then** it holds the selection plus the floor.
3. **Given** a manual token created with one tool, **When** it is used, **Then** it can also
   call the floor tools.

### User Story 2 - The floor discloses nothing new (Priority: P1)

As an owner, the floor gives a credential no access to business records or changes.

**Acceptance Scenarios**:

1. **Given** a credential holding only the floor, **When** it calls any other tool, **Then**
   it is refused.
2. **Given** a credential for company A, **When** it calls `company_context`, **Then** it
   receives only company A's id, name and purpose.

### Edge Cases

- A grant approved before the change: see decision D-2.
- A floor tool renamed later resolves through the existing legacy-name map.
- Connected clients lists the floor tools with the selection, marked as included by Reality.

## Requirements

### Functional Requirements

- **FR-001**: Reality MUST define one fixed set of discovery floor tools in the catalog,
  each of access class `read`.
- **FR-002**: Every interactive grant and every manual token MUST be able to call every
  floor tool, whatever its selection.
- **FR-003**: The consent screen and the manual token form MUST present the floor as always
  included and MUST NOT offer to remove it.
- **FR-004**: A test MUST fail if a floor member is not `read` or is missing from the
  catalog.

### Decisions requested

- **D-1**: Floor members. Proposal: `capability_catalog` and `company_context`.
  Candidates left out: `capability_describe`, `business_journey_guide`,
  `business_records_discover`.
- **D-2**: Existing credentials. (a) The floor is added when a credential is resolved, so
  existing grants and tokens gain it at once, a deliberate exception to "a grant's tool list
  is frozen"; or (b) only grants and tokens created after the change hold it.
  Proposal: (a), because the floor is defined to disclose nothing new.
- **D-3**: Whether the floor appears in the stored `allowed_tools` (explicit, visible in
  exports) or only in the resolved principal (no stored change). Proposal: stored for new
  credentials, resolved for existing ones under D-2 (a).

## Success Criteria

### Measurable Outcomes

- **SC-001**: A grant approved with only a proposal tool can call both floor tools, in an
  executed test.
- **SC-002**: A floor-only credential is refused every other tool, in an executed test.

## Assumptions and Dependencies

- Spec 382: every interactive grant holds `reality:read`, so read floor tools pass the
  principal's scope check.
- Spec 271: both grant paths share one permission validation, where the floor is added.
- Spec 264: access classes are authoritative.

## Requirement Traceability

FR-001, FR-004 → US2. FR-002, FR-003 → US1.
