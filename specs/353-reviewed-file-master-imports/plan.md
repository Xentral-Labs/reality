# Implementation Plan: Reviewed file, master-data and stock imports

**Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)
**Language**: English
**Status**: Design prepared; implementation and runtime verification pending

## Summary

Reuse artifact staging and item-import review hashing. Add a streaming file_intake reader with a whole-input bounded validation pass, stable row identities and frozen package boundaries. Retain the 500-row single-package transaction contract; the controlled small-row 5,000-row fixture becomes ten independent packages; other files may need more packages to respect the byte bound. File-derived order sources cite the original artifact/source. Remove interpreter-internal commits on every migrated profile. Display full paginated row coverage and excluded issues before creating the batch manifest.

## Technical Context

- Python 3.12+, SQLAlchemy 2, PostgreSQL, Pydantic v2, Decimal and UTC.
- Existing ChangeProposal, SourceRecord/SourceArtifact, ImportJob/outcome and
  application services; FastAPI/MCP/Typer remain adapters. React/Vite presentation
  is in scope only for stories that name frontend files.
- pytest with isolated real PostgreSQL; existing browser harness for changed flows.
- No parallel execution within a shared SQLAlchemy session; bounded independent
  work can use existing worker capacity under current authorization.
- Reviewed atomic package: at most 500 rows and the existing 2 MiB package profile;
  batch manifest: at most 500 independent proposals; continuation: at most 25 units.
- Larger raw item CSV: at most 5,000 rows/20 MiB via spec 353's separate packaging
  path. A coherent oversized order is review-required, never silently split.

## Constitution Check

| Principle | Concrete design evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Raw remains immutable; proposal precedes accepted evidence/effects; receipt cites shortest source links | PASS |
| Reality owns operational state | No provisional Document status or stored derived payment/stock authority | PASS |
| Proven schema only | Reuse proposal JSON; any mandate schema has repeated execution/expiry/revocation checks, documented in data-model.md | PASS |
| Tenant + shared services | Server-bound scope; composite links; adapters call common prepare/review/apply | PASS |
| Spec/test traceability | Every requirement maps to a story, exact planned test and ordered tasks | PASS |
| Explainable web | Review exposes exact meaning/effects and full source/receipt links; recovery reads only | PASS |
| Received values | Preserve stated values; never recalculate a source total or invent missing prices | PASS |
| Smallest coherent design | Existing proposal/jobs; no second workflow engine or business staging tables | PASS |

This is a design-level check, not evidence that the runtime has passed. Recheck
against the implemented diff and migration before marking tasks complete.

## Repository Structure and Layer Changes

- `apps/web/src/unified/ItemImportPanel.tsx`
- `packages/reality-core/src/reality/services/external_stock.py`
- `packages/reality-core/src/reality/services/file_intake.py`
- `packages/reality-core/src/reality/services/file_interpreters.py`
- `packages/reality-core/src/reality/services/item_imports.py`
- `packages/reality-core/tests/test_file_intake_admission.py`

- No new schema in this package; see data-model.md for reused storage and compatibility.

## Design

### Reality flow

Immutable source/artifact → non-authoritative prepared proposal → exact authorized
decision → canonical accepted evidence and explicit Reality effects → retained
receipt. The proposal is an interpretation stage, not accepted business evidence.

### Service and adapter flow

Reuse artifact staging and item-import review hashing. Add a streaming file_intake reader with a whole-input bounded validation pass, stable row identities and frozen package boundaries. Retain the 500-row single-package transaction contract; the controlled small-row 5,000-row fixture becomes ten independent packages; other files may need more packages to respect the byte bound. File-derived order sources cite the original artifact/source. Remove interpreter-internal commits on every migrated profile. Display full paginated row coverage and excluded issues before creating the batch manifest.

### Data and migration impact

Reuse SourceArtifact, SourceRecord, ChangeProposal and existing business tables. New package/file manifest schemas live in proposal JSON, not business staging tables. Raw file SourceRecord uses artifact identity/hash and received metadata, with bytes in SourceArtifact; normalized proposed rows are separately identified as interpretation. No new table is required. Any master-data update continues its existing expected revision contract.

### Failure, security and tenant behavior

Validate current permission and exact digest under the relevant locks. Known
no-effect failure rolls back its coherent unit. An unknown outcome is reconciled
against its retained proposal/run/receipt before redispatch. No token, queue receipt
or source text authorizes broader effects. Never substitute a fallback tenant.

### Bulk atomicity and freshness

An atomic package is one decision. A manifest groups independent child decisions.
The unit's reviewed source/mapping remains frozen; current relevant state is checked
at apply. Do not refresh review during confirmation or accept a new digest merely
because an earlier sibling completed. Stale children require an explicitly renewed
review and a new matching manifest selection; already completed children replay.

## Test Strategy and Traceability

The spec traceability table names every planned test and implementation task.
Tests are written and observed failing before their implementation where practical.
Shared negative matrix covers foreign tenants, direct service/interpreter calls,
forged action IDs, changed intent/state/permission and scope reuse across sessions
or transactions. PostgreSQL tests inject failure before commit and replay after
commit, and coordinate two competing approvers rather than mocking lock behavior.

Existing regression suites to update without weakening refusal assertions:

- `packages/reality-core/tests/test_unified_item_csv_import.py`
- `packages/reality-core/tests/test_import_demo_files.py`
- `packages/reality-core/tests/test_master_data_parity.py`
- `packages/reality-core/tests/test_external_stock.py`

## Rollout and Rollback

Deliver dependency contracts before activating this adapter. Keep raw capture
available while review waits. Stop/drain old commit-owning interpreter workers
before cutover; do not use a feature flag as a business-approval bypass. Retain all
historical sources/effects with honest legacy attribution. On interruption, leave
pending decisions inspectable. Rollback disables new automatic review but preserves
the admission boundary and receipts; code that restores direct interpretation
writes is not a safe rollback target. Spec 356 owns the final cross-path cutover.

## Review Risks

- Legacy location/party/order/stock branches commit internally and can leave partial imports.
- A normalized SourceRecord must not be presented as the original file contents.
- Packaging must not split an order or silently replace whole-package atomicity with per-row progress.

## Complexity Tracking

No constitutional exception is proposed. New agent authority is an explicit scoped
feature in spec 355, not an exception to existing finance/tenant rules. No new
external-I/O scheduler contract is proposed: provider inference stays client-side.

## Shared phase and locking contract

Follow spec 351's common lock hierarchy and immutable phase/outcome attempt
allocation; do not acquire business/finance locks after proposal/source locks.
Replay never appends a new phase outcome or re-invokes interpretation.
