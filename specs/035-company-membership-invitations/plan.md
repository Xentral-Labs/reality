# Implementation Plan: Company Membership Invitations

**Branch**: `[035-company-membership-invitations]` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)
**Status**: Approved for checklist and task generation
**Language**: English for all repository artifacts and review evidence.

## Summary

Add one owner-controlled, tenant-scoped invitation flow that is identical for existing
and new accounts. Persist a minimal invitation, retryable email-delivery intent, and
tenant-addressable security audit fields; reuse the existing unique membership row for
`active → removed → active`. One focused membership service owns authorization,
locking, state transitions, audit, and notification intent. HTTP, Product Web, and
confirmed internal Chat delegate to it. CLI and external MCP omit human membership
administration because neither currently carries an authenticated human owner.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript in Product Web
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI,
Typer, React/Vite; existing Resend/SMTP adapter
**Storage**: PostgreSQL; no new broker or cache
**Testing**: pytest unit/service/API/story tests; real multi-session PostgreSQL
concurrency/migration tests; frontend contracts, localization, build, and manual UI
**Project Type**: Shared Python core with HTTP/CLI/MCP adapters and React frontend
**Constraints**: UTC, opaque IDs, normalized email only for matching, token hashes only
at rest, tenant scope, service-level owner authorization, Chat confirmation
**Scale/Scope**: Low-frequency administration across the expected 5,000 tenants;
bounded lists; no fine-grained RBAC
**Unknowns**: None; decisions are resolved in [research.md](research.md).

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Invitations/audits are administrative Evidence, not business Source/Documents/Reality; access only authorizes existing flows. | PASS |
| Reality owns operational state | No fulfillment, stock, document, delivery, reservation, or finance state changes. | PASS |
| Proven schema only | Lifecycle, uniqueness, expiry, retry, audit filtering, role/status constraints, and worker claims are required by approved FRs. | PASS |
| Tenant + shared service boundaries | Every new row/query is tenant-scoped; one service owns authorization; foreign IDs are not found. | PASS |
| Spec/test traceability | All FR/DR groups map to named tests and expected initial failures below. | PASS |
| Explainable web behavior | Settings exposes authoritative access/delivery state; business Reality explanation is unaffected. | PASS |
| Smallest coherent design | Reuses membership/PostgreSQL/audit, omits RBAC/MCP/CLI admin, and adds no broker. | PASS |

Post-design re-evaluation: **PASS**. No exception or unresolved clarification remains.
The product owner approved this plan on 2026-09-02.

## Repository Structure and Layer Changes

```text
packages/reality-core/
├── migrations/versions/0030_company_membership_invitations.py
├── config/{command_catalog,data_model,tenant_isolation_catalog}.yaml
├── src/reality/
│   ├── db/core.py
│   ├── services/{memberships,notifications}.py
│   ├── tools/application.py
│   └── web/{api,app,auth,email}.py
└── tests/
    ├── test_membership_invitations.py
    ├── test_{user_access,master_data_api,application_tools,email_delivery}.py
    ├── test_{postgresql_integration,migrations}.py
    └── tenant_isolation/test_families.py
apps/web/src/{App.tsx,Auth.tsx,api.ts,localization.tsx,companies.css,auth.css}
apps/web/scripts/ux-configuration-contract.test.mjs
compose.yml
docs/{DATA_MODEL,WEB_SPEC,TEST_STRATEGY}.md
docs/features/tenancy.md
```

`services/memberships.py` owns rules/authorization;
`services/notifications.py` owns queue state. Provider calls remain in `web/email.py`.
API, auth, tools, the CLI worker, and React only adapt requests/results. The worker
receives the sender as an adapter dependency and never owns invitation authority.

## Design

### Reality flow

```text
owner principal
  → CompanyInvitation (administrative Evidence)
  → InvitationDelivery (retryable intent)
  → verified matching AppUser explicitly accepts
  → TenantMembership (direct User ↔ Tenant authority)
  → existing tenant-scoped Source → Evidence → Reality access
```

