# Implementation Plan: Drafted cost reviews

**Branch**: `282-cost-review-draft` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One read service, `services/cost_review_draft.py`, assembles `cost.change` review arguments
for one inventory or contribution scope from held records. It returns them complete, or it
returns open inputs. It is exposed as the read tool `cost.review.draft` (MCP
`cost_review_draft`, also offered to chat). A web endpoint re-drafts on the server with the
person's answers and creates the proposal through `create_change_proposal`, so the browser
never assembles arguments. The opening stock form gains an optional acquisition cost with an
evidence reference. It is recorded as a SourceRecord that the opening movement points to.
The spec 279 guidance steps open a review dialog instead of chat, and chat stays as the
alternative path.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript (React/Vite) for `apps/web`
**Primary Dependencies**: SQLAlchemy 2, Pydantic v2, FastAPI, React
**Storage**: PostgreSQL. No migration: the existing `SourceRecord` and
`Movement.source_record_id` carry the opening cost evidence.
**Testing**: pytest service tests; `node --test` contracts; Playwright fixture browser test;
the live walk-through script from spec 279
**Constraints**: read-only drafting; READ COMMITTED for current reads (the contribution
preview requires it); inventory bounds of 100 movements and 20 receipts; strict tenant scope
**Scale/Scope**: one service, one read tool, one proposal endpoint, one opening-cost
extension, one dialog

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The opening cost enters as a SourceRecord (`source_type` `opening_cost_statement`) with the stated amount, currency and evidence reference as received. The opening Movement points to it through its existing `source_record_id`. The review cites that record as `evidence_source_record_id`. | PASS |
| Reality owns operational state | No document status fields. Reviews stay the authority; drafts are not stored. | PASS |
| Proven schema only | No new table or column. The movement's existing `source_record_id` is the shortest true link. | PASS |
| Tenant + shared service boundaries | One service is called by Web (endpoint), MCP and chat. The endpoint only re-drafts and calls `create_change_proposal`. Every lookup filters `tenant_id`. | PASS |
| Spec/test traceability | Every FR, DR and SC maps to tasks (Requirement Coverage in `tasks.md`). | PASS |
| Explainable web behavior | The dialog shows the business summary. A collapsed technical section lists the opaque IDs, and each record links to the Inspector. | PASS |
| Received values not recomputed | The form records the total acquisition value as the evidence states it; it never multiplies unit cost by quantity. The draft copies stated amounts and derived identities only. The contribution draft takes preview values unchanged. | PASS |
| Smallest coherent design | Rejected: (1) teaching the agent to assemble arguments, which is non-deterministic and duplicates rules; (2) letting the browser assemble arguments, which violates IV and VI; (3) storing drafts, which violates VIII; (4) a separate opening-cost document, which the owner declined. | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/domain/cost_review_draft.py     # NEW pure draft/open-input shapes, method rule
packages/reality-core/src/reality/services/cost_review_draft.py   # NEW inventory + contribution drafting
packages/reality-core/src/reality/services/opening_cost.py        # NEW opening cost statement → SourceRecord
packages/reality-core/src/reality/tools/application.py            # TOOLS["cost.review.draft"]; movement_create opening_cost
packages/reality-core/src/reality/mcp/catalog.py                  # MCP cost_review_draft (read); movement_create schema
packages/reality-core/src/reality/agent/mcp_chat.py               # offer cost_review_draft to chat
packages/reality-core/src/reality/web/api.py                      # GET /cost-review-draft, POST /cost-review-proposals
packages/reality-core/config/command_catalog.yaml                 # capability guidance (read), cost_change_propose → draft first
packages/reality-core/config/tool_catalog.json                    # mcp_topics entry
packages/reality-core/config/tenant_isolation_catalog.yaml        # tool:cost.review.draft
packages/reality-core/config/resource_catalog.yaml                # resource membership + labels.de
packages/reality-core/config/resolution_guidance.json             # review steps: path review_draft, chat alternative; open-input reasons
packages/reality-core/src/reality/domain/resolution_guidance.py   # PATHS += review_draft
packages/reality-core/tests/test_cost_review_draft.py             # NEW service tests
packages/reality-core/tests/test_opening_cost.py                  # NEW opening cost evidence tests
packages/reality-core/tests/test_cost_review_proposal_api.py      # NEW endpoint tests
apps/web/src/api.ts                                                # draft + proposal clients, types
apps/web/src/unified/CostReviewDraftDialog.tsx                     # NEW review dialog
apps/web/src/unified/ResolutionGuidance.tsx                        # review_draft path opens the dialog
apps/web/src/unified/OpeningStockCard.tsx                          # optional cost + evidence fields
apps/web/src/localization.tsx                                      # de/nl/es
apps/web/scripts/cost-review-draft-browser.mjs                     # NEW fixture browser test
apps/web/scripts/cost-review-draft-contract.test.mjs               # NEW contract test
docs/features/receipt-costing.md, docs/WEB_SPEC.md                 # contract updates
```

## Design

### Draft result (domain)

```text
CostReviewDraft
  kind: inventory | contribution
  scope_id
  event_sequence            # the sequence the arguments are bound to
  arguments: dict | None    # complete cost.change arguments, or None
  open_inputs: [ {code, label_code, target?, choices?} ]
  basis: [ {kind, id, role} ]   # records used, by opaque ID
