# Verification: Executed Decisions by affected order
## Regression-first evidence
Initial fixture confirmation was corrected to use the existing review token and confirmed decision boundary. The actual product failure then reproduced as unsupported discovery family. After implementation, 123 focused discovery/read/HTTP/demo/review/permission/policy tests passed (80 + 43), including deduplication, shortest membership, tenant collisions, cursor scope, private-payload absence and read-only legacy/page behavior.
## Fresh authenticated MCP acceptance
The existing paused synthetic company Reality MCP PR370 Retest 2026-10-04 was read through isolated source-mounted API/MCP runtimes. Seven calls completed the flow: resolve SO-006 by existing document discovery, discover executed_decision by its opaque order ID, follow the returned proposal_id to exact review and execution status, compare legacy transport, and compare order Reality before/after. Discovery did not receive an advance Decision ID. It returned act_ab05b56ee6, status executed, reserve, existing review/verification names and retained execution-event coverage.
The original receipt was verified; event sequence stayed 526 and reservations, movements and fulfillment were identical. No reservation, shipment or proposal execution was repeated. Legacy MCP still emits one content block per record; the harness initially treated a single block as an array and was corrected without a product change.
## External client
Claude acceptance is pending: computer automation currently reports the Mac locked; an unlock request was sent while direct verification and CI continued. No model completion is claimed.
## Required completion gates
Ruff and spec policy passed. Generated catalog consistency and spec policy passed after staging. Complete final-head Quality CI remains required. Review and temporary credential/connector/runtime cleanup remain pending. Tasks are not complete until required evidence is green.

## CI finding and correction
The full run for a665fc30 failed only the coded-refusal ratchet in backend shard 2: the new non-order lookup raised an uncatalogued sentence. It now uses existing record_not_found with the registered Document term. A regression covers the non-order branch; 38 focused discovery/HTTP/refusal tests passed. The other backend shards and all browser/frontend/docs checks passed on that run. No gate was weakened; complete CI is rerun for the corrected source.
