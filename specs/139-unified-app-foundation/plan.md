# Implementation Plan: Unified App Foundation

**Feature**: `139-unified-app-foundation` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)
**Checkout**: Existing detached checkout preserved; implementation must use an isolated feature checkout before code changes.
**Language**: English for repository artifacts. Owner approved the concrete scope in this conversation.
**Status**: Design complete; runtime work and reviewer-owned pre-implementation checklist remain pending.

## Summary

Build the new presentation in the current React application, backed by existing company authentication, shared services and ChangeProposal execution. Deliver only Home, company Chat, delivery work/case, Decisions and two shared action families. Keep legacy/support and Playground access during this additive increment. Do not implement later Analytics/master-data screens as placeholders.

The largest service changes are revision/correction-aware delivery reads, exact stock-bound action review, different-proposal concurrency and verifiable shipment/reservation recovery. These are necessary to meet the approved scope rather than optional UI polish. See [research.md](research.md), [data-model.md](data-model.md) and [contracts/foundation.md](contracts/foundation.md).

## Technical Context

**Language/Version**: Existing Python 3.12+, TypeScript, React 19 and Vite.
**Dependencies**: Existing SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, application tools, Tailwind/br-* and localization. No new production library planned.
**Storage**: Existing PostgreSQL models; additive versioned proposal/message metadata in existing storage. No schema migration.
**Testing**: pytest service/API/business stories, PostgreSQL concurrency, Node contracts, TypeScript/build/i18n and browser journeys.
**Constraints**: Decimal strings; UTC business timestamps; localized presentation; server-derived values; opaque identities; explicit confirmation.
**Scope**: Four new destinations, two mutations, three entry points, ordinary-company admission; practice unchanged.
**Bounds**: Delivery/decision/reference queries default 50 and cap 100. Related history defaults 20 with has-more/next cursor. Sort/filter effective values before paging. Never derive totals from samples. Existing large-tenant read budgets remain applicable; record baseline/query-count changes instead of inventing a new latency promise.

## Constitution Check

Design review before and after research: all rows PASS at the design level. This is not a runtime certification.

| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Delivery/inspector reads return actual shortest links and missing-evidence states | PASS |
| Reality owns operational state | Revision/correction-aware services; no stored case status or document fulfillment fields | PASS |
| Proven schema only | Reuse proposal/event/message storage; no schema expansion | PASS |
| Tenant + shared service boundaries | AuthGate and API principal checks; scoped reads, locks, proposal tools and context resolution | PASS |
| Spec/test traceability | All FR/DR map to test and implementation tasks; baseline tests precede code | PASS |
| Explainable web behavior | One case/inspector and exact reviewed/result links | PASS |
| Received values not recomputed | No money recalculation; stock/delivery are shared read observations | PASS |
| Smallest coherent design | Existing React/tool stack, two-action adapter, tenant row guard before finer locks | PASS |

No constitutional exception is requested. Independent architecture scrutiny is concentrated on shared lock coverage and reviewed-proposal backward compatibility in the review checklist.

## Repository Structure and Layer Changes

Existing paths are anchors; new filenames below are planned, not yet implemented.

```text
packages/reality-core/src/reality/
  services/delivery_reads.py       # new authoritative case composition
  services/delivery_actions.py     # new bounded review helpers
  services/business_locks.py       # shared transaction mutation guard
  services/core.py                 # existing authorities and Chat dispatch
  tools/application.py            # proposal prepare/approve/status parity
  mcp/server.py                   # existing MCP adapter
  cli/app.py                      # existing direct commands, shared service guard
  web/read_models.py              # effective-value bounded SQL
  web/api.py                      # additive thin endpoints and context body
apps/web/src/
  App.tsx                         # authenticated dispatch only
  legacy/LegacyProductApp.tsx      # relocated old module, not redesigned
  unified/UnifiedApp.tsx
  unified/routing.ts
  unified/useCompanyContext.ts
  unified/Shell.tsx
  unified/HomePage.tsx
  unified/DeliveryWorkPage.tsx
  unified/DeliveryCase.tsx
  unified/Inspector.tsx
  unified/ActionLauncher.tsx
  unified/ActionCard.tsx
  unified/useProposal.ts
  unified/DecisionsPage.tsx
  unified/ChatPage.tsx
  unified/CaseAssistant.tsx
  api.ts                          # existing plus additive typed contracts
  tailwind.css                    # shared primitives only
```