```

- Open-input codes include `valuation_method`, `company_party_missing`,
  `receipt_cost_incomplete`, `opening_cost_missing`, `movement_unclassified`,
  `ownership_ambiguous`, `return_portion_undetermined`, `review_bound_exceeded` and
  `upstream_not_ready`.
- Their labels live in `resolution_guidance.json` (`reasons`), so the translation test from
  spec 279 covers them.
- `valuation_method` carries `choices` (`fifo` always; `specific` only when the item's
  `tracking_type` is `serial` or `lot`) and a `default` of `fifo` (FR-011). Because the
  method is always asked, an inventory draft always has at least this one open input.
  `arguments` holds the rest, with `method` left for the answer.

### Contribution draft

1. Call `costing.contribution_preview(line)`.
2. If `state == "candidate"`, the arguments are `{operation: contribution_review,
   expected_event_sequence: preview.event_sequence, document_line_id,
   expected_candidate_hash, profile: "commercial_v1", profile_confirmed: true,
   revenue_complete: true, economic_at: trace.proposed_economic_at, reason}`.
   `selling_categories` is omitted (DB1 only).
3. Otherwise, one open input `upstream_not_ready`, with the preview's gap as its reason and
   the spec 279 guidance step as its target.

`reason` is a fixed catalog sentence ("Drafted from held evidence and confirmed by …"). The
endpoint fills in the person, and the human proposer can edit the text.

### Inventory draft

The derivation mirrors `inventory_costing._check`, so its own validation is the proof:

- **owner_party_id**: the tenant's party with role `company`. None gives
  `company_party_missing`, with target master data. More than one gives the same input with
  choices.
- **currency**: the currency of the receipts' current manifests. With openings only, the
  currency of the opening cost statement. Mixed currencies give an open input.
- **base_unit**: `item.unit`.
- **history_start**: the first effective movement's `occurred_at` minus one second (as the
  demo seed does). **effective_at**: now. `history_complete_from_zero: true` and
  `receipt_cost_scopes_confirmed: true`; the draft only claims them when every receipt is
  complete.
- **Movement classification**, over effective movements (corrected originals and
  compensations excluded, replacements included, as in `_check`):
  - `shipment` → `economic_issue_ids`
  - `return` → `customer_return_ids`, plus `return_parts` from held links
  - `supplier_return` → `supplier_return_ids`
  - `adjustment` → `loss_movement_ids`
  - `transfer` → none
  - `receipt` → `receipts`
  - `opening_stock` → `openings`
  - Anything the links do not determine becomes an open input: an adjustment with
    `resolves_movement_id`, return parts without an exact issue, or specific selections.
- **Receipts**: for each, `manifest_id` from `receipt_cost(...)["manifest_id"]`. If
  `missing_basis - {review_stale}` is not empty, the input is `receipt_cost_incomplete`
  naming the receipt. `ownership_source_record_id` is the receipt movement's
  `source_record_id`, or else the SourceRecord of the document behind the manifest's goods
  component. If neither exists, the input is `ownership_ambiguous`.
- **Openings**: `evidence_source_record_id` is the opening movement's `source_record_id`
  when that record is an `opening_cost_statement`. `acquisition_cost` is that record's
  stated amount, copied exactly. Otherwise the input is `opening_cost_missing`, pointing to
  the movement correction.
- **Ownership parts**: omitted (whole-item ownership), as `_check` allows. When held
  ownership evidence names more than one owner, the input is `ownership_ambiguous`.
- **Bounds**: more than `MAX_MOVEMENTS` or `MAX_RECEIPTS` gives `review_bound_exceeded`
  with no arguments.
- **expected_event_sequence**: `costing._sequence(session, tenant)` at draft time.

### Opening cost statement

`movement_create` accepts, for `movement_type == "opening_stock"` only, an optional
`opening_cost: {amount, currency, evidence_reference}`. `amount` is the total acquisition
value as the evidence states it; `evidence_reference` is free text naming the document.

Inside the same confirmed proposal execution, `services/opening_cost.py` stores a SourceRecord
through the existing source store service:
- `source_system` `reality`, `source_type` `opening_cost_statement`, external ID = the
  proposal action ID;
- a lossless payload with the stated values, the item and the quantity.

It passes the record's ID as `record_movement(..., source_record_id=...)`. Without
`opening_cost`, behavior is unchanged. The delivery review preview shows the stated value, so
the confirmation covers it. Openings recorded earlier use the existing movement correction:
the replacement opening is recorded with `opening_cost`.

### Proposal endpoint

`POST /tenants/{id}/cost-review-proposals` with `{kind, scope_id, event_sequence, answers:
{method?, owner_party_id?}, request_id}`:

1. Re-run the draft with the answers applied.
2. Refuse with `409 draft_changed` when the draft's sequence differs from `event_sequence`
   or open inputs remain (FR-007). The dialog then re-drafts.
3. Call `create_change_proposal(session, tenant, "cost.change", arguments,
   actor_type="human")` under the caller principal. `preview_cost_change` still enforces
   membership.
4. Return the proposal ID and preview.

`request_id` makes a retried submit idempotent through the existing request binding. There
is no owner requirement here, because confirmation stays in Decisions.

### Web

- **`CostReviewDraftDialog`** (the shared decision-review kit from spec 276): it shows the
  summary in business terms (item or line, owner, method, currency, unit, counts per
  movement class, receipts and openings used, and DB1 for contributions), inputs for each
  open input, and a collapsed "System details" section with the IDs and Inspector links.
  Submitting calls the endpoint. On `409` it re-drafts and names what changed. On success it
  closes and fires `recordsChanged`, so the guidance shows the owner step.
- **Guidance catalog**: `inventory_review`, `inventory_review_renew` and
  `contribution_review` switch to path `review_draft`, and chat becomes their
  `alternative`. `ResolutionGuidance` opens the dialog with the host panel's
  `{kind, scope_id}`.
- **`OpeningStockCard`**: optional "Acquisition value per evidence (total)", with currency
  and "Evidence" fields. Evidence is required when a value is entered. The preview row shows
  them.

### Chat

- `mcp_chat.py` adds `cost_review_draft` to the chat's read tools.
- The `cost_change_propose` capability guidance says: first call `cost_review_draft`,
  propose its arguments unchanged, and ask the person only about `open_inputs`, using their
  labels.
- The spec 279 chat prompts stay; the guidance does the steering.

### Data and migration impact

None. Rollback: revert. The response of the new endpoint and tool is additive, and
`movement_create` keeps its old contract when `opening_cost` is absent.

### Failure, security, and tenant behavior

- Cross-tenant scope, party or evidence IDs behave as not found.
- The draft performs no flush (`no_autoflush`), and a test asserts no rows or events are
  added.
- A contribution preview conflict falls back to `upstream_not_ready`, as in spec 279.
- The endpoint refuses a drifted draft instead of proposing stale arguments.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_cost_review_draft.py::test_draft_shape_for_both_kinds` | module absent |
| FR-002 | service | `::test_contribution_draft_equals_preview_values` | absent |
| FR-003 | service | `::test_inventory_draft_passes_inventory_check` (fixtures from `test_inventory_costing_services`) | absent |
| FR-004 | service | `::test_open_input_*` (company party, receipt incomplete, opening cost, unclassified movement, ambiguous ownership) | absent |
| FR-005 | service | `::test_complete_arguments_pass_preview_cost_change` | absent |
| FR-006 | browser | `cost-review-draft-browser.mjs`: dialog summary, no IDs visible, submit creates proposal | dialog absent |
| FR-007 | api + browser | `test_cost_review_proposal_api.py::test_drifted_draft_is_refused`; browser re-draft | absent |
| FR-008 | service | `test_opening_cost.py::test_opening_with_cost_links_statement`, `::test_opening_without_cost_unchanged`, `::test_replacement_opening_carries_cost` | no `opening_cost` |
| FR-009 | service + agent | MCP parity test; `mcp_chat` tool list includes the draft; capability guidance text test | absent |
| FR-010 | service | `::test_bounds_report_instead_of_truncate` | absent |
| FR-011 | service | `::test_method_choices_follow_tracking_type` | absent |
| DR-001 | service | `::test_draft_writes_nothing` | guard |
| DR-002 | service | arguments reference opaque IDs only | guard |
| DR-003 | api | the endpoint uses the service (monkeypatch spy) | absent |
| DR-004 | service + api | cross-tenant not found for scope, party and evidence, with own-company positive control | absent |
| DR-005 | service | the statement is a SourceRecord linked by `Movement.source_record_id`; no new column | absent |
| SC-001 | live | re-run `missing-basis-walkthrough-live.mjs` in a business company, extended with the dialog path | blocked today |
| SC-002 | agent | tool-sequence test: a derivable contribution gives draft → propose with zero questions; an inventory scope asks only for the method | absent |
| SC-003 | service | `::test_demo_profile_scopes_are_drafted_equivalently` | absent |

