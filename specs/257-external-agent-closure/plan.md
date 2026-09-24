# Implementation Plan: External Agent Audit Closure

**Branch**: `257-external-agent-closure` | **Date**: 2026-09-23 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Close the CanisPro audit through five bounded slices over existing authority: enrich the
shared MCP proposal and capability contracts; expose existing proposal rejection and
invoice-credit context; add the missing free-supplier-invoice and dunning MCP adapters;
tighten closed-type validation and return refusals; and add a derived costing-guidance
envelope over the existing owner-confirmed cost workflow. Existing settlement,
invoice-credit, return-disposition and demo-cost capabilities receive regression and
end-to-end proof rather than replacement implementations. No business table or migration
is planned. The fresh 2026-09-24 qualification adds a sixth bounded follow-up: repair the
advertised customer-credit adapter, replace tenant-global cost freshness with evidence-scoped
freshness, preserve acquisition history across internal transfers, retain source-stated invoice
net/tax evidence, make effect-free execution failures terminal, and publish complete
operation-specific MCP contracts. Existing JSON evidence payloads, cost manifests and proposal
records are sufficient; no new business table or migration is planned.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React where Web presentation is in scope
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, React/Vite, MCP runtime
**Storage**: Existing PostgreSQL business, proposal, finance, return and costing records; no new persistence
**Testing**: pytest unit/service/business-story/PostgreSQL/adapter tests; generated-catalog contracts; focused Web contracts/browser journeys
**Project Type**: shared domain/services/tools with MCP, API, CLI, Chat and Web adapters
**Constraints**: Decimal; UTC; opaque IDs; immutable source evidence; strict tenant scope; explicit owner confirmation; no inferred actual cost
**Scale/Scope**: One proposal/action at a time; bounded independent receipt reviews; complete public MCP catalog parity; fresh CanisPro qualification tenants; no bulk workflow engine

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Free supplier invoices create immutable SourceRecord and Document/DocumentLine evidence before ledger effects; credits retain invoice-line links; return and cost actions reuse their existing evidence chains. | PASS |
| Reality owns operational state | Reservation effect, return resolution, settlement, credit and cost readiness remain derived from Reservation, Movement, LedgerEntry/allocation and reviewed cost records; no document status is introduced. | PASS |
| Proven schema only | Existing line payloads already retain `reality_finance_v1` stated net/tax/gross evidence; cost manifests/hashes and proposal status/output express the remaining scenarios. No column or migration is planned. | PASS |
| Tenant + shared service boundaries | Shared tenant-scoped services feed MCP and Web; owner confirmation continues through the existing proposal execution boundary. | PASS |
| Spec/test traceability | FR/DR groups map below to tests added before their implementation slice and to a final fresh-tenant qualification. | PASS |
| Explainable web behavior | Owner review, no/partial/full effects, cost prerequisites and final receipts expose current evidence and next reads. | PASS |
| Received values not recomputed | Supplier invoice, cash, reductions, fees and cost components remain stated values; cost and balance outputs remain derived observations. | PASS |
| Smallest coherent design | Reuse existing proposal, finance, credit, dunning, return and costing services; add only missing composite service/adapters and derived guidance. | PASS |

