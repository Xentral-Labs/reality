# Research: Company Membership Invitations

## Shared authorization

**Decision**: Add a focused membership service with an explicit human principal;
recheck owner authority when a Chat proposal executes.

**Rationale**: Existing owner checks are HTTP helpers, while invitations must share
rules with Chat/tools.

**Alternatives considered**: Transport-only checks could be bypassed; full RBAC exceeds
the approved owner/member scope.

## Interface coverage

**Decision**: Expose HTTP/Product Web and confirmed internal Chat behavior. Omit human
membership administration from external MCP and local CLI in V1.

**Rationale**: MCP establishes tenant authority, not a human owner; CLI has no
authenticated human principal. FR-022 permits omission without alternate rules.

**Alternatives considered**: Treating an MCP token or selected CLI tenant as owner
would weaken authorization; adding new authentication there expands scope.

## Identity and membership reuse

**Decision**: Invitation links to tenant and normalized email only. Acceptance creates
or reactivates the existing unique tenant/account membership; neither object links back
to the other.

**Rationale**: This is the shortest relationship and avoids pre-acceptance account
disclosure. New membership rows on re-invite would lose identity/history.

## Concurrent uniqueness and expiry

**Decision**: Lock the tenant row, persist invitation status, and add a partial unique
pending tenant/email index. Mark elapsed pending rows expired under the lock.

**Rationale**: PostgreSQL cannot use the current clock as a stable partial-index
predicate. A tenant lock matches an existing pattern and is sufficient at low volume.

**Alternatives considered**: Advisory locks add machinery; application-only checks
fail under concurrency; a clock predicate is not a valid durable authority.

## Audit authority

**Decision**: Extend SecurityAuditEvent with nullable tenant, subject type/ID, and
outcome. Global auth events retain null tenant; company access audits are scoped.

**Rationale**: Access changes are administrative security Evidence, not operational
Business Events. Typed fields are required for tenant and subject queries.

**Alternatives considered**: BusinessEvent blurs business Reality; JSON-only scope
cannot enforce/query tenant safely; another audit table duplicates authority.

## Durable email and delivery ambiguity

**Decision**: Add a PostgreSQL invitation-delivery queue containing no clear token or
rendered body. For each attempt the worker creates a fresh token in memory, commits only
its hash, sends, and records the outcome. Only the newest generation is usable.

**Rationale**: This makes invitation plus notification intent atomic while honoring
FR-020 and ADR 0004. A timeout after provider acceptance may produce a stale duplicate
email, but retry converges safely.

**Alternatives considered**: Sending in-transaction is not atomic with the provider;
persisting/encrypting a token makes it recoverable; provider idempotency does not cover
SMTP or ambiguous timeouts; never retrying can lose acknowledged delivery.

## Invite-bound admission

**Decision**: Invite signup bypasses only the public-signup switch after invitation
validation. Verification creates no AccessApplication or automatic-slot claim;
explicit acceptance activates an eligible pending account and membership atomically.

**Rationale**: The invitation is the approved admission authority without granting
access before consent. Suspended/rejected accounts remain authoritative.

**Alternatives considered**: Activation at verification precedes consent; normal
early-access review contradicts FR-004.

## Membership history

**Decision**: Preserve TenantMembership identity/created time and keep remove/reactivate
times in immutable security audits; add no membership transition timestamps.

**Rationale**: Current behavior filters current status only. Typed historical fields
are not yet proven; deletion would destroy history and reactivation identity.

## Frontend validation

**Decision**: Extend current React source-contract/localization checks, backend API
stories, build, and manual responsive review; add no new browser framework.

**Rationale**: Service/API tests prove behavior and current frontend gates prove
structure/localization/build. A new E2E dependency is not justified by this feature.
