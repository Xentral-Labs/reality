# Quickstart Validation: Company Membership Invitations

## Prerequisites

- PostgreSQL test service and migration `0030_company_membership_invitations`.
- Product API, Web, and one invitation-delivery worker share the database.
- Non-production email capture; owner, member, suspended account, two tenants, and one
  unknown address fixtures.

## Automated validation

```bash
.venv/bin/pytest -q \
  packages/reality-core/tests/test_membership_invitations.py \
  packages/reality-core/tests/test_user_access.py \
  packages/reality-core/tests/test_master_data_api.py \
  packages/reality-core/tests/test_application_tools.py \
  packages/reality-core/tests/test_email_delivery.py

.venv/bin/pytest -q \
  packages/reality-core/tests/test_migrations.py \
  packages/reality-core/tests/test_postgresql_integration.py \
  packages/reality-core/tests/tenant_isolation

make spec-check
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

## Manual stories

### Uniform invitation

Invite an existing and unknown address as owner. Verify identical receipt/pending state
and no membership before acceptance. Verify a member cannot invite/manage/remove and
creates no audit transition or delivery intent.

### New invited account

Disable public signup, open the captured invite, and verify the token fragment is
removed from history. Register and verify; confirm no application, admission-slot use,
membership, or normal product access. Explicitly accept and confirm company entry.

### Existing account and stale link

Open an existing-account invite, sign in, then resend as owner. The old link reports a
safe replaced state. Accept the newest link twice; exactly one membership exists.

### Removal and reactivation

Give a user two memberships, remove one, and verify next-request denial there while the
global session/other company remain. Re-invite and accept; the original membership ID
reactivates and audits retain both transitions.

### Delivery recovery and isolation

Force a provider timeout and retry. Confirm only hashes/sanitized outcomes persist and
only the newest link works. Attempt each operation with foreign IDs; no company, member,
email, invitation, or account-existence data is disclosed.

## UI review

Review desktop/mobile Members and invite auth states in English, German, Dutch, and
Spanish. Verify keyboard operation, loading/empty/error states, long values, explicit
company context, and absence of owner controls for members. Record final approval only
after all gates are green.

## Automated evidence — 2026-09-02

- Isolated Spec 035 backend/PostgreSQL suite: **297 passed, 7 skipped** in 23.49 seconds.
- Invitation migration plus real two-session invite/accept/resend/revoke convergence:
  **5 passed**.
- Concurrency isolation regression with tenant lifecycle: **7 passed, 1 skipped**.
- Product Web TypeScript/Vite production build: **passed**; the existing bundle-size
  advisory remains non-blocking.
- Isolated Spec 035 Product Web localization audit: **746/746** source strings covered for English,
  German, Dutch, and Spanish.
- Isolated Spec 035 Product Web frontend contract suite: **41 passed**.
- Internal Chat proposal and authenticated HTTP confirmation story: **20 passed, 2
  skipped**. The run covered effect-free proposal/rejection, replay protection,
  invite/resend/revoke/remove, stale-target and owner reauthorization, unauthenticated
  denial, foreign-tenant non-disclosure, confirming-actor audit propagation, and
  deliberate external MCP omission.
- Invitation delivery failure/recovery story: **8 passed**. The run covered atomic
  invitation/outbox rollback, PostgreSQL `SKIP LOCKED` double-claim prevention, lease
  recovery, durable worker outage, terminal failure after 24 hours, sanitized provider
  diagnostics, ambiguous duplicate delivery with latest-link validity, and retention
  exclusions that preserve token-free audit evidence.
- Multi-company access/isolation story: **2 passed**. Two identically named companies
  remained distinguishable by opaque ID and exposed the authenticated user's `owner`
  or `member` role; member administration stayed owner-only, the member list was
  bounded at 500, hidden companies returned the same not-found result as unknown
  companies, removed memberships disappeared from bootstrap, and the no-company
  fallback returned an empty tenant list.
- Removal/reactivation/session story: **5 passed** across service, authenticated API,
  and real PostgreSQL sessions. Owner protection, member and platform-admin authority,
  archived-company refusal, inviter loss, identity-preserving reactivation, immutable
  redacted UTC audits, global-session and other-company preservation, concurrent
  remove/reinvite, and next-read denial after in-flight work were verified.
- `make lint`, `make spec-check`, and `git diff --check`: **passed**.

The automated portion of T061 passed on 2026-09-02. Because the implementation session
ran through the CLI without a controllable browser, the product owner performed the
manual EN/DE/NL/ES desktop/mobile review and approved it on 2026-09-02.

The product owner supplied an English desktop screenshot on 2026-09-02. It exposed a
missing local migration and an unfinished Members layout. Migration 0030 was applied,
the owner membership and invitation tables were verified, and the Members card was
rebuilt with a bounded invite form, structured access rows, section counts, and a
single-column mobile layout. A post-fix screenshot is still required before treating
the English desktop visual check as approved. After deployment, the product owner
confirmed the corrected desktop and mobile layout in every supported language.

The product owner also completed the delivered invitation-link acceptance path,
confirmed the expected company opened within the five-minute target (excluding any
verification-email wait), and granted final feature acceptance on 2026-09-02.

Manual timing, responsive visual review, and final product-owner acceptance are
complete.
