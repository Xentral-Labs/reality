# Verification

Run make lint, make spec-check, make test and make web-build. Focused regressions are localization-contract.test.mjs and test_payment_projection_performance.py. Repeat local browser clicks for Payments, Journal and Orders with developer tools closed, recording primary-resource response and two following animation frames separately. Live intake continues; timings are local observations. Completed on 2026-09-09; evidence follows.

## Focused evidence

The new lookup tests initially failed because the resolver did not exist. After implementation, exact first-match parity holds for every parsed production catalog value plus blank, unknown and collision cases; repeated resolution of 10,000 distinct business values performs no additional dictionary traversal. Existing language/preferences and original-content boundary tests remain green.

Synthetic 1,000-value lookup diagnostic: previous scan 1,072 ms; indexed resolver including initial index construction 4 ms; warm indexed lookup below the one-millisecond rounding threshold. This isolates lookup cost and is not a browser-navigation measurement.

Payment tests first failed on an unrelated full rebuild. All three new cases now pass: complete page-independent totals, multiple currencies/direction filters, partial payments, reversal, no cross-tenant rows, read-only derivation and unchanged unrelated checkpoints.

Isolated web gates: 45 tests passed plus format, i18n and production build. Integrated local web gates: 47 tests passed plus format, i18n and production build; its two extra work-list tests are outside the isolated branch. Complete backend gates: isolated branch 1,939 passed / 9 skipped; local integration 1,940 passed / 9 skipped. Both lint/spec checks and scoped diff checks passed.


## Browser comparison and rollout

Measured in Chrome on port 8080 against the same local live-demo company, with DevTools closed during real navigation clicks. Resource Timing supplies primary API duration and click-to-response; two subsequent animation frames provide a rendering proxy, not a guarantee that every pixel or background request is complete. Continuous intake remained enabled. Baseline Orders had 385 records; final runs had 410 and 412. Journal displayed 50 rows and Payments had zero records. Populated payment correctness is covered by the regression suite; these local payment timings do not establish populated high-volume latency.

| View | Before: API / click-to-frame ms | After run 1 | After run 2 |
|---|---:|---:|---:|
| Orders & deliveries | 110 / 1,091 | 155 / 219 | 83 / 118 |
| Payments | 4,190 / 4,270 | 37 / 74 | 46 / 72 |
| Journal | 52 / 689 | 38 / 77 | 46 / 76 |

Orders response-to-frame gap fell from 977 ms to 55 / 29 ms (SC-001). Payments primary-resource duration fell by more than 98% (SC-002). A Finance navigation into Journal additionally measured 117 ms API / 147 ms frame. An open-items sanity click measured 374 ms API / 410 ms frame.

Matching API, MCP, invitation-worker, scheduler, worker and web images were rebuilt and recreated using the integration worktree and root environment file. No migrations or data reset. API/MCP health checks passed; all six processes were running with zero restarts. Frontend assets: index-BWiXxOzM.js and index-D2U0O4oS.css. Temporary browser instrumentation was removed after measurement.

## Final review

The scoped diff preserves exact first-match translation semantics and original-content handling, keeps lookup storage bounded by the static catalogs, and reuses the existing canonical payment builder without changing tenant isolation, totals, reversal rules or explicit full refresh. No schema, dependencies or business rules were added. Required local gates are green (SC-003). PR 162 was merged while this follow-up was being validated; its resulting main tree matches this branch's parent exactly. The follow-up targets main independently.

Follow-up PR: https://github.com/Xentral-Labs/reality/pull/163. Required local verification is complete; GitHub checks run independently on the published head.
