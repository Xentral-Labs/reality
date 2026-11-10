# Feature Specification: Revoking a Refresh Token Ends Its Grant

**Feature Branch**: `381-oauth-revoke-ends-grant`
**Language**: English
**Created**: 2026-10-11
**Status**: Draft
**Input**: An MCP client that revokes its refresh token through `/oauth/revoke` still appears as an active connected client, and the access tokens issued under the same grant keep working.

## Context and Intent

### Problem

An MCP client disconnects the way RFC 7009 describes: it posts its refresh token to
`/oauth/revoke`. Reality marks that one credential row revoked and nothing else. The grant
stays active, so Connected clients keeps listing the client as active, and every other
credential row of the grant stays usable: an access token issued before the last rotation
keeps answering until it expires. The client believes it disconnected; the owner sees it
still connected; both are reading the same grant.

RFC 7009 section 2.1 states that revoking a refresh token should also invalidate the access
tokens based on the same authorization grant. Spec 265's lifecycle has a grant reach
`revoked` through revocation, and its settings path already revokes the grant and every
credential. Only the protocol path stops at one row.

There is a second, quieter version of the same gap. An access token and its refresh token
share one credential row, so revoking the current access token already kills the only
refresh token that can renew the grant. The grant can never be used again, yet it is still
listed as active.

### Scope

Make `/oauth/revoke` end the grant whenever the revoked token was the grant's way forward:
any refresh token of the grant, current or already rotated, and the current access token.
The grant is recorded as revoked with the reason `client_revoked`, and every credential of
the grant is refused from then on.

### Non-Goals

- Do not change the endpoint's response: it stays an empty 200 for known, unknown and
  already revoked tokens, so it discloses nothing.
- Do not require client identification on `/oauth/revoke`. Possessing a refresh token
  already confers the power to use the grant; ending it is a lesser power.
- Do not change refresh rotation, refresh reuse detection, token lifetimes, or the settings
  revocation paths.
- Do not refuse the still-unexpired access token of an already rotated row while its grant
  stays active; renewing a token does not revoke the previous access token.

## User Scenarios & Testing

### User Story 1 - A client that disconnects is shown as disconnected (Priority: P1)

As the owner of a company, when an MCP client revokes its refresh token, Connected clients
shows that client as revoked, so what I see matches what the client did.

**Why this priority**: An owner auditing access cannot tell a disconnected client from a
live one; the list is the only place the grant is visible.

**Independent Test**: Connect a client, revoke its refresh token through `/oauth/revoke`,
and read the personal grant inventory.

**Acceptance Scenarios**:

1. **Given** an active grant, **When** the client revokes its current refresh token,
   **Then** the grant is listed as revoked with the reason `client_revoked`, and no human
   is recorded as the revoker.
2. **Given** a grant whose refresh token was rotated, **When** the client revokes the old
   refresh token, **Then** the grant is revoked as well.
3. **Given** an already revoked grant, **When** the same token is revoked again, **Then**
   the response is unchanged and so is the grant.

### User Story 2 - No credential of a revoked grant keeps working (Priority: P1)

As an owner, once a client's grant is revoked through the protocol, no access token issued
under that grant is accepted, whichever rotation it came from.

**Why this priority**: A revocation that leaves a working access token behind is not a
revocation.

**Independent Test**: Rotate once, revoke the newest refresh token, then present both
access tokens and the refresh token.

**Acceptance Scenarios**:

1. **Given** a grant with two generations of credentials, **When** the newest refresh
   token is revoked, **Then** both access tokens are refused and a refresh exchange with
   the revoked token answers `invalid_grant`.
2. **Given** an active grant, **When** the client revokes its current access token,
   **Then** the grant is revoked, because its only renewable refresh token went with it.
3. **Given** a grant rotated once, **When** the client revokes the older access token,
   **Then** only that token is refused and the grant stays active and renewable.

### Edge Cases

- An unknown token changes nothing and still answers an empty 200.
- Revoking a token of a grant whose company or membership became unavailable still records
  the grant as revoked.

## Requirements

### Functional Requirements

- **FR-001**: Revoking any refresh token of a grant through `/oauth/revoke` MUST revoke the
  grant and every credential issued under it.
- **FR-002**: Revoking the grant's current access token MUST revoke the grant in the same
  way; revoking the access token of an already rotated credential MUST revoke only that
  credential.
- **FR-003**: A grant revoked through the protocol MUST record the reason `client_revoked`
  and no human revoker, and MUST be listed as revoked in personal and company inventories.
- **FR-004**: The endpoint's response MUST stay identical for known, unknown and already
  revoked tokens.

### Key Entities

- **MCPClientGrant**: gains no field; `revoke_reason` takes one new controlled value,
  `client_revoked`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: After a client revokes its refresh token, the inventory lists its grant as
  revoked in an executed test.
- **SC-002**: No access token of that grant, from any rotation, is accepted afterwards in an
  executed test.

## Assumptions and Dependencies

- Spec 265's grant lifecycle and the shared `revoke_grant` service are the authority for
  grant revocation; this feature only routes protocol revocation into it.
- The consent and settings screens already show a grant's state and reason; the new reason
  needs only its labels.

## Requirement Traceability

FR-001 and FR-003 → US1. FR-001 and FR-002 → US2. FR-004 → US1 scenario 3 and the edge
cases.
