# Implementation Plan: Non-Blocking Authenticated Reads

**Spec**: [spec.md](spec.md) | **Date**: 2026-08-31

**Language**: English for all repository artifacts and review evidence.

## Summary

Remove the `last_seen_at` assignment from read-only current-user resolution. Preserve
explicit session mutations. Add SQL-observation regression coverage before changing
the implementation, then run focused and full quality gates and restart local services.

## Technical Context

- Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL, pytest
- Files: `backend/src/reality/web/auth.py`, `backend/tests/test_user_access.py`
- No schema, migration, dependency, API contract, or frontend change

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Identity plumbing only; business lineage unchanged |
| Reality operational authority | PASS | No document or Reality state changes |
| Proven schema only | PASS | No schema change |
| Tenant and service boundaries | PASS | Existing authentication boundary remains intact |
| Spec and test evidence | PASS | Approved spec and regression test precede implementation |
| Explainable Web product | PASS | Restores existing Web availability without new rules |
| Simplicity and storage discipline | PASS | Removes a non-durable write; adds no abstraction |

## Test Strategy

Capture SQL statements around `user_from_request` with a valid session. The test must
first fail because current code autoflushes `UPDATE user_session`, then pass after the
assignment is removed. Run the complete user-access module, lint, full PostgreSQL
suite, spec policy, frontend build, and translation audit.

## Rollback

Restore the assignment if rollback is required. No data migration or cleanup is needed.

## Risks

`last_seen_at` will retain its creation-time value because read paths no longer attempt
an update. This matches current durable behavior: those read-path changes were rolled
back when their request-scoped sessions closed. A future durable activity feature must
be specified separately with an explicit write policy.
