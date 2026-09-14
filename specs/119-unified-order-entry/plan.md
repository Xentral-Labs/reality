# Implementation Plan: Unified Order Entry

## Technical Context
Python 3.12, SQLAlchemy/PostgreSQL, shared application tools and FastAPI; React/TypeScript.
Existing proposal locks/recovery and tenant reference searches. No schema/dependencies.

## Constitution Check
| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Lossless manual source, document/lines, commitments | PASS |
| Reality authority | No document operational states or entry stock/money effects | PASS |
| Proven schema | Existing proposal/event/record fields only | PASS |
| Shared services and tenancy | Pure core preview; locked current access and reference checks | PASS |
| Tests first | Backend/browser failing proofs and mapped tasks | PASS |
| Explainability | All lines, stated amounts, original evidence and resulting deliveries | PASS |
| Received values | Header/line amounts retained rather than recomputed | PASS |
| Simplicity | Dedicated order semantics reuse existing action lifecycle | PASS |

## Design
- `packages/reality-core/src/reality/services/core.py`: extract pure manual-document
  validation; private order preview, shared execution validation, missing source total,
  immutable attributed creation snapshot. Existing pricing/line rules reused.
- `services/order_actions.py`: normalized preview and relevant reference state, token,
  exact creation proof, current observations and identical-intent unresolved guard.
- `services/delivery_actions.py`: early order dispatch, eligibility and reconcile.
  `tools/application.py` already calls attributed canonical order service.
- `web/api.py`: prepare allowlist. Existing suggestions and proposal endpoints reused.
- `apps/web/src/unified/OrderCard.tsx`: multi-line form, references, optional fields,
  common recovery/Inspector and order/delivery links. `ActionCard.tsx` dispatch;
  `OrdersPage.tsx`, `UnifiedApp.tsx`, `ActionLauncher.tsx`, `ChatPage.tsx`,
  `DecisionsPage.tsx`, `api.ts`, `localization.tsx` integrate all entry points.

## Validation and rollback
Isolated PostgreSQL tests cover sales/purchase multi-line no-effect preview, source totals,
validation, stale references, actor/tenant/practice, exact proof, duplicate and unknown
outcomes, historical proof after fulfillment. Browser fixtures cover all entries,
line edit/remove, reload, reject, failure recovery and four-language responsive review.
Run complete backend, frontend contracts/build/format/i18n, existing action browser
journeys, spec/Ruff/diff. Restart shared local API and perform only login/form reads.
No migration/deployment/retirement; old presentation remains available.
