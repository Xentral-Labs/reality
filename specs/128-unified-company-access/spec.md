# Unified company and member administration
**Language**: English
## Context and Intent
### Problem
Owners still leave the unified app to create companies and manage invitations. Users without a company cannot start in the new surface.
### Scope
Move existing company creation, company identity and membership administration into unified Settings. Owner approved this increment with “ok mach” after the proposed company/member migration. Existing company details are read-only; this increment does not invent editing APIs.
### Non-Goals
Company rename, role editing, archive/deletion, provider credentials, source setup and legacy retirement. No schema or business policy changes.
## User Scenarios & Testing
### US1 — Company entry (P1)
An active account with no company creates an empty company and enters its unified settings. An existing user can create another company and switch via the shell. Review shows the name before creation; no sample business records are created.
### US2 — Owner access administration (P1)
An owner reviews an email before sending an invitation, sees membership and delivery state separately, resends pending invitations, revokes pending invitations and removes ordinary members after confirmation. Cancel makes no request. Owners cannot be removed. Expired invitations can be resent using the existing service.
### US3 — Safe context and recovery (P1)
Ordinary members see an explanation without owner-only requests. Switching companies discards open reviews. Unknown write results block automatic retry and offer an explicit reload/check; a failed check keeps the block. Accepting an invitation lands in its exact company.
## Requirements
- **FR-001**: Provide a Company settings section with current name/opaque ID/role and New company, including an account with zero companies. Use existing createCompany and refresh bootstrap before selecting the returned ID.
- **FR-002**: Provide invite/resend/revoke/remove through existing API methods with an explicit contextual review, single-flight submission and cancel. Pending or expired invitations can be resent; only pending invitations can be revoked and only non-owner members removed.
- **FR-003**: Preserve backend authorization, bounded 500-member/invitation lists and separate invitation/delivery statuses. Never infer delivery from request acceptance or expose invitation secrets.
- **FR-004**: Rejected writes show an error; transport/server ambiguity blocks resubmission until an explicit successful read, with no claimed success or automatic replay. Company creation recovery must never infer identity from name; users choose an authorized company after refresh.
- **FR-005**: Keep tenant context in navigation and accepted invitation destination; unmount company-specific drafts on company change. Support English, German, Dutch, Spanish, keyboard use and mobile/dark layout.
## Assumptions and Dependencies
Existing active-account gate, membership services, transactional-mail outbox and auth acceptance flow remain authoritative. Tests use intercepted HTTP fixtures or isolated PostgreSQL; no real invitations are sent. Company lifecycle controls remain in supporting administration.
## Success Criteria
All five requirements have green browser/service evidence; new-company/member operations need no legacy screen. Existing settings preferences and owner boundaries remain green.
## Requirement Traceability
| Requirement | Story | Tasks | Proof |
|---|---|---|---|
| FR-001 | US1 | T001,T002 | unified-company-access-browser.mjs |
| FR-002 | US2 | T001,T003 | browser + test_membership_invitations.py |
| FR-003 | US2,US3 | T001,T003 | browser + existing membership/API authorization tests |
| FR-004 | US3 | T001,T002,T003 | browser error/recovery scenarios |
| FR-005 | US3 | T001,T004,T005 | browser + existing settings browser + localization audit |
