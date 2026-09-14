# Implementation Plan: Demo Entrypoint Equivalence

**Branch**: `027-demo-entrypoint-equivalence` | **Date**: 2026-09-02 | **Spec**: [`spec.md`](spec.md)
**Language**: English for all repository artifacts and review evidence.
**Status**: Specification, plan, implementation, and final review approved by the product owner on 2026-09-02.

## Summary

Close `015/FR-010` by treating the existing `ensure_demo` application service as the
single guided-demo operation, adding an explicit confirmed Product Web onboarding path
to it, and proving interactive CLI, CLI auto, and real Web/API execution produce the same
canonical authoritative state. A focused PostgreSQL story builds categorized manifests
from fresh reads, aliases generated identities, and fails on record, topology, provenance,
derived-state, or trace drift. Empty-company onboarding stays separate. No schema changes.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/Node for Product Web
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, FastAPI, Pydantic v2, Typer, Rich, React/Vite
**Storage**: PostgreSQL using existing Tenant, Source, Evidence, Reality, and Chat records
**Testing**: pytest with Typer CliRunner and FastAPI TestClient; Node Web contract tests; Web build
**Project Type**: backend services/API/CLI plus independent React frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless immutable source; tenant scope; explicit Web confirmation
**Scale/Scope**: 3 guided-demo entrypoints, 1 canonical manifest, 2 Web onboarding choices; no new scenario or schema

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Manifest traverses the Shopify SourceRecord through Document/Line into Commitments, Reservation, and Movement. | PASS |
| Reality owns operational state | Inventory and fulfilment values are recalculated from Movements, Reservations, and Commitments; no document status is added. | PASS |
| Proven schema only | Existing records express the complete demo; no model or migration is permitted. | PASS |
| Tenant + shared service boundaries | CLI and authenticated Web/API call `ensure_demo`; proof uses isolated tenants and foreign-access checks. | PASS |
| Spec/test traceability | FR/DR groups map to manifest, adapter, safety, tenant, idempotency, and policy tests below. | PASS |
| Explainable web behavior | Successful Web demo opens the tenant and routes to normal Cockpit/Inspector views over authoritative records. | PASS |
| Smallest coherent design | Extend company onboarding with an explicit demo flag and reuse the current service; no demo framework or new entity. | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py          # existing ensure_demo; fix only if proof exposes drift
packages/reality-core/src/reality/cli/app.py                # existing interactive/auto adapters; conditional fix only
packages/reality-core/src/reality/web/api.py                # explicit company-with-demo request adapter
packages/reality-core/tests/test_demo_entrypoint_parity.py   # PostgreSQL manifests and three-path proof
packages/reality-core/tests/test_user_access.py              # company/demo auth and ownership contract
packages/reality-core/tests/test_cli.py                      # confirmation/cancellation adapter evidence
apps/web/src/api.ts                                         # company creation request option
apps/web/src/App.tsx                                        # explicit empty/demo onboarding choice and confirmation
apps/web/scripts/demo-entrypoint-contract.test.mjs           # actual Web handler/request/confirmation contract
docs/features/demo.md                                       # precise entrypoint and canonical-state contract
docs/DEMO_SPEC.md                                           # guided-demo outcome inventory/version
docs/SPEC_COVERAGE_MATRIX.md                                # close only after final approval
specs/015-demo-scenarios/spec.md                            # close only after final approval
```

Dependency direction remains Product Web → authenticated HTTP adapter → shared demo
service and CLI → shared demo service. Test-only manifest code reads authoritative state;
it is not a new domain or production persistence layer.

## Design

### Reality flow

Before fixing the manifest, a real service execution inventories every persisted family,
including Facts and BusinessEvents produced indirectly by ingestion. The existing compact
guided demo remains authoritative: tenant-scoped references, opening-stock Movement,
immutable Shopify SourceRecord, Document/DocumentLine, outgoing Commitment, Reservation,
incoming Commitment, explanatory Chat history, and every additional inventoried record.
The manifest derives inventory and fulfilment from Reality and walks the shortest links
from Source to Evidence to Reality. It records full source payload semantics while
normalizing generated IDs, timestamps, and execution-date-relative values.

### Service and adapter flow

- Keep `ensure_demo(session, tenant)` as the one idempotent guided-demo application service.
- Interactive CLI keeps its confirmation before calling the service; `--auto` skips only
  presentation confirmation and invokes the same function.
- Extend company creation input with an explicit demo choice. The authenticated company
  adapter creates the tenant/owner membership and invokes `ensure_demo` only when chosen.
- Product Web displays two distinct actions: create an empty company, or preview/confirm
  a demo company. Only the confirmed demo request carries the demo choice.
- After success, refresh bootstrap with the returned opaque tenant ID and open the normal
  product home, where Cockpit and Inspector routes expose the created records.
- A focused Web source contract checks the actually rendered action, confirmation gate,
  request body, success routing, and absence of browser persistence/business rules.

### Canonical outcome manifest

The parity test executes each real entrypoint in a separate empty tenant, reloads all
demo-owned rows, and emits categorized deterministic sections:

1. `reference_data`: Party roles/types, Item, Location, lifecycle state.
2. `source`: source system/type/external identity and complete normalized payload.
3. `evidence`: Document and line business values plus source/party/item aliases.
4. `reality`: Commitment direction/quantities/dates, Reservation, Movement, and shortest-link aliases.
5. `derived`: physical, reserved, available, incoming, projected, fulfilment, and an
   explicit zero financial state when no LedgerEntries/open items exist.
6. `explanation`: representative Source → Evidence → Reality reachability and demo Chat meaning.

Opaque IDs become stable semantic aliases derived from unique demo roles, never human
numbers used as production identity. Execution timestamps, insertion order, and dates
defined relative to the run day are normalized explicitly. No other value is discarded.
Each section is asserted independently so failures identify the drift category.

### Data and migration impact

No table, column, relationship, constraint, index, migration, or backfill. The company
request gains a transport-only demo choice. The manifest carries an explicit contract
version; its metadata remains contract/test data, not a business table. Any model or
migration diff fails review.

### Failure, security, and tenant behavior

- Browser cancellation performs no request and creates no tenant or demo records.
- Empty-company creation never calls `ensure_demo`.
- A populated tenant remains unchanged because the existing service refuses to mix the
  demo once Party data exists; focused before/after counts prove this behavior.
- Repeated successful requests preserve one canonical state without duplicates.
- Authenticated company creation grants only the requesting user owner membership;
  focused two-user tests prove another user cannot inspect the created demo tenant.
- If confirmed Web population fails after the tenant shell exists, the UI reports the
  failure and does not claim demo completion or safe retry. The possibly partial tenant
  remains for explicit operator handling and is never hidden or deleted implicitly.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-004–FR-006, FR-013 | PostgreSQL story/unit | categorized canonical manifest, completeness, topology, derivation, drift diagnostics | No complete manifest or cross-path comparison exists. |
| FR-002–FR-003 | adapter integration | real interactive CLI, CLI auto, and authenticated Web/API executions compare equal | Web has no guided-demo onboarding path. |
| FR-007–FR-010 | Web contract + authenticated API | two choices, confirmation/no request, demo request, empty request, success routing | Current onboarding creates only an empty company. |
| FR-011 | service/adapter story | populated/completed-rerun checks plus injected partial-failure truthfulness | Existing behavior is not proven across entrypoints. |
| FR-012, DR-005 | authenticated two-user story | creator ownership plus foreign demo-inspection non-disclosure | No focused demo ownership-boundary proof exists. |
| FR-014 | regression | normal-month, Chat, and bootstrap tests remain separate and green | Scope separation lacks a focused guard. |
| FR-015 | policy regression | baseline verified, row removed, unrelated gaps retained | Gap intentionally remains open before approval. |
| DR-001–DR-004 | manifest/story review | source payload, shortest links, Reality derivation, rerun semantics | No unified proof exists. |
| DR-006 | diff/policy gate | no model or migration change | Pass unless implementation expands schema. |

Tests precede behavior changes and must demonstrate the missing Web path and comparison
gap before implementation. Full backend, Web contract/localization, build, policy, and
diff gates run before final review.

## Rollout and Rollback

The company-create request remains backward compatible: omitted demo choice means empty
company exactly as today. The Web adds an opt-in action. Rollback removes the optional
adapter/UI path and proof without data migration; demo-created tenants remain truthful
normal tenants and are never deleted automatically. `015/FR-010` changes only after
final product-owner approval.

## Review Risks

- Comparing `ensure_demo` directly three times while claiming real adapter coverage.
- Over-normalizing payload values, dates, counts, or relationships until drift disappears.
- Making empty-company creation seed demo data implicitly.
- Treating a browser confirmation label as proof that no pre-confirmation request occurs.
- Confusing the compact guided demo with the separate normal-month scenario.
- Claiming atomic deletion/rollback of a tenant after a confirmed partial failure.
- Disturbing concurrent Atlas/Investor work in the shared worktree.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Post-Design Constitution Re-check

All checks remain PASS. The design uses existing domain records and one existing shared
service, adds only an opt-in transport/presentation path, and keeps comparison state out
of production persistence.
