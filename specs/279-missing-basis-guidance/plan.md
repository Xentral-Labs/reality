# Implementation Plan: Guidance for missing basis

**Branch**: `279-missing-basis-guidance` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Services already know why a basis is missing. They report it as raw codes, and the web
prints those codes. This plan adds three things:

1. A static **resolution guidance catalog** (`config/resolution_guidance.json`). It holds
   English labels and explanations for every reason, step and blocker code, plus each
   step's required role and path type. It is validated at catalog load against the
   action discovery forms, and it is served with the application catalog the web
   already reads.
2. A read-time derivation of **ordered steps** for the scopes whose state depends on
   held records: inventory cost, contribution cost and stored projections. It lives in
   one new service module and is attached to the existing cost query and projection
   metadata responses.
3. One web component, **`ResolutionGuidance`**. It renders a reason and its steps and
   routes each step through a path that already exists: an action form, the chat
   handoff, a decision review or system status.

There are no new tables, endpoints or write paths.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript (React/Vite) for `apps/web`
**Primary Dependencies**: SQLAlchemy 2, Pydantic v2, FastAPI, PyYAML (JSON catalog), React
**Storage**: PostgreSQL; no schema change
**Testing**: pytest service tests; `node --test` contract tests in `apps/web/scripts`;
Playwright browser scripts (`cost-explanation-browser.mjs`, `projection-freshness-browser.mjs`)
**Project Type**: backend services plus the unified web app
**Constraints**: read-only derivation; READ COMMITTED for current cost reads; strict
tenant scope; bounded work per read (existing receipt bound in `inventory_costing`)
**Scale/Scope**: one catalog, one service module, one web component, eight surfaces

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Guidance only reads existing evidence and Reality: receipts and their cost bases, reviews, proposals and projection checkpoints. Steps link to those records by opaque ID. No stage is added or bypassed. | PASS |
| Reality owns operational state | Nothing is added to documents. Cost and projection states stay derived by their existing services. | PASS |
| Proven schema only | No migration. Two response shapes grow: `guidance.steps` on the cost query, and `failure_code` plus `guidance` on projection metadata. The catalog is a config file like `action_discovery.json`. | PASS |
| Tenant + shared service boundaries | Derivation runs inside `cost.query.get` and `projection_metadata`, which Web, MCP (`cost_query_get`) and chat already call. Every query filters `tenant_id`. The web never writes; action paths reuse existing commands and confirmation. | PASS |
| Spec/test traceability | Every FR and DR maps to a test task in `tasks.md` (Requirement Coverage). | PASS |
| Explainable web behavior | Each step links to its record (receipt movement, review, proposal) through the Inspector or Decisions. The existing "Inspect cost basis" link stays. | PASS |
| Received values not recomputed | No value is computed. The inventory "Unit cost" field is removed rather than derived from acquisition value and quantity, because that would introduce a rounding authority. | PASS |
| Smallest coherent design | Rejected alternatives: hard-coding step logic per page in the browser (duplicates business rules and violates VI); a new `/guidance` endpoint (adds an isolation surface for data the existing reads already return); a stored guidance table (violates VIII). | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/config/resolution_guidance.json              # NEW catalog
packages/reality-core/src/reality/domain/resolution_guidance.py    # NEW pure builder + catalog validation
packages/reality-core/src/reality/domain/cost_query.py             # cost_guidance gains reason_code, steps, writable
packages/reality-core/src/reality/services/cost_resolution.py      # NEW read-time step derivation for cost scopes
packages/reality-core/src/reality/services/cost_query.py           # attach steps; expose carrying_value_state
packages/reality-core/src/reality/services/projections.py          # failure_code + guidance on projection_metadata
packages/reality-core/src/reality/services/attention_reads.py      # cost findings carry the scope's guidance
packages/reality-core/src/reality/catalogs.py                      # load + validate + serve the catalog
packages/reality-core/tests/test_resolution_guidance.py            # NEW catalog + builder tests
packages/reality-core/tests/test_cost_resolution.py                # NEW step derivation service tests
packages/reality-core/tests/test_cost_query.py                     # guidance shape, compatibility
packages/reality-core/tests/test_projection_jobs.py                # failure_code + guidance
packages/reality-core/tests/test_attention_reads.py                # cost finding guidance
apps/web/src/api.ts                                                # types: ResolutionGuidance, catalog, metadata
apps/web/src/unified/ResolutionGuidance.tsx                        # NEW shared component
apps/web/src/unified/resolutionGuidance.ts                         # NEW path → handler mapping, chat draft event
apps/web/src/unified/CostExplanation.tsx                           # use component; drop raw codes, unit cost
apps/web/src/unified/ProjectionFreshness.tsx                       # readiness sentence, failure reason, status link
apps/web/src/unified/AttentionPage.tsx                             # localized class title/guidance; cost steps
apps/web/src/unified/Shell.tsx, ChatPage.tsx                       # open-chat event carries a draft
apps/web/src/unified/analytics/InventoryValuation.tsx             # unavailable explanation
apps/web/src/unified/ReportExplanation.tsx, ProjectionDataDialog.tsx # price determination input
apps/web/src/unified/ReportDataTable.tsx                           # blocker labels + step
apps/web/src/unified/StorylineNarrator.tsx, DataSourcesPage.tsx    # labels + step
apps/web/src/localization.tsx                                      # de/nl/es labels
apps/web/scripts/resolution-guidance-localization.test.mjs         # NEW catalog translation test
apps/web/scripts/exception-catalog-localization.test.mjs           # NEW exception title/guidance test
apps/web/scripts/resolution-guidance-contract.test.mjs             # NEW component contract test
docs/WEB_SPEC.md, docs/features/receipt-costing.md                 # contract updates
```

Dependency direction: the domain builder is pure; `cost_resolution` depends on existing
cost services; `cost_query` and `projections` call it; transports stay unchanged.

## Design

### Catalog

`config/resolution_guidance.json` has this shape:

```json
{
  "version": 1,
  "reasons": {
    "inventory_scope_not_reviewed": {
      "label": "No confirmed acquisition cost for this item yet",
      "explanation": "Stock value appears once receipts carry confirmed cost and an owner has confirmed the item's cost review."
    }
  },
  "steps": {
    "receipt_cost_evidence": {
      "label": "Confirm the cost of each receipt",
      "role": "member",
      "path": "chat",
      "chat_prompt": "Prepare the receipt cost review for {scope}.",
      "alternative": {"path": "web_form", "form": "supplier_invoice_record",
                      "label": "Record the supplier invoice first"}
    },
    "owner_confirmation": {"label": "Confirm the proposal", "role": "owner", "path": "decision_review"}
  },
  "blockers": {"prepayment_invoice_missing": {"label": "…", "step": "sales_invoice_record_step"}}
}
```

- **Roles**: `member`, `owner`, `operator`.
- **Paths**: `web_form` (it must name an `action_discovery.json` form), `chat`,
  `decision_review`, `system_status` and `none`.

`catalogs.py` validates the catalog when it loads:
- every form exists in action discovery;
- every `chat_prompt` contains `{scope}`;
- every role and path is in the closed set;
- each `blockers[*].step` exists.

The catalog is served as `resolution_guidance` in the application catalog response,
beside `discovery`. The web uses it to label static codes (blockers, storyline checks)
that carry no per-scope steps.

Every code that a service can emit is listed once in `domain/resolution_guidance.py`
(`EMITTED_CODES`). A pytest asserts `EMITTED_CODES ⊆ catalog`, and the node test asserts
that every catalog label and explanation has de/nl/es translations. Together they meet
FR-004.

### Step derivation (`services/cost_resolution.py`)

`inventory_steps(session, tenant, item_id, result)` uses the existing `inventory_cost`
result. It lists the item's owned receipt Movements, bounded by the existing
`receipt_limit`, and calls `receipt_cost` for each one. The steps, in order:

1. `receipt_cost_evidence`
   - **done** when every receipt's `missing_basis ⊆ {review_stale}`.
   - otherwise **open**, with targets = receipt movement IDs whose basis is incomplete
     (at most 10, plus a count).
   - The alternative web form is offered when any target's basis is `not_admitted`.
2. `inventory_review` (`inventory_review_renew` when stale)
   - **blocked** until step 1 is done;
   - **open** when step 1 is done and there is no current review;
   - **done** when the review is current.
3. `owner_confirmation`
   - **open**, with target = proposal ID, when a `ChangeProposal` exists with type
     `tool:cost.change`, status `proposed`, and an `input` naming this `item_id` and an
     inventory operation;
   - otherwise **blocked** behind step 2, or **done**.
   - The lookup filters by `tenant_id`, type and status first. Only the few proposed
     rows are parsed.

`contribution_steps(session, tenant, line_id, result)`: when the line has no current
contribution review, it calls the public, read-only `costing.contribution_preview` (the current cost read already
runs at READ COMMITTED, which it requires) to find the **upstream** gap, then maps it:

| Upstream gap | Steps |
|---|---|
| `inventory_scope_not_reviewed`, `inventory_review_stale`, `consumption_not_reviewed`, `consumption_after_cutoff` | inventory steps for the line's item, then `contribution_review`, then `owner_confirmation` |
| `commercial_match_not_reviewed` | `contribution_review` (chat), then `owner_confirmation` |
| `selling_costs_unknown`, `selling_category:*` | `selling_cost_review` (chat); affects DB2 only and never blocks DB1 steps |
| `received_net_missing`, `billed_order_line_missing`, `unsupported_*`, `*_scope_mismatch`, `negative_revenue_requires_match`, `corrected_fulfilment_unsupported` | one step with path `none`: the explanation says which source data or scope limit prevents a contribution |

A stale contribution follows the same mapping, so a stale inventory review is named as
the cause (US2 scenario 2).

Steps are only derived for current reads. Historical reads (`review_id` given) return
`steps: []`.

`writable` is `False` when `tenant_policy.require_core_operation(session, tenant,
"execute_cost_change")` would refuse. It is checked without raising, through a small
predicate added beside it.

### Cost query response

`cost_guidance(...)` keeps `stage`, `reason`, `next_action`, `missing_basis`, `scope`
and `explanation_links` unchanged, for MCP clients. It adds:

- `reason_code`, a catalog reason: the first missing basis, else the stage;
- `steps`: a list of `{code, state, role, path, form?, targets, proposal_id?, alternative?}`;
- `writable`;
- `value_reasons`, for example `{"carrying_value": "assessment_missing"}`, taken from
  `carrying_value_state` in the basis result.

### Projection metadata

`projection_state_expressions` already selects the latest failed `projections.refresh` run.
It also selects that run's `last_error_code` (a code only, never `failure_detail`).
`projection_metadata` adds `failure_code` and `guidance`:

- `reason_code`: `projection_uninitialized`, `projection_pending` or `projection_failed`;
- one step, `system_status`, with role `operator`.

The web adds the readiness sentence by reading the existing
`GET /tenants/{id}/readiness` once per page, as HomePulse does. That is display of two
service facts; no ordering rule lives in the browser.

### Exceptions

- Title: the web renders `t(catalog label)` looked up by `class_id` in the application
  catalog's exception classes. That list gains `label` and `clears_through` next to its
  IDs.
- Resolution text: `t(guidance)`.
- Cost findings: for the four cost classes, `attention_detail` adds `resolution`. It is
  the `cost.query.get` guidance for the finding's record (item → inventory, document line
  → contribution), computed through the shared cost query read.

### Web presentation

`ResolutionGuidance` takes `{guidance, catalog, viewerRole, scopeLabel}` and renders:

- `t(reason.label)` and `t(reason.explanation)`;
- an ordered list of steps with done, open and blocked markers, the first open step
  emphasized;
- one control per open step:
  - `web_form`: `useActionDiscovery().open(form, prefill)`, with a prefill only where
    `paletteActionPrefill` allows it;
  - `chat`: dispatches `reality:open-chat` with `detail.draft =
    t(chat_prompt).replace("{scope}", scopeLabel)`. Shell stores the draft and passes it
    as `initialDraft` to the docked `ChatPage`. On the `/app/chat` route the page reads
    the same event. `ChatPage` resets `question` when a new `initialDraft` arrives. It is
    never sent automatically;
  - `decision_review`: `navigate({route: "decisions", proposal})`;
  - `system_status`: navigate to Home, where HomePulse shows readiness.
- After a form closes, a chat proposal is created or a decision is taken, the host
  panel re-reads its service result; it never marks a step done locally.
- A chat step in a company without AI credentials still opens chat, which already
  shows the existing "AI credentials not configured" notice with its Settings link.
- When `step.role === "owner"` and the viewer is not an owner, or `!writable`: a sentence
  naming who must act ("A company owner must confirm this", "This company is read-only")
  instead of a control.
- Operator steps: a sentence with the system status link.
- Unknown codes: the generic "Missing basis" sentence and no raw code (edge case).

`CostExplanation` changes:
- replaces the readiness section with `ResolutionGuidance`;
- removes the duplicate `guidance.reason`;
- renders the missing-basis list through catalog labels;
- drops the inventory "Unit cost" field;
- shows `t(value_reasons.carrying_value)` under a missing carrying value.

The other surfaces:
- **Price determination:** gets party and item inputs (shared autocomplete). It calls
  the existing `GET /prices/resolve` with quantity 1, the report's direction, the
  company currency and the item's base unit. A 404 renders the `no_applicable_price`
  reason, with step path `none` and role `operator`, because no web or MCP writer for
  price lists exists (verified: MCP only reads price lists).
- **Delivery blockers** (`ReportDataTable`): the catalog label, plus the blocker's
  step: `prepayment_invoice_missing` → `sales_invoice_record`; `commitment_hold` →
  `commitment_hold_release` with the commitment prefilled; `party_delivery_hold` →
  `party_delivery_hold_release`; `insufficient_stock` → `receipt`.
- **Storyline checks and Data sources:** catalog labels; Data sources without an import
  job gets a step to the existing source configuration view.

### Data and migration impact

None. Rollback is reverting the change. Response fields are additive, and old clients
ignore them.

### Failure, security, and tenant behavior

- Every query in `cost_resolution` filters `tenant_id`. Cross-tenant scope IDs raise
  `NotFound` through the existing `_row` helpers.
- The proposal lookup never exposes a proposal of another company.
- Chat drafts carry only the scope label and opaque ID of the active company.
- Guidance derivation performs no flush (`session.no_autoflush`, as the cost readers
  do). A test asserts that the event sequence and row counts are unchanged.
- The bounded receipt loop reuses the existing limit. When it is exceeded, the step
  reports `open` with a count instead of failing the read.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_cost_resolution.py::test_inventory_steps_in_order_for_each_state` | no `steps` key |
