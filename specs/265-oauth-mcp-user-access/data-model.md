# Data Model: OAuth MCP User Access

## Design boundary

These records are account/security authority, not business Evidence or Reality. They
may reference a company to constrain access but never participate in business reads,
projections or provenance. Existing `MCPAccessToken` remains the authority for manual
unattended integrations and is not migrated.

## MCPClientGrant

One revocable user decision allowing one identified MCP client to use selected Reality
tools in one company.

| Field | Meaning and validation |
|---|---|
| `id` | Opaque primary identity. |
| `tenant_id` | Exact company boundary; FK to `tenant`; indexed. |
| `user_id` | Authorizing human; FK to `app_user`; indexed. |
| `client_id` | Stable pre-registered identifier or validated HTTPS CIMD URL; bounded length. |
| `client_name` | Bounded consent-time display snapshot; explanatory, never identity. |
| `client_uri` | Optional validated HTTPS display link; not followed during tool use. |
| `allowed_tools` | Nonempty bounded JSON array of exact canonical tool names approved from the initially fully selected eligible set; the user may deselect tools and interactive grants store no wildcard. |
| `scopes` | Bounded JSON array from `reality:read`, `reality:propose`, `reality:confirm`; must cover every allowed tool's access class. |
| `created_at` | UTC grant decision time. |
| `last_used_at` | Optional bounded-cadence usage observation; not credential validity. |
| `revoked_at` | Optional UTC terminal revocation time. |
| `revoked_by_user_id` | Optional human revoker; FK to `app_user`. |
| `revoke_reason` | Controlled bounded reason such as user, company owner, membership, account or security response. |

### Constraints and relationships

- Composite uniqueness `(tenant_id, id)` supports tenant-safe relationships.
- One grant has exactly one user, tenant and client for its lifetime.
- Re-consent always creates a new grant. Approval atomically revokes any still-active
  grant for the same user, tenant and client; the historical decision is never mutated
  into a broader grant. A company change therefore always has a distinct identity.
- `allowed_tools` is validated against the current canonical catalog when granted and
  when used. Eligible choices are limited by the client's requested coarse scopes and
  all current matching tools are initially selected for review. The user may reduce
  that selection. A later catalog addition never enters the stored list automatically.
- A grant is effective only while user/account, active membership, tenant, scopes and
  operation policy remain valid. `revoked_at IS NULL` alone is insufficient.

### Lifecycle

```text
approved ──explicit/security/membership/account/company revocation──> revoked
```

Membership/account/company changes need not rewrite the grant synchronously. They make
it ineffective immediately through live resolution and may later record a revoke
reason as cleanup.

## MCPAuthorizationInteraction

Bounded single-use OAuth authorization request and authorization-code state. It never
contains a password, browser session cookie, PKCE verifier, access token or refresh
token.

| Field | Meaning and validation |
|---|---|
| `id` | High-entropy opaque browser interaction ID; primary identity. |
| `client_id` | Validated client identity. |
| `client_metadata` | Bounded validated display snapshot needed for consent; no arbitrary document retention. |
| `redirect_uri` | Exact URI validated against pre-registration or CIMD. |
| `resource` | Exact canonical MCP resource URL. |
| `requested_scopes` | Bounded supported scopes requested by the client. |
| `code_challenge` | PKCE S256 challenge; verifier is never stored. |
| `code_challenge_method` | Fixed `S256`. |
| `client_state` | Bounded opaque value returned unchanged to the exact validated redirect; excluded from logs/audits. |
| `user_id` | Nullable until authenticated/approved; then exact signed-in user. |
| `tenant_id` | Nullable until approved; exact selected ready company, including a Sandbox. |
| `grant_id` | Nullable composite link to approved grant. |
| `authorization_code_hash` | Nullable SHA-256 hash populated only after approval. |
| `status` | `pending`, `approved`, `denied`, `consumed`, or `expired`. |
| `expires_at` | Short UTC interaction/code deadline. |
| `created_at`, `decided_at`, `consumed_at` | UTC lifecycle evidence. |

### Constraints and lifecycle

- Status-specific checks require grant/code only for `approved`/`consumed`, decision
  time for approved/denied, and consumption time only for consumed.
