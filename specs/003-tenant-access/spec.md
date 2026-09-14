# Feature Specification: Tenant Access and Isolation Baseline

**Baseline ID**: `003-tenant-access`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline the existing tenant lifecycle, human access, membership, workspace selection, and tenant-isolation behavior."

## Context and Intent

### Problem

Business users need authenticated access to company workspaces, while every business
record and operation must remain isolated from every other tenant. Product owners and
contributors need one baseline that separates platform identity, tenant membership,
company lifecycle, and business-data isolation without treating company names or other
human values as authority.

### Scope

- Email/password signup, email verification, sessions, and profile preferences.
- Automatic admission capacity and platform-administrator access review.
- Explicit user-to-tenant membership and protected API access.
- Tenant creation, listing, workspace selection, archive, restore, usage summary, and
  guarded permanent deletion.
- Tenant-scoped reads, writes, relationships, identifiers, and aggregate calculations.
- CLI tenant selection and Web company/workspace access behavior.

### Non-Goals

- Fine-grained permissions or user-defined roles inside a tenant.
- Enterprise SSO, social login, or external identity providers.
- Per-tenant databases or tenant-specific application deployments.
- Invitations, ownership transfer, or membership administration beyond current active
  membership creation.
- Defining business-specific access controls for individual Reality record types.

### Existing Contracts

