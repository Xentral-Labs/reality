# Implementation Plan: Platform Admin Own Private Analytics

**Branch**: `codex/platform-admin-own-reports` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary
Permit current active platform administrators to use their own private analytics across accessible business companies while retaining exact author/company filters. Explain admin access without creating memberships.

## Technical Context
Python 3.12+, SQLAlchemy 2, PostgreSQL, existing FastAPI tools and workers; TypeScript/React frontend with existing authenticated identity. pytest, PostgreSQL service/adapter tests and four-language Playwright fixtures. No new dependencies, tables, endpoints, background handlers or permission catalogs. No extra network calls in the browser; one scalar eligibility query per existing guard.

## Constitution Check
| Principle | Result | Proof |
|---|---|---|
| I Source/Evidence/Reality | PASS | No business evidence changes |
| II Reality authority/identity | PASS | Existing opaque user/company/author IDs |
| III Proven schema | PASS | No schema change |
| IV Tenant/services/confirmation | PASS | Shared eligibility; tenant+author predicates and proposal confirmation unchanged |
| V Spec/test evidence | PASS | Approved privacy scope and tests first |
| VI Explainable Web | PASS | Explicit access labels from authenticated identity |
| VII Simplicity/storage | PASS | Existing PostgreSQL and SQLAlchemy; no dependencies |
| VIII Received values | PASS | No source or derived value writes |
Pre-research and post-design checks both PASS. No constitutional exception.

## Project Structure
Services: packages/reality-core/src/reality/services/analytics/reports.py and requests.py. Their existing scheduling/worker consumers remain unchanged.
Adapters: no alternative rules in API/MCP; existing principals and owner filters remain.
Frontend: apps/web/src/unified/companyAccess.ts, CompanySwitcher.tsx, CompanySettings.tsx, Shell.tsx, SettingsPage.tsx and src/localization.tsx.
Tests: test_reporting_graph_lifecycle.py, test_reporting_graph_surfaces.py, test_requested_analysis.py, test_proposal_decision_policy.py; apps/web/scripts/unified-settings-browser.mjs.

## Design and Rollback
Use SQL EXISTS predicates for current active membership or current active persisted administrator plus nonarchived business tenant. Retain per-artifact author identity. Delegate deferred _member, translating shared refusal to existing Company-not-found. Practice/archived visibility and all owner administration/confirmation/delegation rules stay unchanged. Frontend passes explicit admin identity to a shared label function; a truthful admin card explanation does not expose new management controls.
No migration. Rollback is a code revert; report ownership and memberships require no repair. Source → Evidence → Reality and source values are untouched.

## Tests and Verification
Tests first: admin lifecycle without membership; foreign authors/tenants; real DB admin versus forged/stale principal; inactive user and revoked privilege; unavailable/practice tenants; deferred own request plus worker revocation; private sealed proposal author defense; authenticated HTTP admin library; four-language switcher/card labels and ordinary nonmember regression. Run related complete service/adapter suites, existing proposal-policy tests, frontend contracts/format/build/i18n audit, settings and analytics browser scenarios, lint/spec/docs parity and full hosted CI. Merge/deploy under existing session authorization; live read-only My reports in the current admin's nonmember companies must load without private author leakage. Do not grant a production role or create a live report to test.
