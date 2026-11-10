# Feature Specification: Unattended Refresh for Interactive MCP Grants

**Feature Branch**: `385-unattended-mcp-refresh`
**Language**: English
**Created**: 2026-10-11
**Status**: Proposal — needs the owner's decision before planning continues
**Input**: Every interactive MCP connection ends 30 days after consent however actively it is used, and one lost token response ends it at once. An agent that runs a company unattended cannot depend on either.

## Context and Intent

### Problem

An interactive grant issues a refresh token valid for 30 days from the code exchange
(`REFRESH_TTL`). Rotation caps each replacement at the original expiry, so the family dies
on day 30 regardless of use, and the person must consent again. For a person at a desk that
is a minor chore. For an agent that reads and proposes on a company's behalf around the
clock, it is a scheduled outage, and it lands on whoever happens to own the consent.

Rotation also has no tolerance for a lost response. Presenting a refresh token that was
already rotated revokes the whole grant, as RFC 9700 recommends for detecting stolen
tokens. A client whose refresh request reached Reality but whose response was lost in
transit (a timeout, a restart, a dropped connection) still holds only the old token. Its
next attempt is indistinguishable from theft, and the grant ends. A careful client can only
avoid this by never retrying a refresh, and it still loses the grant when the first
response is lost.

### Scope of the decision

This proposal asks the owner to choose between the options below and to set their numbers.
It changes no behavior until approved; the implementation plan follows the decision.

1. **Sliding refresh window (recommended).** Each successful rotation issues a refresh
   token valid for a fixed idle window from now, instead of capping it at the first expiry.
   A grant then lives while it is used and ends after the idle window without use. Every
   token and refresh keeps re-checking the live account, membership, company readiness and
   grant state, exactly as today. An optional absolute ceiling can bound a grant's total life
   even when used.
2. **Long-lived service grant.** A separate grant kind for unattended services, owned by the
   company rather than one person's membership, with its own consent and inventory. It
   solves a second problem as well (approvals ending with one person's membership) but is a
   new authorization model, with schema, consent and inventory changes.
3. **Reuse grace after a lost response (recommended, independent of 1 and 2).** Within a
   short window after a rotation, and only while the replacement has never been used,
   presenting the just-rotated refresh token rotates again: the unused replacement is
   revoked and a fresh one issued. Outside that window, or once the replacement has been
   used, reuse revokes the family as today.

### Non-Goals

- Do not change access-token lifetime (15 minutes), PKCE, resource binding, scopes or tool
  allowlists.
- Do not relax reuse detection beyond the grace conditions; a replacement that has been used
  keeps the family's reuse revocation.
- Do not ask for a tenant identifier in the grant; `company_context` already returns the
  company id a client compares.
- Do not build option 2 in the same change as option 1 or 3.

## User Scenarios & Testing

### User Story 1 - An agent in daily use keeps its connection (Priority: P1)

As an owner, a connection my agent uses every day keeps working past day 30, and one I stop
using ends on its own.

**Independent Test**: Rotate a grant's refresh token on day 29 and on day 58; both succeed.
Leave a grant unused past the idle window; its refresh is refused.

**Acceptance Scenarios**:

1. **Given** a grant refreshed at least once per idle window, **When** 30 days pass since
   consent, **Then** refresh still succeeds.
2. **Given** a grant not refreshed for longer than the idle window, **When** the client
   refreshes, **Then** it receives `invalid_grant` and the grant is shown as expired.
3. **Given** an absolute ceiling is configured, **When** a grant reaches it, **Then** refresh
   is refused however recently it was used.
4. **Given** the consenting person loses their membership, **When** the client refreshes or
   calls a tool, **Then** it is refused, as today.

### User Story 2 - A lost refresh response does not end the connection (Priority: P1)

As an owner, a connection survives one refresh whose response never reached the client.

**Independent Test**: Rotate once, discard the response, present the old refresh token again
within the grace window; receive a working pair. Then present the discarded replacement;
it is refused.

**Acceptance Scenarios**:

1. **Given** a rotation whose replacement was never used, **When** the old refresh token is
   presented within the grace window, **Then** a new pair is issued and the unused
   replacement is revoked.
2. **Given** a rotation whose replacement was used, **When** the old refresh token is
   presented at any time, **Then** the family is revoked, as today.
3. **Given** a rotation older than the grace window, **When** the old refresh token is
   presented, **Then** the family is revoked, as today.
4. **Given** a replacement revoked by the grace path, **When** it is presented later,
   **Then** the family is revoked, because two holders of one family is the theft signal.

### Edge Cases

- Two concurrent refreshes with the same token: the row lock already serializes them; the
  second sees a rotated row and takes the grace path only if the first's replacement is
  unused.
- Grants issued before the change keep their stored expiry until their next rotation.

## Requirements

### Functional Requirements

- **FR-001** (option 1): A successful rotation MUST set the replacement's refresh expiry to
  the configured idle window from the rotation time, bounded by an absolute ceiling when one
  is configured.
- **FR-002** (option 1): Refresh and every tool call MUST keep re-checking live account,
  membership, company readiness and grant revocation.
- **FR-003** (option 3): Presenting a rotated refresh token MUST rotate again only when the
  rotation is younger than the grace window and its replacement has never been used for
  access or refresh; otherwise it MUST revoke the family.
- **FR-004** (option 3): A replacement revoked by the grace path MUST be treated as reuse if
  presented later.
- **FR-005**: Connected clients MUST show when a grant's current refresh window ends.

### Decisions requested

- **D-1**: Option 1, option 2, or both (option 2 as its own later feature).
- **D-2**: Idle window length (proposal: 30 days) and absolute ceiling (proposal: none, or
  365 days).
- **D-3**: Option 3, and its grace window (proposal: 60 seconds).

## Success Criteria

### Measurable Outcomes

- **SC-001**: A grant refreshed daily works on day 60 in an executed test.
- **SC-002**: A grant unused past the idle window is refused in an executed test.
- **SC-003**: A refresh whose response was discarded can be retried once within the grace
  window without ending the grant, in an executed test.

## Assumptions and Dependencies

- Spec 265's grant and credential model; `MCPUserCredential` already records
  `rotated_at`, `replaced_by_id` and `last_used_at`, which the grace conditions need.
- RFC 9700 (OAuth 2.0 Security BCP) section 4.14 permits refresh token rotation with reuse
  detection and does not prohibit a bounded grace for an unused replacement.
- Spec 381 (refresh-token revocation ends the grant) is independent and composes with this.

## Requirement Traceability

FR-001, FR-002, FR-005 → US1. FR-003, FR-004 → US2.
