# Implementation Plan: The Capability Catalog Names the Company's Purpose

**Branch**: `feat/tenant-purpose-in-capability-catalog` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)

## Summary

Add one key, `tenant.purpose`, to the topic index of `capability_catalog`, read from the stored
company record of the calling tenant through the existing shared read service. No new tool,
schema, input or migration.

## Technical Context

Python 3.12+, SQLAlchemy 2, PostgreSQL, MCP SDK, pytest. No new dependency, domain table or
web change. The value already exists as `Tenant.purpose`, fixed at company creation.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | The value is the stored company purpose, read as recorded | PASS |
| Reality owns operational state | Nothing is derived or cached; the company record is the source | PASS |
| Proven schema only | No stored field added | PASS |
| Tenant + shared services | One query filtered by the server-verified tenant id in `services/capability_catalog.py`; the MCP adapter is unchanged | PASS |
| Spec/test traceability | FR-001, FR-002 and DR-001 mapped below | PASS |
| Explainable web | No UI change | PASS |
| Received values | Not applicable; no external value is received | PASS |
| Smallest design | One key on an existing read | PASS |

## Repository Structure and Layer Changes

- `services/capability_catalog.py`: `_tenant` reads `Tenant.purpose` for the calling tenant and
  refuses a missing company; `topic_index` returns it as `tenant`.
- `specs/270-mcp-capability-discovery/contracts/capability_catalog.md`: the contract names the
  object and states that it is a metadata read.
- No change to `mcp/catalog.py`, `mcp/server.py` or `tools/application.py`: the existing
  dispatcher already passes the server-verified principal's tenant id to the read.

## Design

### Reality flow

Company record → shared catalog read → MCP adapter. No business record is read, no evidence is
created, and the answer carries no company id or name.

### Data and migration impact

None. Additive response key; existing readers ignore it.

### Failure, security and tenant behavior

The query is filtered by the tenant id the dispatcher derives from the verified principal; a
caller cannot name another tenant. A missing company is refused, never answered with a default.
Single-topic answers are unchanged.

## Test Strategy and Traceability

| Requirement | Test level / path | Proof |
|---|---|---|
| FR-001 | service, `tests/test_capability_catalog.py::test_topic_index_names_the_tenant_purpose` | Business and playground companies answer their own purpose |
| FR-001, FR-002 | read tool, `::test_the_token_reads_only_its_own_tenant_purpose` | Two principals; each answer its own purpose, no foreign id or name |
| FR-001, FR-002, DR-001 | MCP boundary, `::test_each_verified_token_reads_its_own_tenant_purpose_over_mcp` | Two bearer tokens over the HTTP MCP runtime; the server verifies each |
| SC-001 | contract, `specs/270-mcp-capability-discovery/contracts/capability_catalog.md` | A client reads the purpose without asking a person |

## Rollout and Rollback

Roll back the code; no data changes. Clients that ignore the key are unaffected.

## Review Risks

- A client may treat the purpose as a description of every proposal shape. Since spec 364 a
  playground reservation carries the same review as a business one; the purpose says which
  company it is, not how each tool previews.

## Complexity Tracking

None.
