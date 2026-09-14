# Validation

From the active worktree, run make spec-check, make lint and make test with the existing isolated PostgreSQL test setup. Run make web-build and make site-build for the repository gates. Run tests/test_operational_read_performance.py first for focused failure/parity/query-budget evidence.

Before deployment, build the matching local API/MCP/background images using the root .env and Compose project reality as described in docs/LOCAL_STACK.md. Recreate only matching code services; no migrations, database reset or demo-control action.

Measure two actual sidebar cycles in the existing authorized browser session for the selected local live-demo tenant. Record ResourceTiming from click to primary response and two subsequent animation frames separately; the latter is a render opportunity, not a DOM-stability assertion. Live demo intake continues. Baseline: Exceptions response 2715/2889 ms, frame 2850/3015 ms; Finance response 4330/4193 ms, frame 4707/4563 ms; Orders response 123/75 ms, frame 1251/1133 ms.

Final evidence will be appended after validation, with limitations.

## Interim evidence — 2026-09-09

The initial failing regressions observed 634 queries for 21 commitments and an unrelated full-projection build from a finance read. The focused suite now passes, including payment/reversal refresh, unchanged unrelated checkpoints, unknown tenant, nested/session-bound inputs and invoice-linked credit evidence. All 239 existing operational exception tests pass.

A read-only REPEATABLE READ transaction compared the pre-change exceptions module and new implementation at one fixed instant against the same live company: all 244 complete exceptions were identical (dataclass fields including sort values and trace). Queries fell from 13,448 to 1,483. Host-to-container timings during concurrent test work were 14,527 ms and 883 ms respectively; these are service diagnostics, not browser timings or a comparable replacement for the initial browser baseline.

The first full-suite run identified missing catalog registration of the new shared refresh service and its exact-count assertion. Both were corrected; the affected catalog/focused tests pass. Full final verification and deployment remain pending.

The large-tenant register regression identified a missing explicit LIMIT on the unique selective checkpoint lookup. The lookup now carries LIMIT 1; all 11 focused register/performance checks passed. Final review also reproduced a READ COMMITTED intake race when a commitment appears after the batch load; helpers now fall back to canonical reads for identities outside that evaluation's batch. The dedicated regression failed with KeyError before the guard and now passes. All seven new performance regressions pass. No business rule or transaction-isolation change was needed.

## Final verification and local rollout

- Final complete PostgreSQL suite: **1,937 passed, 9 skipped**, 236.74 seconds (`pytest -n 2 --dist loadscope -q`). Historical optional/skipped checks remain skipped; no failing test remains.
- All seven new semantic/performance tests pass, including the intake race; all 239 existing exception tests passed in the earlier focused run, and are included again in the final suite.
- Web: 45 tests pass, formatting/i18n audit/build pass. Site: 55 tests pass, formatting/i18n audit/build pass.
- `make lint`, `make spec-check`, and `git diff --check` pass.
- Updated local `api`, `mcp`, `invitation-worker`, `scheduler`, and `worker` with matching images. API/MCP healthy; all five running with zero restarts. No migrations, database/storage recreation, demo source-control changes or frontend changes. Port 8080 retains assets `index-BBEZqmjS.js` / `index-CntsBkR0.css`.
- Browser instrumentation removed; browser left on the same company's Exceptions view.

### Browser results (milliseconds)

| View | Before click → response | After click → response | Before click → frame | After click → frame |
|---|---|---|---|---|
| Exceptions | 2715 / 2889 | 556 / 407 | 2850 / 3015 | 679 / 524 |
| Finance | 4330 / 4193 | 159 / 61 | 4707 / 4563 | 508 / 397 |
| Orders & deliveries | 123 / 75 | 204 / 87 | 1251 / 1133 | 1261 / 1068 |

Two cycles, same browser and tenant, same measurement method. SC-001 passes: median primary response improves about 83% for Exceptions and 97% for Finance. The corresponding frame approximation improves about 80% and 90%. Orders remains a comparison case; its roughly one-second response-to-frame gap was not changed. These are local observations, not a load/capacity/SLA claim. The frame measure is two animation frames after the primary resource response, not exact fully rendered completion; each loaded view was checked visually through its accessibility state.

Live intake continued: the browser showed 228–229 delivery records, 24 financial items, and 256 exceptions; subsequent service measurements showed 230 deliveries / 257 exceptions. These changing counts are expected live-demo activity, not parity failures. The fixed-snapshot parity comparison above used the exact same 244 exceptions for both implementations.

### Deployed service measurements

See service-measurements.json. Exceptions: 318–389 ms and 1,498 queries versus the original 2,733–3,324 ms / 12,514 queries (later fixed-snapshot baseline: 13,448 queries). Finance: 66 ms / 281 queries on the first refresh, then 4 ms / 10 queries; original first full rebuild: 4,706 ms / 20,335 queries. The final finance probe explicitly used `outstanding`, matching the browser; the initial service-only probe had no status filter. Browser before/after filters match. Orders: 23–31 ms / 2 queries.

### Final review

No new authority, business rule, schema, dependency, background timer, TTL or source mutation was introduced. The core scalar and bulk paths share correction and latest-stated-value rules. Evaluation contexts reset on normal completion and failure; unknown identities arriving during evaluation use canonical fallback reads. Targeted refresh does not advance unrelated checkpoints; full-refresh callers remain compatible. Tenant-scoped queries, complete filtered totals, payment/reversal behavior and evidence links are covered by passing regressions. No unresolved product decision remains.

## Isolated pull request verification

The implementation patch applies cleanly to origin/main `06eeb61` without the unrelated integration/work-list edits. The complete isolated suite passes: **1,936 passed, 9 skipped**, 172.60 seconds. The one-test count difference from the integrated local stack reflects its additional work-list test, not an omitted failing check. Lint, specification policy and diff checks pass on the isolated branch. The local browser evidence above continues to describe the port-8080 integration stack; no frontend code is changed by this PR.
