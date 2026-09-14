# Feature Specification: Temporary Hosted Product Demo

**Feature Branch**: `codex/railway-demo-deployment`
**Created**: 2026-09-02
**Status**: Reviewed
**Language**: English
**Input**: "Publish Reality through a simple provider for a short-lived, independently reachable product demonstration while the permanent AWS deployment is still being built."

## Context and Intent

### Problem

The owner needs to demonstrate the authenticated Reality product to invited people over the next several days without keeping a development laptop online and without waiting for the permanent AWS environment. The existing repository defines deployable Web/API, Product Web, MCP, public Site, PostgreSQL, and object-storage boundaries, but it does not provide a smallest temporary hosted-demo profile.

### Scope

- Provide separate HTTPS URLs for the public Site, authenticated Product App, and authenticated MCP runtime.
- Link homepage account actions to the deployed Product App origin.
- Persist the demo's business records across application restarts.
- Run schema migrations before the application accepts traffic.
- Keep the database and internal application boundary unavailable from the public internet.
- Document exact setup, verification, shutdown, and cleanup steps for the temporary environment.
- Use anonymised or synthetic demonstration data only.

### Non-Goals

- Replacing or redefining the permanent AWS production architecture.
- Connecting third-party MCP clients with production credentials or granting broad tool permissions.
- Providing production availability, disaster recovery, high availability, or a service-level agreement.
- Connecting live Shopify, email, AI, payment, or accounting credentials.
- Preserving uploaded binary artifacts beyond the lifetime guarantees explicitly documented for the demo environment.
- Changing Business Reality domain behavior, schemas, or tenant rules.

### Existing Contracts

- [`README.md`](../../README.md) — deployable application boundaries and public URL contract.
- [`infra/README.md`](../../infra/README.md) — permanent AWS deployment remains the recommended production shape.
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) — shared application core and transport boundaries.
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md) — authenticated Product Web behavior and confirmation rules.
- [`docs/TEST_STRATEGY.md`](../../docs/TEST_STRATEGY.md) — integration, migration, and browser-facing verification expectations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open a hosted Reality demo (Priority: P1)

An invited evaluator opens the public Site, follows an account link to the Product App, signs in, and explores a prepared tenant without installing software or connecting to the owner's local machine.

**Why this priority**: This is the immediate demonstration outcome and the reason the temporary environment exists.

**Independent Test**: From a network outside the deployment environment, open the generated HTTPS URL, authenticate with a dedicated demo account, load the dashboard, and read a tenant-scoped operational page.

**Acceptance Scenarios**:

1. **Given** a running demo environment and a valid demo account, **When** an evaluator opens the HTTPS URL and signs in, **Then** the Product Web loads and tenant-scoped operational data is readable.
2. **Given** an unauthenticated browser, **When** it requests an authenticated product route, **Then** no tenant data is disclosed and the normal authentication flow is presented.
3. **Given** a healthy Product App and a private API deployment, **When** only the API is redeployed and its private address changes, **Then** the Product App discovers the current address without its own restart and resumes serving API requests within 30 seconds.

### User Story 2 - Restart without losing business records (Priority: P2)

The owner can restart or redeploy the application during the demonstration period without losing the prepared tenant and business records.

**Why this priority**: A short-lived hosted demo is useful only if routine application restarts do not erase its core state.

**Independent Test**: Create or load a known tenant record, restart the application services without deleting the managed data store, and verify that the same record remains available afterward.

**Acceptance Scenarios**:

1. **Given** prepared demo records, **When** application services restart, **Then** the records remain accessible after health is restored.
2. **Given** a schema migration failure, **When** a release is attempted, **Then** the new application version does not claim readiness and the failure is visible to the operator.
3. **Given** the private scheduler and worker services, **When** the repeat deployment completes, **Then** both run the same core revision, connect through PostgreSQL with Psycopg 3, emit their role-specific sweep heartbeat, and remain inaccessible from the public network.

### User Story 3 - Remove the temporary environment safely (Priority: P3)

After the demonstration, the owner can disable public access and identify all temporary resources that must be removed to stop access and billing.

**Why this priority**: Temporary infrastructure and credentials must not remain active unintentionally.

**Independent Test**: Follow the cleanup checklist, verify that the public URL no longer serves Reality, and confirm that no demo secrets remain active.

**Acceptance Scenarios**:

1. **Given** a completed demonstration, **When** the operator follows the documented shutdown procedure, **Then** public access stops and every billable resource is explicitly accounted for.
2. **Given** a revoked deployment credential, **When** it is reused, **Then** it cannot alter or redeploy the environment.

### Edge Cases

