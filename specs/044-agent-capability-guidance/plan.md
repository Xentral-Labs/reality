# Implementation Plan: Agent Capability Guidance

**Branch**: `044-agent-capability-guidance` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Extend the canonical command catalog with validated semantic guidance and compose it
into read-only capability descriptions. Expose the same description through one
application tool and one MCP/Chat schema. Prove the boundary for `observe_fact`,
`create_manual_order`, `reserve`, and `record_movement`; keep execution on their
existing proposal and confirmation paths. No business schema or migration is required.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: PyYAML, Pydantic v2, existing application-tool and MCP registries
**Storage**: Existing PostgreSQL store; guidance is versioned YAML configuration, not tenant data
**Testing**: pytest catalog/unit and PostgreSQL stories; public Docs contracts/build
**Project Type**: Python application core with Chat/MCP adapters and public Docs
**Constraints**: Read-only lookup; opaque IDs; shared Chat/MCP path; no alternate validation
**Scale/Scope**: Four initial governed mutations and one generic description lookup

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Guidance distinguishes source-supported Facts, order Evidence, Commitments, Reservations, and Movements. | PASS |
| Reality owns operational state | Configuration describes existing services and projections but performs no mutation or calculation. | PASS |
| Proven schema only | No business table, field, relationship, or migration is added. | PASS |
| Tenant + shared service boundaries | One read-only application tool serves Chat and MCP; mutations remain proposal-bound. | PASS |
| Spec/test traceability | FR/DR mappings below name catalog, application, MCP, story, and Docs proofs. | PASS |
| Explainable web behavior | Public Docs explain selection and verification; Product Web behavior does not change. | PASS |
| Smallest coherent design | Existing catalogs are reused; no database model, workflow engine, or prompt registry is added. | PASS |

Post-design re-evaluation: all rows remain PASS. The contract adds only validated
application metadata and one read-only query path.

## Repository Structure and Layer Changes

```text
packages/reality-core/config/command_catalog.yaml
packages/reality-core/src/reality/catalogs.py
packages/reality-core/src/reality/tools/application.py
packages/reality-core/src/reality/mcp/catalog.py
packages/reality-core/tests/test_capability_guidance.py
apps/docs/content/concepts/agent-capabilities.md
apps/docs/scripts/docs-contract.test.mjs
specs/044-agent-capability-guidance/
```

**Dependency direction**: YAML vocabulary → catalog validation/composition → shared
application tool → MCP/Chat adapter. Mutation services remain authoritative.

## Design

### Reality flow

The feature changes no Reality flow. Descriptions explain the existing paths:

```text
SourceRecord -> Fact
SourceRecord -> Document/DocumentLine -> Commitment -> Reservation -> Movement
```

Fact verification uses Timeline plus the returned Fact identity and source trace.
Manual orders use Document and Commitment registers. Reservations use Inventory and
Commitment register. Movements use Inventory, Commitment register, and Timeline.

### Service and adapter flow

`load_application_catalog()` validates and composes `capability_guidance`. A read-only
`capability_describe` application handler resolves an advertised proposal tool to one
canonical command. It rejects unknown, excluded, blocked, or ambiguous tools without
consulting tenant rows. MCP/Chat expose a matching read tool that delegates to it.

### Guidance contract

Each adopted public-tool entry contains purpose, non-empty use and non-use conditions, required
context, preconditions, confirmation behavior, idempotency guidance, refusals, events,
verification reads, and positive/negative examples. Event references resolve against
the Event catalog; verification reads resolve against projections or registered
read-only application tools. Validation requires complete guidance for the four
initial services and validates every later guidance entry without inventing content
for all current commands.

### Data and migration impact

No SQLAlchemy model, PostgreSQL table, Alembic migration, or tenant record changes.
Descriptions are normalized in-memory catalog values derived from reviewed YAML.

### Failure, security, and tenant behavior

- Lookup is read-only and cannot create proposals or Business Events.
- Only mapped public proposal-tool names are accepted, preventing enumeration of
  administrative services.
- Catalog validation fails on incomplete fields, stale mappings, unknown references,
  or confirmation disagreement.
- Descriptions grant no authority and never weaken service validation.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-002, FR-006–FR-009 | catalog/unit | `tests/test_capability_guidance.py` description and selection matrix | No guidance structure exists. |
| FR-003–FR-005 | application/MCP | Shared read lookup and bounded unknown tests | No description tool exists. |
| FR-010 | parity | Extend `tests/test_agent_command_parity.py` | New read tool is not cross-validated. |
| FR-011 | story/catalog | Verification-reference and post-command re-read tests | No declared verification path exists. |
| FR-012 | unit | Planted missing, stale, unknown-reference, and confirmation-drift fixtures | Validator ignores guidance. |
| FR-013 | Docs | Extend `apps/docs/scripts/docs-contract.test.mjs` | No public guidance page exists. |
| DR-001–DR-003 | story/adapter | Twelve-case selection and shared-handler tests | Semantics cannot be queried. |
| DR-004–DR-005 | review/service | Schema-diff and existing service refusal regression | Requires explicit no-schema proof. |

## Rollout and Rollback

The change is additive. Agents that do not call `capability_describe` continue using
existing schemas. Rollback removes the read tool and metadata without data migration.

## Review Risks

- Guidance could become an unvalidated second implementation of domain rules.
- Service-name lookup could disclose internal operations; public tool identity is used.
- Syntactically valid verification reads may be semantically weak; stories prove four.
- Generalizing all commands now would manufacture unproven semantics.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
