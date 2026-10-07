# Operational cases

Spec: [371](../../specs/371-operational-cases/spec.md), superseded adoption policy: [377](../../specs/377-default-operational-cases/spec.md).

The default v1 layer gives accepted work a stable responsibility boundary. It does not store delivery, inventory or financial balances. Current goals and source coverage are read from Reality; notifications drive a bounded database-only reconciliation consumer.

Every company receives coordination without an owner activation. New accepted
customer-delivery commitments of a sales order share one `order_fulfillment` case;
each accepted open ReturnAnnouncement has its own `customer_return` case. Products,
locations, raw Sources and staged proposals never create goals. Completed history is
excluded; partial/open supported work is covered during bounded upgrade. Corrections
reuse the anchored identity. Historical owner-approved CaseAdoption records and their
capture/selection are retained unchanged, separate from platform version rollout.


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

The register returns additive `kind_counts` for each supported case kind, including
zero cohorts: total, automation, human, outstanding, completed and abandoned.
The existing canonical goal clauses and tenant-scoped whole-register aggregate are
grouped by kind; legacy totals sum these same observations. Page filters and cursors
do not reduce the whole-register counts. Ownership includes completed work and is
independent of currently outstanding goals. The Control Tower reuses that observation
and the same filtered register for bounded read-only previews; it introduces no
additional controllable family or inferred Agent execution state.

`operational_case_list` pages at most 100 cases using `after`; `operational_case_object` discovers associations from a document, commitment, return announcement or proposal. Explanation includes root IDs, current work, ownership, related cases, source IDs, obsolescence reasons, executing actions, coverage gaps and consumer progress/last job status. Order explanation, document inspector, proposal reviews and execution-status reads expose additive `case_ids`; stored receipts are not rewritten.

The shared scheduler discovers every non-archived company with missing/incomplete
rollout or event lag. Actorless, unscheduled `operational_cases.reconcile` runs have a
narrow persisted-run authorization check, never fabricated owner consent. Previously
queued owner runs keep their original current-owner authorization. Public schedule/run
creation cannot request this internal capability. Revocation/archive and real failures
remain explicit; database-only infrastructure/lease exhaustion resumes with a new platform run while retaining failed history. A definitively rejected legacy owner run also permits a new internal run; unresolved outcomes and other verdicts remain explicit.

Migration 0145 adds CaseRollout traversal/version metadata and the specific internal
job constraint; scheduler/worker startup never migrates. Each transaction scans at
most 100 supported historical IDs and consumes at most 100 events. Cursors, links and
checkpoint commit with job success. Rollback/retry cannot duplicate cases. Both scans
and event catch-up must complete before `operational_case_status.coverage_ready` is
true. `migration_ready`, `last_job_status`, `last_error_code`, `rollout_version` and
`rollout_provenance=platform_version` distinguish observed readiness from policy.
Source acceptance and correction hooks plus synchronous guards protect new/current
work while the background consumer is delayed. Missing schema refuses automated starts
explicitly; incomplete rollout is never represented as an end-user enable toggle.
Rollout changes no commitments, movements, balances, immutable Sources or provider state.

Legacy adoption/status clients remain supported: status returns adopted=true and
can_adopt=false. Confirmed authenticated owner adoption calls acknowledge the default
without resetting responsibility or creating fabricated owner adoption. Exact old
executed request replay keeps its original receipt. Old pending business proposals
without current case binding/review require fresh preparation; executed receipts and
uncertain executions remain unchanged. Populated rollout/history downgrade is refused.


This feature does **not** supply live Shopify authentication/webhooks/API retrieval, outbound provider transport or refund intent/execution. Financial refund evidence is bookkeeping, not payout authority. Unanchored customer promises, exchange replacements and unannounced return automation are unavailable under default coordination; existing authorized human/evidence workflows remain available. Supplier, Finance, warehouse and other proposed case families remain backlog. Default coordination does not prove that a live Shopify agent can run the whole business.

Implementation and verification evidence: [quickstart](../../specs/371-operational-cases/quickstart.md).

Default rollout verification: [spec 377 quickstart](../../specs/377-default-operational-cases/quickstart.md).

## Shared object presentation

Spec 378 FR-077 styles the existing case disclosure in Orders and the document
Inspector independently of the Control Tower. Readiness/refresh, each case's
kind/responsibility/work state and the control action row have bounded grouping.
Technical IDs, work/source links and ID copying are initially collapsed. Shared
manual takeover and exact handback reviews load their own confirmation styles.
Disclosure and navigation perform reads only; membership, revision, retry and
unresolved-execution guards remain in the shared application services.
