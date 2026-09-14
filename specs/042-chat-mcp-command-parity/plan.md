# Implementation Plan: Complete Chat and MCP Command Coverage

**Branch**: `042-chat-mcp-command-parity` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Make the canonical command catalog executable as a parity contract. Every eligible
tenant business read is exposed directly to Chat and MCP, while every eligible
mutation creates an exact durable proposal and executes only after explicit approval.
Existing application services remain authoritative. The only missing business entry
point is a small manual order service that writes immutable manual Source evidence,
Document/DocumentLine evidence, and derives Commitments through the existing
interpretation path. No database schema change is required.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, Typer, FastMCP
**Storage**: PostgreSQL; existing immutable artifact storage for source binaries
**Testing**: pytest unit, service, business-story, Chat/MCP adapter, and catalog policy tests
**Project Type**: backend services/API/CLI plus independent MCP runtime and React frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope; mutation proposals require explicit confirmation
**Scale/Scope**: Approximately 34 canonical command families plus bounded discovery/detail reads; no generic CRUD or platform maintenance exposure

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Order creation records manual SourceRecord evidence, creates Document/DocumentLine evidence, then derives Commitments through existing interpretation. Master/source changes preserve their existing evidence behavior. | PASS |
| Reality owns operational state | Orders add no fulfillment fields to Documents. Reservation, holds, movement, settlement, and ledger state remain Reality-derived. | PASS |
| Proven schema only | No schema or migration is planned. Tool eligibility and schemas are configuration/code metadata; existing ChangeProposal JSON stores exact inputs/previews/results. | PASS |
| Tenant + shared service boundaries | Catalog handlers call existing tenant-scoped application services. Chat uses the same registry as MCP; adapters never write through ORM. Approval rechecks tenant and authorization. | PASS |
| Spec/test traceability | Every FR/DR is mapped below and tasks will require tests before implementation. | PASS |
| Explainable web behavior | Executed proposals retain exact inputs/results and link to events where supported; order explanation traverses Source, Evidence, and Reality. No browser business rule is added. | PASS |
| Smallest coherent design | Extend the existing Tool/ChangeProposal/MCP registry, generate coverage from the canonical command catalog, and add only one missing order orchestration service. | PASS |

Planning may continue: all rows pass and no constitutional exception is requested.

## Repository Structure and Layer Changes

```text
packages/reality-core/config/
  command_catalog.yaml                 # executable agent eligibility and mapping metadata
packages/reality-core/src/reality/
  catalogs.py                          # load and validate parity metadata
  services/core.py                     # smallest manual-order orchestration and reused services
  tools/application.py                 # canonical read/mutation handlers and proposal lifecycle
  mcp/catalog.py                       # typed public schemas generated/bound to application tools
  agent/mcp_chat.py                    # consumes the same MCP definitions; no separate list
packages/reality-core/tests/
  test_agent_command_parity.py         # catalog completeness and schema/registry drift
  test_agent_discovery.py              # bounded tenant-scoped discovery/details
  test_chat_mcp_business_commands.py   # representative proposal/approval families
  test_chat_mcp_orders.py              # sales/purchase Source→Evidence→Reality stories
docs/
  CLI_SPEC.md                          # surfaces and confirmation semantics
  WEB_SPEC.md                          # shared registry and approval behavior
  features/chat.md                     # durable Chat/MCP capability contract
```

Dependency direction remains adapter → application tools → services → persistence.
Configuration describes eligibility and mapping but never implements behavior.

## Design

### Reality flow

For existing commands, handlers preserve the service's established shortest links.
Manual order creation uses approved proposal → manual immutable SourceRecord/version →
Document + DocumentLine evidence → existing interpretation → customer or supplier
Commitments → existing projections and order explanation. Human order numbers, names,
and SKUs may be discovery inputs but are never foreign-key identity.

### Service and adapter flow

`command_catalog.yaml` gains explicit agent exposure metadata for every canonical
command: `eligible` with a bound tool, `excluded` with a durable reason, or `blocked`
with a concrete missing service. A validator fails for missing, stale, duplicate, or
unjustified entries. The application Tool registry remains executable authority. MCP
binds strict JSON Schemas and managed Chat consumes those same definitions. Reads call
services immediately. Mutations normalize inputs, calculate exact previews, persist a
proposal without business effects, and call the canonical service only on approval.
Discovery returns bounded, tenant-scoped IDs and current mutation-relevant values.

### Data and migration impact

No database schema, migration, or backfill. Existing ChangeProposal JSON holds exact
inputs, previews, and results. Existing Source/Evidence/Reality structures remain
unchanged. Rollback is code/config only; executed immutable business effects remain.

### Failure, security, and tenant behavior

Cross-tenant IDs behave as not found. Approval repeats tenant, existence,
authorization, lifecycle, and stale-state checks. Multi-record/line execution is one
service transaction. Membership approval requires a current human owner. Rejection,
validation failure, stale state, and replay persist no business success or partial
effect. Input schemas reject unknown fields and errors disclose no secrets.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-019 | policy/unit | `test_agent_command_parity.py` classifies every command and rejects drift | Catalog lacks classifications and most mappings |
| FR-002, FR-004–FR-005 | service/adapter | `test_agent_discovery.py` proves bounded tenant reads, details, opaque IDs | Discovery tools are absent |
| FR-003, FR-006–FR-009 | service/story | proposal preview, no pre-approval effect, atomic execution, same service result | Eligible mutations are absent from registry |
| FR-010–FR-011 | business story | sales/purchase proposals produce Source→Document/Lines→Commitments | No order create tool/service exists |
| FR-012 | business story | movement, identity, reserve/release, and hold/release proposals | Only reserve and correction are exposed |
| FR-013 | business story | payment, reversal, terms, and pricing proposals | Finance/pricing proposals are absent |
| FR-014–FR-015 | story/auth | source lifecycle and owner-authorized membership proposals | Source configuration parity is absent |
| FR-016–FR-022, DR-001–DR-006 | policy/story/adapter | exclusions, compatibility, schema parity, audit, failure, evidence, and tenant tests | Coverage is incomplete |

## Rollout and Rollback

Existing tool names remain stable; new definitions are additive. Existing token
allowlists do not automatically gain new permissions. No migration ordering is needed.
Application and MCP runtimes roll back together; pending proposals whose tools are no
longer available fail safely and never use an alternate execution path.

## Review Risks

- Mechanical completeness could expose technical/dangerous operations; exclusions need review.
- Large nested inputs need exact but compact structured previews.
- Service transaction behavior must be proven, not assumed.
- MCP token permission alone must never authorize membership changes.
- Human references must not become persisted relationships.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Post-Design Constitution Recheck

The design introduces no schema, duplicate rules, alternate persistence path, or
document-owned operational state. All Constitution Check rows remain PASS.
