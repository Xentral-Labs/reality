# Feature Specification: Retire legacy browser surfaces

**Feature Branch**: `retire-legacy-surfaces`
**Language**: English
**Created**: 2026-09-08
**Status**: Accepted scope
**Input**: Owner requested a new PR removing Playground and the old app after merging the unified app.

## Context and Intent

### Problem
The product still ships two obsolete interfaces and a temporary switch despite the unified app being accepted and merged.

### Scope
Make the unified app the sole operational interface. Remove obsolete screens, styles, and their presentation tests; preserve shared features and historical data. Translate old operational bookmarks to their current workspaces. Explain retirement at old Playground entries.

### Non-Goals
No database deletion, historical migration rewrite, sandbox conversion, deployment, new operational features, or removal of supported backend services. Existing protected Playground APIs remain available for historical runs and compatibility; they are not a second browser interface.

## User Scenarios & Testing

### User Story 1 - One application (Priority: P1)
An approved user opens the app and consistently gets the current interface.
**Independent Test**: Build without a feature flag and open Home, Orders and Inspector.
**Acceptance Scenarios**:
1. Given an approved account, when opening /app without a migration flag, then the unified shell loads.
2. Given an old warehouse or finance bookmark with a tenant, when opened, then the corresponding current register and tenant are selected without executing an action.
3. Given an unknown app route, when opened, then a clear unavailable-page message offers Home rather than silently choosing a different workspace.

### User Story 2 - Retire Playground safely (Priority: P1)
A user with an old Playground bookmark understands the retirement while saved records remain intact.
**Independent Test**: Open old entry/run links signed out and signed in; run existing sandbox security/history tests.
**Acceptance Scenarios**:
1. Given a Playground entry or run bookmark, when opened, then retirement is explained and the user can open the current app; no sandbox is created or replayed.
2. Given a pending account, when entering the operational app, then production approval remains required.
3. Given recorded sandbox runs and unknown outcomes, when this code is installed, then their data, identities and protected API access remain unchanged.

### User Story 3 - Maintain a coherent distribution (Priority: P2)
Maintainers build one UI and users follow current documentation links.
**Independent Test**: Production build plus route/browser and documentation checks.
**Acceptance Scenarios**:
1. The shipped bundle contains no old app or Playground workspace.
2. Exception catalog, authentication, translations and current app styling continue to work.
3. Build instructions and public documentation links describe the current app without a migration switch.

### Edge Cases
Signed-out bookmarks; pending or rejected accounts; trailing slashes; external or malformed return destinations; unsupported legacy pages; company identifiers; stale query parameters; invitation fragments; persisted sandbox history. Compatibility navigation never submits, confirms, rejects or retries a business action.

## Requirements

### Functional Requirements
- **FR-001**: The unified app MUST be the sole operational browser interface without an opt-in flag.
- **FR-002**: Recognized old operational bookmarks MUST resolve to documented current destinations, retaining tenant and compatible read context; unknown app paths MUST show an explicit unavailable state.
- **FR-003**: Playground browser entries MUST explain retirement and link to the app without starting or replaying work.
- **FR-004**: Stored business/sandbox records, historical migrations, shared services and existing protected backend contracts MUST remain intact.
- **FR-005**: Shared authentication, account approval, exception catalog, localization and styling MUST remain usable after deleting obsolete presentation code.
- **FR-006**: Build configuration, executable checks and current public links MUST target the sole app; tests specific only to deleted presentation MUST be retired with replacement route/boundary coverage.

## Success Criteria
- **SC-001**: All supported bookmark scenarios reach their documented destination without a business write.
- **SC-002**: No obsolete operational screen is reachable or included in the production browser distribution.
- **SC-003**: Existing history and security checks and retained app checks pass.

## Assumptions and Dependencies
The owner authorized removal and a new PR, not deployment or data deletion. The merged unified app is the accepted operational scope; rebuilding every experimental workflow is excluded. Existing sandbox APIs preserve historical access. Git history and the preceding deployment artifact provide rollback without a database operation.

## Requirement Traceability

| Requirement | Tasks | Evidence |
| --- | --- | --- |
| FR-001 | T003, T004, T009 | entry-routing, product-boundary and retirement-browser |
| FR-002 | T003, T004, T009 | entry-routing and retirement-browser |
| FR-003 | T005, T006, T009 | entry-routing and retirement-browser |
| FR-004 | T006, T009 | Unchanged migrations/services; full backend sandbox tests |
| FR-005 | T003–T007, T009 | Browser auth/catalog, localization/build, retained contracts |
| FR-006 | T007–T010 | Docs/site checks, sole-bundle assertion, diff review |

## Profile menu follow-up

The owner requested a bottom sidebar profile menu after the local cutover.
- **FR-007**: The sidebar MUST provide an account disclosure showing the current user, Profile & preferences, Documentation, Reality website and Sign out. Profile opens existing personal settings; external links use configured origins in new tabs. Sign out calls the existing logout endpoint once, navigates to login only on success, and retains an actionable error on failure. Keyboard dismissal and small-screen access must work.

