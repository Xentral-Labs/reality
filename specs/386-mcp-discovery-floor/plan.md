# Implementation Plan (Draft): A Discovery Floor Every MCP Grant Holds

**Branch**: `386-mcp-discovery-floor` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Status**: Draft for the owner's decision (spec D-1 to D-3). No code in this pull request.

## Sketch, assuming the proposed decisions

- `mcp/catalog.py`: `DISCOVERY_FLOOR = frozenset({"capability_catalog", "company_context"})`,
  with an import-time or test-time check that each member exists and is `read`.
  `validate_tool_permissions` appends the floor to any non-wildcard selection, so both grant
  paths get it from the one shared validation (spec 271).
- `services/mcp_authorization.py`: `interaction_view` returns the floor separately from
  `eligible_tools`; `resolve_interactive_principal` unions the floor into `tools` (D-2 a).
- `mcp/auth.py`: the manual token branch unions the floor into `allowed_tools`.
- `apps/web`: the consent screen and the token form list the floor as "Always included" above
  the selectable tools; labels in four languages.

## Constitution Check *(blocking gate, provisional)*

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Untouched. | PASS |
| Reality owns operational state | No business state. | PASS |
| Proven schema only | No schema. | PASS |
| Tenant + shared service boundaries | Floor added in the shared validation and resolution; floor tools are already tenant-scoped reads. | PASS |
| Spec/test traceability | Tests below. | PASS |
| Explainable web behavior | The floor is shown, not hidden. | PASS |
| Received values not recomputed | No business value. | PASS |
| Smallest coherent design | One constant, applied where permissions are already normalized and resolved. | PASS |

## Tests to write first

A grant of one proposal tool calls both floor tools; a floor-only credential is refused
other tools; a manual token of one tool calls both floor tools; the consent view marks the
floor as included; a catalog test asserts every floor member exists and is `read`; spec 271's
parity test still holds with the floor added to both paths.

## Security review focus

- `capability_catalog` reveals which tools exist and which this credential holds; the
  credential's holder can already discover that by calling tools.
- `company_context` reveals the company's id, name and purpose to a credential already scoped
  to that company.

## Rollback

Remove the constant and the unions. Grants created meanwhile keep the floor in their stored
list under D-3, which is still read-only.
