# Implementation Plan: Daily evidence summary

**Branch**: `codex/daily-evidence-summary` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)

## Summary
Extend existing shared reads with a deterministic shown-page summary and explicit
order-line explanation scope. No new public tool, table, calculation authority or timer.

## Technical Context
Python 3.12, SQLAlchemy 2, PostgreSQL, pytest; existing tools and MCP dispatch.
Bounded at 100 shown records; O(page size), no aggregate scan, extra business query or write.
Native provider adapters use the same result. External agents read the same MCP envelope.

## Constitution Check
| Principle | Before research | After design | Proof |
|---|---|---|---|
| Source/Evidence/Reality | PASS | PASS | Original records/IDs remain; observations transient |
| Reality operational authority | PASS | PASS | Existing readiness service owns blockers |
| Proven schema | PASS | PASS | No persistence/schema expansion |
| Tenant/service boundary | PASS | PASS | Existing shared tenant-scoped reads |
| Spec/test first | PASS | PASS | Tests precede code; final CI required |
| Explainable product | PASS | PASS | Returned IDs and scope accompany counts |
| Simplicity/storage | PASS | PASS | No new tool/infrastructure |
| Received values | PASS | PASS | Counts are read observations, no quantity recomputation |

## Project Structure
- `packages/reality-core/src/reality/services/read_contracts.py`: page summary,
  count only `page["records"]`; preserve opaque IDs and existing metadata.
- `packages/reality-core/src/reality/services/core.py`: the existing scoped Item lookup
  for unit also supplies name/SKU to quantity references; no extra query or guessed label.
- `packages/reality-core/src/reality/services/projections.py`: per-line
  `unfulfilled_cause` status unknown/not_applicable and readiness boundary notice.
- `packages/reality-core/src/reality/agent/mcp_chat.py`: native guidance and canonical
  bounded return context; both provider loops share this helper.
- `packages/reality-core/src/reality/mcp/catalog.py`: executable tool descriptions.
- `packages/reality-core/tests/test_mcp_read_contract.py`: mixed counts, cursor,
  empty/exact/tenant/legacy/no-write and ready/blocked/partial/closed order proofs.
- `packages/reality-core/tests/test_chat_scope_security.py`: both provider-loop contexts
  and refused return evidence; no prose-correctness claim from stubbed responses.
- `apps/docs/content/{de/,}getting-started/demo-company.md`: assignment guidance.

## Implementation and Validation
US1/US2 share one service helper; tests before it. US3 independent order tests before
projection change. Existing full read/provider/demo/HTTP suites validate compatibility.
No migrations. Rollback removes additive fields and guidance only. Legacy lists retain
shape. Existing credentials need no new grants; no browser operational dependency.
Run package Ruff, spec policy, generated catalog check, docs build and full Quality CI.
Actual model mission is separately observed when local provider runtime is available;
if unavailable, state that limitation rather than substituting a prompt assertion.

## Complexity Tracking
No exceptions. Product scope accepted by user's next-point authorization.

Durable existing read authority: `docs/features/mcp_reads.md`; its new Spec 366 section
documents these additive fields and the retained legacy list shape.
