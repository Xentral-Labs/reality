# Implementation Plan: Interpretation Coverage

**Branch**: `045-interpretation-coverage` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Add an append-only tenant-scoped outcome for every terminal import attempt and a shared read capability. Successful outcomes commit atomically with produced Reality; failures are recorded only after rollback. Intake-only classifications use attempt zero.

## Technical Context

Python 3.12, SQLAlchemy 2, Alembic, PostgreSQL, pytest, existing application tools and MCP catalog. No dependency or web UI change.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Outcome links source/job and references existing results. |
| Reality authority / shortest links | PASS | Audit metadata owns no business state. |
| Proven schema | PASS | Mutable jobs cannot retain attempts and result sets. |
| Tenant/service boundaries | PASS | Tenant-filtered services; adapters use application tools. |
| Spec/tests first | PASS | Contract tests precede code. |
| Explainability | PASS | Coverage exposes bounded reasons and opaque result IDs. |
| Simplicity | PASS | Two narrow tables and a computed read; no framework. |

Post-design check: PASS. No exceptions.

## Design

Create `interpretation_outcome` and child `interpretation_record_reference`; unique `(tenant_id, import_job_id, attempt)` prevents duplicates. Child rows avoid an unvalidated JSON relationship format. `ImportJob` remains mutable queue state. Coverage is computed rather than persisted. Initial controlled result types are document, document_line, and commitment. Raw errors are reduced to bounded safe summaries.

## Repository Changes

Models and migration; core write/read services; application read tool; MCP catalog; service/parity/isolation tests; durable data-model, ingestion, and docs-site documentation.

## Migration and Rollback

Upgrade creates empty audit tables. Existing sources report `not_recorded`; no fabricated backfill. Downgrade drops only those tables after code rollback and never changes source or Reality records.

## Verification

Targeted tests, migration tests, tenant catalog, `make spec-check`, `make lint`, `make test`, `make site-build`, and `make web-build`. Unrelated dirty web files remain excluded.

## Risks

- Sensitive failures: store reason codes plus generic bounded summaries.
- Rolled-back IDs: create successful outcomes inside the producing transaction only.
- Historical gaps: expose `not_recorded` honestly.

