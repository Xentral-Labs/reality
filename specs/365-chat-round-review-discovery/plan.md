# Implementation Plan

## Summary

Fix the proven shared selection defect before adding a speculative prose-verification
layer. Movement.type joins the existing substring-search columns only for Movement;
all adapters consume business_discovery_statement. A configured standalone capability
entry exposes generic confirmation under review while retaining intake aliases.
Validate real daily Chat and client-owned repeated read-only operation separately.

## Technical Context

Python 3.12, SQLAlchemy 2, PostgreSQL, existing MCP registry, catalog generator and
both provider loops. No new dependency or business schema. Existing isolated pytest
database; live synthetic company only for authorized provider/client acceptance.

## Constitution Check

| Principle | Result | Proof |
| --- | --- | --- |
| Source / Evidence / Reality | PASS | Read existing Movement evidence; create no business authority. |
| Operational authority | PASS | No status stored on Documents; existing reads derive state. |
| Proven schema | PASS | No table/field/migration; search held typed Movement.type. |
| Tenant and services | PASS | Shared selection retains model.tenant_id; catalog cannot grant authority. |
| Specification / tests | PASS | FR/DR acceptance and test-first tasks before implementation. |
| Explainable product | PASS | Correct sample IDs and scope, unchanged exact-order evidence. |
| Storage discipline | PASS | Existing PostgreSQL pagination and libraries. |
| Stated values | PASS | No mixed-unit totals or recomputation. |

Post-design result: PASS. No exceptions. Product scope accepted in the current session;
implementation/review do not authorize merge or autonomous confirmation.

## Design and Repository Paths

1. Domain: no changes. `Movement.type` already drives stock/fulfillment rules.
2. Service: `services/core.py:business_discovery_statement` includes Movement.type in
   searchable columns, before cursor/limit; both legacy and `read_contracts.py`
   continue sharing this selection. Preserve exact record identity precedence.
3. Catalog/tool: `config/tool_catalog.json` explicitly requests one standalone generic
   confirmation entry. `tool_catalog.py` honors this presentation declaration even
   when the tool is also bound to an intake command. Validate unknown standalone names;
   preserve topic tool-count deduplication, grants and actual dispatch.
4. Adapter: `mcp/catalog.py` query description names movement-type search; Chat's
   existing `_shipping_context` uses it unchanged. Both loops are tested through
   multiple calls with padded non-shipping evidence and current read-first access.
5. Documentation: generated Tool Usage, demo guide and capability contract reference
   the actual generic tool, read scope and external recurring boundary.
6. Qualification: existing client controls only. Retain actual mission, runtime/time
   evidence, explicit next-run/pause and cleanup; unsupported/blocked outcome is a
   recorded limitation, not infrastructure to build in this feature.

## Tests Planned Before Implementation

- Shared service/HTTP MCP discovery: more than five preceding non-shipping IDs,
  substring/case/nonmatch/empty query, same-tenant paging, foreign identity, cursor
  mismatch, legacy/page parity, no writes.
- Both provider loops: published EN/DE read-first mission, multi-round evidence and
  absence of Shipment objects; refusal remains unknown and unrelated turns unchanged.
- Capability catalog: read-only and confirm-capable principals, direct generic review
  entry, retained intake mapping, unique tool counts, unchanged access reasons.
- Complete required Quality workflow, Python lint, spec policy and regenerated docs.
- Live actual daily mission assessed against retained evidence; client recurring
  qualification records actual/manual/unsupported outcomes and preserves original
  connections. Provider prose is not treated as deterministic unit-test evidence.

## Migration, Rollback and Risks

No migration. Roll back service/catalog metadata together and regenerate docs. Live
keyset pages are not snapshots; an old cursor keeps its declared query but selections
now actually honor it. Movement query matching is substring/type only, never an
order-number search or commitment join. Generic capability appears in two topics by
intent, without a second execution path. More focused evidence may improve model
wording but does not guarantee it; a failed live mission remains an open acceptance
finding. External schedules require the Mac/client/runtime to be available and an
active scoped credential. Pause test timing before credential cleanup.

## Complexity Tracking

No Constitution exception; no typed final-report schema or second provider reviewer
introduced before the concrete read defect is corrected and retested.

## Live-test amendment

The actual daily mission failed when the provider supplied undeclared `limit` to
`shipments_list` (declared `size`). Before implementation, add FR-005, test the
canonical additionalProperties=false boundary and both provider retries. Reject
unknown top-level names before dispatch, using existing InvalidOperation; do not
catch arbitrary TypeError or silently translate arguments. Preserve union schemas
and genuine handler failures. No dependency, schema or business rule change.
Constitution Check: PASS.
