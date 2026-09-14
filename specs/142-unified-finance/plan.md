# Implementation Plan: Unified Finance

Branch: `139-unified-app-foundation` | 2026-09-07 | [Spec](spec.md)

## Summary and Technical Context
React/TypeScript presentation using existing GET APIs and shared Inspector. No new backend endpoint, domain calculation, schema or dependency. PostgreSQL/Python services remain unchanged. Add optional page arguments to existing client payment/journal reads, preserving defaults and callers. Tables use bounded 50-row pages and server-clamped pager state.

## Constitution Check
| Principle | Result | Evidence |
| --- | --- | --- |
| I Source → Evidence → Reality | PASS | Existing document/payment/ledger Inspector |
| II Reality authority | PASS | Existing ledger/allocation observations; no document status writes |
| III Proven schema | PASS | No schema changes |
| IV Tenant/services | PASS | Existing authenticated tenant APIs and ordinary-company shell |
| V Spec/test evidence | PASS | Owner continuation; tests precede UI; full gates planned |
| VI Explainability | PASS | Exact opaque row IDs and account-sheet support |
| VII Simplicity/storage | PASS | Reuse GETs, no backend duplication or dependency |
| VIII Received values | PASS | Render canonical strings; no browser totals or recomputation |

All rows pass before and after design. No exception or complexity waiver.

## Design and Repository Paths
- `apps/web/src/api.ts`: additive optional page parameters for payments and journal.
- `apps/web/src/unified/FinancePage.tsx`: three tabs, read/loading/error, shared pager, per-currency open-item/journal controls, exact Inspector IDs. No payment aggregate because existing row and total search scopes differ.
- `routing.ts`, `CaseAssistant.tsx`, `UnifiedApp.tsx`, `Shell.tsx`: finance route and finance_view/flow/status/direction/account/entry URL state; reset scoped context on company changes.
- `localization.tsx`: four-language business controls. Existing account codes and source data retained.
- `apps/web/scripts/unified-finance-browser.mjs`: fixture navigation and 48-shot matrix with multi-page data and differing currencies.
- `apps/web/scripts/unified-app-contract.test.mjs`: route round trip, filter allowlists, reset proof.
- Existing backend finance tests remain authoritative and run in the full suite.

## Implementation Order and Tests
No domain/service/tool changes needed. Add route and browser proof first, observe missing route red. Extend client reads and build UI. Verify no non-GET requests, error/retry, search/filter/paging, total stability, selected Inspector reload and keyboard return. Run full Python suite, lint/spec, frontend contracts/i18n/format/build, all unified browser harnesses, docs checks/build.

## Risks / Rollback
No promise of due dates, aging, liquidity or accounting statements. Payment paging preserves existing canonical behavior and aggregate responses are ignored. Existing advanced financial actions remain supporting paths. The opt-in switch provides rollback; no effects/data migration to undo. Owner visual acceptance and final retirement remain separate.
