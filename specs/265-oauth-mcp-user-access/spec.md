# Feature Specification: OAuth MCP User Access

**Feature Branch**: `[265-oauth-mcp-user-access]`
**Created**: 2026-09-24
**Status**: Product/domain, architecture and security direction approved for implementation on 2026-09-24
**Language**: English
**Input**: "Allow a person to connect an MCP client by signing in as a Reality user instead of first creating a manual API token, select or create a company, and operate MCP with that user's authorized company context while following current market-standard MCP authorization."

## Context and Intent

### Problem

Reality's remote MCP endpoint currently requires a tenant administrator to enter the
Web product, create a named bearer token, select its tools, copy the clear token once,
and configure it in an MCP client. This is appropriate for unattended integrations but
creates unnecessary setup and secret-handling work when a person wants to use an
interactive MCP client under their existing Reality identity.

The current token subject is the company authority. It does not represent the human,
the connecting client, the user's current membership, or an explicit authorization
grant between them. Extending it by trusting a company identifier supplied in a tool
argument or by passing a Web session to MCP would weaken tenant isolation and make it
unclear whose authority a call exercised.

Interactive MCP access needs a standards-based sign-in and consent journey. A user
must be able to select exactly one authorized company, understand the access granted
to the connecting client, revoke that grant, and retain Reality's proposal and human
confirmation boundary. A user with no company also needs a safe path to the existing
confirmed company setup rather than a second MCP-specific creation implementation.

## Clarifications

### Session 2026-09-24

- Q: Should a new grant automatically include all tools that belong to the OAuth access classes requested by the client, including proposal and confirmation tools? → A: Preselect every currently eligible tool within the requested access classes; the user may deselect tools before consent, and consent never confirms a concrete business action.
- Q: Should a Sandbox receive the same complete MCP access as an ordinary company, including read, proposal and confirmation tools? → A: Yes. Remove the blanket Sandbox MCP prohibition; the same user, tenant, tool, proposal and explicit-confirmation controls apply.
- Q: Should the removed Sandbox restriction apply to both interactive OAuth grants and manually issued MCP tokens? → A: Yes. Both credential kinds may address a Sandbox under their otherwise unchanged authority and controls.

### Scope

- Let an interactive remote MCP client discover that Reality uses delegated user
  authorization and start a browser-based sign-in journey without a manually created
  Reality API token.
- Identify the signed-in user, the connecting client, the selected company, and the
  granted capabilities for every authorized MCP request.
- Let the user select one company from current active memberships during authorization.
- Let an eligible signed-in user with no suitable company use the existing confirmed
  company-setup choices. Any newly created ready company, including a Sandbox, may then
  be authorized under the same MCP access and confirmation rules.
- Present and record explicit consent for the client and the requested access.
- Preserve per-client tool restriction, immediate authorization checks, revocation,
  auditability, tenant isolation, proposal review, and explicit human confirmation.
- Retain manually issued MCP credentials for unattended integrations and controlled
  migration; distinguish them clearly from interactive user grants.
- Follow the interoperable authorization and discovery behavior expected by current
  remote MCP clients while retaining the dedicated MCP runtime.

### Non-Goals

- Replacing Reality's Web login, account verification, invitation, admission, company
  membership, or company-setup policies.
- Sending Reality browser session cookies, passwords, verification codes, or company
  API-token secrets to an MCP client.
- Allowing a client or tool argument to choose an arbitrary company or to change the
  company bound to an existing authorization.
- Treating sign-in or authorization consent as confirmation of a company creation or
  business mutation.
- Giving an MCP client broader permissions than the signed-in user currently holds.
- Removing manually issued MCP credentials or forcing unattended integrations through
  an interactive user journey in this feature.
- Creating an MCP-specific identity store, company service, membership model, business
  rule, proposal lifecycle, or persistence authority.
- Authorizing one access token across multiple companies or introducing a global
  cross-company MCP tool surface.
- Selecting a commercial identity provider or deciding deployment vendor topology in
  this specification; planning must choose the smallest conforming boundary.
- Adding third-party source credentials or upstream OAuth connections unrelated to
  authorizing the MCP client to Reality itself.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Spec-driven workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Agent interaction](../014-agent-interaction/spec.md)
