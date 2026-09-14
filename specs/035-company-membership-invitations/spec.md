# Feature Specification: Company Membership Invitations

**Feature Branch**: `[035-company-membership-invitations]`
**Created**: 2026-09-02
**Status**: Approved for planning
**Language**: English
**Input**: "Create a Spec Kit feature specification from `docs/ideas/company-membership-invitations.md`."

## Context and Intent

### Problem

An active company owner needs a safe way to invite another person into the same
company. The recipient may already have a Reality account or may need to register.
Both cases must produce the same observable invitation flow, require the recipient's
consent, preserve tenant isolation, and avoid revealing whether an email address is
already registered.

The current product separates global account identity from company membership but does
not provide invitation acceptance or membership administration. The smallest useful
extension must preserve that separation and the existing owner safeguards without
introducing fine-grained permissions.

### Scope

- Invite one email address to one active company through a uniform, expiring invitation.
- Let a recipient sign in or complete invite-bound registration and email verification
  before explicitly accepting the invitation.
- Treat a valid invitation as platform admission for the invited access, including when
  public signup is disabled, without overriding suspended or rejected account state.
- List active members and pending or expired invitations in company settings.
- Resend or revoke a pending invitation and safely retry invitation email delivery.
- Remove and later re-invite a non-owner member while retaining an auditable history.
- Switch among all companies for which an account has an active membership.
- Retain `owner` as a narrow lifecycle, recovery, secret, credential, and membership-
  safety boundary; grant `member` all ordinary company product functions.
- Restrict invitation and membership administration to active owners while keeping
  ordinary product access equal for active owners and members.
- Make the same membership rules available through shared application operations so
  Web, API, CLI, MCP, and Chat cannot create alternate behavior.

### Non-Goals

- Viewer/editor, custom, or per-feature permissions.
- Admin, accountant, operator, guest, or directory-managed roles.
- Ownership transfer, removal of an owner, or legal-company ownership semantics.
- Approval chains, domain-wide automatic membership, SCIM, SSO group synchronization,
  or external directory provisioning.
- Guest access limited to selected records or invitation of mailing lists/shared identities.
- Account merging or accepting an invitation through a different email address.
- Changing operational Source, Evidence, or Reality records as a consequence of
  membership administration.

### Existing Contracts

