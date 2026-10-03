# Research: Live Business Blueprints

## Runtime authority

**Decision**: Resolve registered handlers to actual imported code objects and inspect their installed source on demand. Verify source consistency and expose release revision plus evidence digests.
**Rationale**: `catalogs.catalog_code` already shows installed function source; API/MCP images expose `REALITY_VERSION` and `REALITY_COMMIT`. Repository HEAD or working-copy text can differ from executed code.
**Alternatives considered**: Default-branch fetching and generated source catalogs were rejected as potentially different from the running application. A release digest manifest is provenance of raw source only, not a blueprint.

## Explanation method

**Decision**: A bounded AST/data-flow graph and deterministic business rendering, shared by every channel. Unsupported syntax or semantics are visible partial nodes. No new external provider.
**Rationale**: Public docs cannot depend on tenant AI settings. AST preserves exact operators and citations, and deterministic graph rendering lets diagrams and prose agree. Existing labels help name concepts without specifying outcomes.
**Alternatives considered**: Prewritten rule catalog violates the live-source requirement. Unconstrained LLM translation cannot prove branch fidelity. General Python/SQL symbolic execution is much larger than the bounded reference use case. Existing Chat may summarize the grounded response, never invent missing rules.

## Stable identity

**Decision**: Existing public IDs identify roots; inert rule identity markers may label crucial source decisions. No saved rule descriptions or outcome parameters. Qualified symbols and structural IDs identify unmarked source.
**Rationale**: Line numbers and AST offsets move during edits. Explicit identity is compatible with dynamic extraction because the behavior still comes from the expression.
**Alternatives considered**: Content hashes alone change identity on every edit; semantic maps with authored logic risk becoming a second authority.

## Test discovery and execution evidence

**Decision**: Ship approved actual synthetic test files and helper/fixture sources matching the release. Parse without importing or executing them. Treat direct calls as candidates and assertion-linked facts as evidence; report unresolved setup as unknown. Run evidence stays optional and independently revision-bound.
**Rationale**: `catalogs.py` explicitly skips test evidence validation when tests are absent from the production wheel. API/MCP Dockerfiles omit tests. Existing credit tests prove amounts, currencies, owner release and source-stated value usage but their fixtures require conservative resolution.
**Alternatives considered**: Generated test stories violate the requirement. Running tests per public request risks writes, slow requests and arbitrary execution. Raw discovery does not demonstrate passing execution or exhaustive coverage.

## Cross-surface integration

**Decision**: Extend existing Web catalog details and VitePress `ToolUsage.vue` with live reads. Docs target is configured and visible. Generic public reads are separated from private case comparison; both invoke the same core service.
**Rationale**: A static docs deployment has no live source. Fetching an approved generic backend read preserves its static deployment boundary and prevents tenant access. Existing generated vocabulary stays intact.
**Alternatives considered**: Embedding blueprints in docs builds violates on-demand freshness. Exporting all application source indiscriminately would exceed the approved business-source boundary.

## Concrete cases

**Decision**: Existing exposure/readiness and credit-hold facts supply values. Distinguish current state from recorded decision context. Conservative comparison uses extracted supported scenario inputs, with differences and unknowns explicit.
**Rationale**: No new history system is authorized. Existing `credit_hold_actions.py` explicitly shows exposure rather than pinning it for release; later payment changes must not be mistaken for the original state.
**Alternatives considered**: Replaying mutations, inventing historical values or building another financial calculation path violate shared-service and authority requirements.

## Research completion

No unresolved technical clarification remains. Research was performed against repository code with a read-only research agent, as required by the planning skill. Acceptance of the bounded analyzer's completeness is an implementation verification gate, not an assumption that all Python is explainable.