Existing MCP and CLI entry points are `mcp/server.py` and `cli/app.py`; the authoritative mutation/token gate lives in `tools/application.py` regardless of transport. No direct ORM writes from new browser/agent adapters.

## Design

### Shell, route and company boundary

Use `VITE_UNIFIED_APP` as an internal build-time rollout switch, default off until this increment passes acceptance. With it on, `/app`, `/app/copilot`, `/app/work` and `/app/decisions` use the new shell. Selection is URL state: `tenant`, `commitment`, `proposal`, `session` where applicable; whitelist and encode each value. A selection never grants access. Existing other `/app/*` routes remain legacy compatibility/support destinations with clearly labeled links from the new shell. No global Old/New button.

AuthGate runs before either ProductApp. `/playground` still selects existing practice admission/shell. Never load ordinary bootstrap for a pending practice-only account. Handle company switch by canceling reads, resetting selected record/draft view and validating request-generation identity before accepting responses. Server-persisted proposals remain available in their own company.

Lazy-load the relocated legacy module only on its routes. Use full document navigation across legacy/new boundaries to remove old styles. Within new routes, keep history/back-forward, focus and selection coherent without a new router package.

### Read flow

Domain quantity/revision/correction helpers → `delivery_reads` and corrected bounded SQL → application read tool where needed → API → typed browser presentation. The list selects open customer-delivery commitments using effective quantity/date and correct fulfillment before LIMIT. Case detail is independent of open-list membership.

Update old commitment inspection to delegate to the same semantics so the new case and supporting evidence cannot disagree. Scope physical/reserved/available by item/location and carry the unit. Use existing exception authorities rather than independently deciding shortage/lateness. Expose truncation metadata for related history. Home may reuse true dashboard counts, but sampled inventory/facts/exceptions must be labeled as samples with scope/coverage.

### Action flow

Final state validation runs under the tenant transaction guard after the existing proposal claim commit and immediately before the handler. A pre-handler validation refusal safely restores proposed; handler uncertainty never does. This supersedes the research-stage session-lock proposal.

The canonical proposal path in `tools/application.py` detects ordinary-company reserve and shipment-only movement_create. It invokes `delivery_actions` for reference resolution, normalized exact intent, effect preview, relevant state and review token. New APIs are adapters to this same path. Other tools and practice remain on their existing paths.

Reservation preserves capped allocation semantics and discloses requested, expected applied and shortage. Case prefill is only a suggestion. The global card selects a commitment; item/location derive from actual relationships, and shipment-only fields/tracking identities follow the existing command schema. A changed intent requires a different proposal and fresh approval; pending history is not overwritten.

Store a versioned immutable review in existing proposal input; strip internal metadata before handler execution. Require review-token validation for the new reviewed proposal version in every approve adapter, including token-aware legacy/MCP handling and guarded direct CLI services. Rejecting or navigating does not execute anything.

### Concurrency and result recovery

Use the existing tenant row as a transaction guard shared by final review validation and every relevant inventory, fulfillment, correction, revision and hold writer. The final validation and domain effects share one transaction after the proposal CAS commit. Acquire the guard before capacity reads and event locks; audit outer source/document/run locks. Write down the writer coverage in code/tests; a lock only in the new endpoint is insufficient. No connection pinning or session advisory lock is introduced.

The existing proposal CAS still ensures same-ID execution once. Cross-proposal stock competition is serialized. Determine known pre-execution validation errors before claiming execution where possible. After uncertain handler failure, preserve executing/unknown until immutable evidence proves a recorded effect. No event is not proof of failure.

