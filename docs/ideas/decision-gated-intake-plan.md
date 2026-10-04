# Decision-gated intake implementation roadmap

## Approved scope clarification (2026-10-04)

This rollout governs external sources, imports and agent-proposed business effects.
They require an exact retained proposal and an authorized confirmation before acceptance.
A direct action by an authenticated human is itself the decision and uses the existing
application authorization and audit trail; it does not require a second proposal or
confirmation cycle. Derived effects of one operation share its transaction and receipt.

The owner retained PRs #333–#346 and withdrew the later universal canonical-writer
rollout. Internal service calls and every manual UI/CLI operation are not additional
admission projects. Existing tenant, domain, Finance and Chat confirmation rules remain.
A static writer inventory is discovery material, not a mandate to guard every writer.
References below to governed writes mean external intake only; broader earlier planning
and universal-writer tasks are superseded by this clarification.

Status: specified and technically planned in packages 356–361, including the
owner's bulk-processing direction. Runtime implementation remains pending.
No runtime behavior is changed by this document. Numbered feature specifications,
technical plans, requirement-to-test tasks and analysis are linked below. Actual
implementation and runtime acceptance still follow `docs/SPEC_DRIVEN_WORKFLOW.md`.

## Prepared specification packages

| Package | Specification | Technical plan | Tasks |
| --- | --- | --- | --- |
| Foundation | [356](../../specs/356-decision-gated-intake/spec.md) | [Plan](../../specs/356-decision-gated-intake/plan.md) | [Tasks](../../specs/356-decision-gated-intake/tasks.md) |
| Shopify | [357](../../specs/357-shopify-reviewed-intake/spec.md) | [Plan](../../specs/357-shopify-reviewed-intake/plan.md) | [Tasks](../../specs/357-shopify-reviewed-intake/tasks.md) |
| File/master/stock | [358](../../specs/358-reviewed-file-master-imports/spec.md) | [Plan](../../specs/358-reviewed-file-master-imports/plan.md) | [Tasks](../../specs/358-reviewed-file-master-imports/tasks.md) |
| Financial intake | [359](../../specs/359-reviewed-financial-intake/spec.md) | [Plan](../../specs/359-reviewed-financial-intake/plan.md) | [Tasks](../../specs/359-reviewed-financial-intake/tasks.md) |
| Bulk and agents | [360](../../specs/360-bulk-intake-agent-review/spec.md) | [Plan](../../specs/360-bulk-intake-agent-review/plan.md) | [Tasks](../../specs/360-bulk-intake-agent-review/tasks.md) |
| Coverage and rollout | [361](../../specs/361-intake-coverage-rollout/spec.md) | [Plan](../../specs/361-intake-coverage-rollout/plan.md) | [Tasks](../../specs/361-intake-coverage-rollout/tasks.md) |

The linked contracts define immutable outcome phase numbering, common lock order,
dual row/byte package limits, original-reviewer handoff to workers, reference-only
queue payloads, scoped expiring agent mandates and demo awaiting-reviewer fallback.
The foundation includes a current writer matrix and 507 static writer candidates;
that inventory is not a claim of complete implemented enforcement.

## Goal

Store immutable raw sources immediately. Prepare a reviewable interpretation or
change proposal before accepting valid business evidence, master data or Reality
effects. A permitted person or agent decides on the exact proposal; execution
applies only its authorized effects through shared application services.

Documents and lines must not become accepted business evidence merely because an
interpreter produced them. A proposal can describe both evidence and its planned
Reality effects without creating authoritative records before approval.

Reuse the existing proposal lifecycle, decision attribution and scheduling
infrastructure. Derived read-time observations do not require decisions. Initial
setup exceptions must be explicit and narrowly justified, never implicit bypasses.

## Specification packages

| Package | Scope | Dependencies |
| --- | --- | --- |
| 1. Shared interpretation and admission boundary | Prepared interpretations; exact source/proposal binding; shared service enforcement; rejection, stale review, replay and failure semantics; bulk contract; writer inventory | Existing proposal and authorization contracts |
| 2. Shopify admission | First orders, lines and delivery commitments; version changes, cancellations, refunds and return announcements; preserve update guards and source ordering | 1 |
| 3. File and master-data admission | Items, parties, locations, orders, inventory assertions and correction effects; integrate reviewed item CSV import; close inventoried master-data bypasses | 1 |
| 4. Financial intake admission | Invoice evidence and posting; incoming/outgoing payment interpretation; partner/reference resolution and explicit allocation effects | 1 |
| 5. Agent review and bulk operation | Bounded background decision authority, independent source review, deterministic validation, human escalation, shared review surfaces and bulk controls | 1; exercised against 2–4 |
| 6. Coverage and rollout | External intake entrypoints across UI/CLI/MCP/Chat/workers; demo source admission and existing setup; historical records, pending jobs, documentation and operational visibility | 1–5 |

