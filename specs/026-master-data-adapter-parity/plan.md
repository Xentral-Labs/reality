# Implementation Plan: Master Data Adapter Parity

**Branch**: `026-master-data-adapter-parity` | **Date**: 2026-09-02 | **Spec**: [`spec.md`](spec.md)
**Language**: English for all repository artifacts and review evidence.
**Status**: Specification and plan approved by the product owner on 2026-09-02.

## Summary

Close `004/FR-016` with a declared 36-cell Party/Item/Location lifecycle matrix and a
cross-adapter acceptance harness. Real CLI and JSON API operations run against isolated
tenants, then authoritative records are reloaded into canonical business snapshots. A
focused Product Web contract proves that actual create/edit/toggle actions call the
existing API client and routes. Production code changes only if the proof exposes drift.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/Node for Product Web contract proof
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, Typer, Rich, React/Vite
**Storage**: PostgreSQL; existing immutable SourceRecord semantics
**Testing**: pytest with Typer CliRunner and FastAPI TestClient; Node contract tests; Web build
**Project Type**: backend services/API/CLI plus independent React frontend
**Constraints**: Decimal; opaque IDs; lossless source; strict tenant scope; adapters never write ORM directly
**Scale/Scope**: 3 families × 4 operations × 3 interfaces; no new capability or schema

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Optional SourceRecord provenance is compared; lifecycle changes preserve Evidence/Reality links. | PASS |
| Reality owns operational state | Only reference-data lifecycle is covered; no operational state moves onto master data. | PASS |
| Proven schema only | Existing models are sufficient; migrations are prohibited. | PASS |
| Tenant + shared service boundaries | Real adapters converge on existing tenant-scoped services; foreign IDs remain not found. | PASS |
| Spec/test traceability | Every FR/DR maps to matrix, state, failure, tenant, lifecycle, or boundary evidence. | PASS |
| Explainable web behavior | Existing Inspector/source trace stays unchanged; Web proof verifies real action wiring. | PASS |
| Smallest coherent design | Test-only snapshots and contracts precede conditional production corrections. | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py       # conditional shared-service fix only
packages/reality-core/src/reality/cli/app.py             # conditional adapter fix only
packages/reality-core/src/reality/web/api.py             # conditional adapter fix only
packages/reality-core/tests/test_master_data_parity.py    # matrix and PostgreSQL snapshots
apps/web/src/App.tsx                                     # existing operator actions; conditional fix only
apps/web/src/api.ts                                      # existing request boundary; conditional fix only
apps/web/scripts/master-data-parity.test.mjs             # actual-action contract
docs/features/master_data.md                             # parity clarification
docs/SPEC_COVERAGE_MATRIX.md                             # close only after final approval
specs/004-master-data/spec.md                            # close only after final approval
```

Dependency direction remains Product Web → JSON API → shared service and CLI → shared
service. Tests observe stored state through fresh tenant-scoped reads.

## Design

### Reality flow

Party, Item, and Location remain operational references. SourceRecord remains optional
lossless Source; Documents remain Evidence; Commitments, Reservations, Movements, and
LedgerEntries remain Reality. Lifecycle changes preserve opaque IDs and shortest links.
The parity matrix and snapshots are test evidence, never persisted business state.

### Service and adapter flow

- Declare `party|item|location × create|update|deactivate|reactivate × cli|api|web`.
- Invoke real Typer commands and HTTP application paths in isolated equivalent tenants.
- Execute a focused structural Node contract over the actual Product Web handler source,
  API-client calls, tenant-scoped method/path/body mappings, and API-owned error
  rendering; backend HTTP stories prove stored results.
- Reload authoritative records into family-specific snapshots including all business
  fields, relationships, lifecycle, roles, and full optional source provenance.
- Map generated opaque IDs to scenario aliases only inside comparisons. Ignore terminal
  formatting, HTTP envelopes, React labels, generated timestamps, and literal IDs.
- Change production behavior only for a demonstrated mismatch.

### Data and migration impact

No table, column, constraint, index, migration, seed, or backfill. A schema/model diff
fails the feature gate.

### Failure, security, and tenant behavior

Invalid and foreign-ID cases compare local and foreign state before/after, including
roles, sources, events, Evidence, and Reality. Foreign values must not be disclosed.
Lifecycle changes preserve IDs and historical links. Web exposes API-owned failures and
must not use a local mutation fallback.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-009 | matrix contract | complete 36-cell declaration | No unified matrix exists. |
| FR-002–FR-003, FR-008 | PostgreSQL adapter story | CLI/API canonical snapshot parity | Current tests never compare surfaces. |
| FR-004 | boundary contract | adapter delegation and no direct persistence | No cross-interface invariant exists. |
| FR-005 | failure + Web structural contract | atomic snapshots and same-input/API-owned-error wiring | No unified failure comparison exists. |
| FR-006, DR-003 | two-tenant story | matching-visible-value foreign IDs | Non-disclosure is not compared across adapters. |
| FR-007 | lifecycle story | identity/source/history before and after | Current tests do not prove full preservation. |
| FR-010 | Node structural contract + API integration | actual handlers, client methods, routes, bodies, and error rendering | All 12 Web action groups are not enumerated. |
| FR-011 | policy regression | baseline and matrix closure after approval | Gap intentionally remains open. |
| DR-001–DR-005 | snapshot/review | boundaries plus no-schema guard | Focused parity vocabulary is missing. |

Tests come first and fail where practical. Existing production code changes only for a
proven contract mismatch.

## Rollout and Rollback

There is no data rollout. Proof and documentation are additive. Any conditional adapter
fix keeps existing commands/routes and shared services. Rollback needs no database
action. `004/FR-016` changes only after final owner approval.

## Review Risks

- Comparing transport output instead of authoritative domain state.
- Checking only the API or an unused helper and claiming actual Product Web wiring was proven.
- Hiding a real mismatch through over-broad canonicalization.
- Comparing generated IDs literally or ignoring relationship identity semantics.
- Expanding scope to PaymentTerm/pricing or adding a generic CRUD layer.
- Disturbing concurrent Atlas/Investor work.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Post-Design Constitution Re-check

All checks remain PASS. The design adds no persistence, capability, or competing
business layer.
