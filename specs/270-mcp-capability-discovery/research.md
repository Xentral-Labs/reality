# Research: One Way In to the Capability Catalog

**Branch**: `270-mcp-capability-discovery` | **Date**: 2026-09-25

Everything below was measured against `main` at `8f77dc43` with the repository's own catalog, not
estimated.

## R1 — The classification already exists and never leaves the process

`reality.tool_catalog.build_tool_catalog`, reached through `reality.catalogs.runtime_application_catalog`,
produces 181 capability entries. 167 of them carry MCP tools, covering all 179 tools with no gaps:

```text
payments 32 caps / 33 tools      master       13 / 18
accounting 22 / 27               stock        12 / 12
review 17 / 17                   evidence     11 / 15
orders 16 / 18                   contribution 10 / 10
shipping 16 / 22                 company       4 / 4
analytics 14 / 14
```

Purposes across those entries: 96 `change`, 52 `read`, 19 `understand`. German labels: 99 of 167.
`finance_dunning_record_propose` already carries `Mahnung erfassen`, `finance_dunning_reverse_propose`
`Mahnung stornieren`.

Eleven tools appear in more than one entry (among them `shipment_dispatch_propose`,
`movement_create_propose`, `supplier_payment_post_propose`), which is why coverage must be counted
over unique names.

**Consequence**: the feature transmits an existing structure. It introduces no vocabulary, and a
tool without a classification already fails `build_tool_catalog`, so discovery cannot silently omit
one.

## R2 — What the wire actually carries today

Built through `reality.mcp.server.build_server` and read from the tool manager:

- 179 tools, flat. The `group` on `MCPToolDefinition` is not transmitted; it appears only in the
  settings metadata.
- Per tool: `name`, `description`, `annotations.title`, `readOnlyHint`, `destructiveHint`, and the
  argument schema.
- Server instructions, in full: *"Inspect operational reality through shared application services.
  Mutations are proposals and require separate human approval."*
- `tools/list` is not filtered per credential: `build_server` registers every definition and
  `_handler.invoke` checks `principal.permits` only when the call arrives.

## R3 — Answer sizes, and why the answer is two steps

Serialized as JSON, for the slim shape an agent needs (capability, both labels, purpose,
description, tools with grant state):

| Step | Bytes |
|---|---|
| Topics only | 697 |
| Largest topic (`payments`) | 9,358 |
| Second largest (`accounting`) | 6,912 |
| Every topic at once | 49,943 |
| The built classification unslimmed | 269,360 |

**Consequence**: one dump would cost roughly 12k tokens before the agent has asked anything. The
topic step costs almost nothing and the largest topic is affordable, so the two steps are the shape.

## R4 — Two refusal reasons exist, and the principal cannot tell them apart

`dispatch_mcp_tool` performs two checks: `principal.permits(tool_name)`, then, for interactive
credentials, `reality:<access>` in `principal.scopes`.

But `resolve_interactive_principal` builds `allowed_tools` as
`name in grant.allowed_tools AND ACCESS_SCOPE[access] in grant.scopes`. A tool excluded by scope is
therefore already absent from `allowed_tools`, fails the *first* check, and the agent is told
"does not allow tool" rather than "does not allow that access". The two reasons are distinguishable
only from the `mcp_client_grant` row.

Manual tokens model no access-class scopes at all: `DatabaseTokenVerifier` builds their scope set as
`reality:read` plus one `reality:tool:<name>` per permission, and the interactive scope check is
skipped for them. `scope_excluded` cannot occur for a manual token.

A second rule decides which reason is the useful one. `approve_interaction` refuses an approval whose
tools exceed the requested scopes, so no grant can hold a tool of an access class its scopes exclude.
An excluded class is therefore always *absent* from the grant, and the actionable distinction is not
"named but out of scope" against "not named" but rather: is the whole access class out of scope, so
that selecting the tool would not have been possible, or is the class in scope and the tool merely
unselected? The first calls for a broader scope, the second for a wider tool list.

**Consequence**: the service reads the grant row once per call for interactive credentials, decides
the reason from whether the access class is in scope, and reports `not_in_token` for manual ones.

**Correction**: an earlier reading of this plan assumed a grant could name a tool its scopes exclude,
and would report `scope_excluded` for that case alone. Consent makes that state unreachable, so the
rule was inverted during implementation and the contract updated with it.

## R5 — Catalog access cost

`runtime_application_catalog()` deep-copies all nineteen sections: **45.5 ms per call**, measured
over five calls after warm-up. The tool-catalog slice alone is 263 KB.

**Consequence**: a narrow accessor for the slice. Isolation is kept; only the amount copied changes.

## R6 — The gates a new read tool must pass

Verified by reading the checks rather than by recalling them:

1. `config/tool_catalog.json` → `mcp_topics` needs the name, or `build_tool_catalog` raises
   "MCP tool needs an explicit capability topic" and takes the catalog with it. `capability_describe`
   sits in `evidence` and in `understand_tools`.
2. `catalogs.py` requires a full capability-guidance block in `command_catalog.yaml` for every MCP
   read tool except `capability_describe`, which is exempted by name in `public_business_read_names`.
   A guidance block demands a `data_basis` of real tables, which a catalog read has none of.
3. `config/tenant_isolation_catalog.yaml` → `tool:<application name>` in the `application_boundaries`
   family, beside `tool:capability_describe`.
4. `config/resource_catalog.yaml` → the agent-work resource's `match` pattern already names
   `capability_describe` and `business_records_discover` explicitly; an unmatched entry fails the
   generator with "entries without a business resource".
5. `make docs-generate` plus `make docs-catalog-check`; CI fails on stale output.
6. A new test file must appear in `docs/SPEC_COVERAGE_MATRIX.md`.

The tenant isolation catalog's `discovery.modules` lists nine service modules; a new
`reality.services.capability_catalog` is not among them, so no pinned operation count moves.

## R7 — The reported failure, reproduced in reasoning

The five dunning tools have been in `MCP_TOOL_CATALOG` since #165 and deployed since 2026-09-24
05:23 UTC. An agent whose credential was issued before that addition sees them in `tools/list` —
which is unfiltered — and is refused on call with `MCP token does not allow tool: …`, because an
allowlist is a frozen list of names that no later addition joins. Reporting the capability as
missing is the honest reading of that message, and nothing in the surface offers a better one.

Widening credentials is spec 269's neighbouring non-goal. Making the refusal legible is this
feature.