- [`specs/003-tenant-access/spec.md`](../003-tenant-access/spec.md)
- [`docs/ideas/company-membership-invitations.md`](../../docs/ideas/company-membership-invitations.md)
- [`docs/features/tenancy.md`](../../docs/features/tenancy.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [Business Reality Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Invite and Join a Company (Priority: P1)

As an active company owner, I can invite a person, and that person can knowingly join
the company after proving control of the invited email address.

**Why this priority**: No other membership-management behavior has value until an
invitation can safely establish company access.

**Independent Test**: Invite one new address and one address with an existing account,
complete both flows, and verify identical inviter-visible pending states followed by
one active membership per recipient only after explicit acceptance.

**Acceptance Scenarios**:

1. **Given** an active owner and an address without an account, **When** the owner
   invites it and the recipient registers, verifies that address, and explicitly
   accepts, **Then** one active member membership is created and the company opens.
2. **Given** an active owner and an address with an existing verified account, **When**
   the owner invites it, **Then** the inviter sees the same response and pending state
   as for an unknown address, and no membership exists before recipient acceptance.
3. **Given** a signed-in account whose verified email does not match the invitation,
   **When** acceptance is attempted, **Then** access is refused without disclosing
   account or company data beyond the invitation landing context.
4. **Given** public signup is disabled, **When** a valid invited recipient without an
   account follows the invitation, **Then** invite-bound registration remains available
   and successful acceptance admits that account without a separate access application.
5. **Given** a suspended or rejected account, **When** it attempts to accept a valid
   invitation, **Then** it remains blocked and no membership is activated.
6. **Given** an active non-owner member, **When** that member attempts to invite an
   address, **Then** the action is refused and no invitation or notification intent is
   created.

### User Story 2 - Manage Invitations (Priority: P1)

As an active company owner, I can see and manage invitations without learning whether
their email addresses belong to existing Reality accounts.

**Why this priority**: Members need recovery from lost mail and mistaken invitations,
while the workflow must not become an account-discovery channel.

**Independent Test**: Create, duplicate, resend, expire, revoke, and concurrently
accept invitations for existing and unknown addresses and compare all inviter-visible
states and responses.

**Acceptance Scenarios**:

1. **Given** no usable invitation or active membership for a normalized address,
   **When** an active owner invites it, **Then** one pending seven-day invitation is
   shown and a retryable notification outcome is recorded before delivery is attempted.
2. **Given** a usable invitation already exists for the same company and normalized
   address, **When** another invite is requested, **Then** no duplicate usable
   invitation is created and the response remains neutral.
3. **Given** a pending invitation whose most recent delivery request is at least 60
   seconds old, **When** resend is requested, **Then** a new link is issued, every older
   link becomes unusable, and delivery can be retried safely.
4. **Given** a pending invitation, **When** an active owner revokes it, **Then** all of
   its links become unusable and subsequent acceptance has no effect.
5. **Given** an expired, revoked, or already accepted invitation, **When** acceptance is
   attempted, **Then** no additional membership is created and a safe status-specific
   recovery message is shown.
6. **Given** accept races with accept, revoke, or resend, **When** the requests complete,
   **Then** at most one acceptance succeeds and the final invitation and membership
   states are internally consistent.

### User Story 3 - Review and Switch Company Access (Priority: P2)

As a member of one or more companies, I can see who currently has access and switch
only among companies where my membership is active.

**Why this priority**: Membership must be understandable to people and remain the
authoritative tenant-access boundary.

**Independent Test**: Give one account memberships in two identically named companies,
remove one membership, and verify the explicit company context, switcher choices, and
tenant access before and after removal.

**Acceptance Scenarios**:

1. **Given** an account with active memberships in multiple companies, **When** the
   company switcher opens, **Then** every accessible company is distinguishable by
   opaque identity and the current company is explicit.
2. **Given** an active membership is removed while the account session remains valid,
   **When** the next request or navigation targets that company, **Then** access is
   denied without revealing company records and another accessible company or a safe
   no-company state is offered.
3. **Given** two companies with the same display name, **When** members or invitations
   are viewed, **Then** the records remain isolated and cannot be joined or acted on by
   company name.

### User Story 4 - Remove and Re-invite a Member (Priority: P2)

As a company owner, I can remove a non-owner member and later invite that person again
without deleting the historical membership trail or weakening owner continuity.

**Why this priority**: Companies need a bounded way to end access, but recovery and
ownership rules must remain safe.

**Independent Test**: Remove a member, prove immediate loss of tenant access, invite
and accept again, and verify that one membership identity is reactivated with a
complete audit trail.

**Acceptance Scenarios**:

1. **Given** an owner and an active non-owner member, **When** the owner removes that
   member, **Then** the membership becomes removed and subsequent tenant requests fail.
2. **Given** a non-owner member, **When** that member attempts to remove any member,
   **Then** the action is refused without changing membership state.
3. **Given** an owner membership, **When** removal through this feature is attempted,
   **Then** it is refused because owner removal and transfer are outside this scope.
4. **Given** a removed member, **When** that address is invited and accepts again,
   **Then** the existing membership is reactivated rather than duplicated.

### User Story 5 - Use Safe Membership Actions Across Interfaces (Priority: P3)

As an operator using Web, CLI, API, MCP, or Chat, I receive the same authorization,
privacy, validation, idempotency, and audit behavior for membership operations.

**Why this priority**: Alternate interfaces must not bypass the tenant or confirmation
boundaries established by the product workflow.

**Independent Test**: Exercise each exposed interface against the same membership
scenarios and verify equivalent outcomes; verify that Chat cannot execute an invite,
revoke, resend, or removal without preview and explicit confirmation.

**Acceptance Scenarios**:

1. **Given** equivalent authorized requests through supported interfaces, **When** the
   same operation is performed, **Then** the resulting invitation, membership, and
   audit states are equivalent.
2. **Given** a Chat request to invite, resend, revoke, or remove, **When** confirmation
   has not been explicitly granted, **Then** no state or email-delivery intent changes.
3. **Given** a user from another company, **When** any invitation or membership
   identifier is supplied through any interface, **Then** the operation behaves as not
   found and reveals no foreign member, email, company, or invitation data.

### Edge Cases

- An invitation targets the inviter's own address or an existing active member.
- Email case or surrounding whitespace differs between invitation and account.
- The recipient changes account email before accepting.
- The invitation is opened while another account is already signed in.
- The company is archived while an invitation is pending or being accepted.
- The inviter loses membership after creating an invitation; the invitation remains a
  company invitation unless another active owner revokes it.
- The company name changes after email delivery or two companies share the same name.
- Email delivery fails temporarily, is duplicated, bounces, or is suppressed after a complaint.
- An invitation link appears in browser history, logs, analytics, or referral metadata.
- Removal races with an in-flight tenant request, invitation acceptance, or re-invitation.
- An account has no remaining active memberships after removal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Any active company owner MUST be able to invite one normalized email
  address to that active company.
- **FR-002**: The system MUST create the same pending invitation and expose the same
  response and member-list state regardless of whether the email belongs to an account.
- **FR-003**: An invitation MUST NOT create or activate membership until an authenticated
  recipient with the matching verified email explicitly accepts it.
- **FR-004**: Invite-bound registration MUST remain available when public signup is
  disabled, and successful invitation acceptance MUST admit the recipient without a
  separate early-access application.
- **FR-005**: Invitation acceptance MUST NOT activate a suspended or rejected account.
- **FR-006**: A usable invitation MUST expire seven days after issuance and MUST become
  unusable after acceptance, revocation, or replacement by resend.
- **FR-007**: At most one usable invitation MAY exist per company and normalized email;
  at most one membership MAY exist per company and account.
- **FR-008**: Acceptance MUST be atomic and idempotent under retries and concurrency.
- **FR-009**: Resend MUST be available no sooner than 60 seconds after the previous
  delivery request, MUST rotate the invitation secret, and MUST preserve one logical
  invitation history.
- **FR-010**: Invitation creation, resend, and retry MUST durably record both intended
  company state and retryable notification intent before attempting email delivery.
- **FR-011**: Active owners MUST be able to list active members and pending or expired
  invitations for their company without seeing account-existence information.
- **FR-012**: Active owners MUST be able to revoke pending invitations; accepted,
  revoked, and expired invitations MUST not be accepted.
- **FR-013**: Only an active owner or platform administrator MUST be able to remove an
  active non-owner member; removing or transferring an owner is outside this feature.
- **FR-014**: Removing membership MUST deny company access on the next protected request
  while leaving the global account session and other company memberships intact.
- **FR-015**: Re-inviting and accepting a removed member MUST reactivate the existing
  membership identity rather than create a duplicate.
- **FR-016**: Archived companies MUST reject new invitations, resends, acceptance, and
  membership changes; their pending invitations MUST remain unusable while archived.
- **FR-017**: Pending invitations MUST remain valid if their original inviter loses
  membership, unless another active owner revokes them.
- **FR-018**: Every invite, resend, delivery outcome, revoke, accept, remove, and
  reactivate transition MUST retain company, subject, actor where known, outcome, and
  UTC occurrence time for audit.
- **FR-019**: Invitation emails MUST identify the company, support a safe English
  fallback, provide a way to report an unexpected invitation, and use the same content
  whether or not an account exists.
- **FR-020**: Invitation secrets MUST be random, single-purpose, expiring, stored only
  in non-recoverable form, and prevented from leaking to third-party page resources,
  analytics, application logs, or referral metadata.
- **FR-021**: Every invitation and membership read, write, list, and relationship MUST
  enforce company scope and cross-company non-disclosure.
- **FR-022**: Web, CLI, API, MCP, and Chat MUST delegate exposed membership behavior to
  the same application operations; an interface MAY omit an operation but MUST NOT
  implement different rules.
- **FR-023**: Chat-based invite, resend, revoke, and removal MUST require a server-derived
  preview and explicit confirmation before any state or notification intent changes.
- **FR-024**: The company switcher MUST show only active memberships and MUST keep the
  current company explicit when an account belongs to multiple companies.
- **FR-025**: Ordinary operational, financial, explainability, and non-secret company
  configuration functions MUST be equally available to active owners and members;
  invitation/member administration, archive/restore/delete, recovery, secret-bearing
  AI configuration, MCP/API credential management, and owner-continuity actions MUST
  remain owner-only.
- **FR-026**: A non-owner member MUST NOT create, resend, or revoke invitations and
  MUST NOT create notification intent for those operations.
- **FR-027**: Email normalization MUST trim surrounding whitespace and compare case-
  insensitively; it MUST NOT infer provider-specific equivalence for dots, plus aliases,
  or other provider conventions.
- **FR-028**: Failed invitation delivery MUST retry with increasing delay for up to 24
  hours, then become visibly failed and remain eligible for owner resend; when no worker
  is available, the invitation MUST remain durable and visibly delivery-pending.
- **FR-029**: Accepted, revoked, and expired invitation plus delivery details MUST be
  deleted 90 days after terminal transition; the minimal token-free security audit MUST
  remain until permanent company deletion.
- **FR-030**: One company MUST create at most 20 new logical invitations per rolling 24
  hours and one invitation MUST accept at most five resend requests per rolling 24
  hours, in addition to the 60-second resend cooldown. Neutral requests for an already
  usable invitation or active member MUST NOT consume the creation quota. Once a quota
  is exhausted, every otherwise eligible owner request in that scope MUST receive the
  same rate-limit response independent of account existence; eligibility returns as
  counted events leave the rolling window.
- **FR-031**: When an invited verified account has a pending AccessApplication,
  acceptance MUST retain it and mark it approved with the reason `admitted through
  company invitation`; it MUST NOT create a second application.
- **FR-032**: Account existence MUST cause no intentional difference in invitation
  response body, status code, member-list state, or processing path observable to the
  owner; no exact constant-time guarantee is required.
- **FR-033**: Product Web MUST retain the invite secret only in session-scoped browser
  storage after removing it from the URL, restore an interrupted signup/verification
  flow after reload, and delete it after acceptance, explicit cancellation, or expiry.
- **FR-034**: Members and invitation surfaces MUST define accessible empty, loading,
  validation, delivery-pending, failed, forbidden, and recovery states; every action
  MUST be keyboard-operable with visible focus, programmatically determinable names,
  and status/error announcements that are understandable with assistive technology.
- **FR-035**: Company names, display names, email addresses, and provider diagnostics
  MUST be escaped or sanitized for their output context; raw provider diagnostics MUST
  never be shown to users.
- **FR-036**: Inspecting a usable invitation MUST name the invited email address to the
  holder of that invitation secret, and invite-bound registration MUST present that
  address as the account email without offering it for editing. Inspecting an unusable
  invitation MUST name neither the company nor the address.

### Domain and Traceability Requirements

- **DR-001**: Membership invitations are administrative access Evidence; they do not
  create SourceRecords, Documents, or business Reality state. All business records
  accessed after acceptance retain the existing Source → Evidence → Reality chain.
- **DR-002**: Invitation MUST link directly to its company and invited normalized
  address; membership MUST retain only the shortest authoritative links to company and
  account and MUST NOT duplicate invitation, document, line, or source relationships.
- **DR-003**: Invitation and membership identity MUST use opaque identifiers; email and
  company name are matching/display values and MUST NOT become relationship identity.
- **DR-004**: Invitation and membership lifecycle state is stored administrative truth;
  expiry and usable status MAY be derived from stored terminal transitions and time.
- **DR-005**: Every repository query and application operation involving invitations or
  memberships MUST receive or resolve explicit company authority and enforce it before
  returning or mutating data.
- **DR-006**: Audit history and retryable notification intent MUST be durable and MUST
  not be reconstructed from mutable member-list presentation state or provider logs.

### Key Entities

- **Company Invitation**: Company-scoped administrative evidence that one normalized
  email may join one company before a deadline; records lifecycle and actor context but
  is not membership.
- **AppUser**: Global account identity whose verified email must match the invitation.
- **Tenant Membership**: Direct authority connecting one account to one company as
  owner or member, with active or removed lifecycle.
- **Security Audit Event**: Immutable record of invitation and membership transitions,
  actors, outcomes, and occurrence times.
- **Notification Intent**: Durable request to deliver an invitation message, including
  retry and delivery outcome without becoming membership authority.

## Success Criteria *(mandatory)*

- **SC-001**: In acceptance testing, 100% of new-account and existing-account invites
  expose identical inviter-visible responses and pending states until acceptance.
- **SC-002**: From opening an already delivered invitation link, a recipient can
  complete sign-in or invite-bound registration, email verification where needed,
  explicit acceptance, and opening the company in under five minutes, excluding only
  time spent waiting for the verification email.
- **SC-003**: In retry and concurrency tests, each company/account pair finishes with at
  most one membership and each company/address pair with at most one usable invitation.
- **SC-004**: Revoked, expired, replaced, mismatched-address, archived-company,
  suspended-account, and already-used invitations grant zero unauthorized memberships.
- **SC-005**: A removed member loses access on the next protected company request while
  retaining access to every other actively joined company.
- **SC-006**: Every delivery failure leaves a visible retryable invitation outcome and
  no invitation email is intentionally sent before that outcome is durable.
- **SC-007**: Cross-company tests disclose zero foreign member identities, email
  addresses, invitations, membership states, or company records through every exposed
  interface.
- **SC-008**: Every FR and DR has an acceptance scenario and executable proof or an
  explicit review-approved reason why automation is not appropriate.

## Assumptions and Dependencies

- The product owner approved this specification for planning on 2026-09-02.
- Invitation lifetime defaults to seven days and resend cooldown to 60 seconds; abuse
  controls may add stricter bounded rate limits during planning without changing the
  recipient journey.
- Existing owner memberships remain authoritative. Ownership transfer and owner removal
  require a later feature specification.
- An invitation becomes company authority once created; loss of the original inviter's
  membership alone does not revoke it.
- Removing membership does not revoke the global account session because one account
  may belong to other companies; membership is rechecked on every protected request.
- Company-owned MCP/API credentials are not personal membership credentials and are not
  automatically revoked when a member is removed.
- Transactional email delivery and a retry-capable worker/runtime are dependencies for
  reliable notification; provider-specific design belongs in the plan.
- Supported locale preference is used when known; otherwise the invitation is English.
- Delivery retry uses increasing delay over 24 hours; provider-specific scheduling
  details do not change recipient-visible semantics.
- Terminal invitation/delivery details are retained for 90 days, while minimal
  token-free security audits follow company lifetime.

## Open Questions

None. The product owner approved the recorded product choices on 2026-09-02.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-005 | US1 scenarios 1–6 | Owner authorization, new/existing account, invite-bound admission, matching-email, and blocked-account stories |
| FR-006–FR-012 | US2 scenarios 1–6 | Lifecycle, duplicate, expiry, resend, revoke, delivery-failure, idempotency, and concurrency stories |
| FR-013–FR-017 | US3 scenario 2; US4 scenarios 1–4 | Removal authorization, archived company, inviter loss, and reactivation stories |
| FR-018–FR-020 | US1–US4; edge cases | Audit completeness, notification content, secret storage, and leakage review |
| FR-021–FR-023 | US5 scenarios 1–3 | Cross-company, interface-parity, and Chat confirmation stories |
| FR-024–FR-025 | US3 scenarios 1–3; US4 scenarios 1–3 | Company-switcher and owner/member capability-boundary stories |
| FR-026 | US1 scenario 6 | Non-owner invitation-administration denial story |
| FR-027, FR-031–FR-032 | US1 scenarios 1–6 | Normalization, existing-application admission, and account-privacy stories |
| FR-028–FR-030 | US2 scenarios 1–6; delivery edge cases | Retry/outage, retention, invite/resend limit, and cleanup stories |
| FR-033–FR-035 | US1; US3; UI edge cases | Reload recovery, accessibility/state, and contextual escaping evidence |
| FR-036 | US1 scenarios 1–3 | Invited-address disclosure to the secret holder and invite-bound registration stories |
| DR-001–DR-006 | All stories | Constitution, shortest-link, tenant-query, audit, and notification durability review |