- [Separate MCP runtime](../018-separate-mcp-runtime/spec.md)
- [Unified AI and MCP access settings](../131-unified-ai-access/spec.md)
- [Company setup and demo](../146-company-setup-demo/spec.md)
- [Company setup/demo durable contract](../../docs/features/company-setup-demo.md)
- [MCP read contracts](../../docs/features/mcp_reads.md)
- [Web product and AI/MCP boundary](../../docs/WEB_SPEC.md)
- [Deployable application boundary](../../docs/decisions/0005-frontend-backend-object-storage.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect an MCP client with my Reality account (Priority: P1)

As a Reality user, I can connect a compatible remote MCP client, sign in through
Reality, choose one company I may access, review the requested access, and begin using
authorized tools without creating or copying a manual API token.

**Why this priority**: Removing manual secret provisioning for an interactive person
is the primary user value and establishes the identity and tenant boundary required by
all other stories.

**Independent Test**: Start from a clean compatible MCP client with no Reality
credential, connect to the public Reality MCP endpoint, complete sign-in, select one
company, approve restricted read access, and execute one permitted read tool.

**Acceptance Scenarios**:

1. **Given** a compatible client with no Reality credential, **When** it connects to
   the public MCP endpoint, **Then** it can discover the supported authorization
   journey and direct the user to Reality sign-in without asking for a Reality API
   token.
2. **Given** a signed-in user with active membership in one company, **When** the user
   reviews the connection, **Then** Reality identifies the client, company and
   requested access before consent, and successful consent returns the user to the
   connecting client.
3. **Given** a signed-in user with active memberships in multiple companies, **When**
   the user authorizes the client, **Then** the user selects exactly one company and
   the resulting access cannot read or act in another company.
4. **Given** the user cancels sign-in, company selection or consent, **When** the client
   resumes, **Then** it receives no usable authorization and Reality creates no grant
   or business change.
5. **Given** an invalid, expired, incorrectly targeted or otherwise unusable
   credential, **When** it is presented to MCP, **Then** Reality denies the request
   without disclosing user, company, client, catalog or business data.

### User Story 2 - Exercise only the authority I granted (Priority: P1)

As a company member or owner, I need every MCP request to remain constrained by my
current membership, the selected company, the connecting client and the access I
approved.

**Why this priority**: Delegated login is unacceptable if it weakens existing tenant,
tool or human-confirmation controls.

**Independent Test**: Authorize two clients with different tool grants for one user,
then exercise permitted, ungranted, revoked-membership, wrong-company and mutation
cases and verify that only the exact permitted operations proceed.

**Acceptance Scenarios**:

1. **Given** a valid user grant for company A and selected read tools, **When** the
   client calls a permitted tool, **Then** the shared application tool executes as
   that user in company A and records attributable security context.
2. **Given** the same grant, **When** the client requests an ungranted tool or supplies
   an identifier owned by company B, **Then** access is denied or the object behaves as
   not found without cross-company disclosure.
3. **Given** the user's membership is removed, suspended or no longer sufficient,
   **When** a previously authorized client makes another request, **Then** the request
   is refused even if its credential has not reached its nominal expiry.
4. **Given** a read-only grant, **When** a client requests proposal preparation or
   approval/execution, **Then** the missing authority is reported without creating or
   executing a business change.
5. **Given** a grant that permits proposal preparation, **When** the client invokes a
   mutation-oriented tool, **Then** Reality creates only the existing reviewable
   proposal and does not infer human approval from login or consent.
6. **Given** a separately authorized confirmation attempt, **When** current role,
   grant, proposal and explicit-confirmation requirements are satisfied, **Then** the
   existing shared confirmation service decides and records the outcome; otherwise it
   refuses without partial execution.

### User Story 3 - Create my first company during connection (Priority: P1)

As an eligible signed-in user without a suitable company, I can create a company from
the connection journey and then authorize the MCP client for that company without
leaving behind duplicates or bypassing the existing setup policy.

**Why this priority**: User authorization alone does not solve first use when tenant
authority does not yet exist; the path must reuse the canonical company-setup contract.

**Independent Test**: Sign in as an eligible verified user with no company, review and
confirm one supported company setup, recover the result after a simulated lost
response, and authorize a read-only client for the single resulting company.

**Acceptance Scenarios**:

1. **Given** an eligible user with no active company membership, **When** company
   selection is required, **Then** the journey offers the same authorized setup
   choices and consequence descriptions as the canonical company-creation flow and
   identifies which choices can continue to an external MCP grant.
2. **Given** valid setup choices, **When** the user reviews but does not explicitly
   confirm company creation, **Then** no company, membership, demo profile or live
   source is created and MCP consent alone cannot create them.
3. **Given** an explicitly confirmed setup, **When** creation succeeds, **Then** the
   canonical service creates at most one company and owner membership for the request,
   and the authorization journey can continue only when that exact company is ready.
4. **Given** a lost or interrupted creation response, **When** the journey is resumed,
   **Then** Reality reconciles the existing request and never creates a second company,
   seed or live source.
5. **Given** a user who is unverified, ineligible, awaiting required admission, or not
   allowed to create the selected company type, **When** creation is attempted,
   **Then** the existing policy refuses it with an understandable next step and no
   partial authorization.
6. **Given** a setup that remains initializing or failed, **When** authorization
   resumes, **Then** the company is not represented as ready for MCP business tools and
   the existing recovery path remains authoritative.
7. **Given** a user creates or selects a Sandbox from the canonical setup choices,
   **When** setup completes, **Then** Reality permits an MCP grant for that Sandbox with
   the same user, tenant, tool, proposal and confirmation controls as any other company.

### User Story 4 - Inspect and revoke connected clients (Priority: P2)

As a user or company administrator, I can understand which MCP clients have access,
which user and company authorized them, what they may do, and revoke access without
handling their secret material.

**Why this priority**: Delegated access must remain governable after the initial
connection and must not turn short setup convenience into invisible standing access.

**Independent Test**: Create two user grants and one manual integration credential,
inspect their distinct metadata, revoke one user grant, and verify immediate denial for
that grant while the others continue according to their own authority.

**Acceptance Scenarios**:

1. **Given** one or more connected MCP clients, **When** an authorized user opens MCP
   access management, **Then** each grant shows its client identity, authorizing user,
   company, granted access, creation time, last-use time and revocation state without
   exposing credentials.
2. **Given** a user grant and a manual integration credential, **When** they are
   inspected, **Then** Reality distinguishes interactive delegated access from
   unattended integration access and applies each one's existing administration
   policy.
3. **Given** an authorized revocation, **When** it is confirmed, **Then** later use of
   that grant is denied while unrelated grants remain unchanged.
4. **Given** a company switch requested by a connected user, **When** the user chooses
   another authorized company, **Then** Reality requires a distinct authorization for
   that company rather than mutating the existing grant's tenant authority.
5. **Given** a removed user, archived company or terminated membership, **When** active
   grants are inspected or used, **Then** they cannot provide effective business
   access and their disabled state is explainable to authorized reviewers.

### User Story 5 - Preserve unattended integrations and interoperability (Priority: P2)

As an integration owner or operator, I can continue using explicitly managed
non-interactive credentials while compatible interactive MCP clients use standard
authorization discovery and both paths reach the same Reality tools.

**Why this priority**: Interactive access should reduce setup friction without
breaking existing enterprise agents or creating a second tool implementation.

**Independent Test**: Run the same permitted read through an interactive user grant
and a restricted manual integration credential, verify shared tool behavior and tenant
results, and verify that an unsupported client receives a safe actionable failure.

**Acceptance Scenarios**:

1. **Given** an existing active manual MCP credential, **When** this feature becomes
   available, **Then** the credential retains its current tenant and tool authority
   until separately revoked or migrated.
2. **Given** interactive and unattended credentials with equivalent company and tool
   permission, **When** each invokes a tool, **Then** both reach the same catalogued
   application operation while retaining distinguishable principals and audit context.
   This parity includes ready Sandbox companies.
3. **Given** a compatible MCP client, **When** it follows Reality's advertised
   authorization metadata, **Then** it can complete connection without Reality-specific
   secret-entry instructions.
4. **Given** a client that cannot perform the advertised interactive journey, **When**
   connection fails, **Then** Reality does not downgrade to anonymous or shared access
   and the user receives a safe explanation of supported connection options.
5. **Given** an authorization service outage while the MCP process remains alive,
   **When** new authorization is attempted, **Then** new connection fails visibly
   without invalidating unrelated already-revoked state or weakening token checks.

### Edge Cases

- The user signs in with no memberships, one membership, several memberships, a
  removed membership, or membership removal while the consent page is open.
- Two companies share the same display name; selection and authorization use opaque
  identity rather than human-readable names.
- The user changes account in the browser during authorization or has an unrelated
  existing Web session.
- The connecting client requests no access, unknown access, broader access after an
  earlier grant, or a tool removed from the current catalog.
- Authorization is cancelled, expires, is replayed, uses a mismatched callback, loses
  its final response, or resumes after the user has revoked the grant.
- A credential is validly issued but intended for another protected service, company,
  client or deployment environment.
- A company is archived or setup fails after creation but before client authorization.
- Concurrent company creation and authorization retries must not create duplicate
  companies, memberships, grants or business changes.
- Tool catalog changes must not silently expand an existing exact-tool grant.
- Clock skew, key rotation and authorization-service unavailability must fail safely
  without requiring disclosure of credential contents.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The public remote MCP service MUST advertise a standards-based delegated
  authorization journey that compatible clients can discover without prior Reality
  client configuration or a manually issued user token.
- **FR-002**: An unauthenticated or unusably authenticated MCP request MUST receive an
  authorization challenge suitable for starting or repairing that journey; access
  denial MUST occur at the protected-service boundary rather than as a successful tool
  result containing an authentication error.
- **FR-003**: Interactive authorization MUST authenticate through Reality's human
  account boundary and MUST NOT disclose the user's password, verification material,
  browser session credential or authorization credential to business tools.
- **FR-004**: Before consent, Reality MUST show the connecting client identity, signed-in
  user, selected company, client-requested coarse access classes and the exact tools the
  user is choosing to grant. The exact-tool selection MUST initially include every
  current tool whose access class fits the requested scopes, and the user MUST be able
  to deselect individual tools before consent. Cancellation MUST create no effective
  grant, company or business change.
- **FR-005**: Each interactive authorization MUST bind one user, one client, one company
  and an explicit access grant. It MUST be valid only for the Reality MCP service for
  which it was issued and MUST NOT authorize company selection through tool arguments.
- **FR-006**: Company choices MUST be limited to current active memberships visible to
  the signed-in user. Same-name companies MUST remain distinct by opaque identity.
- **FR-007**: Effective authority for every call MUST be the intersection of current
  user status and company membership, current company policy, the client grant, the
  requested tool's access class and operation-specific service policy. Stale identity
  or membership authority MUST NOT survive solely because a credential remains
  unexpired.
- **FR-008**: Interactive grants MUST support explicit least-privilege access. Existing
  read, propose and confirm distinctions and exact-tool restrictions MUST remain
  enforceable. MCP clients request coarse scopes; Reality MUST preselect the current
  tools in those requested scopes and MUST show that exact selection before consent.
  The user MAY reduce it but MUST approve a nonempty exact-tool subset. A later catalog
  change MUST NOT silently add a tool to an existing exact-tool grant.
- **FR-009**: A request for more access than an existing grant provides MUST require a
  new user decision. It MUST NOT silently broaden the existing grant or substitute an
  unrelated company authorization.
- **FR-010**: Reality MUST validate credential issuer, intended protected service,
  validity period, client binding where applicable, revocation state and required
  authority before dispatching a tool. Invalid credentials MUST fail without identity,
  tenant, catalog or business-data disclosure.
- **FR-011**: User-grant credentials MUST be short-lived. Continued access beyond their
  validity MUST require a bounded renewal mechanism that rechecks the grant and current
  user, membership and company eligibility; renewal material MUST be revocable and
  unavailable to business tools.
- **FR-012**: Read tools MAY execute immediately within their effective authority.
  Mutation-oriented tools MUST preserve the existing proposal-first behavior, and
  neither authentication nor connection consent MUST count as explicit confirmation of
  company creation, proposal approval or business execution.
- **FR-013**: Company creation offered during connection MUST reuse the canonical
  company-setup options, validation, admission, confirmation, idempotency, readiness,
  retry and recovery behavior. The MCP adapter MUST NOT create a parallel company or
  membership path. Every ready company type exposed by canonical setup, including a
  Sandbox, MAY continue to an external MCP grant under the same authorization rules.
- **FR-014**: A created company MUST become selectable only for its authorized owner
  and MUST not be exposed as operationally ready before the existing setup contract
  reports readiness. Resuming authorization MUST reuse the exact recovered setup
  result.
- **FR-015**: Authorized users MUST be able to inspect and explicitly revoke interactive
  client grants without seeing credential material. Revocation, user disablement,
  membership loss and company archival MUST prevent subsequent effective access.
- **FR-016**: Changing companies MUST create or select a distinct company-bound grant;
  Reality MUST NOT rewrite the tenant authority of an existing grant or MCP session.
- **FR-017**: Existing manually issued MCP credentials MUST remain independently
  revocable and retain their existing tenant/tool meaning during migration. Management
  views and audit evidence MUST distinguish unattended integration credentials from
  interactive user grants. Manual credentials and interactive grants MUST both be
  permitted for ready Sandbox companies; credential kind MUST NOT change Sandbox
  eligibility.
- **FR-018**: Interactive and unattended access MUST dispatch the same catalogued
  application tools and services. No MCP authorization or transport component may
  perform direct business persistence or implement alternative business rules.
- **FR-019**: Security evidence MUST attribute authorization, use, denial, scope
  elevation, renewal and revocation to the available user, client, company and grant
  identities without recording clear credentials or business payloads as security
  metadata.
- **FR-020**: The authorization and consent journey MUST provide safe, actionable
  outcomes for cancellation, expiry, unsupported clients, inaccessible companies,
  authorization-service failure and interrupted company setup; none may fall back to
  anonymous, shared or broader access.
- **FR-021**: Interactive authorization MUST follow the current MCP authorization
  discovery profile and applicable OAuth security best practices, including protection
  against authorization-response interception, replay, client impersonation,
  authorization-server confusion and credentials issued for another resource.
- **FR-022**: The feature MUST define an explicit compatibility baseline for supported
  MCP clients and a migration path for client registration approaches during planning;
  a compatibility fallback MUST never weaken FR-005, FR-007, FR-010 or FR-021.

### Domain and Traceability Requirements

- **DR-001**: This feature changes access authority, not business evidence. Source →
  Evidence → Reality is not entered by authentication or consent; any subsequently
  authorized business tool MUST preserve its existing traceability chain unchanged.
- **DR-002**: The shortest true access relationships are user → membership → company
  and client grant → user/company/access. The feature MUST NOT duplicate company or
  source references onto business records merely to record MCP access.
- **DR-003**: Every business read, proposal and confirmation MUST receive company
  authority derived server-side from the verified principal and MUST continue through
  the shared tenant-scoped service/repository path. Cross-company access behaves as not
  found or is refused without disclosure.
- **DR-004**: Company creation MUST remain an account-scoped confirmed platform action
  until it creates the company and owner membership. Subsequent business records are
  governed by the created company's tenant scope; an authorization grant is neither a
  business record nor an alternative company identity.
- **DR-005**: Authorization state and security audit evidence MUST describe access and
  decisions only. They MUST NOT become operational authority, document status, derived
  Reality, or a substitute for proposal and execution receipts.

### Key Entities

- **Human account**: The authenticated person. Identity alone grants no company data;
  effective access also requires current company membership and a client grant.
- **Company membership**: The current relationship assigning a user a role in one
  company; it remains the authority for whether the user may act there.
- **MCP client identity**: The stable identity of the software requesting delegated
  access, shown to the user and bound to the grant.
- **Interactive client grant**: Revocable authorization connecting one user, one MCP
  client, one company and explicitly approved access. It is access-control state, not
  business evidence.
- **User MCP credential**: Short-lived proof presented by a client for one protected
  Reality MCP service and resolved to the interactive grant; clear credential material
  is never persisted or displayed by Reality.
- **Manual integration credential**: Existing independently managed, tenant-bound MCP
  authority for unattended agents; retained as a separate credential class.
- **Authenticated principal**: Per-request security context containing the verified
  actor, client, company and effective authority used by shared application tools.
- **Company setup request**: Existing confirmed, replay-safe request that creates one
  company and owner membership and reports initialization readiness.

## Success Criteria *(mandatory)*

- **SC-001**: In a representative supported MCP client, a verified user can connect,
  sign in, select one existing company, approve read access and complete an authorized
  read without creating or copying a manual Reality token.
- **SC-002**: Across automated boundary tests, 100% of absent, malformed, expired,
  revoked, wrong-service, wrong-client, wrong-company and insufficient-access cases
  are denied before application-tool dispatch and disclose no foreign business data.
- **SC-003**: For a user with access to at least three companies, every authorized
  session and credential provides effective access to exactly one selected company;
  switching company requires a distinct authorization.
- **SC-004**: Membership removal, user disablement, company archival or explicit grant
  revocation prevents all subsequent tested business calls for that grant, including
  calls made before the credential's nominal expiry.
- **SC-005**: A cancelled company-creation journey creates zero companies. Repeated,
  interrupted or recovered submission of one confirmed request creates at most one
  company, one owner membership and one setup run, after which that exact company can
  be authorized.
- **SC-006**: In every tested mutation journey, connection consent produces zero
  business mutations; proposal access creates only the existing proposal, and execution
  occurs only after the existing separate confirmation requirements succeed.
- **SC-007**: Existing active manual MCP credentials pass their previous tenant and
  tool-authorization regression suite unchanged, while management and audit results
  unambiguously distinguish them from interactive grants.
- **SC-008**: At least two independently implemented compatible MCP clients complete
  authorization from the advertised metadata without Reality-specific manual-token
  instructions; unsupported clients fail without an insecure fallback.
- **SC-009**: An authorized reviewer can identify the client, user, company, granted
  access, creation, last use and revocation state for every interactive grant, while
  no stored or displayed audit/management value contains a usable credential.
- **SC-010**: Every FR and DR maps to acceptance evidence before implementation is
  declared complete, and all required security, service, MCP, company-setup and
  cross-tenant suites are green.

## Assumptions and Dependencies

- The phrase "OAuth server" means a standards-conforming authorization service used
  by remote MCP clients; user authentication may reuse Reality's existing account
  experience, but the final deployment boundary is a planning decision.
- Interactive clients use a browser-capable authorization journey. Unattended agents
  continue to use explicitly managed machine credentials in this feature.
- One company per interactive grant is the intentional safe default. Cross-company
  reporting or one token spanning several tenants requires a separate product and
  authorization specification.
- The existing user, membership, invitation, admission and company-setup services
  remain authoritative. This feature may expose them through a new access journey but
  does not redefine their eligibility decisions.
- Current company setup already requires explicit confirmation and replay-safe request
  identity. Those properties are dependencies, not new MCP-owned behavior.
- Standard MCP clients request coarse OAuth scopes rather than Reality tool names. The
  exact-tool grant is therefore a separate visible Reality consent choice. It starts
  with all current tools in the requested scopes selected, permits individual tools to
  be removed before approval, and never expands silently after approval.
- Exact tool grants remain the compatibility baseline. Planning may define friendly
  capability groups only if they deterministically resolve to reviewed current tools
  and never expand an existing grant silently.
- Current MCP authorization standards and widely deployed clients evolve. Planning
  must record the selected protocol version, client-registration compatibility and
  conformance evidence without weakening the stable product requirements above.
- No business schema expansion is authorized by this specification. Any account-level
  authorization persistence must be proven as the smallest auditable model in the plan
  and kept separate from tenant business tables.
- The dedicated MCP runtime remains a stateless adapter to the shared application core.
  Authorization availability and key material are deployment concerns; MCP does not
  become a second business backend.

## Open Questions

No unresolved product-scope clarification. Product/domain review must approve the
one-company-per-grant boundary, retained manual integration credentials, and the
separation between connection consent and mutation confirmation before planning.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 scenarios 1, 5; US5 scenarios 3–4 | Authorization discovery/challenge conformance and credential-isolation tests |
| FR-004–FR-006 | US1 scenarios 2–4 | Sign-in, company selection, consent cancellation and same-name-company journeys |
| FR-007–FR-010 | US2 scenarios 1–4 | Principal intersection, current-membership, tool-grant, audience and cross-tenant service tests |
| FR-011 | US1 scenario 5; US4 scenarios 3, 5 | Expiry, renewal, rotation, revocation and stale-authority tests |
| FR-012 | US2 scenarios 4–6; US3 scenario 2 | Read/propose/confirm business-story tests proving consent is not confirmation |
| FR-013–FR-014 | US3 scenarios 1–6 | Canonical setup parity, confirmation, replay, readiness and recovery tests |
| FR-015–FR-017 | US4 scenarios 1–5; US5 scenario 1 | Grant inventory/revocation tests and existing manual-token regression suite |
| FR-018 | US2 scenario 1; US5 scenario 2 | Application-tool parity and no-direct-persistence adapter test |
| FR-019 | US2 scenario 1; US4 scenarios 1–3 | Security attribution, redaction and audit lifecycle tests |
| FR-020 | US1 scenarios 4–5; US3 scenarios 4–6; US5 scenarios 4–5 | Cancellation, outage, unsupported-client and interrupted-setup journeys |
| FR-021–FR-022 | US1 scenarios 1–5; US5 scenarios 3–5 | Protocol/security conformance matrix across supported client-registration modes |
| DR-001–DR-005 | US2 scenarios 1–6; US3 scenarios 2–6; US5 scenario 2 | Domain-boundary review, tenant tests, traceability regression and persistence audit |
