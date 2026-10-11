# Feature Specification: Resource Metadata Lists Every Supported Scope

**Feature Branch**: `382-resource-metadata-scopes`
**Language**: English
**Created**: 2026-10-11
**Status**: Draft
**Input**: The MCP server's protected-resource metadata lists only `reality:read`, so standard MCP clients never request proposal or confirmation access. A grant without a read tool is refused on every call.

## Context and Intent

### Problem

An MCP client discovers what to ask for from the protected-resource metadata (RFC 9728).
The MCP SDK's client requests exactly the scopes listed there. Reality's authorization
server lists `reality:read reality:propose reality:confirm`, but the resource metadata lists
only `reality:read`. The SDK publishes the transport's required scopes as
`scopes_supported`, and Reality requires `reality:read`. An SDK client therefore always
requests read access. Its user is never offered proposal tools in the consent screen, and the
connection cannot propose anything.

The same required scope causes a second failure. An interactive grant's scopes are derived
from the tools its user selected, so a user who deselects every read tool gets a grant
without `reality:read`. Reality issues the token, and the transport then refuses every call
with `insufficient_scope`. Manual company tokens always carry `reality:read`, so only the
interactive path has this failure.

### Decision: `reality:read` stays required

The transport keeps requiring `reality:read` of every credential, and that is now an
explicit invariant: every interactive grant holds `reality:read`, as every manual token
already does. The scope permits no tool by itself. A grant's frozen tool list stays its
allowlist, and a scope only narrows that list. A grant without read tools gains no read
tool. Keeping the requirement preserves spec 265's 401/403 transport challenges unchanged.
Dropping it would leave the transport with no minimum scope to state.

### Scope

Publish all three supported scopes in the protected-resource metadata, identical to the
authorization server's list. Every newly approved interactive grant records `reality:read`
among its scopes.

### Non-Goals

- Do not change which tools a scope makes eligible, the consent preselection, or any tool's
  access class.
- Do not decide which tools every grant must hold. That is a separate proposal (a
  server-defined floor of discovery tools).
- Do not rewrite grants approved before this change. A stored grant whose scopes lack
  `reality:read` stays refused at the transport until its user consents again, because
  widening a stored scope at read time would revive tools a narrowed scope removed.

## User Scenarios & Testing

### User Story 1 - A standard MCP client can request proposal access (Priority: P1)

As a person connecting an MCP client built on the MCP SDK, I am offered proposal and
confirmation tools in the consent screen, because the client learned those scopes from the
resource it connects to.

**Why this priority**: Without it, no SDK-based client can propose anything through
interactive authorization.

**Independent Test**: Read the resource metadata and the authorization server metadata and
compare their `scopes_supported`.

**Acceptance Scenarios**:

1. **Given** the MCP runtime, **When** a client reads
   `/.well-known/oauth-protected-resource`, **Then** `scopes_supported` lists
   `reality:confirm`, `reality:propose` and `reality:read`, identical to the authorization
   server metadata.
2. **Given** no credential, **When** a client calls the MCP endpoint, **Then** it still
   receives the 401 challenge naming the resource metadata.

### User Story 2 - A grant without read tools still connects (Priority: P2)

As a user who selects only proposal tools, my client can call those tools instead of being
refused on every request.

**Why this priority**: The consent screen allows this selection, and the grant it produces
fails silently.

**Independent Test**: Approve a grant holding one proposal tool and nothing else, exchange
its code, and resolve the token.

**Acceptance Scenarios**:

1. **Given** a consent requesting read and propose, **When** the user selects one proposal
   tool only, **Then** the grant's scopes are `reality:propose reality:read`, and so is the
   token response's `scope`.
2. **Given** that grant, **When** its token is resolved, **Then** it carries `reality:read`
   and permits the proposal tool and no read tool.

### Edge Cases

- A credential lacking `reality:read` still receives the 403 `insufficient_scope` challenge.
- A client that requests only `reality:propose` is granted `reality:read` as well. The token
  response states the granted scope, as OAuth requires when it differs from the request.

## Requirements

### Functional Requirements

- **FR-001**: The protected-resource metadata MUST list every scope the authorization
  server supports, identical to the authorization server metadata.
- **FR-002**: The MCP transport MUST keep requiring `reality:read` of every credential, and
  every newly approved interactive grant MUST hold `reality:read` among its scopes.
- **FR-003**: Holding `reality:read` MUST NOT permit any tool outside the grant's selected
  tools.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The resource metadata and authorization metadata list the same scopes in an
  executed test.
- **SC-002**: A grant holding only a proposal tool resolves to a principal with that tool and
  no other, in an executed test.

## Assumptions and Dependencies

- MCP SDK 2.3 publishes `AuthSettings.required_scopes` as the resource's `scopes_supported`
  and offers no separate setting. Reality replaces that one route with the SDK's own route
  builder.
- Spec 265's transport challenges and spec 264's access classes stay authoritative.

## Requirement Traceability

FR-001 → US1. FR-002 and FR-003 → US2 and the edge cases.
