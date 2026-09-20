# Captured report publication: concrete model amendment

Status: owner approved the basis relationship, four-table slice and captured report
semantics on 2026-09-19. Implementation is authorized; live migration and release are not.
Scope: FR-007/012/014/018/019; next integration of T079–T081 after T186–T189.

## Approved decision

Use the already proposed generic calculation-cache family for a fixed captured report.
Implement four of its seven planned tables first: cost_generation, cost_inventory_row,
cost_contribution_row and cost_publication. Reference cost_captured_basis instead of
pretending that it is the historical cost_input_manifest required by the original design.
Keep the existing single-review inventory/contribution generation tables unchanged.

A captured report means: these are the supported observations from exactly this retained
selection of reviews at this captured census boundary. It does not mean that every input
was reviewed together, that all business evidence was admitted, or that an arbitrary past
knowledge_at can be reconstructed. Display each review's own knowledge boundary underneath.
The original basis keeps publication_eligible=false for financial company publication.
A separate captured-report publication guard may publish a reproducible diagnostic cache;
it must never convert that flag into financial eligibility or call the historical company
guard with invented values. Use an explicit report kind, captured_review_selection_v1.

The owner explicitly approved this amendment on 2026-09-19 because the original generic
model named a sealed historical financial manifest as its generation authority. The
earlier captured-basis retention approval alone did not authorize this substitution.

## User-visible result and limits

- Rows, subtotals, coverage, pagination and explanations all name one generation and
  retained basis. A report cannot combine a new total with an old detail page.
- Known acquisition/carrying values and DB1/DB2 remain independent. Preserve all unknown
  subjects, unsupported economic candidates and header/source gaps. Do not infer their
  amounts, currency, unit or economic eligibility from current master data.
- Reuse captured_cost_summary semantics: currency/base-unit groups; inventory additionally
  partitions by owner and method. DB1/DB2 sum supported rows through the existing SQL
  expressions. Final totals and rates remain null, even with complete subject coverage.
- The product label must say captured review selection, not complete company valuation.
  Show capture observation time, effective cutoff, event cursor and per-subject reviews.
  A later event marks current assessment pending without rewriting the fixed report.
- No all-time sum across inventory cutoffs. No new public calculation engine. Connect the
  indexed relation to graph.ask / saved reports after storage and service proofs pass.
- The first integration retains the existing ten-subject bound and has no production-scale
  claim. Larger-company support is a release prerequisite, not a hidden truncation or a
  reason to silently return only the first ten subjects.

Example: two same-unit sales show revenue 200. Only one has goods cost 60 and selling
cost 10. Known DB1 is 40 and known DB2 is 30; both cover one of two positions. Publishing
this report does not turn either into a final total. Later completed inputs create a
new captured basis and report; the old report and saved fixed selection remain unchanged.

## Four typed disposable tables

All tables use opaque IDs, tenant scope, composite same-tenant FKs and restrictive links.
Amounts/quantities follow existing exact four-decimal admission; reject overflow before
writing. Aggregate SQL uses unconstrained NUMERIC so sums do not inherit row overflow.
Only service-verified canonical output can populate cache values. No authoritative
financial decision or retained input may reference a disposable cache row.

| Table | Proven fields and constraints | Query / relationship purpose |
|---|---|---|
| cost_generation | captured_basis_id FK; fixed kind; algorithm version; trusted scope_key; building/sealed state; completed_at; inventory/contribution counts; output hash; unique tenant/basis/algorithm; unique tenant/scope_key/id | One reproducible cache per retained basis and algorithm; exact scope FK target for publication. Source context stays reachable through the basis/census, not duplicated times or policy FKs. |
| cost_inventory_row | generation_id FK; inventory_basis_member_id FK; unique tenant/generation/member; available/unknown state; nullable currency/base_unit/method/owner_party_id; remaining_quantity, acquisition_value, carrying_value nullable | One row for every retained inventory member, including unknowns. Typed dimensions support partitions and indexed pages; shortest evidence path is member -> review. Method/owner partitions cannot be omitted. |
| cost_contribution_row | generation_id FK; contribution_basis_member_id FK; unique tenant/generation/member; available/unknown state; nullable currency/base_unit; received revenue, consumed goods cost, complete direct/allocated selling amounts nullable | One row per retained sales candidate, including unsupported candidates. DB1/DB2 stay derived by the existing SQL aggregates; no stored second DB formula. |
| cost_publication | trusted scope_key unique with tenant; generation_id; composite tenant/scope_key/generation FK | Atomically point to a sealed captured report of exactly the same scope. A fixed historical read uses its generation directly. |

Known zero is a non-null amount. Unknown rows have no numeric values or inferred dimensions.
An available review may still have unknown carrying or selling costs. SQL checks enforce
state/null shapes; service verification checks every row against canonical replay and
checks review/member/subject correspondence, exact sets and counts. Inventory owners use
same-tenant party links if stored; their presence is required only for available rows.

Indexes: generation/basis lookup; tenant/generation/member stable keyset pagination;
tenant/generation/currency/base_unit grouping; inventory adds method/owner. Defer order,
customer, channel and economic-period dimensions until their exact retained source and
admission are proved. Do not copy them from mutable documents for convenience.

