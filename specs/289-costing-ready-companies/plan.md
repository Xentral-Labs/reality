# Implementation Plan: Every business company knows its own business partner

**Branch**: `289-costing-ready-companies` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

This plan adds a company business partner in two places:
1. **At creation.** `company_setup.create_company` records the company business partner in
   the same transaction that creates an ordinary business company. It is named as requested,
   and its SourceRecord states that request.
2. **For existing companies.** One new proposal command, `company_party_record`, records the
   partner with the current company name after confirmation, through the master data service
   `create_parties`. The cost review draft offers that command in its `company_party_missing`
   input, or names the waiting proposal, for the web, chat and MCP.

There is no schema change and no migration.

## Findings that shape the plan (2026-09-27)

- **Creation paths.** The product creates companies only through `/api/company-setup` →
  `company_setup.create_company`. Its `environment == "business"` branch calls
  `create_tenant` and adds the owner membership and `OrdinaryCompanyCreation` (the replay
  marker, keyed by `request_key`).
  - The legacy `POST /api/v1/companies` (`api.createCompany`) has no caller in `apps/web/src`.
    Its `guided_demo` flag runs `ensure_demo`, which only seeds a company without parties.
  - The CLI `tenant create` is a developer path.
  - Both stay unchanged. "Ordinary business company" in FR-001 means the company setup
    `business` environment.
- **Master data workspace.** `reference_workspace.prepare_reference` supports the families
  customer, supplier, item and location only (`FAMILIES`), not "company". It also cannot
  refuse a stale confirmation. A dedicated command is smaller than widening the workspace, and
  it is the only way to meet FR-006. It still records through `create_parties`, the service
  behind `party_create` (FR-005).
- **The draft.** `cost_review_draft._company_parties` treats a party with role `company` or type
  `company` as the company itself. It picks the only one, asks among several, and reports
  `company_party_missing` when there is none. The web dialog shows a picker only when there are
  choices.
- **Empty sandboxes and Demo Data.** `demo_data.preview` connects only to a sandbox without
  parties. Empty sandboxes are therefore untouched (FR-003); they do not go through the
  business branch anyway.
- **Spec 286 gate.** New refusals in `tools/application.py` and `services/cost_review_draft.py`
  (in-scope modules) must be coded, with de/nl/es translations.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript (React/Vite)
**Storage**: PostgreSQL, no migration. Party, PartyRole and SourceRecord already exist.
**Testing**:
- pytest: service, proposal, draft, MCP parity and catalog gates;
- `node --test`: the web contract;
- a Playwright fixture browser test;
- a live walk-through.

**Constraints**:
- tenant-scoped;
- confirmation before any write to an existing company;
- idempotent under request replay.

**Scale/Scope**: one creation branch, one command, one draft input, one dialog button, one MCP
tool.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The partner created with a company carries a SourceRecord (`source_system="reality"`, `source_type="company_setup"`, `external_id=<request_key>`) that states the requested name and role. The partner created through the command carries the proposal's master-data source, as `party_create` does today. | PASS |
| Reality owns operational state | No document or status fields. | PASS |
| Proven schema only | No new table or column. | PASS |
| Tenant + shared service boundaries | Creation stays in `company_setup`. The command's handler calls `create_parties`. Web, chat and MCP propose through `create_change_proposal`, and no adapter creates a party. | PASS |
| Spec/test traceability | Every FR and DR maps to tasks. | PASS |
| Explainable web behavior | The draft names the prefilled name before anything is proposed. The proposal is reviewed in Decisions like any other, and the partner links to its source. | PASS |
| Mutating chat actions require confirmation | The command is a proposal with `requires_confirmation`; nothing is recorded before an owner confirms. | PASS |
| Smallest coherent design | Rejected: (1) a migration backfill, which the owner declined and which creates records without a confirming person; (2) widening the master data workspace with a "company" family, which is more surface and still has no stale refusal; (3) creating the partner on the fly when the draft is read, which is a read with a side effect. | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/company_setup.py        # business branch records the company partner (FR-001/002, DR-001)
packages/reality-core/src/reality/services/company_party.py        # NEW propose/record the company partner: current name, waiting proposal, stale refusal
packages/reality-core/src/reality/tools/application.py             # tool company_party_record (proposal, confirmation, handler)
packages/reality-core/src/reality/services/cost_review_draft.py    # company_party_missing input carries {action | proposal_id, name}
packages/reality-core/src/reality/domain/cost_review_draft.py      # open_input accepts the action detail
packages/reality-core/src/reality/mcp/catalog.py                   # company_party_record_propose (application_name)
packages/reality-core/src/reality/web/api.py                       # POST /company-party/prepare → proposal detail
packages/reality-core/config/command_catalog.yaml, tool_catalog.json, resource_catalog.yaml (labels.de),
  tenant_isolation_catalog.yaml, action_discovery.json               # catalog gates for the new command
