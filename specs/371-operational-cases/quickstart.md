# Local acceptance and verification

The owner approved the concrete five-table first slice on 2026-10-05. Runtime implementation and focused proofs are present. This is internal acceptance against retained Shopify evidence, not live Shopify qualification.

## Recorded local results

- Focused case/policy/worker/adapter/current-state suites: 100 passed; final lower-boundary additions: 18 passed; cross-adapter retry/provenance/batch review: 20 passed. Suites overlap, so these counts must not be added together.
- Real Chromium component test: explicit activation/takeover confirmation, same-request retry after a failed HTTP call, source links, blocked unresolved handback and exact clean handback passed. Registered in the shared browser suite.
- Migration 0144: isolated PostgreSQL upgrade, empty downgrade/re-upgrade, and refusal to discard adoption history passed.
- `make lint`, `make spec-check`, `make business-annotations-check`: passed (647 described root functions; no missing business annotations).
- `make web-build`: passed, including 463 Web contract/localization tests, 2,795 covered messages in each of English/German/Dutch/Spanish, TypeScript and production Vite bundle.
- `make docs-build`: passed, including 16 Python reference tests, 145 documentation tests and VitePress rendering.
- `make docs-generate`: passed. Repeated generation preserved hashes of all 26 generated catalog/journey/advisor artifacts.
- `make docs-catalog-check`: clean committed-head verification follows the explicitly authorized commit. Remote CI remains required before merge.
- Complete PostgreSQL suite on the frozen final backend: **6,432 passed, 10 skipped, 717 warnings**, no failures; `pytest -n 4 -q`, 21m16s. Warnings are retained in the full run log, including SQLAlchemy deprecation/fixture transaction warnings. Earlier failed/infrastructure runs are not acceptance evidence.

- Final ownership/worker/current-state focused check: 14 passed. This includes independent return execution, raw/Finance/read-reference separation, closed-history party holds, refusal of unanchored automatic physical shipments and queued-human-batch takeover. The full suite above includes these proofs.

## Integration review

Rebased onto origin/main ce642dc3 without discarding its Decision discovery and qualified read answers. Feature number moved from 368 to 371 because main had independently allocated 368 to payment evidence. Migration remains 0144. Focused combined case/worker/discovery/read/payment regressions passed **53 tests** after rebase. The 6,432-test complete result above predates that rebase; remote CI must verify the integrated head. Repository script tests (16), lint, spec policy and business annotations passed locally. The gateway proof passed in remote frontend CI; local gateway reruns encountered environment HTTP403 and are not acceptance evidence.

Next adapter work is concretely planned in [Shopify adapter readiness](contracts/shopify-adapter-readiness.md); provider fencing and physical-dispatch authority are explicit gates.

## Environment and rollout boundary

An isolated PostgreSQL 17 container provides localhost:54329. The pytest fixture creates temporary databases; no production data, Shopify credentials or vendor calls are used. Test-server `max_locks_per_transaction=2048` permits concurrent metadata fixtures. Migration startup performs no DDL.

Production deployment has not been performed. The owner authorized commit and CI on 2026-10-05; remote CI outcome is recorded separately when available. Live Shopify acceptance additionally requires real capture coverage, an authoritative pre-dispatch reread and provider outcome reconciliation in a separately reviewed adapter feature. Refund intent/execution is unavailable in this slice. Return goal observation follows the canonical announcement receipt status, without implying refund/replacement completion.

## Acceptance stories

1. Accept a two-line order using the canonical exact intake decision. Process all events twice and after worker restart. Assert one fulfillment case, no duplicate commitments/effects, one atomic checkpoint progression. Partially fulfill and assert the same case with remaining work derived from Reality.
2. Prepare case-bound delivery work. Delay the case worker, commit a supported order reduction, attempt execution and assert stale current business-state refusal. Renew the plan, take over, then assert human-ownership/revision refusal for an automated start. An authorized manual repair remains possible.
3. Represent an already-started external action with supported retained execution evidence. Take over and assert the unsettled action stays visible. Handback refuses until actual outcome is reconciled. After exact handback, previous generation stays invalid.
4. Announce a return and process accepted successful refund evidence. Assert a distinct return case and no new payout intent/case from the refund notification. If no authoritative refund intent capability exists, assert unavailable rather than inventing one.
5. Supply newer relevant unaccepted source evidence. Assert automation/handback refuse coverage uncertainty without applying raw business changes. Accept it through normal intake, then renew review.
6. Exercise cross-tenant IDs, revoked actor, multi-case actions, replayed executed receipts, concurrent takeover/claim, rollback before checkpoint commit, layer-event recursion and a correction reopening outstanding work.
7. Enable at a captured boundary, explicitly select one existing open order and leave completed history unselected. Assert guard coverage for enabled agent actions and no implicit historical responsibility.

Required release gates: `make spec-check`, `make lint`, complete PostgreSQL `make test`, migration upgrade/downgrade review, `make web-build`, Web i18n audit, `make docs-generate`, `make docs-catalog-check`, and required committed-head CI. Live Shopify acceptance adds real capture coverage, authoritative pre-dispatch reread and provider outcome reconciliation in a separate adapter feature.

8. Pass an external correlation ID distinct from case/action IDs through supported intake/preparation/event paths; assert exact preservation. Repeat without an external value and assert no fabricated foreign-system correlation. Verify different correlations can map to one case and a shared correlation does not merge different goals.

9. Discover the same case through an existing order read, proposal review, execution receipt read envelope and case-list MCP tool. Assert copyable UI ID, all associations for multi-case work, empty historical associations without writes, additive old-client compatibility and refusal of a forged case ID. Follow user-guide takeover/review/handback examples and verify controls change real responsibility, not just labels.

10. For every enabled row in `contracts/entrypoint-coverage.md`, exercise its real channel and direct canonical path. Assert accepted outstanding goal plus case commit/rollback together, event replay cannot duplicate it, raw preparation cannot accept a goal, omitted case IDs cannot bypass automation guards, and authorized human repair remains possible. Activation refuses any unclassified reachable scoped path.

## Remote verification and UI containment

Integrated backend head `dbe10499a51c9ff4c4f056a36df10950f2bf94d8`: all four PostgreSQL shards and backend-quality passed, totaling **6,462 passed and 10 skipped**. Installer script/end-to-end, frontend, docs and spec gates passed. Run: https://github.com/Xentral-Labs/reality/actions/runs/37344735499.

That first complete CI attempt exposed an additive UI compatibility defect: legacy generic fixture responses were treated as case arrays and crashed the Orders page. The focused browser proof reproduced the failure. Case initial-load/pagination now validate list shape before setting state; failure is contained with a localized error and refresh can recover without business writes. The real component browser proof passed after the fix, including its original takeover/retry/handback/source/direct-object assertions. The updated head must pass full CI before release. This UI-only correction does not change the already-verified backend. Draft review: https://github.com/Xentral-Labs/reality/pull/378.

UI containment verification: `make web-build` passed after the correction with the required execution permissions. Default-sandbox Node-to-Python catalog spawning returned EPERM; that failed environment run is not product acceptance evidence. No additional backend or business behavior changed.
