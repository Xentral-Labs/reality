# Implementation Plan: Practice Companies

**Branch**: feature/playground-free-operations | **Date**: 2026-09-07
**Spec**: [spec.md](spec.md) | **Language**: English

## Technical Context
FR-008/009 extension: derive eligibility from persisted active practice run, tenant,
owner account and membership. No new schema or conversion. Add a reviewed allowlist
of local business service operations, leaving egress, sharing and lifecycle guarded.
Bootstrap includes owned practice tenant metadata (purpose/run ID) without changing
business rows. Tenant surface dependency allows authenticated owners to use normal
App routes; service policy still checks operation and current eligibility. App uses
the existing pages, plus Sandbox banner and contextual run links. Playground-to-App
URL carries an opaque tenant ID validated against bootstrap, never implicit access.
Tests first for discoverability, master-data write/read across surfaces, foreign and
inactive ownership, temporary restrictions, egress/unknown operation denial. Run
full backend suite and web build/contracts/audit/browser checks. Constitution PASS:
same services and records, no source/authority duplication; user explicitly approved
full App editing. No unresolved clarification or critical analysis finding. T013–15
cover both requirements. Rollback removes additive eligibility and navigation only.

Python 3.12, SQLAlchemy/Alembic/PostgreSQL, FastAPI/Pydantic; existing React/Vite UI.
Add a constrained usage kind to PlaygroundRun and reuse Tenant.name. Setup remains
owner-serialized and confirmed. No new endpoint, tool or business rule.

## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Only existing synthetic setup; operations unchanged | PASS |
| Reality owns state | No document or balance fields | PASS |
| Proven schema | Kind constrains active-run lifecycle and restart | PASS |
| Tenant/services | Owner checks and distinct purpose=playground tenants | PASS |
| Tests first | Named setup, alternating starts, retries and boundary tests | PASS |
| Explainable UI | Explicit kind/name, same record inspectors | PASS |
| Received values | No quantity/amount computation | PASS |
| Simplicity | Reuse Tenant.name; no duplicate company engine | PASS |

## Design and Files
- db/core.py: sandbox_kind=temporary|practice on PlaygroundRun, default temporary;
  active-owner uniqueness applies only to temporary runs.
- migrations/versions/0043_playground_practice_companies.py: additive column/check and
  narrowed index. Based on local 0041; remote 0042 belongs to another feature, so later
  integration must merge migration heads rather than rewrite deployed revisions.
- services/playground.py: validate kind/name before writes; compare retry inputs;
  retain active practice companies, keep pending initialization owner-serialized;
  temporary start still requires explicit restart of an active temporary run.
  Reject restart of practice companies. Name own-company Party from Tenant.name.
  Summaries join tenant name without per-row reads.
- web/playground.py: additive typed creation parameters; no wider authority.
- api.ts, PlaygroundPage.tsx, PlaygroundWorkspace.tsx: kind/name setup, durable retry
  form state and named entries/context. Restart only an active temporary run when
  starting temporary; practice always uses start. Four-language labels and shared CSS.
- config/data_model.yaml and docs/WEB_SPEC.md: metadata and lifecycle contract.

## Test Strategy
test_playground_practice_companies.py covers FR-001–004/DR-001–002: names, idempotent
retry, changed input conflict, distinct tenants, multiple practice companies,
temporary replacement, old defaults, invalid API input, foreign read and restart refusal.
Frontend contracts and browser fixtures cover named creation/reopen and guided flow.
Full backend, migration upgrade/check, Ruff, web build/audit, spec policy and browser
journeys required. No new technology or unresolved research question.

## Rollout and Rollback
Integration with main retains the already-used `0043_practice_companies` revision
and joins it with `0043_return_announcements` through the no-op
`0044_playground_returns_merge` revision. The branches modify independent tables.
The migration convergence regression runs from both prior heads and verifies both
the return-announcement table and sandbox-kind column without restamping or data loss.
Spec impact: none for this integration; it preserves both specified behaviors.

Migration before API/web deployment; old clients default temporary. Existing runs
remain unchanged except typed default. Downgrade refuses while practice rows exist
rather than losing semantics or archiving companies. No destructive cleanup.

## Review Risks
Preserve retry identity across lost responses; never select a practice company for
restart. No production tenant ID input. Names are labels, not keys.

## Complexity Tracking
No constitutional exception. Schema justified by FR-002 lifecycle constraints.

## Exception catalog information
FR-007: a read-only authenticated account endpoint in web/playground.py delegates to
load_operational_exception_catalog, returning version and public descriptive class
fields (id, label, description, severity, owner, clears_through). No tenant records
or new persisted data. The Playground adds an Info control and native modal dialog
with shared br-* primitives, fresh fetch on mount, search, details, error retry,
Escape/focus restoration. Canonical descriptions remain source-language metadata.
Tests first: API parity/auth test and synthetic browser fixtures for dynamic classes,
search, reopening and dismiss. Constitution PASS; no clarification or critical finding.
Rollback removes the additive read endpoint and UI only.

## Creation form refinement
FR-010: Replace the fixed company-list cap with a viewport-bounded flex menu and
a shrinkable scrolling list. Preserve handlers and eligibility. Add a CSS regression
before implementation and run frontend contracts/build. Constitution PASS: presentation
only, no schema or service changes. Rollback restores these CSS declarations.
Review: owner-approved sizing request, no clarifications or critical coverage findings.

FR-005 is presentation-only in PlaygroundPage.tsx using shared br-* form/button
primitives and existing theme tokens. Replace nested titles with one conditional
heading; hide library refresh/back navigation during review. Keep submit/cancel
handlers unchanged. Add browser assertions before markup changes, then verify
contracts, localization, build, desktop/mobile and light/dark creation review.
Constitution review: PASS; no schema, API or domain changes. Revert markup to roll back.
FR-006 adds local explanatory state to OperationChooser and a guarded guided-editor
exit in PlaygroundPage. No command is reversed or replayed. Existing pending/rejection
branch stays authoritative. Browser proof covers unavailable-return/back and exiting
after a recorded step without extra writes. Constitution PASS; no new business rules.