Extend existing execution-status verification to shipment and immutable reservation-created events. Original receipt proof must survive later reservation consumption, movement correction and changing live observations. Current observation failure never changes an executed receipt into a failed action. Repeated confirmation of an executed reviewed proposal rechecks access and returns the same authorized result.

### Chat

Reuse existing sessions/history/provider; add server-validated case context to sends and versioned historical context annotation in existing message content. Strip/validate annotations before provider assembly; source/user text cannot supply authority. Shared `ActionCard` renders actual proposal IDs from Chat, launcher and case. Legacy messages/proposals remain readable. Bound history according to existing provider policies. Provider error retains the question and deterministic controls.

### Data and migration impact

No new business tables or columns. See data-model for metadata shape/lifecycle. Do not extract prototype arithmetic or scripted replies into production. Do not migrate practice state in this increment. Any schema need discovered during implementation requires returning to the approved spec/design gate.

## Test Strategy and Traceability

Full requirement-to-task coverage is in [tasks.md](tasks.md). Primary tests:

| Scope | Planned path | Expected initial failure |
| --- | --- | --- |
| Effective delivery and provenance | `packages/reality-core/tests/test_unified_delivery_reads.py` | New read contracts absent; old inspector ignores revisions/corrections |
| Prepare/review/recovery | `packages/reality-core/tests/test_unified_delivery_actions.py` | No ordinary-company state-bound preview or verified shipment |
| Two-proposal contention | `packages/reality-core/tests/test_postgresql_integration.py` | No complete shared stock/review guard |
| API/principal/context | `packages/reality-core/tests/test_unified_app_api.py` | New detail/prepare/context contracts absent |
| Chat parity | `packages/reality-core/tests/test_chat_confirmation.py`, `test_application_tools.py` | New reviewed token and structured context coverage absent |
| Shell/state | `apps/web/scripts/unified-app-contract.test.mjs` | New dispatch/routes absent |
| Actual browser journeys | `apps/web/scripts/unified-app-browser.mjs` | No new interactive surface or recovery journey |

Fixtures use service/tool calls for stock 20 and commitment 12; reserve 12; ship 5; then ship 7. Test partial/multi-line/corrected/revised/multi-location variants, unsafe markup, provider failure, delayed tenant responses, and all six action-entry combinations. Run existing inventory, corrections, holds, application-tool, admission and Playground suites unchanged where their behavior remains in scope.

## Rollout and Rollback

1. Ship shared read fixes and additive proposal/review APIs with the new UI switch off.
2. Make old relevant approval adapters token-aware before creating reviewed proposal versions.
3. Build and review the new shell behind the switch; preserve legacy access.
4. Activate the new four routes only after all required tests and visual review pass.
5. Roll back presentation by disabling the switch, retaining new endpoints and token-aware handlers until all reviewed proposals settle. Never roll back to an engine that can bypass review tokens or strand pending IDs.

No deletion, deployment or final retirement is included in this planning turn.

## Review Risks

- Missing a writer in the shared lock contract can invalidate exact reviewed stock guarantees.
- Correcting existing inspector SQL must preserve pagination, effective date filters and large-tenant performance.
- A generic token gate must not block legacy pending reads or permit older adapters to bypass a new review.
- Moving a large legacy module can break imports/source-text tests; preserve behavior and semantic tests.
- Existing browser tooling may need its documented local setup before visual acceptance can run.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
| --- | --- | --- | --- |
| None | — | — | — |

## Explicit workspace migration followups

Owner reminder, 2026-09-07: the accepted HTML includes Orders & deliveries and
Facts. These are separate increments, not foundation acceptance requirements.

- **Orders & deliveries**: implemented in Spec113 with customer/supplier order
  evidence, outgoing/incoming delivery registers, exact-order drilldown and
  existing customer action cases. Advanced order operations remain supporting.
- **Facts**: implemented in Spec114 as a recorded-observation register with
  search, exact subject/source filters and shared Inspector provenance. It is
  distinct from master data and evidence documents; no current-truth winner is inferred.

Do not retire the old UI or Playground while required replacement workflows remain
unresolved. Spec impact: none for this tracking note; behavior is specified in the
individual migration increments.