packages/reality-core/config/service_refusals.json                 # codes for the new refusals (spec 286)
packages/reality-core/config/resolution_guidance.json              # company_party_missing wording names the action
packages/reality-core/tests/test_company_party.py                  # NEW creation, command, draft, parity tests
apps/web/src/api.ts, unified/CostReviewDraftDialog.tsx, localization.tsx  # the button, waiting link, de/nl/es
apps/web/scripts/company-party-contract.test.mjs                   # NEW contract
apps/web/scripts/company-party-browser.mjs                         # NEW browser proof (added to browser-suite.json)
apps/web/scripts/fixtures/action-reference.json                    # mirrors the new command
docs/features/company-setup-demo.md, docs/features/master_data.md  # contract notes
```

## Design

### At creation (FR-001, FR-002, FR-003, DR-001)

In the `business` branch of `company_setup.create_company`, after `create_tenant` and before
the commit, the service calls `create_party` with:
- `name=name`, `party_type="company"`, `roles=["company"]`;
- `source_system="reality"` and `external_id=f"company-setup:{request_key}"`;
- a source payload of `{"name": name, "roles": ["company"], "request_key": request_key}`.

The source payload holds only the name and role the person requested; nothing is derived.
- **Replay:** it is covered by the existing `OrdinaryCompanyCreation` marker. A replayed
  request returns before this branch, so a second partner is impossible. A test pins it.
- **Other environments:** demo, practice, sandbox and Storyline paths are untouched.

### The command `company_party_record` (FR-004, FR-005, FR-006, DR-003, DR-004)

- **Preview** (`company_party.preview`):
  - refuses when a company partner exists (`company_party_exists`);
  - refuses demo and practice companies (the business mutation policy);
  - otherwise returns `{name: <current tenant name>, roles: ["company"]}`.

  The arguments are empty. The name comes from the server, so a client cannot record another
  name.
- **Proposal:** `create_change_proposal(tenant, "company_party_record", {})` with confirmation
  required. It is idempotent per request id, like the other proposals, and is confirmed by the
  same principals as `party_create` (A3).
- **Handler at confirmation:**
  - rechecks under the master data lock that no company partner exists; otherwise it refuses
    with `company_party_exists` ("A company business partner already exists.");
  - calls `create_parties` with the previewed record and the proposal's action id, so the
    party carries the proposal's master-data source.
- **Waiting proposal** (`company_party.waiting`): the newest `proposed` proposal of type
  `tool:company_party_record` in the tenant.

### The draft (FR-004, FR-006, FR-008)

`company_party_missing` with no candidates carries one of two details:
- `{"proposal_id": <id>}` while a proposal waits;
- otherwise `{"action": "company_party_record", "name": <current company name>}`.

The action is offered only where recording master data is allowed
(`tenant_policy.business_operation_allowed(session, tenant, "create_party")`). In a practice,
demo or archived company, the input keeps today's plain form (A2).

With candidates it keeps today's `choices`. `domain.open_input` accepts the two optional keys.
The MCP `cost_review_draft` read returns the same input, so chat and MCP see the same prefilled
name (FR-007).

### Web (FR-004, FR-006, FR-007)

- **Button:** `CostReviewDraftDialog` shows "Record my company as a business partner" with the
  prefilled name ("{name} will be recorded as your company.").
- **Proposal:** the button posts `/api/tenants/{t}/company-party/prepare`, which returns the
  proposal detail; the dialog then shows "Waiting for confirmation" with "Review in Decisions".
- **Waiting:** with a `proposal_id`, the dialog shows only that link.
- **Translations:** de/nl/es, in the du/je/tú register; the phrase "business partner" follows
  the app's own labels.
- **Guidance:** in `resolution_guidance.json`, the `company_party_missing` explanation is
  reworded to name the action; the chat prompt stays the owner's plain request.

### Chat and MCP (FR-007)

- **Tool:** `company_party_record_propose` (no arguments, `application_name`). It proposes and
  returns the proposal id. Its capability guidance tells the agent to use it only when the draft
  reports `company_party_missing` without choices.
- **Catalog gates:**
  - the command catalog entry, its parameter descriptions and capability guidance;
  - agent coverage;
  - tool topics;
  - the resource catalog (business partner) with `labels.de`;
  - tenant isolation and pinned counts;
  - action discovery;
  - the action-reference fixture;
  - `make docs-generate`.

### Data and migration impact

None. Rollback is revert. Companies created with the partner keep it, which is ordinary master
data.

### Failure, security, and tenant behavior

- **Concurrent confirmations:** of two proposals, one records and the other is refused
  (`company_party_exists`).
- **Demo and practice companies:** the command refuses; the draft never offers it there,
  because those companies refuse cost decisions first.
- **Tenant scope:** every read and write is tenant-scoped; the isolation catalog lists the new
  operations.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_company_party.py::test_business_company_records_its_partner` | no company partner |