Invitation links directly to tenant and normalized email, not a pre-existing account.
Membership retains only tenant and user links and never gains an invitation FK. Typed
opaque audit subjects point to invitation, delivery, or membership. Names/emails never
become identity.

### Service and adapter flow

The membership service accepts an explicit principal (`user_id`, platform-admin flag)
and owns owner-only list/invite/resend/revoke, owner/platform-admin removal of
non-owner members, safe public inspection, matching-email acceptance/reactivation,
archived/account/privacy/cooldown rules, locks, audits, and delivery enqueue.
It also owns trim-plus-casefold normalization without provider alias rewriting,
rolling invitation/resend limits, existing AccessApplication admission, and cleanup.

Mutations use one transaction and lock in one order: tenant, invitation when applicable,
then membership. The coarse tenant lock is proportionate for low-frequency access
administration and existing PostgreSQL constraints remain the final backstop.

HTTP follows [contracts/http-membership-api.md](contracts/http-membership-api.md).
Email links place the secret in a URL fragment. Product Web removes it from browser
history immediately, retains it only in session-scoped storage for reload recovery,
deletes it on accept/cancel/expiry, and submits it only in request bodies. Invite-bound verification
proves email but creates no AccessApplication or admission-slot claim. Explicit accept
activates an eligible pending account and creates/reactivates membership atomically.
Suspended/rejected accounts remain blocked.

Internal Chat exposes owner-only mutations through the existing proposal workflow.
Proposal creation has no invitation/email effect; approval passes the confirming human
principal and rechecks owner authority and target state. External MCP and local CLI
omit membership administration under FR-022.

### Notification delivery

Invitation creation/resend commits invitation, audit, and delivery intent before
provider contact. A PostgreSQL worker claims due intents with row locking and a lease,
generates a fresh clear token in memory, commits only its hash/generation, sends it,
then records success or retryable failure. A timeout after provider acceptance may
produce duplicate email; retry rotates the token so only the newest link works. No
clear token or rendered body is stored. The existing image runs the worker as a Compose
polling process; PostgreSQL remains the only queue.
Retries use increasing delays for 24 hours and then expose `failed`; worker downtime
leaves durable `delivery pending` state. Terminal invitation/delivery rows are purged
after 90 days while token-free tenant audits remain until company deletion.

### Data and migration impact

Migration `0030_company_membership_invitations`:

1. adds nullable tenant, subject type/ID, and outcome to SecurityAuditEvent for company
   audit queries while preserving global auth audits;
2. validates then constrains membership role to `owner|member` and status to
   `active|removed`;
3. creates CompanyInvitation with timestamp/state checks, unique token hash, and partial
   unique pending tenant/email index, including `terminal_at` as the explicit retention
   anchor populated for accepted, revoked, and expired transitions;
4. creates InvitationDelivery with unique generation, due-work index, retry/lease
   timestamps, attempts, and sanitized provider result fields.

Elapsed pending invitations become expired under the tenant lock before replacement;
no time-dependent partial-index predicate is used. Membership transition times stay in
immutable audits because no approved scenario filters them. No invitation FK or
operational field is added to membership.

Downgrade refuses to discard invitations, deliveries, tenant access audits, member
roles, or removed memberships. With no new state it drops child delivery first, then
invitation, constraints/indexes, and nullable audit columns. Existing owner memberships
need no backfill.

### Failure, security, and tenant behavior

- Foreign/unknown tenant, invitation, membership, and token-derived subjects are not
  found without disclosure; same-tenant non-owner admin is forbidden with no effects.
- Duplicate create is neutral; member-list state never indicates account existence.
- Invite creation uses an account-independent path and enforces 20 newly persisted
  logical invitations per company and five resends per invitation in each rolling
  24-hour window. Neutral duplicate or active-member attempts do not consume creation
  quota; exhausted quotas produce an account-independent rate-limit response and
  recover automatically as counted events leave the rolling window.
