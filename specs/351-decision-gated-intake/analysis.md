# Cross-artifact analysis: 351-decision-gated-intake

**Date**: 2026-10-03
**Language**: English
**Scope**: Specification, technical plan, tasks, data model and interface contracts.
**Result**: No remaining HIGH/CRITICAL design finding identified after remediation.
This is not runtime verification or completed business-writer coverage.

## Review method

Repository-grounded analysis compared intended behavior with existing interpreter,
proposal, source/outcome, finance, item-import and scheduler code. Independent
read-only research/review agents covered shared admission/Shopify/financial/rollout
and bulk/agent/file/demo design respectively. Root resolved their findings and
rechecked cross-package wording and requirement/task references. No extension
hooks are configured. Spec-Kit prerequisites are checked per feature.

## Findings and resolution

| ID | Original severity | Finding | Resolution |
| --- | --- | --- | --- |
| A001 | HIGH | Prepared and applied outcomes could collide on immutable attempt identity | Resolved: monotonic locked phase allocation, idempotent replay and phase-local retry in data-model.md, contracts and US2 tasks. |
| A002 | HIGH | New proposal-first/source-first order could deadlock with existing business/finance/raw locks | Resolved: Tenant-row-first prefix, matching signed-bigint source advisory-key ordering, no later separate event lock; raw admission changes before activation. |
| A003 | HIGH | Writer coverage artifact referenced by tasks was missing | Resolved at planning level: writer-coverage.md and 507-candidate inventory added; full semantic enforcement/test completion remains explicitly pending. |

## Coverage summary

- 10 functional and 3 domain requirements; three acceptance stories.
- 16 ordered implementation tasks, all intentionally unchecked.
- Every FR/DR has scenario and planned executable proof; spec task IDs resolve.
- Constitution check passes at design level with no proposed exception.
- Local document links and dependency references resolve; unresolved template or
  product clarification markers are absent.
- Tests precede corresponding implementation, then domain/schema/services/tools/
  adapters. Actual migrations are not allocated or claimed applied by planning.

## Implementation evidence still required

Real PostgreSQL concurrency, phase numbering, crash/replay, current authorization
and transport refusal proofs; all required regression/frontend/catalog/migration
checks; and actual volume/resource measurements where in scope. Existing sources
and test behavior may expose additional engineering issues during implementation;
those must be resolved before completion, not hidden by this design-level result.

The static writer inventory intentionally includes read/audit candidates and does
not prove every dynamically registered or nested writer is covered. Spec 356 owns
final semantic closure. Automated agent verdict fixtures prove pipeline behavior,
not independent model quality or live-provider cost.