Planning may proceed. No Constitution exception or unresolved clarification exists.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/domain/cost_query.py
packages/reality-core/src/reality/services/core.py
packages/reality-core/src/reality/services/cost_query.py
packages/reality-core/src/reality/services/costing.py
packages/reality-core/src/reality/services/inventory_costing.py
packages/reality-core/src/reality/services/finance/components.py
packages/reality-core/src/reality/services/credit_actions.py
packages/reality-core/src/reality/services/dunning.py
packages/reality-core/src/reality/services/invoice_actions.py
packages/reality-core/src/reality/services/proposal_reviews.py
packages/reality-core/src/reality/services/return_dispositions.py
packages/reality-core/src/reality/tools/application.py
packages/reality-core/src/reality/tools/costing.py
packages/reality-core/src/reality/tools/finance.py
packages/reality-core/src/reality/mcp/catalog.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/config/command_catalog.yaml
packages/reality-core/config/resource_catalog.yaml
packages/reality-core/tests/
packages/reality-core/tests/finance/
packages/reality-core/tests/scenarios/
packages/reality-core/tests/test_costing_services.py
packages/reality-core/tests/test_inventory_costing_services.py
packages/reality-core/tests/test_unified_invoice_credit.py
packages/reality-core/tests/test_contribution_services.py
apps/web/src/api.ts
apps/web/src/unified/CostExplanation.tsx
apps/web/src/unified/ProposalReviewCard.tsx
apps/web/src/localization.tsx
apps/web/scripts/
apps/docs/scripts/generate-catalog-reference.py
apps/docs/content/tool-usage/
apps/docs/.vitepress/data/tool-usage.json
docs/WEB_SPEC.md
docs/features/receipt-costing.md
```

**Files/layers affected**: the focused `invoice_actions.py` service owns atomic free supplier
invoice recording and reuses only existing normalization/posting primitives from `core.py`;
existing finance/dunning/credit/return/cost services remain business authority. Application tools
expose shared service results. MCP and Web are adapters only.
Exact files may narrow after failing tests identify an already suitable seam; dependency
direction remains domain → services → tools → adapters.

## Design

### Reality flow

**Proposal and reservation**: public schema → tenant-scoped ChangeProposal → current
server review → explicit human decision → existing application action → stable receipt.
Reservation receipts derive `none`, `partial` or `complete` from requested/applied/shortage
and point to the current Commitment, Reservation/event when present and verification reads.
Exact-location allocation remains unchanged.

**Free supplier invoice**: immutable stated invoice source → supplier-invoice Document and
free DocumentLines → balanced payable LedgerEntries → correlated event/receipt. No purchase
order or supplier commitment is invented. The existing order-linked invoice path is unchanged.

**Settlement and dunning**: agent proposal → authenticated owner review → existing finance
command. Actual cash, bounded allocation, stated reduction and available credit remain
separate evidence. Dunning records the existing notice and optional source-stated fee; it
does not send a reminder or calculate a fee.

**Credit and return**: invoice-credit context derives eligible invoice-line capacity. The
confirmed credit preserves CreditLine → InvoiceLine → OrderLine links and ledger effects.
Return disposition separately resolves the arrived Movement and applicable tracking identity.
Neither money nor goods implies the other.

**Costing**: held SourceRecord/Document/Movement/component evidence → read-time prerequisite
guidance → owner-confirmed existing `cost.change` proposal → retained cost reviews/bases →
current or historical inventory/DB observations. Guidance and generated results are not new
authority. Demo readiness continues through spec 251's existing profile/setup path.

### Service and adapter flow

1. Extend the shared MCP propose result with structured next-step metadata sourced from the
   existing review contract: proposal identity, review requirement/read, required principal,
   confirmation boundary and verification read. Never copy a stale token into generic guidance.
2. Resolve capability descriptions by exact public tool identity first and then by a unique
   application-tool identity; always return the canonical public name and refuse ambiguity.
3. Extend reservation receipts with effect classification and remaining work while preserving
   existing quantities and record/event identities.
4. Bind a controlled MCP rejection tool directly to existing tenant-scoped `reject_proposal`,
   require an explicit authorized-human rejection decision, exclude it from default model
   selection and return stable lifecycle information without exposing rejection to inference.
5. Bind one MCP invoice-credit-context read to the existing credit-context service. Preserve
   the already complete nested credit proposal schema and add regression coverage rather than
   a second schema.
6. Add one atomic free supplier-invoice application service in `invoice_actions.py` for supported
   stated free positions, reusing `core.py` manual-evidence normalization and supplier-invoice
   posting primitives; apply ordinary explicit human confirmation rather than owner-only policy.
7. Publish existing dunning context/list/detail, record and reverse commands through MCP;
   owner confirmation remains enforced by the existing finance command executor.
8. Centralize the public manual operational document vocabulary (`sales_order`,
   `purchase_order`, `sales_invoice`, `supplier_invoice`, `credit_note`,
   `supplier_credit_note`) in the shared service, validate public action preview before proposal
   persistence and derive the MCP enum/reference from that contract. Unknown source labels stay
   in SourceRecord payloads; lossless intake is not constrained by this operational allow-list.
9. Refine return validation messages at the shared service boundary. Do not relax the required
   arrived return Movement, destination, commitment or tracking relationships.
10. Enrich the existing cost-query result, or a focused read service called by it, with a
    stage-aware derived prerequisite graph and next owner action. Web, MCP, CLI and API render
    the same envelope and mutations continue through existing cost proposals.
11. Keep `finance_payments.direction`; reject unsupported `side` rather than adding a
    semantically incorrect alias. Add regression coverage for every public filter.
12. Generate Tool Usage reference from the canonical catalogs and run a release qualification
    that compares the deployed MCP `tools/list` projection with the checked-in reference.
13. Keep optimistic concurrency for cost mutations, but bind retained receipt-review freshness to
    a canonical fingerprint of the receipt basis, admitted financial components, attributions,
    corrections and retained category decisions. Unrelated business events do not alter that
    fingerprint. Relevant changes report the changed evidence scope.
14. Treat transfer movements as physical continuity in inventory costing. The transfer-out and
    transfer-in legs move the existing cost layer and owner; they do not create an independently
    valued acquisition receipt. Refusals enumerate exact missing movement or receipt identities.
15. Retain source-stated `net`, `tax`, `gross`, currency and codes in the existing
    `DocumentLine.payload.reality_finance_v1` envelope during invoice recording. Never derive a
    missing received value; gross-only invoices remain valid evidence but unavailable for a net
    contribution basis.
16. Validate customer-credit shape and billed relationships while preparing the proposal. The MCP
    adapter forwards the complete normalized input rather than flattening it to an empty mapping.
17. When confirmation reaches a deterministic domain refusal and the transaction proves no
    business effect, persist a terminal `failed` proposal outcome with a bounded error receipt.
    Unknown commit outcomes remain `executing`; the implementation must not misclassify them.
18. Publish operation-discriminated schemas for costing and purpose-specific shipment contracts
    from the same typed request models used at runtime, and verify the live MCP projection.

### Data and migration impact

No column/table schema change, migration or backfill is planned. Existing SourceRecord, Document,
DocumentLine, LedgerEntry, SettlementAllocation, ChangeProposal, DunningNotice, Movement,
Reservation and retained cost records express all accepted behavior. Review handoff,
capability aliasing, effect classification and costing guidance are derived read contracts.
Source-stated invoice finance detail is retained in the existing lossless line payload contract.
The proposal lifecycle adds the terminal semantic value `failed` to the existing status field and
stores only a bounded non-secret failure receipt in existing output; no persistence shape changes.

Historical CanisPro records remain untouched. Its pending probes may be rejected later through
the new public lifecycle action, but no rollout task silently cleans them. If implementation
discovers that a requirement cannot be expressed without persistence, planning must stop and
return to specification/Constitution review with a proven schema use case.

### Failure, security, and tenant behavior

- All reads, preparation, review, rejection, confirmation and verification carry tenant scope;
  foreign identities behave as not found.
- Agent credentials never satisfy active-owner requirements. Owner-governed effects occur only
  after an authenticated owner reviews the unchanged stored proposal.
- Stale state-bound reviews refuse before effect. Repeated executed confirmation replays the
  receipt; executing/indeterminate state is reconciled and never blindly replayed.
- Rejection requires an explicit authorized-human decision, is excluded from default model
  selection, is limited to pending proposals and creates no business effect. Repeated rejection
  returns stable rejected state; executed or executing proposals cannot be rewritten as rejected.
- Composite free-invoice creation/posting is atomic and action-idempotent; any validation or
  posting failure rolls back all evidence/effects from that attempt.
- Unsupported document/movement values and malformed nested relationships fail before durable
  proposal/document creation. No adapter silently ignores an unknown field or filter.
- Cost guidance performs no writes and grants no authority. Incomplete evidence keeps actual
  values unavailable; DB1 and DB2 retain independent coverage.
- Receipt-review freshness ignores unrelated tenant events but rejects a changed bounded evidence
  fingerprint. Prepare-time optimistic concurrency remains required for the mutation itself.
- Internal transfers preserve quantity, owner and cost-layer continuity; they cannot manufacture
  new acquisition value or erase the trace to the original supplier receipt.
- A deterministic validated refusal may become terminal `failed` only after rollback proves no
  business effect. Transport loss, timeout or ambiguous commit remains `executing` and requires
  reconciliation.
- Server-side proposal review remains responsible for redacting sensitive input before Web
  presentation.

## Test Strategy and Traceability

Tests are written or extended first and observed failing where practical.

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-004, FR-030 | registry/application/release | Extend `test_ai_mcp.py`, `test_capability_guidance.py` and docs contracts; compare deployed schema projection in quickstart | Propose lacks structured handoff; capability application identities and deployed parity are not covered |
| FR-005–FR-006 | service/application/MCP | Extend `test_application_tools.py` and `test_ai_mcp.py` for zero/partial/full exact-location receipts | Receipt exposes quantities but no explicit effect/remaining-work classification |
| FR-007–FR-008 | service/API/Web story | Extend proposal-review parity tests and owner-confirmed finance browser journey | End-to-end agent→owner→agent handoff is not qualified as one story |
| FR-009–FR-011, FR-026 | finance service/MCP story | Extend `tests/finance/test_settlement_flows.py` and payment-read tests for reductions, overpayment and strict direction filtering | Canonical behavior exists but discoverability/filter rejection lacks complete public proof |
| FR-012 | finance/MCP/Web | Extend commercial-edge tests and add MCP dunning context/record/reverse tests | Dunning exists in service/Web but has no MCP definitions |
| FR-013 | service/application/MCP story | New free supplier-invoice tests covering ordinary/charge lines, ordinary human confirmation, rollback, idempotency and tenant scope | Current specialized tool requires purchase-order lines |
| FR-014–FR-016, FR-025, FR-027 | credit service/MCP/exception story | Extend `test_unified_invoice_credit.py`, `test_ai_mcp.py` and return exception derivation | MCP has no invoice-credit context read; clean client cannot discover line identities |
| FR-017–FR-018 | return service/adapter | Extend `test_returns.py` and `test_return_announcement_adapters.py` for precise refusals and four dispositions | Dispositions exist; missing relationship errors and public regression coverage are incomplete |
| FR-019 | service/application/catalog | Add manual-document-type validation tests and registry enum contract | Generic manual creation accepts any nonblank operational type |
| FR-020–FR-023 | cost read/service/Web story | Extend `test_cost_query.py`, costing tool tests and CostExplanation contracts; add ordinary-company complete/incomplete story | Cost reads expose raw missing codes but no coherent next authorized stage |
| FR-024 | application/MCP lifecycle | Extend proposal tests for explicit human rejection, default-model exclusion, replay, executed/executing refusal and cross-tenant scope | Rejection exists only through Web/application, not MCP; replay is not public |
| FR-028–FR-029, SC-001–SC-010 | end-to-end qualification | Fresh CanisPro public MCP + owner Web review protocol with artifacted F1–F13 closure matrix | Original run required invalid probes/workarounds and mixed real gaps with expected boundaries |
| FR-031 | application/MCP/business story | Extend `test_unified_invoice_credit.py` and `test_ai_mcp.py` for full argument retention, empty-shape refusal and canonical invoice credit | Live wrapper discarded supplied arguments and retained `{}` |
| FR-032, SC-012 | cost service | Extend `test_costing_services.py` for unrelated-event stability and targeted invalidation with named evidence | Global tenant input sequence invalidates every review |
| FR-033–FR-034, SC-014 | proposal service/application | Extend proposal, invoice and credit execution tests for prepare-time validation, rollback, terminal `failed` and genuinely indeterminate `executing` | Deterministic refusals remain permanently `executing` |
| FR-035, SC-013 | inventory domain/service | Extend `test_inventory_costing_services.py` with purchase-transfer-sale continuity and exact missing-scope refusal | Transfer destination is treated as an unsupported new receipt |
| FR-036 | registry/MCP/docs/release | Extend `test_ai_mcp.py`, capability guidance and deployed catalog comparison for complete union/purpose contracts | Live cost schema was empty and shipment movement values required probing |
| FR-037, SC-013 | invoice evidence/contribution | Extend invoice, finance-component and contribution tests for stated net/tax/gross and gross-only unavailability | Regular invoice intake omitted the retained net basis |
| DR-001–DR-008, SC-011 | architecture/full gates | Source/evidence trace assertions, tenant suites, schema-diff review, full required checks | Cross-slice regression and no-schema proof are not yet gathered together |

Required final gates include focused pytest suites, PostgreSQL concurrency where applicable,
`make lint`, `make test`, `make web-build`, localization audit, `make spec-check`,
`make docs-generate`, `make docs-catalog-check`, and the fresh external qualification.

## Rollout and Rollback

Ship shared core, API/MCP and Web from one revision so proposal handoff and schemas cannot
drift. New MCP reads/actions are additive; enriched receipts and propose responses add fields.
Strict early document-type validation can refuse inputs that previously created unusable
records and must be called out in release notes. No data migration or automatic repair runs.

Rollback is a code revert. Existing evidence, proposals, notices, credits, settlements,
returns and cost reviews remain valid. Before rollback, inspect proposals created with newly
added public tools; never replay executing actions or delete audit history automatically.

## Review Risks

- The umbrella scope can encourage duplicate implementations of specs 249–251; tasks must
  first mark existing behavior and reuse its services/tests.
- Initial propose guidance must not leak or freeze a review token that becomes stale before
  human review.
- A generic document-type allow-list can accidentally reject legitimate evidence imports;
  validation applies to supported operational meaning, while unknown upstream labels stay in
  lossless payloads.
- Free supplier invoices must not invent purchase commitments or conflate charge items with
  stocked quantities.
- Capability alias resolution must refuse ambiguity rather than select an arbitrary tool.
- Cost guidance must not become stored workflow state, automatic financial authority or a
  second calculation implementation.
- A live endpoint comparison needs release credentials without storing secrets in evidence.
- Evidence-scoped freshness must include every authoritative cost input without falling back to a
  global cursor or persisting a second cost authority.
- Adding `failed` must not convert genuinely indeterminate executions into safe failures; rollback
  and absence-of-effect proof are mandatory.
- Invoice finance detail must preserve exactly what the source stated and must not infer net or tax
  from gross, rates or account postings.
- Transfer valuation must preserve shortest links to the original acquisition receipt and must not
  duplicate acquisition attribution on the destination movement.

## Post-Design Constitution Check

Phase 1 introduces no table, duplicated authority, document-owned operational state, adapter
business rule, inferred received value or automatic financial approval. All eight blocking
Constitution rows remain PASS.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
