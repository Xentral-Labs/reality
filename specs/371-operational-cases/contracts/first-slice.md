# First executable slice: accepted scope and concrete implementation decisions

**Product scope authorization**: The owner accepted the recommended first slice in chat on 2026-10-05: fulfillment and announced returns, exact ownership controls, synchronous guard and an integrated repair/handback story. Additional families remain backlog. The owner subsequently approved this concrete five-table schema in the same session ("ja gebe ich frei"). Implementation uses migration 0144; production deployment is separate.

## Enabled and unavailable policies

- Enabled candidates: `order_fulfillment`, anchored to an accepted sales-order Document with outstanding customer-delivery commitments; `customer_return`, anchored to an accepted ReturnAnnouncement.
- Refund remains unavailable as an executable case kind; successful refund evidence may update related explanation without creating payout intent.
- Supplier/warehouse/Finance candidate kinds are not enabled.
- Documentless customer promises, exchange replacements without an order and unannounced returns retain human/evidence support but do not silently enter enabled automation. Case discovery reports the coverage gap explicitly.

## Proposed minimum stored coordination

| Proposed table | Exact purpose and essential fields | Proven invariant |
|---|---|---|
| `operational_case` | `(tenant_id,id)`, kind, nullable order_document_id or return_announcement_id, policy_version, control_mode, control_revision, takeover_user_id?, created_at | Exactly one correct typed same-tenant anchor for kind; unique tenant/kind/anchor; no copied quantities/business status |
| `case_commitment_link` | `(tenant_id,case_id,commitment_id)`, role | Typed same-tenant membership for owned customer delivery promises; reservation/movement/source links derived through commitments |
| `case_proposal_link` | `(tenant_id,case_id,proposal_id)`, bound_control_revision | Many-case applicability; stored binding is not approval; preserve immutable executed receipts |
| `case_adoption` | tenant_id, confirmed adoption proposal ID, enabled policy version/set, capture_sequence, exact explicitly selected historical roots | New-work boundary plus reviewed old-work selection; no automatic historical takeover |
| `case_consumer_checkpoint` | `(tenant_id,policy_version)`, incorporated_sequence | Case effects and progress commit together; job runs remain lease/retry authority |

For the first slice, return membership uses its root and `ReturnAnnouncement.commitment_id`; do not add redundant return-link or generic related-case tables. Derive fulfillment/return relation through authoritative commitment/order links. Explain related goals without recursive transfer. Further membership roots require their own reviewed extension.

Control reason, actor, request key, exact review and receipt use existing ChangeProposal/BusinessEvent conventions; no second control journal. `takeover_user_id` is an AppUser reference, not proof of active membership; service checks current same-tenant membership on every control. Current facts determine goal state at read time. Add all composite foreign-key indexes through the existing migration conventions.

## Action origin and authority

Case guards cannot classify automation by `ChangeProposal.actor_type` alone: a human can confirm an agent-prepared proposal. Derive execution context server-side from authenticated channel/principal, actual finite mandate and job child authorization. Explicit currently authorized human repair is allowed under human case ownership; named-agent/background mandate execution must honor automation mode. Token-only calls gain no fabricated human identity. Trusted local calls retain their actual authority, but adopted autonomous execution requires explicit classified context rather than assuming a boolean means human review.

Existing proposal decision policy remains intact. Every bound action retains an exact business review as well as case control generation. Returning to automation does not refresh an old approval.

## Exact core insertion decisions

1. `core.create_commitment`: after accepted object insertion/flush and before `_commit`, ensure/match order case for in-scope anchored customer work. Supplier/unadopted work is explicit no-case. Use existing tenant serialization and no-commit semantics.
2. `core.announce_customer_return`: after announcement insertion/flush and before `_commit`, ensure return case. Its relation to original fulfillment is derived, not a second owned order goal.
3. `intake._apply_prepared_intake`: resolve affected existing cases after current-plan validation and before `_apply_effects`; execute guards under real current intake decision/mandate context. New roots are ensured by accepted canonical leaf operations in the same transaction.
4. `application.create_change_proposal`: resolve all existing directly affected goals, freeze case generations along with existing review and expose additive case IDs; a proposed new order remains unaccepted until execution.
5. `application.approve_and_execute_proposal`: preserve executed receipt replay. Check case authority under tenant/case locks before Finance/special Intake execution and before generic proposed→executing durable claim. Recheck lower effect boundary after the claim's transaction commits.
6. `core.record_movement` / `_append_movement`, reservation/revision/cancellation leaves and outbound/shipment/exchange/disposition services: resolve actual scoped authoritative objects and enforce classified automation guards. No caller-supplied case ID is trusted; inventory rows define all enabled paths.
7. `intake_batches.settle_chunk` and `intake_review` agent/child acceptance: validate every child case at actual apply, not only the fixed-manifest approval.
8. New case controls share existing proposal review/decision paths. Takeover and handback lock tenant first, then ordered case rows with current authorization. Handback binds observed goal, current source coverage and unresolved execution set.
9. New database-only worker consumes committed events in batches of at most 100, reconciling current authoritative membership/state. It cannot issue provider calls or accept evidence. Keep ownership/ID stable during reconciliation.
10. UI/MCP expose IDs, ownership and source-grounded explanation only after canonical guard coverage is proven; no control button that only changes a label.

## Failing proofs before implementation

- Accepted manual and reviewed Shopify order paths create the same anchored coordination in their transactions; a rollback leaves neither new promise nor case.
- Partial shipment/revision/cancel and worker replay retain case identity.
- Named-agent execution cannot start after committed takeover, including direct service and delayed-consumer paths. Explicit authorized human repair remains possible.
- Takeover after durable claim shows executing/uncertain work; no invented external cancellation. Handback refuses until known outcomes and source coverage are settled.
- State changes between handback preview and confirmation refuse. After successful handback, old generations remain invalid.
- Accepted announced return produces a distinct case; no unrelated graph transfer. Unannounced return and unanchored replacement are visible unsupported automation roots.
- Cross-tenant roots/links are denied, current member revocation denies controls, external correlation remains separate and unchanged.
- Existing API/MCP response envelopes add `case_ids` without modifying historical receipts; executed replay remains valid.

## Isolated verification environment

The initially absent localhost:54329 test endpoint was supplied by an isolated local PostgreSQL 17 Docker container. Tests use ephemeral databases; no production data or vendor credentials are involved. The test server lock capacity was increased to accommodate concurrent full-suite metadata fixtures. Runtime startup performs no DDL.

## Implemented acceptance evidence

The shared producer hooks, synchronous guards, bounded consumer, Web/API and shared CLI/MCP tools implement this first slice. `test_operational_cases`, `test_case_action_guards`, `test_operational_case_controls`, `test_operational_case_jobs`, `test_operational_case_adapters`, `test_case_entrypoint_coverage`, `test_shopify_case_recovery` and the real-component browser script provide local evidence. See [quickstart](../quickstart.md) for exact verification results and remaining release checks. Return goal observation follows the authoritative announcement receipt status; financial refund or replacement execution is not inferred from it.

## Read adapter failure containment

Unavailable or malformed case-list responses must stay inside the case panel, display the existing localized load error and permit refresh. They must not crash the containing Orders/Inspector page or enable controls from an unverified response. The component browser regression proves malformed initial data, zero writes and recovery to the normal operator flow; pagination applies the same shape check.