- Accept is POST-only and locks/rechecks all authority. Same-account replay is success.
- Resend increments generation and invalidates older hashes; concurrency serializes.
- Removal changes only membership status. The global session/other memberships remain;
  the next protected tenant request is denied.
- Archived tenants reject every mutation in the service.
- Tokens/passwords/raw provider errors are redacted from logs, audits, and responses.
- Provider failure never rolls back an acknowledged invitation and remains retryable.
- Dynamic names, emails, and diagnostics are context-escaped; raw provider errors never
  reach owner or recipient UI.

## Test Strategy and Traceability

Tests are added before implementation where practical.

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-003, FR-006–FR-012, FR-026–FR-027, FR-030, FR-032 | unit/service | `test_membership_invitations.py`: owner guard, normalization, neutral path, limits, lifecycle, cooldown, rotation | Models/service absent. |
| FR-004–FR-005, FR-031 | auth/story | `test_user_access.py`: disabled-public-signup invite, verify without slot, existing application outcome, explicit accept, blocked accounts | Current auth enters normal admission or blocks signup. |
| FR-007–FR-009, FR-015–FR-017 | PostgreSQL concurrency | `test_postgresql_integration.py`: duplicate, accept races, remove/reinvite, worker double claim | Locks/constraints absent. |
| FR-013–FR-017, FR-021 | service/API/isolation | Membership/API/family tests: removal, reactivation, archive, inviter loss, 403/404 | No admin boundary exists. |
| FR-018 | service/migration | Audit completeness, tenant subject/outcome, redaction, guarded rollback | Audit lacks typed scope/subject. |
| FR-019–FR-020, FR-028–FR-029, FR-035 | adapter/security | `test_email_delivery.py`: escaped/localized template, report link, no leakage, retry/outage/retention/stale link | No template/consumer exists. |
| FR-022–FR-023 | tools/Chat | `test_application_tools.py` and Chat API: proposal-only, confirmation, owner reauthorization, no MCP/CLI exposure | Tools/principal absent. |
| FR-024–FR-025, FR-033–FR-034 | API/Web | Auth/API tests, frontend contract, reload/accessibility/manual responsive flow | Bootstrap role/UI absent. |
| DR-001–DR-006 | catalog/migration/review | Migration, model parity, command/tenant catalog, shortest-link diff review | New model/operations absent. |

Required final gates:

```bash
make spec-check
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

Concurrency/migration proofs use real PostgreSQL. Manual acceptance covers fragment
scrubbing, email links, both account cases, owner/member controls, stale tenant
selection, and desktop/mobile layouts in all supported locales.

## Rollout and Rollback

1. Deploy additive migration/code with notification worker disabled.
2. Verify owner/member reads and invite-bound auth routes.
3. Start one worker; observe due/retry/delivered counts and provider errors, then allow
   invite traffic. Row claims/leases keep multiple workers safe.
4. If invitations exist, roll back app code while retaining additive schema; older code
   still enforces active membership but cannot administer it.
5. Database downgrade is allowed only before new access state/evidence exists.

## Review Risks

- Invite verification must not bypass suspended/rejected state, create an application,
  or consume admission capacity.
- Raw tokens must avoid server access logs, retained history, analytics, referrers,
  audit JSON, provider errors, and persisted email content.
- Provider timeout creates at-least-once ambiguity; latest-token-wins must be tested.
- Retention cleanup must never remove pending invitations, memberships, or audit rows.
- Service and confirmed Chat execution must recheck owner authority.
- Clock-based expiry cannot be the partial-index authority; transition occurs in-lock.
- Migration must validate all existing role/status values before adding constraints.
- Owner controls in stale UI are convenience only; service enforcement is decisive.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