Begin the writer inventory in package 1 and close it in package 6. Recommended
first implementation slice: shared boundary plus Shopify first-order admission.
Agent review can follow the foundation while other intake adapters are migrated.

## Required bulk contract

Bulk processing is part of the foundation, not a later optimization. Preserve two
different operations:

1. **One decision for an import package.** A bounded set of related records, such
   as a new-item CSV package, is reviewed and approved as an exact unit.
2. **Batch settlement of independent decisions.** Multiple orders retain separate
   proposals, attribution and receipts while a person or permitted agent settles
   the exact selected set through one bulk operation.

Both operations must meet these requirements:

- Bind approval to an immutable manifest or equivalent exact membership,
  source versions, prepared effects and relevant review basis. Never include
  later arrivals or unreviewed replacements through an open-ended filter.
- Recheck current actor authority and stale-state conditions for each execution
  unit. Batch access must not grant broader business authority.
- Keep a coherent business unit atomic: for example, an order and its lines and
  authorized commitments succeed together or produce no accepted business effect.
- Isolate independent units. An invalid order must not block unrelated valid
  orders; splitting a package changes its approval scope and requires a matching
  review before settlement.
- Report accepted/executed, rejected, awaiting review, failed and stale units
  distinctly, with reasons and per-unit receipts where applicable.
- Support bounded chunks, durable progress and restart without duplicate effects
  or repeating already settled decisions. Progress is not business authority.
- Keep execution faithful to the approved proposal. Do not silently reinterpret
  a source under new mappings or changed business state during resumption.
- Bound review input size and preserve access to full source evidence. A summary
  must not conceal exceptions or replace the review basis.
- Preserve tenant isolation and truthful attribution throughout selection,
  review, settlement, retries and result reads.

Package 1 specifies these semantics and the smallest persistence needed to prove
them. Package 5 specifies selection, review presentation, agent invocation and
operator controls. Packages 2–4 define their business units and allowed grouping.

## Review and agent authority

Automatic processing still requires an explicit decision on an exact proposal.
An agent reviews against the complete source and planned effects, supported by
deterministic checks. Merely accepting the interpreter's summary is insufficient.
Uncertainty, conflicting source values or insufficient authority require escalation.

Background decision authority is a separate design requirement: existing token or
Chat access must not be treated as unlimited autonomous approval. Reconcile specs
274, 278 and 323 and actual enforcement before changing agent permissions.

## Verification plan

- Before approval, assert absence of accepted Documents, DocumentLines, master
  records and Reality effects for every migrated intake scenario.
- Prove exact approval binding, stale-source/state refusal, role revocation,
  tenant isolation, rejection and repeat-execution idempotency.
- Exercise concurrent settlement, source arrivals during review, process crashes
  and restart at chunk boundaries without partial coherent units or duplicates.
- Exercise both package approval and batch settlement, including mixed valid,
  invalid, stale and unauthorized units and correct result attribution.
- Test large item imports (including a 5,000-item scenario) and batches of orders
  (including a 500-order scenario) with realistic line counts. These are test
  workloads, not promised product limits or proven throughput figures.
- Measure preparation/review/execution time, peak memory, database round trips,
  agent cost and restart overhead separately. Set numeric throughput and resource
  acceptance targets in the numbered plans from the baseline measurements; do
  not declare performance complete without measurable agreed targets.
- Maintain a writer coverage matrix with owning service, entrypoints, decision
  enforcement, tests and any explicit exception.
- Run required backend, adapter, frontend, migration, spec and generated-document
  gates for each implementation package before marking it complete.

## Rollout and historical data

Retain existing records and source truth; never fabricate retrospective approval.
Define the transition for queued jobs, prepared proposals and in-flight workers
before enabling enforcement for a migrated path. A review outage must leave raw
ingestion available while accepted effects wait safely. Rollback must not silently
restore direct-write admission or lose decisions and receipts.

## Existing baseline references

- `specs/005-source-ingestion/`
- `specs/059-safe-proposal-confirmation/`
- `specs/081-shopify-update-guard/`
- `specs/129-unified-item-csv-import/`
- `specs/146-company-setup-demo/`
- `specs/168-demo-order-to-cash/`
- `specs/263-decision-trail/`
- `specs/273-stale-review-refresh/`
- `specs/274-chat-agent-decisions/`
- `specs/296-shop-order-changes/`
- `specs/323-proposal-decision-policy/`
- `specs/325-readable-proposal-reviews/`
- `specs/344-external-stock/`

Allocate feature numbers with `scripts/next_feature_number.py` when creating each
specification; the package numbers above are sequencing labels, not feature IDs.
No new schema or infrastructure is approved solely by this roadmap.

Spec impact: none for this documentation-only change. It records intended future
scope and sequencing; observable behavior changes require the numbered specs above.
