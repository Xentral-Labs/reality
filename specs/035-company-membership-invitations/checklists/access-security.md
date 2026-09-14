# Access Security Requirements Checklist: Company Membership Invitations

**Purpose**: Validate access, privacy, lifecycle, delivery, tenancy, and UI requirement
quality before implementation
**Created**: 2026-09-02
**Feature**: [spec.md](../spec.md)

`[x]` means a reviewer approved the quality of the written requirement; it does not
mean the behavior has been implemented. `$speckit-implement` reads but does not change
these markers.

## Requirement Completeness

- [x] CHK001 Are owner-authorized invite, resend, revoke, list, and removal boundaries all explicitly specified? [Completeness, Spec §FR-001, §FR-011–FR-013, §FR-026]
- [x] CHK002 Are recipient requirements complete for unknown, existing, pending, active, suspended, and rejected account states? [Completeness, Spec §US1, §FR-003–FR-005]
- [x] CHK003 Are every invitation and membership lifecycle state and permitted transition defined? [Completeness, Spec §Candidate behavior, §FR-006–FR-017]
- [x] CHK004 Are delivery-intent requirements complete for initial send, resend, retry, ambiguous provider outcome, terminal failure, and stale generation? [Completeness, Spec §FR-009–FR-010, §FR-018–FR-020]
- [x] CHK005 Are member-list requirements complete for active, pending, expired, empty, loading, and unavailable states? [Gap, Spec §FR-011]
- [x] CHK006 Are requirements defined for the recipient losing invite context during signup or verification? [Gap, Spec §US1]

## Requirement Clarity

- [x] CHK007 Is “normalized email” defined consistently enough to decide matching and uniqueness without provider-specific alias guessing? [Clarity, Spec §FR-001, §FR-007]
- [x] CHK008 Is the neutral outcome precisely bounded for duplicate invitations, existing members, and account-existence privacy? [Clarity, Spec §FR-002, §FR-007, §FR-011]
- [x] CHK009 Is the exact point at which seven-day expiry starts or resets unambiguous? [Clarity, Spec §FR-006, §FR-009]
- [x] CHK010 Is “eligible pending account” defined clearly relative to verification, platform admission, and explicit acceptance? [Ambiguity, Spec §FR-003–FR-005]
- [x] CHK011 Are “ordinary configuration” and the owner-only lifecycle, recovery, secret, credential, and continuity actions exhaustively distinguishable? [Clarity, Spec §FR-025]
- [x] CHK012 Is the observable recovery message requirement specific enough for expired, revoked, replaced, accepted, mismatched, and archived cases without disclosing protected data? [Clarity, Spec §US2 scenario 5, §FR-020–FR-021]

## Requirement Consistency

- [x] CHK013 Are owner-only administration requirements consistent across Scope, all stories, FR-001/FR-011–FR-013/FR-026, and the HTTP contract? [Consistency]
- [x] CHK014 Is invitation survival after inviter departure consistent with owner-only revocation and owner-removal being out of scope? [Consistency, Spec §FR-013, §FR-017]
- [x] CHK015 Are invite-bound admission requirements consistent with the continuing rule that registration or verification alone grants no company access? [Consistency, Spec §US1, §FR-003–FR-004]
- [x] CHK016 Is the requirement to share application behavior consistent with explicitly omitted CLI and external MCP operations? [Consistency, Spec §FR-022]
- [x] CHK017 Are audit requirements consistent with classifying access records as administrative Evidence rather than Business Reality events? [Consistency, Spec §FR-018, §DR-001, §DR-006]
- [x] CHK018 Are privacy requirements consistent between neutral owner-visible state and the recipient-specific information needed to complete acceptance? [Consistency, Spec §FR-002–FR-003, §FR-011]

## Acceptance Criteria Quality

