# Feature Specification: Platform Administration Overview

**Feature Branch**: `[036-platform-admin-overview]`
**Created**: 2026-09-02
**Status**: Approved for planning
**Language**: English
**Input**: "A simple first version of an admin panel for the environment-configured
administrator, showing accounts, companies, and whatever else matters."

## Context and Intent

### Problem

Reality bootstraps exactly one privileged account from `REALITY_PLATFORM_ADMIN_EMAIL`
and `REALITY_PLATFORM_ADMIN_PASSWORD`. That account currently reaches a single page,
`/admin/access`, which reviews access applications. Every other question an operator
must answer — who holds an account, which companies exist, whether the runtime is
configured, whether the schema is migrated, whether invitation email left the system,
whether projections are stalled — requires database or shell access.

Hosted deployments make the gap concrete: the operator is accountable for the instance
but has no console, so a stalled projection or an unset master key stays invisible
until a user reports damage.

### Scope

- Serve one platform overview to the environment-configured administrator only.
- Report deployment posture: runtime flags, applied schema revision against the shipped
  migration head, and whether required secrets are present.
- Report every account with status, company memberships, active sessions and login
  recency, plus account totals by status and the pending-application backlog.
- Report every company with membership counts by role, open invitations, recorded
  Business Event volume and last activity.
- Report the processing that fails silently: import jobs, projection checkpoints,
  invitation delivery attempts and live agent tokens.
- Report the most recent security audit events with actor and subject identity.
- Keep the existing access-application review reachable from the same shell.

### Non-Goals

- Reading, exporting or editing any tenant's business records through this surface.
- Impersonating an account, resetting a password, or editing account identity.
- Changing the existing platform-admin tenant API bypass in either direction; that
  decision is tracked separately in `docs/ideas/platform-admin-panel.md`.
- Company lifecycle actions, session revocation, or token revocation from this page.
- A second privileged role, per-panel permissions, or delegated platform access.
- Localizing the platform administration surface; it stays English, like the existing
  access-application page.
- Alerting, notification, retention or paging of the reported signals.

### Existing Contracts

- [`specs/003-tenant-access/spec.md`](../003-tenant-access/spec.md)
- [`specs/035-company-membership-invitations/spec.md`](../035-company-membership-invitations/spec.md)
- [`docs/ideas/platform-admin-panel.md`](../../docs/ideas/platform-admin-panel.md)
- [`docs/features/tenancy.md`](../../docs/features/tenancy.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Business Reality Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the Platform at a Glance (Priority: P1)

As the environment-configured administrator, I open `/admin` and see how the deployment
is configured, who has an account, which companies exist, and whether any processing is
stuck — without a database console.

**Acceptance**: The page reports deployment posture, account rows, company rows,
operations counts and the recent security trail in one response.

### User Story 2 - Detect a Misconfigured Deployment (Priority: P1)

As the administrator of a freshly deployed instance, I see immediately that the schema
is behind the shipped migration head or that the master key is unset, before a user
meets the resulting failure.

**Acceptance**: The overview compares the applied revision against the migration head
and reports the presence of each required secret.

### User Story 3 - Refuse Every Other Caller (Priority: P1)

As a product user without platform administration, my request for the overview is
refused, and the overview never discloses secret values to anyone.

**Acceptance**: A non-admin request is refused; the payload reports secrets as presence
flags only.

### Testing

`packages/reality-core/tests/test_platform_admin_overview.py` proves authorization,
payload content, the secret-disclosure limit and migration-drift reporting. Product Web
contract tests and the translation audit keep the surface within the existing browser
gates.

## Requirements

- **FR-001**: The platform overview MUST be served only to an authenticated account
  with platform administration, and MUST be refused to every other authenticated
  account.
- **FR-002**: The overview MUST report deployment posture including authentication
  mode, session-cookie posture, verification-code exposure, artifact storage, email
  provider, and the automatic admission slots used against the configured limit.
- **FR-003**: The overview MUST report the applied database revision, the shipped
  migration head, and whether the two agree.
- **FR-004**: The overview MUST report each required secret as a presence flag and MUST
  NOT disclose a secret value or any part of one.
- **FR-005**: The overview MUST report account totals by status, the pending
  access-application count, and the oldest pending application time.
- **FR-006**: The overview MUST list accounts with email, display name, status,
  platform-administration flag, email verification time, last login, creation time,
  active session count, and active company memberships with role.
- **FR-007**: The overview MUST list companies with name, identifier, creation time,
  archival time, active membership counts by role, open invitation count, recorded
  Business Event count, and last recorded event time.
- **FR-008**: The overview MUST report import job counts by status, the number of
  projection checkpoints that are not ready, invitation delivery counts by status, and
  the number of unrevoked agent access tokens.
- **FR-009**: The overview MUST report the most recent security audit events with event
  type, outcome, occurrence time, tenant, and the email of actor and subject.
- **FR-010**: The overview MUST NOT expose any tenant business record content; company
  reporting is limited to counts, states, identifiers and timestamps.
- **FR-011**: The platform administration surface MUST offer navigation between the
  overview and the existing access-application review.
- **FR-012**: Account and company listings MUST be bounded so that the overview stays a
  bounded read as the platform grows.

## Success Criteria

- **SC-001**: The environment-configured administrator answers "who uses this instance,
  and is it healthy?" from the browser alone, with no database or shell access.
- **SC-002**: A deployment whose schema is behind the migration head, or whose master
  key is unset, is visibly flagged on first load.
- **SC-003**: No secret value appears in the overview payload under any configuration.
- **SC-004**: A product user without platform administration cannot retrieve the
  overview.
- **SC-005**: The overview is one bounded request that does not grow unbounded with
  account, company or event volume.

## Assumptions and Dependencies

- Exactly one privileged account exists, bootstrapped from the environment; no second
  privileged role is introduced.
- The applied revision is read from the Alembic bookkeeping table, and the migration
  head is derived from the shipped revision files. A schema built directly from ORM
  metadata reports no applied revision, which is the expected test-suite state.
- Invitation delivery reporting depends on the durable delivery intent introduced by
  Spec 035.
- The surface reuses the existing platform-admin dependency, session cookie and
  administration page styling; no new authentication path is introduced.
- PostgreSQL remains the only supported database, so the revision probe may use
  PostgreSQL catalog functions.

## Requirement Traceability

| Requirement | Implementation | Executable proof |
|---|---|---|
| FR-001 | `packages/reality-core/src/reality/web/auth.py` (`admin_router`, `PlatformAdmin`) | `tests/test_platform_admin_overview.py::test_overview_is_refused_without_platform_administration` |
| FR-002, FR-005–FR-010 | `packages/reality-core/src/reality/services/platform.py` | `tests/test_platform_admin_overview.py::test_overview_reports_people_companies_and_operations` |
| FR-003 | `packages/reality-core/src/reality/services/platform.py` (`_database_revision`, `_expected_revision`) | `tests/test_platform_admin_overview.py::test_overview_flags_a_database_behind_the_shipped_migration_head` |
| FR-004 | `packages/reality-core/src/reality/services/platform.py` (`_configured`) | `tests/test_platform_admin_overview.py::test_overview_reports_secret_presence_without_disclosing_values` |
| FR-011 | `apps/web/src/Auth.tsx` (`AdminShell`) | `apps/web` contract suite (`npm run test:i18n`) |
| FR-012 | `packages/reality-core/src/reality/services/platform.py` (`USER_LIMIT`, `COMPANY_LIMIT`, `AUDIT_LIMIT`) | `tests/test_platform_admin_overview.py::test_overview_is_served_to_the_environment_configured_administrator` |