- The database becomes reachable later than the application process.
- Migrations fail or are run concurrently.
- The externally assigned URL changes before application configuration is updated.
- The application restarts while an evaluator is signed in.
- The API receives a new private network address while the Product App remains running.
- A request is sent directly to an internal service.
- The demo account or deployment token is accidentally exposed.
- Ephemeral file storage is cleared during redeployment.
- A second tenant is created and must remain isolated from the prepared tenant.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The deployment MUST expose the public Site and authenticated Product App through separate HTTPS URLs usable from an external network.
- **FR-001a**: Site login and signup links MUST target the configured Product App HTTPS origin.
- **FR-002**: The Product Web MUST reach the canonical Web/API runtime without exposing the database or relying on the operator's local machine.
- **FR-002a**: The Product Web proxy MUST re-resolve the configured private API hostname at runtime and MUST NOT require a Product Web restart after an API address change.
- **FR-003**: Business records MUST use persistent PostgreSQL storage and survive application restarts.
- **FR-004**: The release process MUST apply all pending schema migrations before the new application instance reports readiness.
- **FR-005**: Authentication MUST remain enabled, cookies MUST use secure hosted-environment settings, and no verification code or secret MUST be exposed in a public response.
- **FR-006**: Only Site, Product App, and authenticated MCP runtime MUST be public; PostgreSQL and Web/API MUST remain on private service networking.
- **FR-006a**: MCP MUST expose liveness and database-backed readiness while refusing anonymous protocol access.
- **FR-007**: Runtime secrets MUST be supplied outside version control and MUST NOT appear in build artifacts, logs, generated documentation, or committed configuration.
- **FR-008**: The deployment MUST expose a health signal that distinguishes a usable application from a failed migration or unavailable dependency.
- **FR-009**: The operator guide MUST describe initial deployment, URL discovery, demo-account preparation, smoke verification, log inspection, shutdown, credential revocation, and resource deletion.
- **FR-010**: The temporary profile MUST be visibly documented as a demo environment and MUST NOT supersede the permanent production architecture.
- **FR-011**: Uploaded artifact durability limitations MUST be stated explicitly; the demo MUST NOT imply durable evidence retention when using ephemeral storage.
- **FR-012**: The hosted demo MUST disable public account creation when no transactional email provider is configured, while preserving login for prepared accounts.
- **FR-013**: The repeatable Railway deployment MUST deploy the private scheduler and worker from the same repository revision as API/MCP, select only their allowlisted process roles, and fail unless each emits a successful database-backed sweep heartbeat.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality behavior is unchanged; the deployment transports and persists existing records without introducing a second business model.
- **DR-002**: Operational state remains derived from Reality records through existing application services and projections; deployment adapters MUST NOT introduce stored document status or alternate business calculations.
- **DR-003**: Every business read and mutation continues through tenant-scoped shared services; public routing MUST NOT bypass authentication, confirmation, or repository tenant enforcement.
- **DR-004**: No new business entity, relationship, typed external field, or persistence table is introduced by this feature.

### Key Entities *(when data is involved)*

- **Demo Environment**: The temporary hosted runtime and its externally reachable Product Web URL.
- **Demo Account**: A dedicated authenticated user authorised only for prepared demonstration tenants.
- **Deployment Credential**: A revocable secret scoped to managing the temporary environment.
- **Managed Data Store**: Persistent PostgreSQL storage for existing Reality records; it remains private and is not a new source of business truth.

## Success Criteria *(mandatory)*

- **SC-001**: An invited evaluator can open the HTTPS URL, authenticate, and reach a tenant dashboard within five minutes without installing software.
- **SC-002**: A controlled application restart preserves 100% of the prepared tenant and business records checked by the smoke test.
- **SC-003**: External checks find the two intended browser entry points and one authenticated MCP origin, and cannot connect directly to the API or database.
- **SC-004**: A failed migration prevents a false healthy result and is diagnosable from operator-visible status or logs.
- **SC-005**: The complete shutdown and cleanup procedure can be executed in under fifteen minutes using the operator guide.
- **SC-006**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The demo runs for days rather than serving production workloads.
- The owner has authorised a dedicated hosted project and supplied a project-scoped deployment token outside version control.
- The provider can build the repository's existing container definitions, supply private service networking, issue an HTTPS domain, and provide managed PostgreSQL.
- The owner accepts provider charges and will remove or suspend resources after the demonstration.
- Only anonymised or synthetic data is loaded.
- The permanent AWS work continues independently and remains authoritative for production deployment.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-002, FR-002a, FR-006 | US1 scenarios 1–3 | Proxy contract test, external HTTPS/private-boundary checks, and API-only restart smoke check |
| FR-003 | US2 scenario 1 | Record-before/restart/record-after persistence check |
| FR-004, FR-008 | US2 scenario 2 | Release and migration failure/readiness tests |
| FR-005, FR-007 | US1 scenario 2; edge cases | Hosted-auth configuration and secret-leak checks |
| FR-009–FR-011 | US3 scenarios 1–2 | Operator-guide contract test and manual cleanup rehearsal |
| FR-012 | US1 scenario 2; signup edge case | Hosted signup-disabled authentication test |
| FR-013 | US2 scenario 2; background-process edge cases | Deployment-script contract plus live scheduler/worker status and sweep logs |
| DR-001–DR-004 | All stories | Existing domain, service-boundary, and tenant test suites |

## Repository split amendment

- **FR-020**: Product deployments use the product checkout root for api, scheduler, worker, mcp, docs and app; the default never uploads the provider website.
- **FR-021**: Site-only or combined deployment requires an explicit separate site checkout containing apps/site/Dockerfile.railway. Validate every selected checkout before any upload.
- **FR-022**: A dry run prints each selected service, source checkout, commit and Dockerfile without authentication or side effects. Real deployment preserves ordering, background heartbeat checks and selected-surface health checks. Unrelated working directories must not change upload sources.

Acceptance: default product mode excludes site; site mode excludes product services; combined mode rejects a missing site root before uploading; running outside the checkout still uploads the correct root.
