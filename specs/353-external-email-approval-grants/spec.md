# Specification 353: Provider-independent external email approval grants

**Language**: English

Status: Draft follow-up; not implemented by PR #332.

## Context and Intent

### Problem

An external application may already obtain a person's exact email approval. A
second independent approval in Reality duplicates that interaction. A bearer
executor token or an agent's assertion cannot prove a person approved it.

### Scope

Define a reviewed contract usable equally by Atlas, Grok applications and other
clients. Reality retains one Decision recognizing a verified external approval,
then uses the normal authenticated claim/report/history chain.

### Non-Goals

No implementation or temporary approval bypass; no vendor-specific trust, mailbox
transport, inferred human identity, retroactive approval or weakening of uncertain
send reconciliation. Retention/deletion is a separate lifecycle design.

## User Scenarios & Testing

A person approves an exact draft once in an external application. Reality verifies
the grant and records its independently verifiable provenance. An executor with
a separate credential can claim only that approved snapshot. Altered recipients,
body, attachments, company, expired/revoked trust or replay must be refused.
Historical outbound capture remains external evidence without matching approval.

## Requirements

- **FR-001**: Bind grants to tenant, exact canonical message digest, attachment hashes,
  business context, stable grant ID, approval time and identified approver.
- **FR-002**: Verify issuer trust and the approver's current company authority through
  configured server-owned trust; never accept a client-supplied identity unchecked.
- **FR-003**: Separate grant verification from proposing/executing credentials and
  retain original grant evidence without exposing secrets or private signing keys.
- **FR-004**: Prevent cross-company replay, duplicate execution and grant reuse for
  another proposal; define expiration/revocation and transactional acceptance.
- **FR-005**: Show external verified attribution distinctly from directly observed
  Reality approval and from unverified captured evidence. Keep original issuer
  and actor provenance; do not label a token issuer as the acting person.
- **FR-006**: Preserve existing claim ownership, exact payload checks, unresolved
  dispatch reconciliation and tenant-scoped evidence navigation.

## Assumptions and Dependencies

Agree canonical digest compatibility, issuer registration/key rotation, supported
proof format, mapping of external approvers to company membership, assurance and
revocation semantics with integrating applications before an implementation plan.
These are explicit design dependencies, not permission for accepting arbitrary
unsigned claims. Tests must cover malicious/mistaken claims and replay alongside
the ordinary Atlas/Grok-independent business journey. No schema is authorized by
this draft; prove necessary persistence during the reviewed implementation plan.

## Success Criteria

Before implementation, a reviewed proof format, issuer/member trust model and
transactional replay design must exist. Acceptance tests must show that a valid
grant leads to one explainable Decision/claim and altered, expired, revoked,
foreign-company or reused grants fail without effects. This draft claims no
implemented behavior or verified grant recognition.

## Requirement Traceability

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-001–FR-006 | Exact single external approval with independent execution and attribution | Follow-up implementation tests after proof format/trust review; intentionally not implemented or tested in PR #332 |
