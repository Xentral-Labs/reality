# Tasks 354

- [x] T001 Review discussion; specify v1 proof, subject mandates, replay and revocation (FR-001–006).
- [x] T002 Review Constitution, persistence proof and manual consistency/coverage analysis.
- [x] T003 Add failing adversarial service/story tests (US1/US2, FR-001–004/006).
- [x] T004 Implement closed models, verifier and atomic acceptance; exact digest and claim revalidation.
- [x] T005 Register separately permissioned MCP/API acceptance adapter with contract tests.
- [x] T006 Extend shared attribution, original Source navigation and UI sentence proof (US3, FR-005).
- [x] T007 Update workflow/spec351/canonical docs and generated catalogs; run local gates.
Completion gate T008: publish in PR #332 and require current-head CI plus final review. The live result is recorded in the PR description; this file does not predeclare a pending run as successful.

Local evidence: 170 broader backend tests passed; 39 final grant tests passed after public verification metadata/production MCP checks. Migration round-trip and populated rollback guard passed. Browser story passed including external attribution and proof Source link; documentation contracts:145 passed. Full frontend contracts:463 passed; all four languages cover2730 strings; production build, Ruff, spec policy and business-description audit passed. Final settlement regression:81 passed, including refusal of stale rejection after concurrent grant acceptance (observed failing before the lock/reread fix). Current-head CI remains the final completion gate.
