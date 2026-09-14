# Idea: Company membership invitations

**Status:** Brainstorming — not approved, not an implementation specification
**Working title:** Invite people to a company

## Problem

An existing company member needs a simple way to invite another person into the same
company. The invited person may already have a Reality account or may need to create
one first. Both cases use the same invitation and explicit-acceptance flow so neither
the response nor the later member list exposes whether an email address was already
registered.

The first version should deliberately avoid a complex permissions system. Active
members are equally entitled to use the company's product functions.

## Step 1 product concept

Account identity and company access are separate concepts:

```text
User account
    |
    +-- Company membership --> Company A
    |
    +-- Company membership --> Company B
```

One account may belong to multiple companies. A membership grants access only to its
company and must never weaken tenant isolation.

### Unified invitation flow

1. An active company owner enters an email address in `Settings → Members`.
2. Reality creates a pending, expiring invitation and sends an email stating that the
   recipient was invited to the named company.
3. The invitation link asks an existing account holder to sign in or lets a new person
   register while retaining the invitation context.
4. The recipient authenticates and must have verified the invited email address.
5. The recipient explicitly accepts the invitation.
6. Reality atomically creates or reactivates the company membership and opens the
   invited company.

Registration alone must not grant access. Company access begins only when the valid
invitation is accepted for the verified invited address.

The inviter sees one neutral success response and the same pending invitation state in
both cases. The UI, member list, and public API do not reveal whether the address
already had an account. A valid company invitation permits invite-bound registration
even when public signup is disabled and replaces the general early-access application
for this invited access. It does not override a suspended or rejected account state.

## Equal access in step 1

Step 1 has one normal product-access role, `member`, while retaining the existing
`owner` role as a minimal safety boundary.

- Every active member can use the same operational, financial, ordinary configuration,
  and explainability functions within the company.
- Only an active owner can invite additional members or manage pending invitations.
- An account may switch between all companies in which it has an active membership.
- Membership never grants access to another company's records.
- Owner-only actions are limited to company lifecycle and recovery, secret-bearing AI
  configuration, MCP/API credential management, and membership actions that could
  leave the company without an active owner.
- Every company must retain at least one active owner.

Equal access does not mean unsafe company lifecycle behavior. Permanent company
deletion, removing the last active member, and other irreversible account-recovery
operations remain protected until their ownership and recovery rules are specified.
Future admin, accountant, operator, editor, or viewer roles are explicitly outside
step 1 and require separate proven workflows. Read-only access is not a flag on the
membership alone: it must be enforced consistently by shared services across Web,
CLI, API, MCP, Chat, exports, and background operations.

## Proposed member experience

For active owners, `Settings → Members` shows:

- active members;
- pending and expired invitations;
- an `Invite member` action;
- invitation status and expiry;
- actions to resend or revoke a pending invitation;
- an action to remove an active member, subject to the last-member safeguard.

The company switcher appears when an account belongs to more than one company. The
current company must always be explicit in the product context.

## Candidate lifecycle

```text
Invitation: pending -> accepted
                    -> revoked
                    -> expired

Membership: active -> removed -> active
```

An invitation is not a membership. Acceptance is an explicit mutation, is never
performed by opening a `GET` link alone, and is atomic and idempotent: repeated link
opens, email retries, or acceptance retries must not create duplicate memberships.
Re-inviting a removed member reactivates the existing membership rather than creating
a second identity or membership history.

If the recipient creates an account through another route before opening the invite,
the still-valid invitation can be accepted after login and email verification.

## Security and tenancy invariants

- Invitations and memberships are company-scoped and use opaque identity.
- Invitation tokens are random, single-purpose, expire, and are stored only as secure
  hashes. Raw tokens may appear only in the delivered link.
- Resending rotates the token and invalidates every older link for that invitation.
- Acceptance requires an authenticated account with the verified invited email address.
- Invite, resend, revoke, accept, and remove operations are audited with actor and UTC
  timestamp.
- Duplicate active memberships and duplicate usable invitations for the same company
  and normalized email address are prevented.
- Email lookup never becomes an external account-discovery endpoint.
- Invite creation, member-list state, response shape, and observable timing do not vary
  based on whether the recipient already has an account.
- Email delivery must not occur before the membership or invitation transaction has a
  durable, retryable outcome. Invitation and email-outbox records are committed in one
  transaction; delivery happens afterward and is safe to retry.
- All reads and writes use tenant-scoped application services. Web, CLI, MCP, and Chat
  must not implement alternative membership rules or write directly through the ORM.
- Chat-based invitation or removal is a mutation and requires explicit confirmation.

## Email behavior

One invitation template is sufficient for step 1: “You were invited to {company}.
Create or sign in to your account to continue.” The call to action uses the expiring
invitation link. Existing and new accounts receive the same template.

Messages should use the recipient's supported locale when known and a safe English
fallback otherwise. They must name the company and provide a way to report an
unexpected invitation or membership.

## Important edge cases

- The email address is already an active member of the company.
- A usable invitation for the same company and email already exists.
- The invitation expired, was revoked, or was already accepted.
- The account email changes before acceptance.
- Two requests accept the same invitation concurrently.
- A removed member is invited again.
- An inviter loses company membership before the recipient accepts.
- The company is archived while an invitation is pending.
- The recipient account is suspended or rejected.
- Resend races with accept, or revoke races with accept.
- A membership is removed while tenant-scoped requests or sessions are active.
- The invitation opens while a different account is already signed in.
- The email provider temporarily fails or delivers the same message more than once.
- A token could leak through logs, analytics, browser history, or a referrer.
- A person belongs to several companies with the same human-readable company name.
- A member attempts to remove themselves or the final active member.

## Explicit non-goals for step 1

- custom roles or per-feature permissions;
- viewer/editor or other read/write permission tiers;
- approval chains for invitations;
- domain-wide automatic membership;
- SCIM, SSO group synchronization, or directory provisioning;
- guest access limited to selected records;
- invitation of mailing lists or shared identities;
- transfer of legal company ownership;
- silently merging accounts that use different email addresses.

## Questions for a future specification

1. What expiry period and resend limits should invitations use?
2. Which company name and inviter identity may safely appear in email before login?
3. Which exact existing operations are owner-only lifecycle, recovery, secret, or
   credential actions?
4. Do pending invitations remain valid when their inviter loses membership, or does a
   removal-for-abuse workflow revoke that inviter's outstanding invitations?
5. Which tenant-bound credentials or active contexts must be invalidated immediately
   when a membership is removed?

When this idea is selected, the specification should first audit the existing account,
company-owner, platform-admission, session, email-delivery, and tenant-lifecycle
behavior. It should then prove the smallest membership and invitation model without
weakening current tenant or company-deletion safeguards.
