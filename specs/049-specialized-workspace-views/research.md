# Research: Specialized Workspace Views

## Decision: Classify business jobs rather than technical rows

**Decision**: Expose Orders, Warehouse Queue, Fulfillment blockers, and Supply & demand. Allow Orders and Warehouse Queue to share `fulfillment_queue`.

**Rationale**: A projection is an implementation mechanism; a View names the user's question. One projection can support two workspace jobs without duplicating calculation logic.

**Alternatives considered**: Technical projection names leak implementation language. A second queue projection duplicates authority. Strict one-to-one aliases ignore workspace intent.

## Decision: Exclude tenant usage and price resolution

**Decision**: Keep `tenant_usage` in administration and `price_resolution` behind Commercial terms and its exact resolve flow.

**Rationale**: Tenant usage is administrative. Price resolution is an on-demand cache of exact questions, not a complete register.

**Alternatives considered**: Exposing every registered projection favors technical completeness over product truthfulness.

## Decision: Five direct Views plus a complete launcher

**Decision**: Render the first five ordered Views and offer `More views` when additional View entries exist. Search includes direct entries.

**Rationale**: Five keeps Company Overview complete, including Activity, while longer operational workspaces remain compact and the complete catalog stays discoverable.

**Alternatives considered**: Overflow-only search is incomplete. Rendering everything regresses as the catalog grows.

## Decision: Bounded allowlisted projection adapter

**Decision**: Add a bounded endpoint for the three in-scope projections, backed by existing `projection_page` and explicit presentation metadata.

**Rationale**: The legacy endpoint returns all rows. An allowlist prevents the workspace from becoming a raw projection browser.

**Alternatives considered**: Client pagination violates the large-tenant contract. Dedicated code per projection duplicates the read boundary.
