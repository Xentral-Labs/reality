# Retained cost-query context

T079 delivers one shared read envelope for already admitted inventory-item and whole
invoice-line contribution scopes. It delegates all arithmetic and historical integrity
checks to existing cost reads. This is not a canonical published generation or a new
company-wide profile. No new schema, financial approval or activation is introduced.

Input: fixed kind inventory/contribution, scope_id, optional exact review_id, optional
aware effective_at/knowledge_at and policy_revision_id constraints. Omitted cutoffs mean
unspecified, not now. An explicit cutoff must exactly equal the retained basis cutoff;
unsupported reconstruction refuses with cost_context_unsupported. Tenant is supplied by
the caller boundary. Foreign/absent scopes and review IDs remain indistinguishable.

Output separates requested selectors from resolved authority: tenant, scope kind/ID,
review ID, actual UTC cutoffs, policy, method, ownership pool, currency/base unit,
algorithm identities, retained event cursor and linked inventory review for contribution.
Canonical generation/profile revision IDs remain null; contribution profile approval is
explicitly scoped to its own review. Never label independently approved lines compatible.
A deterministic context identity covers the retained basis, excluding live freshness and
request spelling. Equivalent timezone representations normalize to UTC. Compatibility
requires two initialized identical basis identities, including tenant and scope.

Current mode requires READ COMMITTED. Sample the tenant event cursor after the bounded
read. If it exceeds the retained review cursor, expose the retained result only as
basis_result and leave result absent; do not promote an old numeric value to current.
Freshness is ready/stale/uninitialized. Historical mode does not read current events and
uses historical freshness, not a claim about current validity. Evidence gaps remain in
the delegated result: ready does not imply DB2 or carrying-value completeness.
Unreviewed scope has no context identity or resolved authority. Explicit constraints
without an available basis refuse rather than being silently ignored.

Use no_autoflush. No writes, jobs, time-based reinterpretation, changing transaction
isolation or stored derived authority. Existing read response shapes and review digests
stay unchanged. Expose through cost.query.get / MCP cost_query_get and CLI cost-query plus GET /api/tenants/{tenant_id}/cost-query;
adapters use this same application service and do not reconstruct context themselves.

Tests first: UTC and strict input handling, retained identity/compatibility, current vs
historical request resolution, unknown/ready/stale independently from coverage, unsupported
cutoffs/policy, foreign tenant/scope/review refusal, no writes and no historical event
scan, existing-kernel amount parity, HTTP/MCP/tool/CLI parity. Run affected/full backend,
catalog, generated docs, spec and scoped/global lint gates. Grouped reports, canonical
generations and generalized profile authority remain T080/T081; this envelope cannot be
used as evidence that those tasks are implemented.