Negative tests are paired with positive controls (memory: vacuous negatives).

## Rollout and Rollback

- The fields and tool are additive, with no migration.
- Run `make docs-generate`, because the MCP schema gains a tool and a field.
- Rollback is revert.
- Completeness gates to run before calling it done: `test_application_catalog.py`,
  `test_tool_catalog.py`, `tests/tenant_isolation`, `test_reporting_graph_coverage.py`,
  `test_schema_indexes.py`, the coverage matrix and the isolation catalog count.

## Review Risks

- **Classification drift from `_check`.** The draft duplicates `_check`'s movement rules.
  Mitigation: every complete draft is fed to `_check` in tests, and SC-003 compares against
  the demo seed's hand-built arguments.
- **Ownership evidence for receipts.** Falling back to the supplier invoice's SourceRecord is
  an interpretation. Tests prove `_check` accepts it. If a reviewer rejects that link, the
  input becomes `ownership_ambiguous` instead.
- **Opening value semantics.** Total versus unit value confuses clerks. The form states
  "total as per evidence" and shows the per-unit figure only as a read-time hint.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Implementation notes (2026-09-26)

- **Earlier openings without cost** are corrected away with the existing movement correction
  and recorded again with cost. The correction tool takes no `opening_cost`, and none was
  needed.
