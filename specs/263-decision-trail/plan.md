# Implementation Plan: Decision Trail

**Branch**: `263-decision-trail` | **Date**: 2026-09-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/263-decision-trail/spec.md`

## Summary

Four changes, ordered by what can never be recovered later:

1. **Token attribution (US1)** — one additive migration: `mcp_access_token.created_by_user_id`
   and `action.decided_via_token_id`. The MCP server hands the verified token id to the
   shared approve/reject services, which record it next to `decided_at`.
2. **Catalog-wide event linking (US2)** — a scoped "executing proposal" context in
   `approve_and_execute_proposal`; `emit_business_event` fills `action_id` from it. This
   replaces reliance on the 31-tool allowlist for the link without removing explicit
   threading.
3. **History register (US3)** — restore specs 054/055 on the Decisions page from the
   existing history endpoint, plus a single-decision deep link.
4. **Decision on records and activities (US4)** — one batched attribution reader used by
   history, review, provenance, timeline and the MCP status tool.

See [research.md](research.md) for the evidence behind each choice and the rejected
alternatives, [data-model.md](data-model.md) for the schema and
[contracts/decision-attribution.md](contracts/decision-attribution.md) for payloads.

## Technical Context

**Language/Version**: Python 3.12, TypeScript (React, Vite)

**Primary Dependencies**: SQLAlchemy 2, Alembic, FastAPI, Pydantic v2, MCP Python SDK (FastMCP)

**Storage**: PostgreSQL; migration `0093_decision_trail`

**Testing**: pytest (service, adapter, MCP runtime, migration), node contract tests in `apps/web/scripts/*.test.mjs`, one Playwright browser script, localization audit

**Target Platform**: `reality-core` API, MCP runtime, web app

**Project Type**: web service + web application

**Performance Goals**: attribution adds a constant number of statements per page (≤ 3: proposals, tokens, users), independent of page size; timeline and register budgets unchanged

**Constraints**: no backfill; no change to approval permissions or the execution boundary; MCP input schemas unchanged

**Scale/Scope**: pages of ≤ 250 events or ≤ 100 decisions; companies with thousands of decisions (spec 054)

## Constitution Check

| Principle | Assessment | Result |
|---|---|---|
| I. Source → Evidence → Reality | Unchanged chain; the decision is reached through the existing `business_event.action_id`, the shortest true link from any Reality record to its cause. | PASS |
| II. Reality is the authority | No state moves to documents; no document or record table gains a decision column. | PASS |
| III. Proven schema only | Two nullable columns, each joined on every attribution read and required by FR-002/FR-004; the simpler alternative (reuse `decided_by_user_id`) would record an untrue statement (research R1). | PASS |
| IV. Tenant and service boundaries | Composite FK keeps a decision's token in its own company; the attribution reader is tenant-scoped and added to the isolation catalog; web, MCP and CLI read through one service; MCP still calls the shared approval service. Confirmation rules unchanged. | PASS |
| V. Specification and tests first | Every FR/DR maps to tests in the phases below; the catalog-wide linking test and the MCP attribution test are written first and observed red on `main`. | PASS |
| VI. Explainable web product | Adds exactly the missing path from a record/activity to its decision and decider; the browser renders a server object and derives nothing. | PASS |
| VII. Simplicity and storage discipline | No new dependency; one ContextVar (existing project pattern, e.g. `tenant_policy`, `analytics.reports.CALLER`) instead of changing dozens of handler signatures. | PASS |
| VIII. Received values recorded | Attribution is recorded at the moment of decision; names are resolved at read time and never stored. | PASS |

No Complexity Tracking entry is required.

## Design

### D1 — Token attribution (FR-001–FR-004, DR-002, DR-003)

- `db/core.py`: add `MCPAccessToken.created_by_user_id` and
  `ChangeProposal.decided_via_token_id` with the composite FK and indexes (FK index gate).
- `mcp/auth.create_mcp_access_token(..., issued_by_user_id: str | None = None)`;
  `web/api.post_mcp_token` passes the signed-in owner's id.
- `mcp/server._handler`: set a `SETTLING_TOKEN` ContextVar (in `mcp/catalog.py`) to
  `access_token.client_id` for the duration of `dispatch_tool`.
- `_approve_proposal` / `_reject_proposal` read it and pass
  `settling_token_id=` explicitly to `approve_and_execute_proposal` / `reject_proposal`.
- `tools/application.py`: `_record_decision`, the finance branch and the claim
  `UPDATE` write `decided_via_token_id` when `confirming_principal is None` and a token
  is given; every reset to `proposed` also clears it. A principal and a token together
  record the principal only (a signed-in person is the stronger statement).
- Revocation keeps the row; the attribution reports `revoked: true`.

### D2 — Executing-proposal context (FR-005, FR-006, DR-001)

- `services/core.py`: `_executing_proposal: ContextVar[tuple[str, str] | None]`
  (tenant id, proposal id) and a context manager `executing_proposal(tenant_id, id)`.
- `emit_business_event`: when `action_id is None` and the scope matches the tenant, use
  the scoped id; an explicit non-null id always wins and is never rejected (research
  R2). Resolve this before `require_decision_action` so the playground guard is
  unchanged.
- `approve_and_execute_proposal`: wrap every handler invocation (finance command,
  analytics, master tools, generic handler) in the scope. The `_action_id` allowlist
  stays for handlers that also persist the id on their own rows (e.g. shipments).
- Jobs enqueued by a handler and executed later by the worker are outside the scope and
  unchanged (spec non-goal: events not written by the proposal's execution).

### D3 — Attribution reader (DR-003, DR-004)

- New `services/decision_attribution.py` with `decision_attributions(session,
  tenant_id, proposal_ids)`: one select of proposals, one of tokens, one of users;
  users resolve only if they decided a proposal or issued a token of this tenant
  (generalises `decision_maker_names`).
- Registered in the tenant isolation catalog; the pinned isolation count is bumped.

### D4 — Surfaces (FR-007–FR-011)

- `web/api._proposal_payload` and `proposal_reviews.proposal_review` embed `decider`.
- `services/provenance._deciding_actors` becomes `_creating_decisions` returning the
  `action_id` of each record's *first* event, and none when that first event has no
  decision (today it takes the first event *with* an `action_id`, which names a later
  update as the creator of a record created without a decision); `record_origins` adds `decision` from D3 and keeps
  `actor` for compatibility.
- `services/core.timeline_activity` adds `decision` per event in one batched call.
- `tools/application._proposal_execution_status` adds `decision`.
- Web: `DecisionsPage.tsx` gains Pending / History tabs (`decisions_view` URL
  parameter); one decision opens through the existing `proposal` parameter and
  `ProposalReviewCard`, which already reads any status via the review endpoint; a shared
  `DecisionLine` component renders the `decision` object in `SourceBadge`,
  `ActivityDrawer` and the register's decider column. German ERP terms: "Entscheidung",
  "bestätigt von", "bestätigt über Token", "ausgestellt von", "unbekannt".

## Test Plan (written before implementation)

| Phase | Test | Proves | Red on `main`? |
|---|---|---|---|
| US1 | `tests/test_decision_trail_mcp.py`: approve and reject through the MCP runtime with a web-issued token and a legacy token, then revoke the token and re-read; web approval as unchanged control case | FR-001–FR-004 | yes |
| US1 | `tests/test_decision_trail_migration.py` upgrade/downgrade, following `test_*_migration.py` | DR-002, SC-005 | yes |
| US1 | Cross-tenant token/issuer resolution returns nothing | DR-003 | yes |
| US2 | `tests/test_decision_trail_events.py`: unit test of the scope default and that an explicit id is kept | FR-005 | yes |
| US2 | Regression: payment term, price list, price tier, price-list assignment through a confirmed proposal all reference it | FR-005, SC-002 | yes |
| US2 | Catalog guard: every handler invocation in `approve_and_execute_proposal` goes through one `_run_handler` helper inside the scope; a test registers a temporary mutating tool whose handler emits an event without `action_id` and asserts it is linked, for the generic, master-tool and finance branches; a second test walks every mutating tool in `TOOLS` and asserts it is routed through a branch covered by the first; a positive control emitting outside the scope stays unlinked | FR-006 | yes |
| US3 | History payload with person, MCP and unknown deciders | FR-007, FR-004 | yes |
| US3 | `apps/web/scripts/decision-history.test.mjs`: register columns, tabs, deep link | FR-007, FR-008 | yes |
| US4 | `tests/test_provenance.py` additions: origin names the creating decision; record without decision has none | FR-009, FR-011 | yes |
| US4 | Timeline payload `decision`; `apps/web/scripts/decision-line.test.mjs` for SourceBadge and ActivityDrawer | FR-010, FR-011 | yes |
| All | `apps/web/scripts/decision-trail-browser.mjs`: open an item created through an MCP decision, follow the link to the decision | SC-003 | — |
| All | `npm run i18n:audit`, `make spec-check`, `make lint`, `make test`, `make web-build`, `make docs-generate` + `make docs-catalog-check` | FR-012, SC-006 | — |
| All | Re-run the agent setup against a fresh company and repeat the research queries | SC-001, SC-002 | — |

## Project Structure

### Documentation (this feature)

```text
specs/263-decision-trail/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/decision-attribution.md
└── tasks.md            # next step
```

### Source Code

```text
packages/reality-core/
├── migrations/versions/0093_decision_trail.py
├── src/reality/db/core.py
├── src/reality/mcp/{auth,catalog,server}.py
├── src/reality/services/{core,provenance,proposal_reviews,decision_attribution}.py
├── src/reality/tools/application.py
├── src/reality/web/api.py
└── tests/test_decision_trail_{mcp,events}.py, test_decision_trail_migration.py, test_provenance.py, tests/tenant_isolation/

apps/web/src/
├── api.ts
├── unified/{DecisionsPage,SourceBadge,ActivityDrawer,DecisionLine,routing}.tsx|ts
└── localization dictionaries (de, nl, es)
```

## Migration and Rollback

- Upgrade adds two nullable columns, one composite FK and two indexes; no data is
  rewritten. Downgrade drops them; attribution recorded meanwhile is lost, business data
  is not.
- Code rollback without schema rollback is safe: old code ignores the columns.
- API, scheduler and worker do not run migrations (AGENTS.md); deploy order is
  migration first, then services.

## Review Risks

- **ContextVar scope leaking** across requests: the context manager always resets in
  `finally`; the unit test asserts no scope after an exception.
- **Existing tests pinning `action_id is None`** for tools newly linked: treat as
  expected changes and review each one.
- **Finance commands** run their own locking branch; the scope must wrap
  `execute_finance_command` too, covered by the catalog guard.
- **Wording overclaim**: review that no string says the issuer "confirmed"; the
  sentence is "confirmed through token …" (spec Principle).
- **Docs catalog drift**: output additions to MCP tools require `make docs-generate`.
