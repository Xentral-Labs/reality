# HTTP and Product Contract: Company Membership Invitations

IDs are opaque. Tenant routes require an active owner unless stated otherwise. Foreign
and unknown tenant-scoped identities are indistinguishable. Errors never disclose
account existence.

## Invite context

Email links use `https://{product-host}/invitation#token={clear-token}`. The fragment is
not sent in HTTP request targets/referrers. Product Web reads it, immediately replaces
browser history with `/invitation`, retains it only for the active flow, and sends it
solely in JSON bodies. Session-scoped storage restores reloads and is cleared after
acceptance, cancellation, or expiry. Analytics are absent on this route.

### Inspect

`POST /api/auth/invitations/inspect` with `{"token":"..."}` returns only status,
company display name, and expiry. Invalid/replaced/expired/revoked/accepted/archived
results expose only a safe recovery state—never invited email, account existence,
inviter email, tenant ID, or membership ID.

### Invite-bound signup and verification

`POST /api/auth/invitations/signup` accepts token, email, password, and terms. It works
when public signup is disabled only after validating usable invitation and matching
normalized email. It creates verification but no membership, AccessApplication, or
automatic-admission claim.
If the account already has a pending AccessApplication, acceptance retains and approves
it with reason `admitted through company invitation`.

The existing email-verification operation accepts optional invitation context. It
verifies email but does not grant product/company access; the flow continues to
explicit acceptance.

### Accept

`POST /api/auth/invitations/accept` with the token requires an authenticated account but
is reachable for an eligible account pending ordinary platform approval. It requires a
matching verified email, refuses suspended/rejected accounts, and atomically activates
an eligible pending account plus creates/reactivates one member membership. It returns
accepted status and opaque company ID/display name. Same-account replay returns the
same logical success. GET and verification alone never accept.

## Owner operations

- `GET /api/tenants/{tenant_id}/settings/members`: bounded active memberships and
  pending/expired invitations; invitation rows never reveal account existence.
- `POST /api/tenants/{tenant_id}/settings/invitations` with email: one neutral receipt
  for unknown/existing account, active member, or duplicate invitation.
- `POST /api/tenants/{tenant_id}/settings/invitations/{id}/resend`: enforce 60-second
  cooldown, increment generation, reset seven-day expiry, invalidate old hash, enqueue.
- `POST /api/tenants/{tenant_id}/settings/invitations/{id}/revoke`: invalidate every
  generation.
- `POST /api/tenants/{tenant_id}/settings/members/{id}/remove`: owner or platform admin
  removes an active non-owner; owner targets are refused; success has no body.

Bootstrap/company summaries include the current user's membership role. Web uses it to
render Members and owner controls, but the service remains authoritative.

Email normalization is trim plus case-insensitive comparison only; provider dot/plus
alias rules are never inferred. A company permits 20 newly persisted logical
invitations per rolling 24 hours and each invitation five resends per rolling 24 hours;
neutral duplicate and active-member requests do not consume the creation quota, and an
exhausted quota returns one account-independent rate-limit response. Delivery retries with
increasing delay for 24 hours, then becomes failed and owner-resendable. Missing workers
leave delivery pending. Terminal invitation/delivery details remain 90 days; minimal
tenant access audits remain until company deletion.

## Chat and omitted interfaces

Internal Chat may expose `member_invite`, `invitation_resend`, `invitation_revoke`, and
`member_remove`. Each creates an effect-free proposal; approval passes the confirming
human principal and rechecks owner authority and target state.

External MCP and local CLI expose none of these V1 operations because they do not
establish an authenticated human owner.

## Common responses

- Same-tenant non-owner: forbidden with no state/audit transition/delivery intent.
- Unknown/foreign identity: not found without disclosure.
- Archived same-tenant company: conflict; foreign caller still receives not found.
- Tokens, hashes, passwords, account lookup results, and raw provider errors never
  appear in responses or logs.
- Account existence does not intentionally alter invitation response body, status,
  owner-visible state, or processing path; exact constant-time behavior is not promised.
- Dynamic names/emails/diagnostics are escaped for their output context. Members and
  invitation screens define keyboard/focus plus empty, loading, validation,
  delivery-pending, failed, forbidden, and recovery states.
- Direct owner invite/resend/revoke need no extra confirmation; removal uses explicit
  confirmation. Chat mutations always require preview and confirmation.
