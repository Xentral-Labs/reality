# Verification: Essential intake completeness

## Test-first evidence

The focused pre-implementation regression run produced 25 expected failures and 4 passing controls (40 deselected). It demonstrated guessed currency/bank defaults, zero for an omitted price, missing review gaps, undated simulator/file orders and unsupported sales units. The source/no-effect assertions form part of each relevant acceptance test.

Final review added a failing proof for two timezone representations of one instant. Header consistency now compares parsed dates/UTC instants while keeping original row payloads unchanged.

Exported MCP schemas also had seven failing parity proofs: they requested a guessed price/unit before reaching the shared service. The corrected schemas permit omitted/blank prices and existing item-unit inheritance, refuse direct null/malformed prices, and confirmed MCP orders retain unknown/zero distinctly.

The native synthetic-order profile had two failing parity proofs as well: missing currency used a generic refusal and a stated box unit could produce a piece-stock promise. It now calls the same essential-value and stock-unit services, preserving the complete synthetic profile and retained failure boundary.

## Local gates

- Spec policy, Ruff and business annotations: passed; 650 described functions, 115 described tests, no remaining required annotations.
- Frontend translations: 463 tests passed; all four locale audits passed.
- TypeScript and production web build: passed.
- Product documentation generation, reference tests, formatting, contract tests and production build: passed; generated vocabulary remains current.
- Browser acceptance: passed; 16 localized responsive reviews, missing price, exact approval, reload/edit/reject and response-loss recovery.
- Affected final regressions before the date refinement: 134 passed, 1 browser-dependent skip in 42.56 seconds.
- A redundant local full run was stopped after 502 passed and 4 skips; the complete GitHub PostgreSQL shards are the full-suite completion gate.

- Date/header and artifact regression matrix after refinement: 53 passed in 24.30 seconds.
- New admission and all affected historical stock/analysis/MCP reader suites: 318 passed in 118.60 seconds. Historical fixtures use explicit source/evidence/commitment service writers; new-admission refusals remain exercised directly.

- Manual MCP/catalog/document/invoice/customer/supplier adapter suite after schema correction: 105 passed in 36.94 seconds; final exported string-price schema controls: 7 passed in 10.13 seconds. Generated tool inputs were refreshed.
- Final essential-intake and native-demo admission, generation and settlement suite: 85 passed in 166.44 seconds.
- Final AI/MCP and intake contract regression after updating the obsolete required-price assertion: 79 passed, 2 integration-dependent skips in 53.02 seconds.
- Final docs contracts: 145 passed; formatting and production build passed. Final Ruff, Spec policy, annotations and regenerated catalogs passed.

## Complete PR verification

[Full regression run 37455739839](https://github.com/Xentral-Labs/reality/actions/runs/37455739839) passed all 24 Quality gates on commit 7d54e900: 6,616 PostgreSQL tests passed with 11 skips across four shards; all seven fixture-browser shards, eight real-backend browser journeys, backend aggregate, frontend, documentation and Spec policy passed. The first full run's 17 historical reader-fixture failures were repaired and covered by the 318-test local run.

Run 37459666061 passed all browser, frontend, documentation, Spec and three backend shards; its only failing test still required a price in the supplier-invoice tool schema. That superseded contract assertion now checks optional prices consistently across all three manual tools, and the full affected AI/MCP suite passes.

The final MCP schema/native-demo refinement is additionally covered by the local suites recorded above. [PR 381 checks](https://github.com/Xentral-Labs/reality/pull/381/checks) provide the authoritative, commit-specific status of the final published head. Every final-head Quality gate must pass before delivery; the PR description records that measured result after the run finishes.

## Review and rollout

The final diff is bounded to spec 379 and its contracts. No schema, historical repair, source mutation or new authority. Spec 301 explicitly records the replacement of its permissive sales-unit control; purchase conversion remains unchanged. Original inputs remain retained when essential financial statements refuse preparation. This PR is not merged by the implementation task.
