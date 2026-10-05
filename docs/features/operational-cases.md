# Operational cases

Spec: [371](../../specs/371-operational-cases/spec.md).

The opt-in v1 layer gives accepted work a stable responsibility boundary. It does not store delivery, inventory or financial balances. Current goals and source coverage are read from Reality; notifications drive a bounded database-only reconciliation consumer.

A confirmed active company owner enables new-work adoption and may explicitly select up to 500 historical orders/announcements. The capture sequence is retained. Unselected historical work is not silently adopted. New customer-delivery commitments of an accepted sales order share one `order_fulfillment` case; each accepted open ReturnAnnouncement has its own `customer_return` case. Products, locations, raw Sources and proposals do not create goals. Completed history does not become new active work. A correction reuses the original anchored identity.

Owned work is distinguished from related work. An announced return is related through its original commitment to the fulfillment case. Taking over an order does not recursively transfer its returns, billing or supplier work. Independent return fragments are not heuristically grouped. The explicit v1 [policy catalog](../../packages/reality-core/config/case_policy_catalog.yaml) and [entrypoint inventory](../../specs/371-operational-cases/contracts/entrypoint-coverage.md) describe the boundary.

## Identity and authority

- `case_id`: internal opaque identity of a stable goal and its responsibility.
- `action_id` / proposal ID: exact decision/execution, with its real outcome.
- `correlation_id`: optional external tracing value. It is preserved as supplied, remains absent when absent, and never grants authority or defines a case. Touched operational writers no longer copy action IDs into this field; historical events are unchanged.
- Consumer event sequence: checkpoint telemetry, not goal identity or business truth.

All five coordination tables preserve tenant scope through composite business-object foreign keys. Case bindings freeze the control revision. Existing pending operational proposals also retain a server-produced exact business-state review alongside the original preview; caller-supplied case IDs or actor labels never authorize execution. Existing delivery/intake reviews and mandate checks still apply.

## Repair and handback

1. An active member reviews the case and confirms **manual takeover** with its exact control revision and a stable request key. The revision advances immediately. New automated starts refuse even before the event consumer catches up.
2. The member repairs Shopify or held Reality through its existing authorized evidence/decision path. Source arrival alone is not acceptance. A newer unresolved relevant Source blocks dependent automation and handback.
3. Already claimed actions remain visible with their actual status. Takeover never asserts external cancellation. An `executing` action must be reconciled through its existing execution recovery mechanism; never automatically redispatch uncertainty.
4. Read the handback review, inspect current work and uncertainty, then confirm that exact digest. The service rechecks current membership, facts, source coverage and unresolved execution under locks. Changed review meaning refuses.
5. Handback advances the revision again. Old proposals retain their obsolete generations; prepare fresh work rather than resuming old approvals.

Web controls use observed authenticated membership. Shared application controls are read/propose through Chat/MCP; an external token cannot impersonate a confirming human. Responsibility controls have only transactional database effects and never leave a fictitious external claim after a refused control. Business permissions remain action-specific.

## Reads, worker and limits

`operational_case_list` pages at most 100 cases using `after`; `operational_case_object` discovers associations from a document, commitment, return announcement or proposal. Explanation includes root IDs, current work, ownership, related cases, source IDs, obsolescence reasons, executing actions, coverage gaps and consumer progress/last job status. Order explanation, document inspector, proposal reviews and execution-status reads expose additive `case_ids`; stored receipts are not rewritten.

The shared scheduler discovers adopted companies with committed event lag and enqueues `operational_cases.reconcile` through the existing registry/queue. Each run incorporates at most 100 events and commits membership and checkpoint together. It performs no provider calls, accepts no evidence and emits no business-goal recursion. The adopting owner's retained decision supplies real job attribution; revoked current job authority is a visible failed run, not an arbitrary replacement actor. Recovery uses existing job controls. Producer hooks and synchronous guards remain authoritative when the consumer is delayed.

This feature does **not** supply live Shopify authentication/webhooks/API retrieval, outbound provider transport or refund intent/execution. Financial refund evidence is bookkeeping, not payout authority. Unanchored customer promises, exchange replacements and unannounced return automation are unavailable in adopted scope; existing authorized human/evidence workflows remain available. Supplier, Finance, warehouse and other proposed case families remain backlog. Enabling this layer does not prove that a live Shopify agent can run the whole business.

Implementation and verification evidence: [quickstart](../../specs/371-operational-cases/quickstart.md).
