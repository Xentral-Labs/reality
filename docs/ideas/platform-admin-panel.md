# Idea: Platform admin panel

**Status:** Brainstorming — not approved, not an implementation specification
**Working title:** Platform operations console for the environment-configured owner

## Problem

Reality already knows exactly one privileged human: the account bootstrapped from
`REALITY_PLATFORM_ADMIN_EMAIL` / `REALITY_PLATFORM_ADMIN_PASSWORD`. That account owns
`is_platform_admin` and today sees a single page, `/admin/access`, which lists access
applications and the automatic admission counter.

Everything else the operator needs in order to answer "is this deployment healthy, and
who is using it?" currently requires `psql`, container logs, or the CLI: how many
companies exist, whether invitation emails actually left the system, whether
projections are stalled, whether import jobs are retrying, which MCP tokens are live,
and whether the runtime is configured the way the deployment intended.

The gap is sharpest on hosted demo deployments (`docs/RAILWAY_DEMO.md`), where the
operator has no shell and no database console but is still accountable for the
instance.

## What this idea is not

It is not a super-user view into tenant business data. Hard rule 8 says every business
table is tenant-scoped and every repository query enforces tenant scope. A platform
admin panel that renders a customer's documents, parties, or ledger would quietly turn
the platform owner into an unbounded reader of every tenant's reality.

The distinguishing question for every proposed tile is:

> Does the operator need this to keep the **platform** running, or to look at a
> **customer's business**?

Only the first belongs here. Counts, health, timestamps, and failure classes are
platform metadata. Payloads, names, amounts, and documents are tenant business content.

## An existing hole this idea should close

`packages/reality-core/src/reality/web/app.py` skips the company-membership check for
platform admins on every `/api/tenants/{id}/...` route. The platform admin can
therefore already read and write any tenant's business data through the normal product
API, silently and without a membership. That is a latent decision nobody made
deliberately.

Two coherent options, to be settled before specification:

1. **Closed:** the platform admin has no implicit tenant access. Support access
   requires an explicit, time-boxed, audited grant that creates a real membership and
   is visible to the company owners.
2. **Declared:** the bypass stays but becomes an explicit, catalogued isolation
   exception, and every request made under it writes a `SecurityAuditEvent` the panel
   surfaces prominently.

Either way, the panel is the natural place to show it, because it makes the privilege
visible instead of implicit.

## Proposed product concept

One page, `/admin`, reachable only for `is_platform_admin`, structured as a short
column of panels that each answer one operator question. It reads from existing
tables; no new business schema. The existing `/admin/access` page becomes one panel.

```text
/admin
  ├── Deployment          is this instance configured and reachable?
  ├── Access              who is waiting to get in?
  ├── People              who exists, and who is actually active?
  ├── Companies           what tenants exist, and how alive are they?
  ├── Delivery            did the emails we promised actually leave?
  ├── Processing          is anything stuck, retrying, or behind?
  ├── Agent access        which non-human credentials are live?
  └── Security trail      what privileged things happened recently?
```

### 1. Deployment

Answers: *is this instance wired up correctly?*

- Application version / build identifier and Alembic revision, with a warning when the
  database revision is not `head`.
- Configured surface URLs (`SITE_URL`, `APP_URL`, `API_URL`, `MCP_URL`, `DOCS_URL`),
  each rendered as a link so a misconfigured URL is obvious on sight.
- Runtime posture flags, name and effective value: `REALITY_AUTH_MODE`,
  `REALITY_COOKIE_SECURE`, `REALITY_AUTH_EXPOSE_CODES`, `REALITY_ARTIFACT_STORAGE`,
  `REALITY_EMAIL_PROVIDER`, `REALITY_AUTO_APPROVE_LIMIT`, `REALITY_BOOTSTRAP_TENANT_NAME`.
- Dependency reachability: PostgreSQL, object storage, email provider, MCP runtime —
  each as reachable / degraded / unreachable with the timestamp of the last check.
- Database pool ceilings (`REALITY_BACKEND_DB_POOL_SIZE` + overflow, MCP equivalents)
  next to the pool's current in-use count, so exhaustion is visible before it bites.

Presence, not secrets: show that `REALITY_MASTER_KEY` and `RESEND_API_KEY` are set,
never their values, never a prefix. A deployment that is missing one should say so
loudly, because encrypted credentials become unreadable without the master key.

### 2. Access

The existing `/admin/access` panel, unchanged in behavior: pending applications with
company, volume and role, approve/reject, and the automatic admission counter against
`REALITY_AUTO_APPROVE_LIMIT`.

Worth adding: the age of the oldest pending application, because a queue that nobody
reviews is the failure mode this panel exists to prevent.

### 3. People

Answers: *who exists on this platform?*

`AppUser` counts by `status` (`email_unverified`, `pending_approval`, `active`,
`rejected`), plus a searchable list with email, display name, status, company
memberships, `email_verified_at`, `last_login_at`, `created_at`.

Useful derived signals:

- Accounts stuck in `email_unverified` for more than a day — usually a mail delivery
  problem, not user hesitation.
- Active accounts with no company membership — approved but never onboarded.
- Active sessions per user from `UserSession`, and the ability to revoke them.

