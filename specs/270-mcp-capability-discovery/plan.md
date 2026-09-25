# Implementation Plan: One Way In to the Capability Catalog

**Branch**: `270-mcp-capability-discovery` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Add one read tool, `capability_catalog`, that answers in two steps: without arguments the eleven
capability topics, with a topic that topic's capabilities and the MCP tools bound to each. Every
listed tool carries whether the calling credential may call it and, when not, which of the two
refusal reasons applies.

Nothing is classified anew. `reality.tool_catalog.build_tool_catalog` already assigns every one of
the 179 MCP tools a topic, a purpose, a description and, where the resource catalog holds one, a
German business label; the tool transmits that and adds the grant state. No schema, no migration,
no new dependency, no write.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, Pydantic v2 (unchanged); the existing application catalog
**Storage**: None. One tenant-scoped read of `mcp_client_grant` for the refusal reason
**Testing**: pytest — catalog coverage, grant state per credential kind, MCP runtime, tenant isolation
**Project Type**: backend service plus application read tool plus MCP adapter; no web change
**Constraints**: read-only, no confirmation, no side effects, no tenant business data in the answer
**Scale/Scope**: 179 tools across 167 capability entries and 11 topics; measured answer sizes in
[research.md](research.md) — 0.7 KB for the topic step, 9.4 KB for the largest topic

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Untouched. The answer describes capabilities, never business evidence, and reaches no Source, Document or Reality record. | PASS |
| Reality owns operational state | No document, status or derived business state is introduced or read. | PASS |
| Proven schema only | No table, column or migration. The classification already exists and is read, not stored. | PASS |
| Tenant + shared service boundaries | The one repository read filters on `tenant_id` and `grant_id` from the server-verified principal. The tool is dispatched through `run_read_tool` like every other read; the adapter writes nothing. Registered in `tenant_isolation_catalog.yaml` under `application_boundaries`. | PASS |
| Spec/test traceability | Every FR maps to a test in Test Strategy below. | PASS |
| Explainable web behavior | No web surface changes. The tool makes the agent surface explainable in the same spirit: what exists, and why it is refused. | PASS |
| Received values not recomputed | No business value is read, compared or derived. Grant state is a property of the credential, evaluated at read time and not stored. | PASS |
| Smallest coherent design | One tool, one service function, no new vocabulary, no new infrastructure. Alternatives rejected in Decisions. | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/
  services/capability_catalog.py      # NEW: topics(), capabilities(topic), grant state per tool
  tools/application.py                # + _capability_catalog handler, + TOOLS["capability_catalog"]
  mcp/catalog.py                      # + MCPToolDefinition("capability_catalog", …, group "Discovery")
  mcp/server.py                       # instructions name the entry point (FR-006)
  catalogs.py                         # narrow accessor for the tool-catalog slice; widen the
                                      #   capability-guidance exemption from one literal to a set
  config/tool_catalog.json            # mcp_topics["capability_catalog"] = "evidence"; understand_tools
  config/tenant_isolation_catalog.yaml# + tool:capability_catalog in application_boundaries
  config/resource_catalog.yaml        # + the name in the agent-work resource's match pattern
packages/reality-core/tests/
  test_capability_catalog.py          # NEW (add to docs/SPEC_COVERAGE_MATRIX.md)