| FR-002 | service | `::test_replayed_creation_keeps_one_partner` | — (pins the marker) |
| FR-003 | service | `::test_sandbox_demo_and_storyline_parties_are_unchanged`, plus the existing company setup, Demo Data and Storyline suites | — |
| FR-004 | service | `::test_draft_offers_the_prefilled_action` | no action in the input |
| FR-005 | service | `::test_confirmed_proposal_records_through_master_data` | command unknown |
| FR-006 | service | `::test_draft_names_the_waiting_proposal`, `::test_confirmation_is_refused_once_a_partner_exists` | — |
| FR-007 | service/MCP | `::test_mcp_draft_and_propose_parity`; guidance catalog test | tool missing |
| FR-008 | service | `::test_several_partners_keep_the_choice` | — |
| DR-001 | service | `::test_creation_source_states_the_requested_name` | no source |
| DR-002 | review | no migration in the diff | — |
| DR-003 | service | `::test_no_party_before_confirmation` via web route and MCP | — |
| DR-004 | service | same as DR-003 | — |
| SC-001/002 | live | a new business company drafts without `company_party_missing`; an existing company records its partner from the draft | — |

## Rollout and Rollback

The change is additive. The new command ships with its catalogs and the generated docs.
Rollback is revert.

## Analysis (2026-09-27)

`$speckit-analyze` over spec, plan and tasks found no CRITICAL findings. Resolved in the
artifacts:

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| A1 | MEDIUM | FR-007 and US3 had the resolution guidance offer the action "with a chat prompt", but guidance entries for draft open inputs carry no prompt. The action lives in the draft's open input (plan). | FR-007 and US3 reworded: the draft input offers the action in the web, chat and MCP; the guidance wording names it. |
| A2 | MEDIUM | The spec says practice and demo companies are not offered the action, but the plan relied on them refusing cost decisions, while the draft is read there too. | The draft offers the action only where `create_party` is allowed; the command refuses otherwise (spec edge case updated). |
| A3 | LOW | Who confirms the proposal was not stated. | The same principals as `party_create`. |
| A4 | LOW | A new business company's first draft may still lack other inputs (opening cost, method), so SC-001 is about `company_party_missing` only. | SC-001 and quickstart check 1 already say so; no change. |

## Review Risks

- **Name drift.** The command records the current company name, and a later rename does not
  follow (spec non-goal).
- **Tests expecting no parties in a fresh business company.** Searched and adjusted in T004; a
  company setup test asserting `parties == 0` would be a correct break.
- **Isolation counts** move by the new operations; the pinned counts are updated in the same
  commit.

## Complexity Tracking

### Normal-month setup regression (2026-10-04, FR-009)

Owner-approved scope: explicitly confirmed example execution may reuse the sole
setup-created company partner. Installation, onboarding, admission, automatic demo
creation, sandbox policy and later company renaming are unchanged.

The shared `demo/normal_month.py` service reads at most two tenant-scoped partners.
Only a sole company partner whose same-tenant SourceRecord identifies the company
setup request is reused; every other populated tenant is refused before example
writes. The original party and source remain unchanged. No schema, adapter,
authority, transaction or confirmation changes are needed; existing fixed-setup
locks and exact reviewed-intent checks remain in place. Rollback is a code revert.

Constitution check: PASS for tenant scope, unchanged source evidence, shared
service execution, unchanged confirmation and no schema expansion. Analysis found
no critical inconsistencies between FR-009, the implementation and the tests.
Tests cover the original ID/name/source, all commitment counterparties, import
selection, cost-draft owner selection, replay, an extra customer/company partner,
an unrelated company partner and the original empty-tenant story. Validation uses
the focused backend suites, Ruff, spec policy and the complete CI gates before merge.

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
