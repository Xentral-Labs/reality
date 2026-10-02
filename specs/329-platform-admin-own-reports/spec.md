# Feature Specification: Platform Admin Access to Own Private Reports

**Feature Branch**: `codex/platform-admin-own-reports`
**Created**: 2026-10-02
**Language**: English
**Status**: Approved scope
**Input**: User approved platform-admin access to every visible company and explicitly required that private reports always remain private per user.

## Context and Intent

### Problem
The company switcher shows companies accessible through platform administration without identifying that access. The private report library then requires company membership even for the administrator's own reports. Visibility therefore appears to imply a membership that does not exist.

### Scope
Allow active platform administrators to use their own private analytics in accessible companies and make the access basis visible. Ordinary members retain existing access.

### Non-Goals
No access to another user's private reports, questions, requested analyses or sealed proposals. No automatic membership, owner assignment, new token authority, company lifecycle/credential administration change, schema expansion or practice-company admission change.

## User Scenarios & Testing

### User Story 1 - Own private analytics across companies (Priority: P1)
An active platform administrator opens My reports in a visible business company without becoming a member.
**Why this priority**: Removes the contradiction between accessible company data and the user's own private workspace.
**Independent Test**: Exercise private-report lifecycle as an administrator without membership.
**Acceptance Scenarios**:
1. Given an active platform administrator without membership, listing and creating their own reports succeeds without creating membership.
2. Given their own report, reading, renaming, duplicating and deleting it follows existing author, confirmation and revision rules.
3. Given their own requested analysis or private proposal, existing author-scoped journeys work under the same access basis.

### User Story 2 - Private means private per user (Priority: P1)
A report author retains exclusive access even against platform administrators and company owners.
**Why this priority**: Explicit user privacy requirement.
**Independent Test**: Compare two users across two companies and all private surfaces.
**Acceptance Scenarios**:
1. Given another author's private artifact, an administrator cannot list, read, change or obtain readable sealed details for it.
2. Given a nonmember ordinary user, private analytics still refuses access; an active member continues to access only their own artifacts.
3. Given a suspended user, removed admin privilege or stale administrator principal, current access is refused unless a current active membership independently permits it.

### User Story 3 - Explain company access (Priority: P2)
The company switcher distinguishes membership from platform-admin access.
**Why this priority**: Visible access should explain why a company is available.
**Independent Test**: Browser scenarios for owner, member, administrator without membership, and development identity.
**Acceptance Scenarios**:
1. Given a real owner/member membership, its role is shown truthfully.
2. Given administrator access without membership, the switcher and company card identify Platform admin access without labeling the user a member or owner.
3. Given an ordinary nonmember or development identity without an authenticated admin, no administrator role is inferred merely from company visibility.

### Edge Cases
Inactive account, revoked admin privilege, stale principal flags, foreign company/report IDs, removed membership, same-name companies, tenant switching, read failures, practice companies, delegated MCP access and confirmation replay retain their existing restrictions.

## Requirements

### Functional Requirements
- **FR-001**: Active platform administrators MUST be able to use their own private analytics in visible business companies without membership.
- **FR-002**: Every private list, detail, operation, requested analysis and readable proposal MUST remain scoped to the current user's authorship and selected company; platform administration MUST NOT bypass authorship.
- **FR-003**: Current account activation and administrator authority MUST be checked from authoritative state; stale claimed admin status MUST NOT grant access. Ordinary users still require active membership.
- **FR-004**: The switcher and company cards MUST distinguish real owner/member roles from Platform admin access without fabricating membership.
- **FR-005**: Administrator access MUST NOT create membership or expand delegated tool permissions, proposal confirmer roles or company owner administration.
- **FR-006**: New presentation MUST be localized in English, German, Dutch and Spanish, and use current state on company switches and access rechecks.

### Domain Requirements
- **DR-001**: No schema or business evidence changes; existing opaque account, company and author identities remain authoritative.
- **DR-002**: All adapters MUST use the shared author-access service; business records and proposals remain company-scoped with existing confirmation and revision enforcement.

### Key Entities
Existing account activation/admin authority, company membership, report author, requested-analysis author and proposal author. Platform-admin access is an access basis, not a new membership.

## Assumptions and Dependencies
The user explicitly approved this scope on 2026-10-02 and confirmed that all private reports remain private per user. Existing specs 035, 323, 325 and 326 remain authoritative except the narrow administrator membership prerequisite superseded here. Existing company visibility and practice admission are unchanged. No production role or credential is issued to test the change.

## Success Criteria
- **SC-001**: An active administrator without membership can complete all existing own-report lifecycle scenarios in an accessible company.
- **SC-002**: All negative scenarios for foreign authors, foreign companies, inactive users and stale admin status refuse access without private disclosure.
- **SC-003**: Every supported language correctly identifies administrator access separately from owner/member membership.
- **SC-004**: Required verification gates pass and live read-only checks show the administrator's private library without a membership error.

## Repository Language

All repository content is English; conversation may use German. Lossless source payloads remain in their original language.

## Requirement Traceability

| Requirement | Acceptance evidence | Tasks |
|---|---|---|
| FR-001 | Admin own lifecycle and deferred worker/HTTP library | T003/T004/T008/T009 |
| FR-002 | Foreign author/company and sealed proposal refusal | T003/T004/T008 |
| FR-003 | Persisted admin, stale claim and revoked/inactive account | T003/T004/T008 |
| FR-004 | Real membership versus admin switcher/card labels | T005/T006/T008/T009 |
| FR-005 | No membership writes; unchanged owner/delegation/confirmation | T003/T004/T006/T008 |
| FR-006 | Four-language labels and current-response recovery | T005/T006/T008 |
| DR-001/DR-002 | Schema diff and shared author/deferred eligibility | T004/T007/T008 |
