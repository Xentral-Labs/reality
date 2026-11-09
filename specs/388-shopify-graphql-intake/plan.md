# Implementation Plan: Reviewed Shopify GraphQL intake

## Technical Context
Python/SQLAlchemy services and existing PostgreSQL source/job/intake records. No migrations, new workers or schema. Use existing MCP tenant principal and explicit tool allowlist; capture access is propose and grants no generic approval.

## Constitution Check
All PASS: original entity unchanged; Source -> existing reviewed Evidence plan; no operational fields on Document; no schema expansion; tenant/service boundaries; received money retained without recomputation; tests first; shared MCP/CLI services. No exceptions.

## Design
- Pure `integrations/shopify/graphql.py` validates a bounded original selected order entity and derives an internal legacy-shaped interpretation input. Source payload remains unchanged. Exact GIDs, complete page, supported new/unfulfilled state and same currencies required. Unknown line amount remains unknown.
- `services/shopify_graphql.py` captures via canonical enqueue_source (hardcoded shopify/order_graphql and upstream timestamp), validates explicit mappings at preparation, refuses accepted cross-type duplicates and delegates to existing prepare_order with internal payload override.
- Existing core registry and intake dispatch recognize order_graphql. Never call apply_prepared_intake.
- MCP `shopify_order_graphql_capture` accepts exact original entity plus optional reviewed mapping and acquisition metadata, returns only source/job/status and explicit no-effects status. It calls the same capture service, never arbitrary proposal execution.
- Source updates, cancellation/refunds, incomplete pages, missing mappings and prior accepted orders retain needs-review/refusal rather than new business records.

## Required Verification and Traceability
| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001,003 | pure projection/identity/currency/partial and original roundtrip tests | GraphQL pure adapter |
| FR-002,004,DR-001 | service real proposal/no effects; missing/foreign mapping retention | capture + prepare + existing intake |
| FR-005,006 | replay/version/cross-type accepted duplicate refusal | shared source service + guarded preparation |
| MCP authority | explicit tool allowlist, no confirm token, no unrelated dispatch | MCP catalog handler + existing principal |

## Rollback
Remove new interpreter registration/MCP tool to stop new preparation; retained immutable sources/jobs/proposals remain explainable. No automatic migration or production deployment. No live company test.

## Risks
GraphQL selected entity is not entire Shopify resource. No cross-store identity inferred from labels; host pins installed shop and destination tenant. Raw fields may be private; do not print sources in test logs or chat. Missing customer is a truthful retained review outcome, not a business-effect proposal. Existing source-type streams are distinct, so cross-type duplicate refusal is necessary.