| FR-002 | service | `test_cost_resolution.py::test_first_open_step_is_upstream_receipt` | missing |
| FR-003 | service | `test_cost_resolution.py::test_contribution_reports_inventory_blocker`, `::test_stale_contribution_names_stale_inventory` | only `commercial_match_not_reviewed` |
| FR-004 | unit + node | `test_resolution_guidance.py::test_emitted_codes_are_cataloged`; `resolution-guidance-localization.test.mjs` | catalog absent |
| FR-005 | node + browser | `resolution-guidance-contract.test.mjs` (no `<code>` of tool names); `cost-explanation-browser.mjs` German assertions | raw codes present |
| FR-006 | node | `resolution-guidance-contract.test.mjs` component structure | component absent |
| FR-007 | browser | `cost-explanation-browser.mjs` form step opens `supplier_invoice_record` | no control |
| FR-008 | browser | `cost-explanation-browser.mjs` chat step fills the composer; no request sent | no handoff |
| FR-009 | service + browser | `test_cost_resolution.py::test_sandbox_not_writable`; browser member vs owner | always shown |
| FR-010 | node + browser | contract: no inventory unit cost field; carrying value reason text | field shown |
| FR-011 | service + browser | `test_projection_jobs.py::test_failed_metadata_carries_failure_code`; `projection-freshness-browser.mjs` | no `failure_code` |
| FR-012 | node + service | `exception-catalog-localization.test.mjs`; `test_attention_reads.py::test_cost_finding_carries_resolution` | English only |
| FR-013 | browser | `unified-operations-browser.mjs` price determination input | no input |
| FR-014 | node | `resolution-guidance-contract.test.mjs` blocker/storyline/data-source labels | raw codes |
| DR-001 | service | `test_cost_resolution.py::test_guidance_writes_nothing` | — (guard) |
| DR-002 | service | `test_cost_resolution.py::test_owner_step_links_proposal_id` | missing |
| DR-003 | service | `test_cost_query.py::test_mcp_cost_query_returns_steps` | missing |
| DR-004 | service | `test_cost_resolution.py::test_cross_tenant_scope_not_found`, `::test_other_company_proposal_ignored` | missing |
| DR-005 | review | `git diff --stat` shows no migration; `make spec-check` | — |

Negative tests are paired with a positive control, so they cannot pass for the wrong
reason. For example, "the other company's proposal is ignored" runs next to "the own
company's proposal is linked".

## Rollout and Rollback

The fields are additive and there are no migrations. The web tolerates guidance without
`steps` (an older API), falling back to the reason sentence. Rollback: revert the commit.
After the catalog change, run `make docs-generate` and commit the regenerated Tool Usage
output if the generator picks up the catalog response.

## Review Risks

- **Read cost of step derivation.** One `receipt_cost` call per receipt could be slow for
  items with many receipts. It is capped by the existing receipt limit. Measure with the
  scale fixture on a quiet machine before merge, and compare statement counts rather than
  wall time.
- **Chat draft wording.** A prompt that the agent misreads leads to a wrong proposal. It
  still needs an explicit confirmation, but each prompt is tested once against the chat
  catalog tools.
- **Catalog drift.** A new service code without a catalog entry falls back to the generic
  sentence. `EMITTED_CODES` must be updated with the service; the pytest makes forgetting
  visible.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
