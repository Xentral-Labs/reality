# Specification 354: Provider-independent external email approval grants

**Language**: English

Status: Implementation authorized by the product owner for PR #332. No concrete
proof format was published in the PR discussion as of this review. This document
proposes v1 for Atlas, Grok applications and any independently operated client.

## Context and Intent

### Problem

A person already approves an exact email in an external application. Repeating
that approval in Reality adds friction. An executor token is not a human approval.

### Scope

Recognize an issuer-signed exact-proposal approval as one existing Reality
Decision, then retain the normal authenticated claim/report/history chain.
Server-controlled company-specific issuer/subject mandates supply the authority;
external people need not become Reality account members.

### Non-Goals

No mailbox transport, generic delegated approval, client-created trust, automatic
issuer discovery, identity provisioning, retroactive approval, unsigned grants,
or external grant approval of uncertain-send risk exceptions. Retention/deletion
and a company-owner trust-management UI remain separate designs.

## User Scenarios & Testing

### US1 — One exact external approval (P1)

An agent proposes a supplier email with durable attachments and business context.
Reality returns its proposal ID, transport fingerprint and approval digest. The
external application shows the normalized preview, observes the authorized
person's affirmative approval and signs that exact digest. A separately
permissioned client submits the grant; Reality verifies the configured issuer,
subject mandate, company, proposal, signature and times, then atomically records
one Decision and immutable original grant Source. A manual MCP token can submit
proof without being recorded as the approving person. Normal claim/report follows.

### US2 — Refuse invalid or stale authority (P1)

Altered contents/context/files, another company/proposal, unknown issuer/key/subject,
wrong algorithm/audience, invalid signature, unsigned assertions, excessive or
expired validity, revoked grants/keys/subjects and replay onto a new proposal fail
without effects. Revocation/expiration is rechecked before each claim, including
claim replay. Executed decisions retain historical attribution after revocation.

### US3 — Explain the approval (P2)

Inspector, Decisions and email history display externally verified approval,
issuer, opaque external subject, configured person label and original grant Source,
separately from a directly observed Reality person or an unverified outbound capture.

## Requirements

- **FR-001**: Use compact JWS with Ed25519 (`alg=EdDSA`), header
  `typ=reality-email-approval+jwt`, `kid`; reject unknown headers, duplicate JSON
  members, algorithm substitution and noncanonical base64url. Strict v1 claims:
  `version=1`, `iss`, `sub`, `aud=reality:email_dispatch`, `jti`, `tenant_id`,
  `proposal_id`, `approval_digest` (lowercase SHA-256), `decision=approve`,
  `human_approved=true`, integer UTC epoch `iat` and `exp`.
- **FR-002**: Return `approval_digest` of the complete normalized proposal input
  using `reality-email-proposal-v1` (SHA-256 of UTF-8 sorted-key compact JSON,
  ensure_ascii=false). Bind every supplied message field, file identity/hash,
  context, rationale, supporting evidence and risk snapshot. Clients sign the
  server-returned digest after showing and approving that normalized preview.
  Transport fingerprint remains distinct and unchanged.
- **FR-003**: Require server-owned `REALITY_EMAIL_APPROVAL_TRUST_JSON` registry:
  issuer public keys by kid; company mandates mapping opaque subjects to a
  configured display name; revoked grant IDs and `revoked_before` epoch per
  company/issuer. No wildcard companies/subjects, request-supplied keys, private
  keys, default trust or issuer network calls. Issuer authenticates the person and
  attests their affirmative approval; a signature proves that attestation, not
  independently observed human presence. Registry must only include issuers whose
  human-approval process the company has authorized. Maximum validity 600 seconds;
  at most 30 seconds future issue skew, no expiry grace. Removing keys/subjects or
  issuer/company trust revokes outstanding grants. Revocation cutoff rejects
  `iat <= revoked_before`. Rotation uses a new kid; old keys must remain configured
  until all desired outstanding grants expire.
- **FR-004**: `email_dispatch_accept_grant` is a separately permissioned confirm
  mutation, accepts only `proposal_id` and compact `grant`. It does not grant generic
  proposal approval. Under the shared company delivery lock and proposal row lock,
  validate before effects, accept only a proposed email authorization, authorize
  through the canonical email service, and commit original grant Source, decision
  attribution and dispatch atomically. Exact same valid grant/proposal replay
  returns its retained receipt. Within a company, stable issuer/jti cannot create a second decision
  or another immutable grant version; changed proof/rebound proposal is refused.
  Roll back all effects on any acceptance failure.
- **FR-005**: Extend the shared decision attribution reader with `external_grant`,
  containing recorded issuer, external subject, configured name, grant Source ID
  and approval time. Never label the submitting token/issuer as the acting person.
  Expose original proof through existing Source navigation; historical reads do
  not require current issuer trust. Bind attribution only through the settled
  decision's retained Source link. Retain the verified public key, kid, mandate and verification time in original grant Source metadata so historical proof can be independently checked after rotation; stored keys never supply current claim trust. No second attribution authority in email/UI.
- **FR-006**: Reverify retained proof and digest under claim lock before granting
  any instruction; keep executor ownership, business context, immutable source
  contents, attachment verification and reconciliation checks. Risk acknowledgements
  still require existing signed-in member/trusted-local approval, not an external
  grant. Outbound capture remains external_unverified; no retroactive link.

## Assumptions and Dependencies

The product owner requested a proposed format and implementation without waiting
for a vendor proposal. V1 is provider-neutral and deliberately supports one strong
algorithm already available through the existing cryptography dependency.
Deployment operators configure server trust only following company authorization;
external users are explicitly enumerated for email approvals, not provisioned as
Reality accounts. Trust changes must be deployed consistently to every API/MCP
process; no process may retain removed mandates. No new table or column: extend the existing channel check constraint to external_grant; the immutable
Source identity plus serialized delivery lock proves replay, and the existing
Decision output links to its grant Source. Future algorithms/remote revocation and
self-service trust management require a reviewed versioned extension.

## Success Criteria

A supplier story proves one external human approval, one Reality Decision/dispatch,
separate executor claim, complete evidence navigation and immutable replay.
Adversarial and concurrent tests prove invalid grants have no effects, revoked
proof cannot claim, and generic token approval/risk retry remains forbidden.
All required current-head PR checks must pass before completion is reported.

## Requirement Traceability

| Requirement | Scenario | Evidence |
|---|---|---|
| FR-001–004 | US1, US2 | test_external_email_approval_grants.py: proof, exact binding, invalid input, authority, lifetime, replay, concurrency and rollback |
| FR-005 | US3 | shared decision_attributions, email_history, UI decision sentence contract and browser story |
| FR-006 | US1, US2 | revoked/expired claim, executor report chain, risk and generic approval refusal tests |
