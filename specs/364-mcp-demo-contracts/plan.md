# Implementation Plan: Complete Live Demo Agent Contracts

**Branch**: `codex/364-mcp-demo-contracts` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)

## Summary

Fix the five accepted live boundaries in the existing services, Chat provider loops
and MCP adapter. Reuse bounded movement discovery, shared retained delivery review,
registered schemas and catalog mappings; preserve stored receipts.

## Technical Context

Python 3.12+, SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI/MCP SDK, pytest. No new
dependency, domain table, migration or web implementation. Decimal and UTC preserved.
Existing full Quality workflow remains required, including four database shards.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Prefetch only held shipment Movements with original IDs and bounded completeness | PASS |
| Reality owns operational state | No document status or replacement calculations | PASS |
| Proven schema only | No stored field added | PASS |
| Tenant + shared services | Chat dispatches canonical scoped read; proposals use existing review and lock services | PASS |
| Spec/test traceability | Every FR/DR mapped below; HTTP and Playground regressions first | PASS |
| Explainable web | Existing consumers retain original receipts and review shape; no UI rules | PASS |
| Received values | Stored execution receipt is never rewritten to change vocabulary | PASS |
| Smallest design | Existing adapter and provider paths; no new public tool or queue | PASS |

## Repository Structure and Layer Changes

- `services/proposal_reviews.py`: complete safe handoff template; derive callable guidance
  from the executable catalog through a reusable helper.
- `services/tenant_policy.py`: recognize only the existing transaction-bound authored
  lesson proposal context; do not grant new authority or change admission.
- `tools/application.py`: create the ordinary retained review for fresh eligible demo
  reservation proposals; annotate and proportionately test changes against demo lessons.
- `mcp/catalog.py`: add separate callable guidance to approval/reconciliation responses;
  reuse the mapping helper without rewriting the recorded receipt.
- `mcp/server.py`: preserve each registered authoritative input schema in actual tools/list
  while retaining typed signatures and canonical handler validation.
- `agent/mcp_chat.py`: shared positive explicit read-first detection for both providers;
  pass read-only access to both schema selection and dispatch. For current shipping
  requests, supply bounded canonical shipment Movement context before the model answers;
  label company-wide retained scope and incomplete samples; no inferred totals.
- Existing EN/DE demo docs, generated references, feature contract and spec matrix.

## Design

### Reality flow

Existing SourceRecord → Document/Line → Commitment/Movement/Reservation stays unchanged.
No evidence is fabricated. A fresh proposal owns its existing retained snapshot and
fingerprint. Runtime guidance is a read-time adapter observation outside the receipt.

### Service and adapter flow

Domain unchanged → shared proposal/review service → application tool → MCP dispatch/HTTP
and model provider adapters. Preloaded Chat shipping evidence uses the existing read
handler with `family=movement`, `query=shipment`, bounded page and tenant scope. It is
separate from consignment search filters; the context explicitly declares that scope.
Only the current human turn constrains proposal access; persisted history and tool
results never widen or define permissions. Read-first is a conservative restriction.

### Data and migration impact

No migration. Retained review follows existing fields. Legacy proposals are not silently
rewritten by reads: handoff names preparation and reread. Receipts remain byte-equivalent
as received; new callable guidance is beside them in current responses.

### Failure, security and tenant behavior

Preserve private review redaction, explicit approval, separate credentials, stale
refusal, idempotency and attribution. Read-only mutation attempts follow the existing
canonical forbidden access boundary and return controlled refusal evidence to the provider.
Update the existing lesson companion test to assert denial and zero persistence rather
than an uncaught provider-loop exception. If preloaded evidence is refused, state unknown;
never treat it as an empty set. No access grant follows from a copyable call template.

## Test Strategy and Traceability

| Requirement | Test level / path | Expected initial failure |
|---|---|---|
| FR-001 | provider + real DB, `tests/test_chat_scope_security.py` | No retained shipping context when no model lookup occurs |
| FR-002 | both providers / actual dispatch, same file | Published read-first request still permits timezone proposals |
| FR-003 | authenticated HTTP, `tests/test_mcp_http_runtime.py` | Real enums/defaults/nested constraints lost |
| FR-004 | shared service and HTTP, `tests/test_demo_mcp_workflow.py` | Playground review generic until confirmation |
| FR-005 | exact review/legacy/authority, same file | No complete arguments/preparation state |
| FR-006 | execution/status/immutable receipt, same file | Follow-ups expose projection names only |
| DR-001/002 | existing privacy, decision, tenant and demo regressions | Scope, staleness, replay and redaction must remain passing |
| DR-003 | review and schema diff | No migration or new entity |

Focused tests first, then required complete GitHub checks. Tests use isolated PostgreSQL
and fake provider transport for deterministic enforcement, not live refusal-rate claims.
Public schema proof exercises tools/list, not only registry definitions.

## Rollout and Rollback

No local deployment in this coding request. Existing legacy confirmation preparation
remains supported and explicitly described. Roll back code without data migration;
retained snapshots and original receipts remain compatible. Generated docs must match.

## Review Risks

- Removing a blanket Playground shortcut can affect authored lessons; constrain the
  correction to the proven reservation case, preserve separate admission boundaries.
- Broader inferred read-only language can overrestrict; use explicit affirmative phrases
  only and test ordinary propose requests and history separation.
- Shipping context is a bounded company sample, never exact consignment-search coverage.
- SDK-generated schemas must still use typed handlers; test actual calls and unions.

## Complexity Tracking

None: no constitutional exception or new infrastructure.
