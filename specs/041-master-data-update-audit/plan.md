# Implementation Plan: Auditable Master Data Updates

**Branch**: `041-master-data-update-audit` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

Extend the explicit Party, Item, and Location application tools with atomic update batches and confirmation-required MCP/Chat proposal schemas. Capture canonical normalized snapshots before and after each effective service mutation, emit only changed fields as `{before, after}`, and link proposal-origin events through the existing action relationship. Reuse existing storage and add no typed business fields.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript for frontend contracts
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite
**Storage**: Existing Party, Item, Location, PartyRole, SourceRecord, ChangeProposal, and BusinessEvent tables
**Testing**: pytest service/story/adapter tests; frontend contract tests and production build
**Project Type**: backend services/API/CLI plus independent frontend
**Constraints**: Decimal; UTC; opaque IDs; immutable sources; tenant scope; confirmed Chat mutations
**Scale/Scope**: Bounded same-family update batches; existing master-data fields only

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Manual changes append events; sourced changes retain immutable SourceRecord versions and lossless payloads. | PASS |
| Reality owns operational state | No Document or operational status changes; events remain audit evidence. | PASS |
| Proven schema only | No schema or typed-field expansion; existing event JSON carries the diff. | PASS |
| Tenant + shared service boundaries | All adapters call tenant-scoped update services; Chat/MCP execute application tools only. | PASS |
| Spec/test traceability | Every requirement maps below to service, proposal, tenant, adapter, or inspection tests. | PASS |
| Explainable web behavior | Existing event/Inspector responses expose the diff; browser adds no mutation rule. | PASS |
| Smallest coherent design | Reuses update services, ChangeProposal, BusinessEvent, and adapters; no generic mutation tool. | PASS |

Planning may proceed: every row passes and no exception is requested.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py       # snapshots, diffs, atomic batches
packages/reality-core/src/reality/tools/application.py   # update tools and stale guards
packages/reality-core/src/reality/mcp/catalog.py         # typed propose schemas
packages/reality-core/src/reality/agent/mcp_chat.py      # discovery and identity guidance
packages/reality-core/src/reality/web/api.py             # event inspection serialization if needed
packages/reality-core/config/command_catalog.yaml        # command reference
packages/reality-core/config/business_event_catalog.yaml # event reference
packages/reality-core/tests/                             # service, story, MCP, adapter proof
apps/web/scripts/                                        # inspection contract proof
docs/features/chat.md                                    # durable Chat contract
```

**Dependency direction**: Chat/MCP → proposal boundary → explicit update tool → tenant-scoped batch/update service → master data + optional SourceRecord version + BusinessEvent in one transaction. CLI/API/Web continue calling the same services.

## Design

### Reality flow

Manual updates do not fabricate Source or Evidence: the stable Party/Item/Location current state changes and one immutable BusinessEvent records the effective diff. When source provenance is supplied, `update_master_source_reference` creates the next immutable SourceRecord version and the event retains its direct source link. The master-data opaque ID remains stable.

### Service and adapter flow

- Canonical snapshot functions cover every supported field, including roles and nullable opaque relationships.
- Update services validate and normalize, compare before/after snapshots, and emit one event only for an effective change.
- `_commit=False` and optional action context let same-family batches share one transaction.
- `update_parties`, `update_items`, and `update_locations` accept records requiring opaque `id` plus complete intended update values.
- Proposal creation stores canonical reviewed revisions and displays intended changes.
- Confirmation rechecks revisions, passes the proposal ID into emitted events, and calls the registered update tool once.
- MCP exposes `party_update_propose`, `item_update_propose`, and `location_update_propose`; Chat may discover by display fields but execution always uses opaque IDs.
- Direct CLI/API/Web updates gain identical event semantics through the service layer.

### Data and migration impact

No migration. BusinessEvent already stores immutable JSON and `action_id`; ChangeProposal stores exact JSON input/output. The additive authoritative payload member is `{"changes":{"field":{"before":value,"after":value}}}`. Decimal values serialize canonically as strings; booleans, nulls, lists, and opaque IDs retain JSON types. Existing concise keys remain for compatibility.

### Failure, security, and tenant behavior

- Cross-tenant IDs behave as not found during preview and confirmation.
- Batch failure rolls back records, roles, SourceRecord versions, and events together.
- A deterministic hash of each reviewed normalized snapshot detects stale approval.
- Duplicate target IDs are rejected.
- Canonical validation remains authoritative for roles, numeric values, relationships, and hierarchy cycles.
- No-op updates and lifecycle commands emit no false business-change event.
- Strict MCP schemas accept only cataloged fields.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-004 | MCP/story | `tests/test_chat_master_data_updates.py`, `tests/test_ai_mcp.py` | Update proposals are absent. |
| FR-005, FR-013 | service/adapter | master-data API, CLI, and parity tests | Event summaries are incomplete. |
| FR-006, FR-011 | service | atomic mixed-validity batch tests | Batch update services are absent. |
| FR-007 | proposal/story | stale reviewed-snapshot confirmation test | No update revision guard exists. |
| FR-008–FR-010, FR-014 | service/event | `tests/test_master_data_update_audit.py` | Events lack diffs/no-op rules. |
| FR-012 | API/Web contract | event serialization and Inspector contract tests | Structured diff exposure is unproven. |
| DR-001–DR-004 | story/tenant | source-version, stable-ID, cross-tenant, unchanged-Reality tests | Full path is uncovered. |

Tests are added and observed failing before implementation where practical.

## Rollout and Rollback

Deploy as an additive tool/event contract. Older events remain readable without `changes`; consumers tolerate both. Rollback requires no database downgrade because new payloads remain valid JSON and old readers ignore unknown keys.

## Review Risks

- A missing snapshot field creates incomplete history.
- Noncanonical Decimal/string serialization creates false changes.
- An inner commit breaks atomicity.
- Missing reviewed-state checks apply obsolete intent.
- Source versions, state, and events must share one transaction.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Post-Design Constitution Re-check

All seven checks remain PASS: no schema expansion, shortest links, shared tenant-scoped services, explicit confirmation, and test traceability are preserved.