- Approval, code creation and grant creation/supersession commit atomically.
- Code exchange locks the approved interaction, verifies client, exact redirect,
  resource and PKCE, then marks it consumed in the same transaction as credential
  issuance. Any replay fails.
- Expired/denied/consumed rows cannot be approved or exchanged.
- Pending interactions and approval codes expire after 10 minutes. Terminal rows are
  eligible for removal after 7 days; `SecurityAuditEvent` retains the minimal
  longer-lived lifecycle evidence.

```text
pending ──approve──> approved ──valid code exchange──> consumed
   │                    │
   ├──deny──────────> denied
   └──deadline──────> expired
approved ──deadline──> expired
```

## MCPUserCredential

Hashed access and optional rotating refresh material for one interactive grant. It is
separate from manual `MCPAccessToken` so the two authorities cannot be confused.

| Field | Meaning and validation |
|---|---|
| `id` | Opaque credential-family identity. |
| `tenant_id`, `grant_id` | Composite FK to the grant; tenant is duplicated only to enforce same-company integrity. |
| `access_token_hash` | Unique SHA-256 digest; clear access token is returned once. |
| `access_token_prefix` | Short non-secret diagnostic prefix. |
| `access_expires_at` | UTC expiry, 15 minutes after issuance. |
| `refresh_token_hash` | Optional unique SHA-256 digest; clear value returned once. |
| `refresh_expires_at` | Optional UTC expiry, at most 30 days after issuance. |
| `generation` | Positive rotation generation. |
| `created_at`, `last_used_at`, `rotated_at`, `revoked_at` | UTC lifecycle values. |
| `replaced_by_id` | Optional same-grant link to the next rotation generation. |

### Constraints and lifecycle

- Access and refresh hashes are globally unique. Clear credentials are never stored.
- Access verification requires both unexpired/unrevoked credential and effective grant.
- Refresh locks the family, consumes the current refresh material, and creates the next
  generation atomically. Reuse of replaced material revokes the family and records a
  security event.
- Revoking a grant makes all related credentials ineffective immediately even if
  credential rows are cleaned up later.

```text
active ──refresh──> rotated ──> active next generation
  │          └──replay detected──> family revoked
  ├──expiry──> expired
  └──grant/user revocation──> revoked/ineffective
```

## MCPPrincipal (non-persistent)

Immutable result of credential verification:

| Field | Meaning |
|---|---|
| `authentication_kind` | `manual` or `interactive`. |
| `credential_id` | Manual token or interactive credential identity. |
| `grant_id` | Interactive grant ID; null for manual credentials. |
| `user_id` | Verified current human; null for manual integrations. |
| `tenant_id` | Sole server-derived company authority. |
| `client_id` | Interactive OAuth client or manual token identity. |
| `scopes` | Effective coarse access after current checks. |
| `allowed_tools` | Effective exact tool set or existing manual wildcard. |

The principal is created afresh per request. Tool inputs cannot populate or override
it. The application dispatcher consumes `tenant_id` and internal actor context only.

## Existing entities reused

- `AppUser`: human identity and current eligibility.
- `TenantMembership`: live user → company role authority.
- `Tenant`: immutable purpose and archive state. Ready ordinary and Sandbox tenants are
  eligible under identical MCP authority checks.
- `UserSession`: browser-only sign-in for the consent UI; never accepted by MCP.
- `SecurityAuditEvent`: minimal redacted grant lifecycle and denial evidence.
- `OrdinaryCompanyCreation` / `PlaygroundRun`: canonical company-setup idempotency and
  readiness; no duplicated setup fields are added to authorization records.
- `MCPAccessToken`: unchanged manual unattended credential authority.

## Migration and retention

- Additive migration only; no backfill.
- Every tenant-bearing new table/query is covered by the repository tenant-key catalog
  and cross-tenant tests even though these are security rather than business records.
- When a new authorization interaction is created, the service may remove at most 500
  terminal interactions older than 7 days and 500 terminal credentials older than 90
  days. This bounded opportunistic sweep is hygiene only and is never required for
  authorization correctness; no API-process timer, new scheduler or public cleanup
  endpoint is introduced. Minimal `SecurityAuditEvent` evidence remains under its
  existing retention contract.
- Downgrade refuses while any of the three new tables contain rows.
