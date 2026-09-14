# Data Model: Company Membership Invitations

## CompanyInvitation

Tenant-scoped administrative Evidence that a normalized email may join one company. It
has no pre-acceptance user relationship.

| Field | Purpose |
|---|---|
| `id` | Opaque invitation identity. |
| `tenant_id` | Required company authority/query scope. |
| `normalized_email` | Matching value, never relationship identity. |
| `status` | `pending`, `accepted`, `revoked`, or `expired`. |
| `token_hash` | Nullable unique one-way hash of the current generation. |
| `token_generation` | Monotone generation invalidating older links. |
| `expires_at` | UTC deadline for the current generation. |
| `invited_by_user_id` | Owner who created the invitation. |
| `accepted_by_user_id` | Matching account after acceptance, otherwise null. |
| `accepted_at`, `revoked_at` | Required UTC terminal transition time when applicable. |
| `created_at`, `updated_at` | UTC lifecycle times. |
| `terminal_at` | UTC retention anchor for accepted, revoked, or expired state. |

Constraints: partial unique pending `(tenant_id, normalized_email)`; unique non-null
token hash; tenant/status and tenant/email indexes; allowed-state and matching terminal
timestamp checks. Usability derives from pending state, future expiry, and hash match.
Elapsed pending rows are persisted as expired when encountered.

## InvitationDelivery

Tenant-scoped retryable intent containing no clear token, link, rendered body,
password, or account-existence result.

| Field | Purpose |
|---|---|
| `id`, `tenant_id`, `invitation_id` | Opaque identity and direct scoped invitation link. |
| `generation` | Invitation generation this intent may issue. |
| `template_key`, `locale` | Stable render selection with English fallback. |
| `status` | `pending`, `processing`, `retry`, `delivered`, or `failed`. |
| `attempt_count`, `next_attempt_at` | Retry scheduling state. |
| `claimed_at`, `attempted_at`, `delivered_at` | UTC lease/attempt/result times. |
| `provider_message_id`, `last_error_code` | Optional bounded non-secret outcome. |
| `created_at` | UTC durable-intent time. |

Unique `(tenant_id, invitation_id, generation)` prevents duplicate enqueue. A due-work
index supports worker claims. Allowed-state, non-negative-attempt, and timestamp checks
apply. A stale generation is failed/superseded without sending.
Retry scheduling uses increasing delay for no more than 24 hours from `created_at`.

```text
pending → processing → delivered
                     → retry → processing
                     → failed
expired processing lease → retry
```

## TenantMembership changes

Keep existing identity and unique `(tenant_id, user_id)`. Constrain role to
`owner|member` and status to `active|removed`. Preserve original `created_at`; add no
invitation or transition-time fields.

```text
none → active member
active member → removed member → active member
active owner (no transition in this feature)
```

## SecurityAuditEvent changes

Add nullable `tenant_id`, `subject_type`, `subject_id`, and `outcome`. Existing global
events keep nulls. Every company-access event has tenant, opaque invitation/membership/
delivery subject, outcome, actor where known, UTC time, and redacted detail.

## Shortest links and deletion

```text
Tenant ──< CompanyInvitation ──< InvitationDelivery
  └──< TenantMembership >── AppUser
SecurityAuditEvent ── typed opaque subject ──> invitation/membership/delivery
```

Invitation and membership do not link to each other. Permanent tenant deletion removes
all tenant-scoped access rows through the existing deletion boundary.
Terminal invitations and deliveries are purged after 90 days; token-free security
audits are excluded from that purge.

## Migration and rollback

`0030_company_membership_invitations` follows `0029_ledger_reversals`. Existing active
owner memberships need no backfill; existing audits receive null new fields. Downgrade
refuses when invitations, deliveries, tenant access audits, member roles, or removed
memberships exist. Otherwise child delivery drops before invitation, then membership
checks and audit index/columns are removed.
