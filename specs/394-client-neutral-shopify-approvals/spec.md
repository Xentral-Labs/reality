# Client-neutral Shopify approval contracts

**Language**: English
**Created**: 2026-11-10
**Status**: Draft
**Scope approval**: Pending repository maintainer review; proposal only.

## Context and Intent

### Problem

The Shopify capabilities in specs 388-393 serve general business needs: retain a
received order, find existing references, prepare its meaning, and accept an exact
authorized order. However, the two external approval interfaces bind proof types
and approval-source attribution to one application identity. Another integrator
should not have to impersonate an unrelated application to use these capabilities.

### Scope

Define client-neutral contracts for existing-buyer mapping and order acceptance.
Identify external applications through explicit configured issuer trust and retain
their actual attribution. Preserve the existing business services, tool names,
tenant boundaries, permission checks and separation of submission from approval.

This PR changes documentation only. It neither changes a protocol nor authorizes
implementation, rollout or modification of retained records.

### Non-Goals

No new business capability, generic arbitrary-effect executor, identity provider,
trust-on-first-use, automatic issuer registration, approval bypass, schema
expansion, payment, inventory movement, fulfillment, deployment or live-data test.
No rewriting of historical sources, signed proofs, receipts or settled decisions.

## User Scenarios & Testing

### US1 - Connect independently implemented clients (P1)

A company administrator explicitly trusts an external issuer for one supported
purpose. Two independently configured synthetic clients can each submit eligible
proofs without adopting another client's identity or changing Reality code.

**Independent test**: Each client completes an isolated existing-buyer mapping
and an exact order acceptance through the same application tools and services.
Receipts identify the actual issuer, subject, submitter and authorization kind.

**Acceptance scenarios**:

1. Given two independently trusted issuers, each eligible proof is verified only
   against its own configured key, tenant, subject, purpose and allowed submitter.
2. Given an untrusted issuer or a valid proof for a different purpose or tenant,
   submission is refused without mapping or order effects.
3. Given a valid submitting token without separate approval authority, submission
   cannot turn the token holder into the approver.

### US2 - Keep retained history trustworthy (P1)

An administrator can still inspect and reconcile an existing approval and its
original result after the neutral contract is introduced.

**Independent test**: Before/after snapshots prove that existing source bytes,
proof digests, receipt identities and business records remain unchanged.

**Acceptance scenarios**:

1. Existing status and lost-response reconciliation return the same original
   result under current read permission; they never create another order.
2. Existing proofs retain their original format and attribution. No translation,
   re-signing or new approval is inferred from a format upgrade.
3. A cross-format replay cannot create a second mapping or accepted order.

### US3 - Revoke trust without losing evidence (P1)

An administrator can revoke an issuer or standing mandate without deleting the
evidence of previously authorized work.

**Independent test**: Revocation during a held operation prevents new effects;
authorized historical inspection remains attributable and does not renew authority.

### Edge Cases

Unknown proof version; overlapping key IDs across issuers; key rotation; expired
or future-dated proofs; changed source or references; stale policy; conflicting
human and standing claims; duplicate external order identity; lost response after
commit; revocation while waiting for locks; exhausted or revised standing limits.

## Requirements

- **FR-001**: Public approval contracts and newly written comments, identifiers,
  errors, documentation and fixtures MUST use operation or issuer terminology,
  with no application brand as a protocol requirement.
- **FR-002**: External trust MUST be explicit, tenant-scoped, purpose-bound and
  deny by default. Application identity MUST come from configured issuer trust,
  not a product-specific constant or an unverified caller-supplied label.
- **FR-003**: Buyer mapping and order acceptance MUST remain separate purposes.
  A signed proof MUST bind the exact reviewed operation and supported format;
  proof validity for one purpose MUST NOT authorize another.
- **FR-004**: Existing current-token, subject, tenant, source/version/hash,
  reference, review-expiry, policy, credit, calendar and concurrency checks MUST
  remain in force. A submitter MUST NOT become an approver by submitting a proof.
- **FR-005**: New approval evidence MUST record the actual external issuer,
  subject, submitter and authorization kind under a neutral source convention.
  It MUST preserve the original signed proof and its digest without inventing
  a local human actor. Secrets and signing keys MUST NOT enter public output.
- **FR-006**: Historical status, original-proof verification and unknown-outcome
  reconciliation MUST remain supported without rewriting immutable records or
  creating replacement effects. Compatibility MUST NOT silently enable new writes.
- **FR-007**: New submissions MUST use the neutral contract. Any temporary legacy
  submission support requires a separate explicit, bounded maintainer-approved
  compatibility decision; it MUST NOT be enabled by default or widen authority.
- **FR-008**: Human and finite standing authority MUST remain distinct. Format
  changes MUST NOT reset cumulative exposure, quota, replay identity, currency
  restrictions or revocation semantics.
- **FR-009**: CLI, agent and MCP routes MUST reuse the same application services.
  Existing Shopify REST ingestion and unrelated tools MUST remain compatible.
- **FR-010**: Implementation MUST update affected executable catalogs, generated
  documentation and frozen contracts, and pass the reviewed regression matrix.
  No implementation or rollout follows from approval of this draft's existence.

### Data Requirements

- **DR-001**: Keep Source -> Evidence -> Reality and existing opaque identities.
  Do not add operational status to documents or create new tables for renaming.
- **DR-002**: Preserve all retained proof/source bytes and business identities.
  Comparisons may establish eligibility; no derived amount becomes a new authority.
- **DR-003**: Evidence lookup MUST distinguish original formats and issuers without
  conflating records through source-namespace changes or display names.

### Key Entities

Issuer trust policy; purpose-bound external proof; exact reviewed operation;
human approval or finite standing mandate; immutable approval source; original
execution receipt. These are existing concepts, not proposed new business tables.

## Assumptions and Dependencies

There are no other known integrated clients today. This does not establish that
there are no retained approvals or external consumers. Maintainer review must
confirm that inventory before selecting a compatibility window. Specs 389 and 392
define the existing operation boundaries; spec 354 is a reference for external
issuer attribution, not permission to share authority across business purposes.
Neutral names and the compatibility approach in [review.md](review.md) are proposals,
not accepted wire contracts. Product and architecture acceptance belong to the
repository maintainer. Technical planning, tasks and implementation follow review.

## Success Criteria

- **SC-001**: Two independently configured clients complete both supported
  operations with their own identities and no client-specific Reality code changes.
- **SC-002**: All retained history in the compatibility fixtures remains identical,
  and every replay or reconciliation returns at most its original business result.
- **SC-003**: Every negative authority case creates zero unauthorized effects.
- **SC-004**: Existing ingestion and unrelated business journeys remain green.

## Requirement Traceability

All checks below are planned, not implemented or passed in this proposal.

| Requirements | Planned acceptance evidence |
| --- | --- |
| FR-001, FR-002, FR-005 | Two independent issuer fixtures; neutral vocabulary scan; exact attribution and secret-exclusion checks |
| FR-003, FR-004 | Wrong issuer/key/tenant/purpose/subject/token; stale source/review/reference; current policy/credit/calendar checks |
| FR-006, FR-007, DR-002, DR-003 | Historical fixture snapshots; old status and unknown reconciliation; cross-format duplicate and disabled-compatibility checks |
| FR-008 | Human/standing separation; revoked/revised mandate; same-mandate cumulative exposure across formats and trusted issuer/key rotation |
| FR-009, DR-001 | Shared tool/service paths; existing REST intake and unrelated business regressions |
| FR-010 | Frozen input/output contracts, catalog generation checks and complete required repository gates |