- [x] CHK019 Can identical owner-visible behavior for existing and unknown accounts be objectively assessed across response, list state, and timing? [Measurability, Spec §SC-001]
- [x] CHK020 Does the five-minute completion criterion define start/end events and excluded email-delivery time sufficiently? [Measurability, Spec §SC-002]
- [x] CHK021 Are zero-unauthorized-membership and zero-cross-tenant-disclosure outcomes measurable for every named invalid state and interface? [Measurability, Spec §SC-004, §SC-007]
- [x] CHK022 Does “next protected request” define the removal-effect boundary without promising cancellation of already-running work? [Clarity, Spec §FR-014, §SC-005]

## Scenario and Edge-Case Coverage

- [x] CHK023 Are primary, alternate, exception, recovery, and concurrency paths covered for both new and existing recipients? [Coverage, Spec §US1–US2]
- [x] CHK024 Are accept/accept, accept/revoke, accept/resend, remove/reinvite, and worker-claim races all represented by requirements or scenarios? [Coverage, Spec §US2 scenario 6, Edge Cases]
- [x] CHK025 Are archived company, same-name company, wrong signed-in account, email change, self-invite, existing member, and no-remaining-company outcomes addressed? [Coverage, Spec §Edge Cases]
- [x] CHK026 Are requirements defined for owner departure when that owner has pending invitations but owner transfer/removal belongs to a later feature? [Assumption, Spec §FR-017, Non-Goals]
- [x] CHK027 Are rate-limit and abuse-control requirements bounded beyond the single 60-second resend cooldown? [Gap, Spec §FR-009, Assumptions]

## Security, Privacy, and Accessibility

- [x] CHK028 Are clear-token protections specified for URL handling, browser storage/history, logs, analytics, referrers, audit, delivery retry, and provider errors? [Security, Spec §FR-020]
- [x] CHK029 Are requirements explicit about reauthorizing the confirming human and revalidating stale target state for Chat execution? [Security, Spec §FR-023]
- [x] CHK030 Are tenant predicates and non-disclosure requirements defined for collections, records, mutations, relationships, audits, delivery jobs, and worker claims? [Security, Spec §FR-021, §DR-005–DR-006]
- [x] CHK031 Are keyboard, focus, validation, responsive, localization, and assistive-technology requirements defined for Members and invitation flows? [Gap, Spec §FR-019, §FR-024]
- [x] CHK032 Are requirements defined for sanitizing company names, display names, emails, and provider diagnostics in UI and email content? [Security, Spec §FR-018–FR-020]

## Dependencies and Assumptions

- [x] CHK033 Is the dependency on a continuously operated retry worker stated with an acceptable delayed-delivery behavior when it is unavailable? [Dependency, Spec §FR-010, Assumptions]
- [x] CHK034 Is latest-token-wins behavior explicitly accepted for ambiguous at-least-once provider delivery? [Assumption, Spec §FR-009–FR-010, §FR-020]
- [x] CHK035 Are retention expectations for invitations, delivery outcomes, and security audits specified or deliberately deferred with rationale? [Gap, Spec §FR-018]
- [x] CHK036 Are rollback requirements consistent with preserving access Evidence and refusing destructive downgrade after use? [Consistency, Plan §Rollout and Rollback]

## Review

- **Specification reviewer**: Product owner, approved 2026-09-02
- **Domain/architecture reviewer**: Product owner, approved 2026-09-02
- **Decision**: Approved after product decisions on 2026-09-02

## Notes

- Focus: formal pre-implementation access-security and privacy review.
- Audience/timing: pull-request/domain reviewer before task analysis and implementation.
- Depth: high because the feature changes authentication, tenant authority, email
  secrets, concurrency, and membership lifecycle.
- Assisted requirements review on 2026-09-02: 23 items satisfied; CHK004–CHK007,
  CHK010–CHK011, CHK019–CHK020, CHK027, CHK031–CHK033, and CHK035 require product
  decisions or specification additions before analysis.
- Product owner approved all three recommended decision groups on 2026-09-02. The
  resulting FR-027–FR-035 additions close every previously open checklist item.