- [`docs/features/tenancy.md`](../../docs/features/tenancy.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/CLI_SPEC.md`](../../docs/CLI_SPEC.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

The platform human identity is global and separate from tenant-scoped business data.
An active membership grants one user access to one tenant. The API boundary enforces
authentication, account state, and membership before tenant routes execute. Shared
services independently require tenant IDs for business lookups and mutations.

Tenant lifecycle is cross-tenant administration: active tenants appear in normal
workspace selection; archived tenants retain their data and can be restored. Permanent
deletion is a destructive exception available only after archival and two exact
confirmations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Access an Approved Company (Priority: P1)

As an approved user, I can sign in and access only companies for which I have an active
membership.

**Why this priority**: Tenant membership is the security boundary for the entire
business product.

**Independent Test**: Create users and tenants with different memberships, then verify
that protected tenant routes allow the assigned tenant and reject a foreign tenant
without exposing foreign business records.

**Acceptance Scenarios**:

1. **Given** an active user with an active tenant membership, **When** the user opens
   that company, **Then** the workspace is available.
2. **Given** an active user without membership in another tenant, **When** the user
   requests that tenant's protected route, **Then** access is denied.
3. **Given** an unauthenticated visitor, **When** the visitor requests a protected API,
   **Then** authentication is required.

### User Story 2 - Obtain Platform Access (Priority: P1)

As a new user, I can verify my email and either receive an automatic admission slot or
wait for a platform administrator's explicit decision.

**Why this priority**: A user must become an approved platform identity before any
company can be created or accessed.

**Independent Test**: Configure a bounded automatic-admission capacity, verify more
accounts than the capacity, and confirm that only the available slots activate while
the remaining application awaits review.

**Acceptance Scenarios**:

1. **Given** an unverified signup, **When** the correct unexpired verification code is
   submitted, **Then** the account is verified and enters the configured admission flow.
2. **Given** available automatic-admission capacity, **When** a user verifies their
   email, **Then** the user becomes active and the slot is consumed atomically.
3. **Given** exhausted or disabled automatic admission, **When** a user verifies their
   email, **Then** the account remains pending until an administrator approves or
   rejects the application.

### User Story 3 - Manage Company Lifecycle (Priority: P2)

As an authorized user, I can create, archive, restore, inspect usage of, and deliberately
delete a company without accidental loss.

**Why this priority**: Company lifecycle must preserve historical Reality by default
while still supporting an explicit destructive administrative action.

**Independent Test**: Create two tenants, archive and restore one, then archive and
permanently delete it using the exact company name and `DELETE` confirmation.

**Acceptance Scenarios**:

1. **Given** two active tenants, **When** one is archived, **Then** it leaves normal
   workspace selection but remains available to lifecycle administration and restore.
2. **Given** only one active tenant, **When** archival is attempted, **Then** the action
   is rejected until another tenant is active.
3. **Given** an archived tenant, **When** either destructive confirmation differs,
   **Then** permanent deletion is rejected.
4. **Given** an archived tenant and both exact confirmations, **When** deletion is
   executed, **Then** its tenant-scoped data and tenant record are removed.

### User Story 4 - Keep Business Data Isolated (Priority: P1)

As a company operator, I can use the same human names, SKUs, document numbers, and
external IDs as another tenant without collision or data leakage.

**Why this priority**: Shared PostgreSQL storage is safe only when identity,
relationships, queries, and aggregates enforce tenant scope.

**Independent Test**: Create duplicate human values in two tenants, attempt foreign
links and lookups, and verify that each tenant's calculations use only its records.

**Acceptance Scenarios**:

1. **Given** identical human values in two tenants, **When** both records are created,
   **Then** they receive different opaque identities and remain independent.
2. **Given** a foreign opaque record ID, **When** a tenant-scoped service tries to link
   or mutate it, **Then** the service returns not found without revealing foreign data.
3. **Given** records in two tenants, **When** an aggregate is calculated for one tenant,
   **Then** records from the other tenant do not affect the result.

### Edge Cases

- Two tenants have the same display name, making name-based CLI selection ambiguous.
- A membership becomes inactive while the browser session remains valid.
- An account is pending or rejected but still holds an old session cookie.
- Concurrent email verifications contend for the final automatic-admission slot.
- An archived tenant is referenced by an old workspace URL.
- Permanent deletion encounters rows in every tenant-scoped business table.
- A platform administrator accesses a tenant without an ordinary membership.
- Authentication is explicitly disabled for local/test operation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Protected application APIs MUST require an authenticated active user,
  except for explicitly public authentication and health routes.
- **FR-002**: A non-administrator user MUST access a tenant route only through an active
  membership for that tenant.
- **FR-003**: Signup MUST require accepted terms, email verification, and secure
  password/session handling before business access is granted.
- **FR-004**: Automatic admission MUST consume at most the configured number of slots
  atomically; additional verified users MUST remain pending approval.
- **FR-005**: Platform access review MUST retain the application, outcome, review note,
  reviewer, and decision time.
- **FR-006**: Approved users MUST be able to create a tenant and receive an active
  membership for it through the shared lifecycle boundary.
- **FR-007**: Active tenant selection MUST exclude archived tenants; archived tenants
  MUST retain their data and remain restorable.
- **FR-008**: The final active tenant MUST NOT be archived.
- **FR-009**: Permanent tenant deletion MUST require prior archival, the exact tenant
  name, and the exact confirmation word `DELETE`.
- **FR-010**: Cross-tenant reads, writes, and relationships MUST fail without exposing
  the foreign record.
- **FR-011**: Human-readable values MUST be reusable across tenants and MUST NOT serve
  as cross-tenant identity.
- **FR-012**: Every public business query and aggregate MUST enforce tenant scope and
  have executable isolation proof.
- **FR-013**: CLI tenant selection by a duplicated name MUST reject ambiguity and require
  the opaque tenant ID.

### Domain and Traceability Requirements

- **DR-001**: Tenant access is a foundation boundary; Source and Evidence are not
  required to establish user identity or membership, while all later Evidence and
  Reality records inherit the selected tenant authority.
- **DR-002**: Tenant and membership lifecycle states are stored security/administrative
  state; business fulfillment, stock, and financial state remain derived from Reality.
- **DR-003**: Tenant-scoped services MUST receive the tenant ID explicitly even after
  API membership enforcement.
- **DR-004**: Tenant, user, membership, and every business relationship MUST use opaque
  IDs; names are display or disambiguated lookup values only.
- **DR-005**: Company management MAY summarize bounded Source, Evidence, and Reality
  usage, but those counts MUST link to or be reproducible from tenant-scoped records.

### Key Entities

- **AppUser**: Global platform identity with verification, approval, profile, and
  administrator state.
- **UserSession**: Revocable browser session represented server-side only by a token
  hash and expiry/lifecycle timestamps.
- **AccessApplication**: Audited request and platform-owner decision for access.
- **AccessAdmissionCounter**: Serialized global capacity for bounded automatic approval.
- **Tenant**: Opaque company/workspace boundary with active or archived lifecycle.
- **TenantMembership**: Explicit user authority for one tenant.
- **SecurityAuditEvent**: Immutable security/account event separate from business events.

## Reality Applicability

- **Source**: Not applicable to platform identity; external identity providers are out
  of scope. Tenant business data received later remains lossless Source.
- **Evidence**: Access applications and security audit events are administrative
  evidence, not business Documents.
- **Reality**: Tenant-owned business primitives carry `tenant_id`; membership authorizes
  access but is not a business Reality record.
- **Shortest links**: Membership → Tenant and User; business record → Tenant. No human
  name or email is used as a relationship.
- **Stored/derived**: Account, membership, session, approval, and tenant archive states
  are stored. Usage summaries are derived from tenant-scoped records.
- **Shared boundary**: HTTP authentication/membership middleware plus tenant-explicit
  application services; CLI selection resolves an opaque tenant context.

## Success Criteria *(mandatory)*

- **SC-001**: All protected tenant routes reject unauthenticated users and users without
  membership, except explicitly authorized platform administrators.
- **SC-002**: Concurrent automatic admissions never activate more accounts than the
  configured capacity.
- **SC-003**: Archived tenants disappear from normal workspace selection while all
  tenant data remains available after restore.
- **SC-004**: Permanent deletion cannot occur without archival and both exact
  confirmations.
- **SC-005**: Duplicate human identifiers across tenants never collide or affect another
  tenant's calculations.
- **SC-006**: Every public business service/query family has a named cross-tenant
  executable proof or an explicit coverage gap.

## Assumptions and Dependencies

- Platform administrators may cross the membership gate for company administration as
  explicitly defined by the HTTP boundary.
- Authentication-disabled mode is a bounded deployment/test configuration, not a
  production authorization model.
- Membership role semantics beyond active access and the initial owner role remain out
  of scope.
- Permanent deletion is intentionally destructive and is not the normal historical
  lifecycle path.

## Open Questions

The owner approved this baseline on 2026-08-31. Fine-grained membership roles,
invitations, SSO, and ownership transfer remain non-goals until a future change spec.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-002 | Verified as-is | `docs/WEB_SPEC.md:8-14` | `web/app.py:protect_application_api` | `tests/test_user_access.py` | — |
| FR-003–FR-005 | Verified as-is | `docs/WEB_SPEC.md:8-14` | `web/auth.py` | `tests/test_user_access.py` | — |
| FR-006 | Verified as-is | `docs/WEB_SPEC.md:11`; `docs/features/web.md` | company API + `create_tenant` | `tests/test_user_access.py`; `tests/test_master_data_api.py` | — |
| FR-007–FR-009 | Verified as-is | `docs/WEB_SPEC.md:655-660` | `archive_tenant`, `restore_tenant`, `permanently_delete_tenant` | `tests/test_tenant_lifecycle.py`; `tests/test_master_data_api.py` | — |
| FR-010–FR-011 | Verified as-is | `docs/features/tenancy.md` | tenant-scoped service lookups | `tests/test_tenancy.py` and domain story tests | — |
| FR-012 | Verified as-is | `AGENTS.md`; `docs/features/tenancy.md`; `specs/019-tenant-isolation-coverage/spec.md` | `catalogs.py`; `config/tenant_isolation_catalog.yaml`; tenant-scoped public services and aggregates | `tests/test_application_catalog.py`; `tests/tenant_isolation/test_families.py`; full PostgreSQL suite | Spec 019 deterministic catalog maps 166 operations across six isolation classes |
| FR-013 | Verified as-is | `docs/CLI_SPEC.md` | `find_tenant` | `tests/test_cli_context.py` | — |
| DR-001–DR-005 | Verified as-is | Constitution; Architecture; Web Spec | tenant models, middleware, services, summaries | tenancy, lifecycle, access, and API tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-006 | US1–US2 | User access and API lifecycle tests |
| FR-007–FR-009 | US3 | Tenant lifecycle and company API tests |
| FR-010–FR-013 | US4 | Tenancy, CLI context, aggregate coverage audit |
| DR-001–DR-005 | All stories | Constitution and cross-layer evidence review |
