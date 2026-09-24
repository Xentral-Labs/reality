# Research: Decision Trail

All findings were read from `origin/main` at `4052ea0b` and measured on the local
company "CanisPro Tiernahrung MCP-Reality-Test 2026-09-24".

## R1 — Why MCP decisions name nobody

- `mcp/catalog.py` `_approve_proposal` and `_reject_proposal` pass
  `confirming_principal=_analytics_caller()`, which reads
  `services/analytics/reports.CALLER`. Only the web chat stream and the analytics API
  set that ContextVar; `mcp/server.py` never does. The value is always `None`.
- `mcp/auth.DatabaseTokenVerifier.verify_token` already returns
  `AccessToken(client_id=record.id, subject=record.tenant_id)`. The settling token's
  id is therefore available in `mcp/server._handler` through `get_access_token()`
  without any new authentication.
- `MCPAccessToken` has no user column. The only issuing path is
  `POST /settings/mcp/tokens` (`web/api.py`), which calls `require_company_owner` and
  so has a signed-in owner at hand.

**Decision**: record the token on the decision and the issuer on the token.
**Rejected**: writing the issuer into `decided_by_user_id` — it would state that the
issuer decided, which Reality cannot observe (spec FR-003); per-user OAuth and
web-only confirmation were rejected by the owner on 2026-09-24.

## R2 — Why some events carry no decision

`approve_and_execute_proposal` sets `arguments["_action_id"] = proposal.id` only for
a hard-coded set of 31 tools, and each handler must then pop the key and thread it to
its service. `payment_term_create`, `price_list_create`, `price_tier_create` and
`party_price_list_assign` are not in the set; nor are finance-command-routed or later
tools unless someone remembers to add them. Across all local companies, 24 event types
occur without `action_id`; many of those come from seeding and scenarios, which is
correct, but the four families above never carry one even when a proposal wrote them.

All business events are written by one function, `services/core.emit_business_event`,
which already accepts `action_id`.

**Decision**: while a proposal executes, a scoped context names it, and
`emit_business_event` uses that id when the caller passes none. An explicit id always
wins and is never rejected: services such as costing and commercial matching thread an
`action` they were handed, and a production refusal on mismatch would turn an
attribution improvement into an execution failure for flows this feature does not
otherwise touch. The existing playground guard keeps enforcing identity where it
already does. Explicit threading stays where it exists.
**Rejected**: extending the allowlist (it drifted once and would drift again);
threading `_action_id` into every handler signature (dozens of services changed for
no additional truth).

The playground guard `tenant_policy.require_decision_action` compares `action_id` with
the playground decision's proposal id. The default is resolved *before* that guard is
called, so the guard sees the same id it expects today.

## R3 — Where the history register went

Specs 054 and 055 are `Approved`; the API `GET /change-proposals?status=history` and
`decision_maker_names` exist and are tested. `apps/web/src/unified/DecisionsPage.tsx`
calls `api.changeProposals(tenant, "pending", …)` only, identically at the initial
public release `3b7978c7`. The register was not ported to the unified workspace.

**Decision**: restore it as a second tab of the Decisions page on the shared
`WorkList` components, reusing the existing argument presentation.

## R4 — Opening one decision

`services/proposal_reviews.proposal_review` reads a proposal of any status and is
served by `GET /change-proposals/{id}/review`. The MCP/CLI read for one decision is the
`proposal_execution_status` tool.

**Decision**: add the attribution read model to both, and deep-link with
`/app/decisions?decision=<id>`.

## R5 — Record origin and activities

- `services/provenance._deciding_actors` already resolves, per record, the first
  event with an `action_id` and then its `decided_by_user_id`. It returns a name only.
- `services/core.timeline_activity` builds activity items in batch and already
  returns `action_id`; `ActivityDrawer.tsx` renders it as a raw "Action ID".

**Decision**: both call one batched attribution reader and return a `decision`
object; the browser only renders it (spec DR-004).

## Analysis pass (2026-09-24)

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| A1 | HIGH | Plan D2 rejected a mismatching explicit `action_id`; costing and commercial matching thread their own `action` argument, so the refusal could fail executions this feature does not otherwise change. | Explicit id always wins (R2, plan D2 and test plan, T023, T029). |
| A2 | HIGH | `_deciding_actors` takes the first event *with* an `action_id`, so a record created without a decision and later updated through one would be shown as created by that decision (violates FR-011, SC-004). | Use the record's first event only (plan D4, T039, T042). |
| A3 | MEDIUM | FR-007 inherits 054 FR-006 (≤ 25 rows per page); the API default is 50 and T033 did not pin it. | T033 pins 25 rows per page. |
| A4 | MEDIUM | New public helpers in discovered modules (`executing_proposal` in `services/core`) and the explicit reader need isolation classification, or `test_application_catalog.py` fails in CI only. | T011, T027 classify; Phase 2 checkpoint runs the catalog gates. |
| A5 | LOW | Assumption names a CLI token path that does not exist; `create_mcp_access_token` is only called from the web. | Harmless: the no-issuer branch still covers tests and future paths. |
| A6 | LOW | MCP output additions may not appear in generated Tool Usage (inputs only). | T048 regenerates and the catalog check confirms either way. |

Coverage: every FR-001–FR-012 and DR-001–DR-005 has at least one test task and one
implementation task (tasks.md, Requirement Coverage). No CRITICAL finding; no
unmapped requirement; no task without a requirement or gate.
