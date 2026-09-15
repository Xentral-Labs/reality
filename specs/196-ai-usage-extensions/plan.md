# Implementation Plan: AI usage extensions

## Technical Context
Python/SQLAlchemy/PostgreSQL service; FastAPI authenticated adapter; React Usage.
Use existing SecurityAuditEvent with recipient user_id, actor_user_id and tenant_id.
No table/migration. Immutable versioned detail contains request_key, questions, mode,
reason and expiry; values are authoritative grant inputs, not derived usage copies.

## Constitution Check
All principles PASS. Account audit is existing non-business infrastructure; normal
business queries remain tenant-scoped. Authentication and membership rechecked in
service; platform admin role comes from AppUser, never request payload. Confirmation
required for every grant. No schema expansion, alternate tool or agent write path.

## Design
Service ai_usage handles target resolution, history and grants. _allowance derives
base and bonus remaining from immutable grants and dispatch events. Grants lock the
same recipient AppUser row as reserve_managed_question. Request-key replay precedes
exhaustion/lifetime checks and rejects changed payload. Self grants require zero
remaining and enforce lifetime cap. Admin grants require reason and 20/100.
Account API under company-setup uses real-cookie Actor even in local auth-disabled
mode. Read accepts selected tenant and optional recipient email (admin only).
Frontend Settings Usage has explicit preview/confirm, retry-stable request key and
history; exhausted chat links to Usage. No grant triggered by navigation.

## Verification / rollback
Service tests first: 3 grants/fourth denial, UTC expiration, preserved consumption,
replay/conflicting replay, missing confirmation, actor/tenant/admin isolation and
concurrent final slot. API tests use authenticated cookies. Browser confirms no write
before confirmation, errors/retry and history. Run focused PostgreSQL suite, full
pytest where feasible, web build/audit, spec policy and diff review. Existing audit
rows remain intact on code rollback; no migration. Local Docker preview then PR.

## FR-007 plan
Adapter-only simplification in ChatUsage.tsx; retain shared grant API and account scope.
Use the explicit Reset usage click as confirmation, preserve retry key until success.
Render total daily allowance without exposing grant accounting. No schema/service change.
Constitution: PASS. Verify browser eligibility, retry, success, exhausted lifetime, admin
view and four locales, plus web build/spec policy.