A seal prevents subsequent cache-row/header edits or member insertion. Cache GC may
remove whole unreferenced generations through a guarded service, never retained bases or
review history. Published generations are protected. Fixed saved selections retain the
basis and algorithm identity; an evicted cache is explicitly unavailable until a rebuild
is requested through an authorized mutation, never silently rebuilt by a read.

## Transaction and shared service contract

Internal service boundaries under services/costing.py:

1. build_captured_cost_generation(session, tenant_id, basis_id): clean REPEATABLE READ;
   verify the sealed basis, pinned canonical replay and size bounds before output writes.
   Build within a savepoint, verify exact persisted rows/content, then seal. Caller owns
   commit. Same basis/algorithm returns the same verified generation; failed builds cannot
   leave partially sealed output if the caller catches the error. No financial approvals.
2. publish_captured_cost_generation(session, tenant_id, generation_id,
   expected_previous_id): load trusted facts, lock the publication scope, validate sealed
   content and scope, compare-and-swap and sample the committed tenant cursor. Follow the
   existing tenant-before-publication lock order. First publication handles absent-pointer
   races through the unique scope key, not an unlocked read-then-insert. Commit belongs to
   the caller; no intermediate pointer is visible.
3. captured_cost_report(session, tenant_id, generation_id or fixed scope selector,
   page cursor): SELECT-only; resolve one generation once and bind every query/cursor to
   it. Verify sealed metadata and serve indexed rows/SQL subtotals without replaying inputs
   or scanning the tenant's source history. Foreign identities behave as not found.

Requests accept identities/selectors, never amounts, membership lists or verification
booleans. Builder and publisher remain internal until the normal authorized shared-job
path is wired. Public mutations, if added, require preview/confirmation and execution-time
permissions. Reads neither enqueue nor activate policies. No new scheduler, timer, queue,
startup migration or external-effect handler is introduced.

Scope key is derived by the service from tenant, report kind and effective cutoff, not
from a caller string. Different cutoffs/kinds cannot replace each other. Newer captured
cursors may replace older ones in that scope; obsolete candidates refuse. Same-generation
retry is unchanged. A different retained basis at the same event cursor refuses as an
ambiguous replacement; cursor equality alone cannot prove equivalent visible evidence.
An advanced live cursor yields pending, never a current claim. Do not
infer currency/unit filtering or financial eligibility from the publication pointer.

## Reuse and rejected shortcuts

- Reuse the approved generic cache names; do not add a second captured-cache table family.
- Retain existing review/input authority and replay. No new financial input manifest is
  claimed by this captured-report branch; the historical company branch remains separate.
- Do not overload selected-review generation tables: their review/action scope excludes
  unknown subjects and cannot represent this whole captured membership.
- Do not put report amounts into cost_captured_basis.observations or mutate sealed census
  JSON. Those records retain selection/discovery and outlive disposable caches.
- Do not store report arrays in generic ProjectionRow text: it cannot provide the indexed,
  typed, coverage-aware relation needed by the reporting compiler.
- At ten subjects, use one atomic bounded build. Do not introduce cost_generation_work,
  cost_trace_part or cost_finding_row merely to reserve future concepts. Explanations
  follow retained member/review links. Chunked company builds need their own measured plan.

## Test-first acceptance and delivery order

1. Domain: strict captured kind/context; no knowledge_at substitution; exact membership,
   supported-versus-unknown coverage, same-scope publication, obsolete/retry/CAS behavior.
   Existing historical CompanyGenerationBasis continues rejecting raw captured contexts.
2. Migration/storage: same-tenant member/generation links, duplicate and malformed rows,
   sealed immutability, guarded cache disposal, retained-input survival, upgrade/downgrade
   on an empty disposable database; migration revision follows the then-current head.
3. Services: real stock 420 / DB1 570 / DB2 456 fixture, missing-cost example above, mixed
   units/currencies/owners/methods, unknown-only/empty, all-null numeric SQL, later-input
   stability, maximum bounds, overflow, no direct caller amounts and foreign-tenant refusal.
4. Transactions: failed-build savepoint, caller rollback, two builders/retries, first-pointer
   race, obsolete worker/candidate, CAS conflict and one-generation metadata/page/total reads.
5. Reporting: graph relation and saved fixed context use the same services/SQL definitions;
   joins do not multiply amounts; unsupported traversals refuse; read paths neither replay
   history nor enqueue work. Test real CLI/MCP/web calls and inspector links.
6. Release: bounded worker integration, larger retained membership and exact chunk closure,
   fixture J on reference hardware, full required suites and existing shared lint gates.
   Backend fixtures do not count as user-facing acceptance or production-scale evidence.

Do not call T079–T081 complete after storage alone. This proposal makes the next steps
finite and reviewable; it does not remove admission, historical knowledge, broad commercial
matching, carrying assessment, demo, exceptions or UX obligations from the original spec.

Implementation detail: this bounded slice loads at most ten cached members for aggregate
verification; it never replays financial inputs on report reads. Larger indexed graph
relations and worker integration remain T194. A guarded deletion removes only an entire
unpublished cache generation; retained input membership survives.
