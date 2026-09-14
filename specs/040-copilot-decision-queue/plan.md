# Implementation Plan: Copilot Decision Queue and Chat Archiving

**Branch**: `040-copilot-decision-queue` | **Date**: 2026-09-02 | **Status**: Approved

## Summary

Add explicit archive state to ChatSession, tenant-scoped archive/restore services and API
operations, and a tenant-wide proposal read endpoint. Extend Exceptions with separate pending
and history tabs using the existing proposal decision endpoints. The Copilot shows proposal
cards only with an active conversation. Dashboard capability state includes exceptions and all
proposal history so onboarding cannot conceal decision work.

## Technical Context

Python 3.12, SQLAlchemy 2, Alembic, PostgreSQL, FastAPI, React/TypeScript, pytest and Web
contract/build tests. Existing application proposal tools remain authoritative.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | No business provenance relationship changes. | PASS |
| Reality authority | Exceptions stay derived; decisions remain Change Proposals. | PASS |
| Proven schema only | `ChatSession.archived_at` is required to filter, restore, and retain chats. | PASS |
| Tenant/service boundaries | Archive, restore, listing, and decisions use tenant-scoped services. | PASS |
| Test evidence | Service/API/Web tests precede implementation. | PASS |
| Explainable Web | Exceptions and decisions are distinct tabs with exact proposal details. | PASS |
| Simplicity | One nullable lifecycle timestamp; no speculative proposal-origin relationship. | PASS |

## Repository Changes

- `packages/reality-core/src/reality/db/core.py`: nullable ChatSession archive timestamp.
- `packages/reality-core/migrations/versions/0031_chat_session_archiving.py`: additive migration.
- `packages/reality-core/src/reality/services/core.py`: filtered lists, archive/restore, proposal list.
- `packages/reality-core/src/reality/web/api.py`: archive/restore and decision queue contracts.
- `apps/web/src/api.ts`: typed archive and decision API.
- `apps/web/src/App.tsx`: decision tabs, archive UI, empty-chat and Home-state corrections.
- Backend and frontend regression tests plus durable Web/Chat documentation.

## Data and Migration

`chat_session.archived_at` is nullable UTC. Existing rows remain active. Archive sets the
timestamp; restore clears it. Messages and Change Proposals are untouched. Downgrade removes
only the presentation lifecycle column.

## Test Strategy

Service tests prove retention, restore, tenant isolation, and proposal invariance. API tests
prove status-filtered decision lists. Web contract tests prove navigation, labels, structured
values, empty-chat suppression, and Home capability logic. Run migration, focused backend,
spec, lint, Web build, and i18n gates.

## Complexity Tracking

No Constitution exceptions.

## Post-Design Constitution Re-check

All rows remain PASS; no business-domain relationship is introduced.
