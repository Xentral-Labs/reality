# Feature Specification: Auditable AI usage extensions

**Language**: English

**Created**: 2026-09-15
**Status**: Accepted scope (user: implement, initially everyone may extend 2–3 times)

## Context and Intent
Allow continued testing without erasing actual consumption or borrowing future days.
### Non-Goals
Billing, paid upgrades, resetting counters, changing provider selection or company admission.

## User Scenarios & Testing
### US1 — Continue testing (P1)
An authenticated eligible user who exhausts managed AI may confirm +20 questions.
Three self-service extensions are available over the lifetime of the account, shared
across all companies and days. Unused extra questions expire at the next UTC reset.
### US2 — Review and administer (P1)
Usage shows daily consumption, bonus availability and grant history with actor,
recipient, timestamp, amount and reason. Platform admins may confirm +20 or +100
for themselves or an eligible user in the selected company, with a required reason.
### Edge cases
Retries must replay one grant; concurrent requests cannot exceed the lifetime count.
Midnight expires bonus but never replenishes self-service grants. No provider/no
managed allowance, missing identity and inaccessible companies cannot grant credits.

## Requirements
- **FR-001**: Exactly three lifetime self extensions of 20 questions each, only when the
  current allowance is exhausted. Account-wide enforcement cannot be bypassed by
  switching companies or retrying requests.
- **FR-002**: Preserve every dispatch; derive available questions from daily base plus
  unexpired grant records. Normal UTC reset and provider exemptions remain intact.
- **FR-003**: Require authentication, explicit confirmation and stable request identity.
  Serialize grants and dispatches on the same account lock; replay is idempotent.
- **FR-004**: Record immutable actor/recipient IDs, amount, reason, timestamp, expiration
  and self/admin mode. Users read only their own history; platform admins may target
  an eligible member of the selected company. No new business tables.
- **FR-005**: Settings Usage provides self-extension preview/confirmation, admin target
  and reason controls, allowance breakdown and history. Exhausted chat links there.
- **FR-006**: Server-authorized admin grants allow 20 or 100; regular users cannot choose
  another account, admin mode, arbitrary amounts or exceed lifetime self limits.

## Success Criteria
Fourth self extension is rejected even across days/companies; concurrent final grants
produce one credit; retries do not duplicate. Real dispatch counts remain unchanged.
UI resumes chat with refreshed allowance and renders attributable history in four languages.

## Assumptions and Dependencies
Three is the selected value within the requested 2–3. Self grants use reason
"Continued testing". Extras expire at midnight UTC. Existing SecurityAuditEvent is
the account-scoped audit authority; AppUser identifies recipient and actor. Existing
platform admin permission is authoritative. No constitutional/schema exception.

## Requirement Traceability
| Requirement | Proof |
|---|---|
| FR-001–004, FR-006 | Service tests for lifetime/reset/replay/concurrency/auth/audit |
| FR-003–006 | Authenticated API tests and browser usage confirmation/history |
| FR-005 | Web tests/build/i18n and responsive browser |