Acceptance: open the bottom profile control; inspect identity and configured links; open personal settings; dismiss via Escape/outside click; simulate failed logout and retry successfully. Existing company settings remain separate.

| Requirement | Tasks | Evidence |
| --- | --- | --- |
| FR-007 | T012–T014 | retirement-browser profile/logout scenarios; frontend build/localization |

- **FR-008**: Company Settings MUST show only Company, Company access and AI configuration, defaulting to Company. Personal preferences MUST be a separate presentation reached through the profile menu, without company-setting tabs or an active Company Settings navigation marker. Existing direct personal-settings links remain valid. Acceptance: open profile preferences, verify no company tabs; choose Company Settings and verify Company is selected with no personal tab; reload both entries.

FR-008 is covered by T015, the routing contract and the profile browser scenarios.

- **FR-009**: Company Settings MUST list every company returned by the authorized bootstrap, including its name, opaque ID and role, mark the current company, and allow switching through the existing company context. Company creation MUST occupy a separate labeled area and preserve its review/confirmation flow. Acceptance: see both accessible companies, switch and reload with the new current marker, and open the separately labeled creation area without a write.

FR-009 maps to T016–T018 and retirement-browser company-list scenarios.

- **FR-010**: Each company MUST distinguish Owner from Member (no invented guest permissions). Owners get company-specific Users and Agents & API tokens entries; members get a clear ownership restriction. Agent token management MUST have a dedicated settings tab using existing MCP authorization/confirmation services; AI provider configuration stays separate. Switching management targets clears prior company context. FR-010 extends T016–T018 with owner/member and target-company browser assertions. This supersedes FR-008’s three-tab enumeration.

FR-010 navigation clarification: Company sidebar and page title use “Manage companies”; member companies show the company list and ownership guidance without offering owner-only tabs. Direct management bookmarks remain guarded.

FR-009 placement clarification: New company is a top-right action beside the Companies heading, opening a modal instead of an inline bottom form. Creation remains distinct from existing companies and preserves review, confirmation and uncertain-result recovery. Modal dismissal restores focus and is blocked while creation/checking is busy or unresolved.

## Final company-management interaction
**FR-011**: The company navigation entry and page title MUST be Companies. Company management is a task-scoped modal, titled with its task and target company. Manage users, Agents & API tokens and AI configuration MUST NOT change the active working company or navigate into application tabs. Only Switch company changes the working context. All management APIs use the chosen authorized company; owner guards remain in force. Existing direct management links open the appropriate guarded modal over the company list. Busy or uncertain mutations prevent modal dismissal. This supersedes FR-010’s top-level tab and automatic context-switch interaction. New company remains the top-right modal action. Acceptance covers member workspace → owned-company modal without URL/context change, correct API tenant, close/focus, direct member denial and explicit company switching.

## Commitment terminology copy correction
The Home primary CTA reads “Review commitments”, matching the already named Commitments register. Its existing Your work destination and delivery-commitment scope remain unchanged. Spec impact: terminology only; no navigation, calculation or business behavior changes. Other delivery labels require scope-specific review rather than mechanical replacement.

The accepted terminology correction also applies to the Home count label, Your work title/search/empty state/selection prompt, case back button and order commitment links. Your work explicitly explains its unchanged scope as open delivery commitments to customers. Actual delivery execution and hold labels remain unchanged. No service, filter, calculation or route changes.

## Initial open-work selection
**FR-012**: On a fresh Your work entry without an explicit commitment, the first row of the successfully loaded current-company result page is selected and its details opened automatically. Preserve explicit deep links, including unavailable IDs. Empty/failed lists select nothing. Initialization occurs once per mount so mobile Back to commitments can return to the list. Replace the URL history entry for automatic selection, without business writes or an extra Back step.

## Commitment register as the sole entry
**FR-013**: Remove Your work navigation and its duplicate list. Home commitment links open the Commitments register. Clicking a register row (or Enter/Open commitment) opens its existing operational detail as a full page within Orders & deliveries. Returning preserves filters, paging, sort, mounted table state and scroll position. Customer actions remain supported; supplier details expose receipt rather than customer shipping/reservation actions. Exceptions and legacy /app/work links resolve to the same detail, or the register when no ID exists. Unavailable IDs retain their error and a return path. This supersedes FR-012 automatic selection and the separate work list. No new business rules or records.

## Product wordmark consistency
**FR-014**: The visible product wordmark in the unified application shell MUST be `Reality`, matching authentication, Site and Docs. Lowercase `reality` remains valid for technical identifiers such as package names, commands, paths and storage keys.

Spec 146 supersedes the unified-app blanket refusal of owned practice companies. Authorized practice companies open in the unified app with a compact Sandbox badge beside the company name; existing server-side tenant and mutation policies remain authoritative. Retired /playground browser URLs remain retired, and no old workspace is reinstated.
