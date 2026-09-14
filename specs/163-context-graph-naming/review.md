# Verification and review

2026-09-10, isolated worktree based on main 7f84c18:
- Web: inspector navigation contract updated to the label Context Graph (3 passed); full
  frontend contract suite 77 passed; four-language audit 1226/1226 with Context Graph as an
  invariant term; TypeScript build passed.
- Site: contract, appearance, localization and audit suites 58 passed, including the new
  contract that visible copy never says subgraph, full graph or temporal plan-versus-actual
  graph; the fulfillment-example contract now asserts the Context Graph eyebrow in English
  and German; TypeScript/Vite build passed.
- Prettier on both apps and spec policy passed.
- Class names such as `reality-subgraph` are unchanged on purpose; only visible copy and
  catalogs carry the new term.

Cross-artifact review: FR-001–003 map to T001–T002 and US1; no unresolved clarification or
Constitution exception. Routes, tabs, reads and layout are untouched.