- **Added open-input codes:** `currency_ambiguous` (receipts or openings in more than one
  currency), plus the reason codes `inventory_history_empty`, `inputs_changed` and
  `specific_selection_required`. All have catalog wording.
- **Tenant policy:** it admits `store_source_record` during proposal execution only for a
  `movement_create` opening whose saved intent carries `opening_cost`.
- **Opening verification:** both opening verifications accept exactly the
  `opening_cost_statement` that the same proposal recorded, and nothing else.
- **Idempotent endpoint:** the proposal endpoint compares the drafted arguments in the
  proposal's normalized form, because the stored input normalizes timestamps and omitted
  fields.
- **Demo seed finding:** the demo seed fixes the opening cost at 6 per unit in code. No source
  states it, so the draft keeps those openings open (SC-003 reworded).
- **Chat proposals (FR-012).** The live chat run first showed the agent not calling the
  draft. After the tool descriptions were sharpened, it drafted but then mistyped copied
  identifiers, and it lost them between turns (chat history carries only answer text).
  The fix is `propose_drafted_review` in `services/cost_review_draft.py`, shared by
  `POST /cost-review-proposals` and the MCP propose tool `cost_review_propose`, which
  takes kind, scope and answers only. Inventory scopes resolve by ID, SKU, exact name or
  unique partial name. Idempotency ignores the draft's "now" cutoff at an unchanged event
  sequence.
- **Live finding outside this spec.** Sales invoices recorded through the web form state
  only a gross amount. The contribution preview then reports `received_net_missing`, so
  DB1 cannot be proven for them. It needs its own spec: the invoice form should state net
  and tax as received.