Actions worth considering, all audited: revoke sessions, resend verification, reject a
spam signup. Password reset and impersonation are deliberately excluded from the first
slice.

### 4. Companies

Answers: *what tenants exist, and are they real?*

Per `Tenant`: name, opaque id, `created_at`, `archived_at`, member count by role
(`owner` / `member`), open invitation count, and a coarse activity signal — the
timestamp and sequence of the newest `BusinessEvent`.

This is the panel where the isolation line matters most. Show shape, not content:
"1,284 business events, newest 3 minutes ago, 4 members, 2 open invitations" is
platform metadata. A list of that tenant's documents is not.

Lifecycle actions belong here — archive and unarchive a tenant — because the isolation
catalog already treats tenant lifecycle as platform-level authority.

### 5. Delivery

Answers: *did the mail we promised actually leave the building?*

`InvitationDelivery` already models this durably: `status` in
`pending / processing / retry / delivered / failed`, `attempt_count`,
`next_attempt_at`, `attempted_at`, `delivered_at`, `provider_message_id`,
`last_error_code`.

Show counts by status, the oldest item still not delivered, and the failed and
retrying rows with tenant, generation, attempt count and error code — never the
recipient's token, never the invitation link.

Access-decision and verification emails currently only log an exception on failure. A
delivery panel makes the case for giving those the same durable treatment, so that
"the customer never got the mail" becomes an answerable question.

### 6. Processing

Answers: *is anything stuck?*

- `ImportJob` by `status`, with attempt counts and the oldest pending job. Failed jobs
  show their error class and the owning tenant, not the source payload.
- `ProjectionCheckpoint` per tenant and projection: `last_event_sequence`,
  `projection_version`, `status`, and lag against the tenant's newest
  `BusinessEvent.sequence`. A projection that is `error` or thousands of events behind
  is the single most useful red light this panel can show.
- Total `BusinessEvent` throughput over the last hour and day, as a platform-wide
  number.

### 7. Agent access

Answers: *which non-human credentials can reach this platform?*

`McpAccessToken` per tenant: name, `token_prefix`, `allowed_tools`, `created_at`,
`last_used_at`, `revoked_at`. Never the hash, never a reconstructable token.

Highlight tokens that have never been used, tokens unused for a long time, and tokens
with unrestricted `["*"]` tool scope. Platform-level revocation belongs here, audited.

### 8. Security trail

Answers: *what privileged things happened, and who did them?*

The newest `SecurityAuditEvent` rows — `event_type`, `outcome`, actor, subject, tenant,
timestamp — filterable by type. This is where access decisions, membership removals,
token revocations, secret access (`SecretAuditEvent`) and any platform-admin tenant
access surface together.

The panel's own actions must appear in this trail. An admin console that is not itself
audited is a blind spot rather than an oversight tool.

## Design principles

1. **Read-first.** The first slice is almost entirely read-only. Every write it does
   add must be reversible or purely revocatory (revoke, archive, reject).
2. **Metadata, not business content.** Counts, states, timestamps, error classes. No
   payloads, no customer names beyond the tenant's own name, no amounts.
3. **Secrets are presence bits.** Configured / missing. Never values, never prefixes.
4. **Every panel answers one operator question** and says plainly when the answer is
   "healthy", so the page is scannable in five seconds.
5. **Self-auditing.** Panel actions write `SecurityAuditEvent` like any other
   privileged action.
6. **No parallel business rules.** The panel reads through services and read models,
   consistent with the web UI invariant; it does not grow its own queries into domain
   tables where a service already exists.

## Smallest plausible implementation shape

- A single `admin_router` group under `/api/admin/*`, already guarded by the existing
  `PlatformAdmin` dependency, returning one payload per panel.
- Read models in `reality/web/read_models.py`; no new tables, no migration.
- One `/admin` page in the existing web app, reusing the current `admin-page` styling
  and the existing routing branch in `Auth.tsx`.
- Env-derived values read once at request time and reduced to presence and posture
  flags before they leave the process.

## First useful slice

The three panels that answer questions the operator cannot answer today at all:

1. **Deployment** — configuration, migration revision, dependency reachability.
2. **Delivery** — invitation delivery states and failures.
3. **Processing** — projection lag and stuck import jobs.

Access stays where it is and moves into the shell afterwards. People, Companies, Agent
access and Security trail follow once the tenant-access question above is settled.

## Open questions

1. Does the platform admin keep implicit tenant API access, or does support access
   become an explicit, time-boxed, audited grant?
2. Is the panel part of the product web app, or a separate surface with its own URL and
   its own deployment, so it can be withheld entirely from a hosted demo?
3. Should tenant archival be reachable from here, or does it require a CLI confirmation
   step, given it affects a paying customer's whole workspace?
4. Which reachability probes are safe to run on request, and which need a cached
   background result to avoid turning a page load into a dependency fan-out?
5. Does an operator need a second privileged role (read-only observer) or is one
   environment-configured owner genuinely enough?
6. How much history does the security trail show before it needs paging and retention
   rules?

## Promotion trigger

Promote to a numbered specification when the tenant-access question is decided and at
least one hosted deployment has produced an incident that the current tooling could not
explain from the browser.
