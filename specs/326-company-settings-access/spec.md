# Feature Specification: Reliable Company Settings and Honest Access Presentation

**Language**: English

**Feature Branch**: `codex/fix-account-settings`
**Created**: 2026-10-02
**Status**: Approved
**Input**: The owner authorized fixing all discovered settings/access defects, adding necessary specifications, and completing review, merge and deployment autonomously during this session.

## Context and Intent

### Problem
The deployed owner account receives a server error from the shared AI/token settings read. Platform administrators inspecting companies without membership are incorrectly labeled members; their private report library reports a nonexistent report instead of explaining the membership requirement.

### Scope
Restore reliable settings reads and clear error states; accurately explain existing membership and private-report boundaries. Determine the shared settings failure with executable regression evidence before selecting its correction.

### Non-Goals
No permission grants, token creation in live accounts, credential replacement, weaker authorization, private-report administrator override, business-data changes, new database fields, or new infrastructure.

## User Scenarios & Testing

### User Story 1 - Read owner settings (Priority: P1)
An active company owner opens Agents & API tokens and AI configuration and sees their configuration safely.
**Independent Test**: API and browser tests load both views with current and historical configuration.
**Acceptance Scenarios**:
1. Given an active owner and valid configuration, opening either view succeeds without credential disclosure.
2. Given production HTTPS MCP/API origins without a separate issuer override, both settings reads succeed; invalid public MCP URLs remain rejected.
3. Given an ordinary authenticated company member without owner or platform-administrator privileges, the protected settings read remains denied. Existing platform-administrator and disabled-development-auth exceptions remain unchanged.

### User Story 2 - Understand company access (Priority: P2)
A user sees the role actually held in each company.
**Independent Test**: Render owner, member and missing-membership company cards.
**Acceptance Scenarios**:
1. Given owner/member membership, the corresponding role and existing actions remain accurate.
2. Given no active membership, the card explicitly states no company membership and offers no owner actions.

### User Story 3 - Understand private report access (Priority: P2)
A platform administrator without company membership understands why their private library cannot be used.
**Independent Test**: Compare library reads for an administrator without membership and an active member.
**Acceptance Scenarios**:
1. Given no active membership, listing private reports produces a stable membership-required explanation.
2. Given active membership, the private library works normally.
3. Given another author's report or another tenant, detail/change requests remain non-disclosing and denied.

### Edge Cases
Revoked membership, inactive user, invalid MCP origins, explicit issuer overrides, invalid listeners, genuine unrelated server failures, tenant switching and retry must preserve authorization and honest error states.

## Requirements

### Functional Requirements
- **FR-001**: Owner AI/token settings MUST load using the current catalog and configuration; the deployed shared failure MUST have a meaningful regression proof.
- **FR-002**: Displaying the MCP public address MUST validate only that address. The MCP runtime MUST use explicit issuer override, then configured API_URL, then local default, preserving production HTTPS and origin validation. Configuration reads MUST preserve credentials and permissions.
- **FR-003**: Company cards MUST distinguish owner, member and absent membership without inferring membership from visibility.
- **FR-004**: Private report library reads without active user membership MUST explain that requirement; private record existence MUST remain undisclosed. Membership refusal MUST be presented as an access state, not a technical loading failure. It MUST explain that a company owner can add the user or the user can switch companies, and offer an explicitly labeled access recheck using the current response. Genuine technical failures retain the normal error/retry treatment.
- **FR-005**: Owner, membership, tenant and author enforcement MUST remain unchanged; invalid or retired token permissions MUST never expand token authority.
- **FR-006**: New visible messages MUST be localized in all supported product languages; retry and company changes MUST use current responses.

### Data Requirements
- **DR-001**: No schema changes; existing configuration, memberships, secrets and tokens remain authoritative.
- **DR-002**: Reads MUST NOT replace or discard historical credential/permission values as a repair mechanism.

## Assumptions and Dependencies
The user's explicit session instruction approves this narrow defect scope and authorizes final merge/deployment. Existing membership, vault, MCP and private-report contracts remain authoritative. The settings API retains its existing platform-administrator exception; this does not confer company membership or private-report authorship. Actual deployed failure cause is a technical research question, not a product clarification. All code changes are isolated from unrelated concurrent work.

## Success Criteria
- **SC-001**: Both deployed owner settings dialogs display their configuration rather than a shared server error.
- **SC-002**: Missing memberships are never presented as Member; private libraries explain membership accurately.
- **SC-003**: Regression, authorization, frontend, spec, documentation and hosted CI gates pass before completion.

## Requirement Traceability

| Requirement | Planned proof | Tasks |
|---|---|---|
| FR-001 | Production settings API and settings browser | T003, T004, T011 |
| FR-002 | Public URL independence, canonical issuer, HTTPS rejection and discovery | T003, T004 |
| FR-003 | Owner/member/missing membership browser cards | T005, T006 |
| FR-004 | Library service/API denial and localized browser recovery | T007, T008, T009 |
| FR-005 | Author/tenant denial and existing approval/owner suites | T007, T008, T011 |
| FR-006 | Four-language browser scenarios and i18n audit | T005, T006, T009, T011 |
| DR-001 | Schema diff review and existing migrations CI | T002, T011, T012 |
| DR-002 | Settings regression performs reads only and no data repair | T003, T004, T012 |
