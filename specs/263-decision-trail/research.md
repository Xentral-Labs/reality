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
`emit_business_event` uses that id when the caller passes none. A caller passing a
*different* id inside the scope raises `InvalidOperation` (a handler must not
substitute its causal identity). Explicit threading stays where it exists.
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
