# Cross-artifact analysis: 360-bulk-intake-agent-review

## Approved scope clarification (2026-10-04)

This rollout governs external sources, imports and agent-proposed business effects.
They require an exact retained proposal and an authorized confirmation before acceptance.
A direct action by an authenticated human is itself the decision and uses the existing
application authorization and audit trail; it does not require a second proposal or
confirmation cycle. Derived effects of one operation share its transaction and receipt.

The owner retained PRs #333–#346 and withdrew the later universal canonical-writer
rollout. Internal service calls and every manual UI/CLI operation are not additional
admission projects. Existing tenant, domain, Finance and Chat confirmation rules remain.
A static writer inventory is discovery material, not a mandate to guard every writer.
References below to governed writes mean external intake only; broader earlier planning
and universal-writer tasks are superseded by this clarification.

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
| B001 | HIGH | Delayed child execution lacked original-reviewer authorization handoff | Resolved: immutable server-authored parent consent, exact child digests, current original-principal/mandate checks and truthful child attribution. |
| B002 | HIGH | Inline 500-member manifests exceed existing job configuration limits | Resolved: only batch/revision/continuation references enter queue configuration; 15,000-byte config and 3,500-byte result proofs. |
| B005 | HIGH | Business refusal and infrastructure failure could have the same partial-commit behavior | Resolved: child savepoint includes effects/attribution/outcome/receipt; domain no-effect dispositions isolated; infrastructure/lease failure aborts the complete chunk. |
| B006 | MEDIUM | Mandate identification, exposure and row/day limits were underdefined | Resolved: explicit mandate ID/revision; strict source/profile/effect scope, rows/unit and units/day, financial source-stated currency amounts and serialized daily quotas. |

## Coverage summary

- 13 functional and 3 domain requirements; three acceptance stories.
- 19 ordered implementation tasks, all intentionally unchecked.
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
not prove every dynamically registered or nested writer is covered. Spec 361 owns
final semantic closure. Automated agent verdict fixtures prove pipeline behavior,
not independent model quality or live-provider cost.