apps/docs/                            # regenerated Tool Usage pages and tool-usage.json
```

**Structure Decision**: domain-free service → application read tool → MCP adapter, the order
`AGENTS.md` requires. The service holds the shape and the grant rule; the adapter only declares the
schema and dispatches.

## Design

### The two steps

Without arguments: every topic with its key, label, and how many capabilities and tools it holds.
With `topic`: that topic's capabilities, each with the English label, the German label where one
exists, the purpose (`read`, `understand`, `change`), the description, and its tools with name,
access class and grant state. An unknown topic is refused by naming the topics that exist. The
response shape is in [contracts/capability_catalog.md](contracts/capability_catalog.md).

Two steps rather than one dump because the whole classification is 263 KB as built and roughly
50 KB even slimmed to what an agent needs — too much for a first call, and it would bury the answer
it was asked for. Measurements in [research.md](research.md).

### Grant state, and why it needs the grant row

The service mirrors exactly the two checks `dispatch_mcp_tool` performs, so a tool it reports as
callable cannot then be refused for permission reasons:

| Caller | Source of truth | Reason when not callable |
|---|---|---|
| No MCP principal (CLI, chat) | — | none; every tool is listed callable and the answer says no credential limits it |
| Manual token | `principal.permits(name)` | `not_in_token` — the token's tool list does not name it |
| Interactive grant | `mcp_client_grant` row for `(tenant_id, grant_id)` | `not_in_grant`, or `scope_excluded` when the grant names it but the granted scopes exclude its access class |

The grant row is necessary because `resolve_interactive_principal` already intersects the grant's
tools with its scopes before a principal exists. Reading only the principal would collapse both
reasons into one, which is the conflation this feature exists to end. The read is by primary key
within the tenant and happens once per call, not once per tool.

Manual tokens model no access-class scopes at all — their scope set is `reality:read` plus one
`reality:tool:<name>` per permission — so `scope_excluded` cannot arise for them. That is a
truthful per-kind outcome of FR-004, not a gap.

### Catalog access

`runtime_application_catalog()` deep-copies all nineteen catalog sections on every call. For a tool
meant to be an agent's first call that is waste, so `catalogs.py` gains a narrow accessor returning
only the tool-catalog slice. It still returns a copy; the saving is in what is copied, not in giving
up isolation. Measured back to back: 16.0 ms against 6.8 ms, a 57% saving (research R5).

### Guidance exemption

Every MCP read tool except `capability_describe` must carry a full capability-guidance block in
`command_catalog.yaml`, including a `data_basis` of real tables. `capability_describe` is exempt by
name because it reads the catalog rather than business data. `capability_catalog` is in exactly that
class, so the literal becomes a named set of catalog-about-capability tools, asserted to hold only
those two. Writing a guidance block instead would require naming tables the tool never reads.

### Decisions

- **The tool listing stays unfiltered per credential** (spec non-goal). Hiding a tool would make it
  indistinguishable from one that does not exist — the very confusion being fixed.
- **No new topic vocabulary.** The eleven topics of `config/tool_catalog.json` are reused as they
  are. A tool that is unclassified fails the existing build, so discovery cannot silently omit it.
- **`capability_describe` is not replaced.** It stays the per-tool answer; the new tool is the way
  to reach a name worth describing.
- **No web surface.** The company's own people already see this vocabulary in the command palette.

## Test Strategy

Written before the implementation, in this order:

1. **Coverage (FR-001, FR-003, FR-008)** — every name in `MCP_TOOL_CATALOG` appears under at least
   one topic; the topic set equals the eleven; counted from the catalog, never from a written list.
   Observed failing first, because the tool does not exist.
2. **Grant state (FR-004)** — four credentials: a manual token holding a subset, an interactive
   grant omitting a tool, an interactive grant whose scopes exclude `propose`, and a full grant.
   Each expected reason asserted by name.
3. **Callable means callable (FR-004)** — a tool the answer marks callable is then called through
   the MCP runtime and is not refused for permission reasons. This is the assertion that keeps the
   answer honest as dispatch changes.
4. **Two-call reachability (SC-001, the reported regression)** — from no arguments, reach the five
   dunning tools under `payments` in one further call.
5. **Labels (FR-005)** — a capability with a German label carries it; one without falls back to
   English and is not an error.
6. **Read discipline (FR-007)** — declared `read`, no confirmation, no side effects; the answer
   contains no tenant business record.
7. **Instructions (FR-006)** — the server's instructions name the tool.
8. **Answer size** — the topic step and the largest topic stay within the bounds in research.md.
9. **Gates** — `pytest tests/test_application_catalog.py tests/test_tool_catalog.py
   tests/test_reporting_graph_coverage.py tests/test_schema_indexes.py tests/tenant_isolation`,
   then `make docs-generate` and `make docs-catalog-check`.

## Rollback

Revert the tool definition, the service, the four config registrations, the instructions line and
the regenerated documentation. No migration, no stored data, no issued credential changes meaning.
An agent that learned the tool name simply gets "unknown tool" again.

## Risks and Review

- **Risk**: the answer says callable and the call is refused. **Mitigation**: test 3 executes the
  call rather than comparing two copies of the same rule.
- **Risk**: per-topic answers grow with the catalog; `payments` is already 9.4 KB. **Mitigation**:
  the size test states the bound, so growth is a decision rather than a surprise.
- **Risk**: the guidance exemption becomes a hole through which business reads skip their block.
  **Mitigation**: the exemption is an explicit set, asserted to hold only the two catalog tools.
- **Risk**: eleven tools are bound to more than one capability entry. **Mitigation**: they are
  listed under each with the same grant state and counted once for coverage; asserted in test 1.
- **Review focus**: that the grant rule and `dispatch_mcp_tool` cannot drift; that no tenant
  business data reaches the answer; that the German labels come from the resource catalog rather
  than from new strings.

## Complexity Tracking

No constitutional exception is required. One new service module, one new tool, no new
infrastructure or dependency.
