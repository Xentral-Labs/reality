# Verification and review

## Pre-implementation review

FR-001–FR-005 map to the five acceptance scenarios and T001–T005. Constitution review passed: no schema, business writes, authorization or account-preference API behavior changes. Explicit profile saves remain the existing service path. No unresolved clarification, uncovered requirement or critical finding. Initial shared-language tests failed because the common module did not exist, then passed after implementation.

## Completed checks

- Site: formatting, 61 tests and all four localization audits pass.
- Web: formatting, 123 contract tests and all four localization audits pass.
- Docs: formatting and 54 contract tests pass.
- All three production frontend builds pass. Docker builds also pass with the common helper copied into each independent image.
- `make spec-check`, `make lint` and `git diff --check` pass. Shared helper formatting passes.
- Browser acceptance passes on isolated built previews and final Docker ports 8082/8080/8083 for all four languages: explicit site choice → correctly localized Docs/fallback → application with conflicting English account preference → website → direct reopen. Navigation performs no profile write.
- Explicit profile save changes the browser preference while retaining en-GB number format and Europe/Rome timezone. Only the requested profile API write occurs.
- Explicit Docs German/English switches replace the original fallback preference. Remembered German redirects to the equivalent deep topic while preserving query, model anchor and reload.
- The first final-container browser run timed out in Playwright's implicit navigation wait after a successful new-tab click. The test now awaits the popup and rendered language explicitly; the complete final-container run passes.

## Scope and limitations

The cookie stores only the language. It shares the known runreality.ai parent domain and the localhost host; unrelated deployments use explicit language-bearing links and their own local preference. It cannot synchronize direct visits between unrelated origins before a handoff, or across devices. Existing account language is the fallback and is never automatically persisted to the server by navigation.

No new dependencies, database migrations or business code changes. PostgreSQL integration suites are not applicable to this presentation-only change. Existing non-failing bundle-size advisories remain.

## Local preview

Docker site, web and docs were rebuilt from this worktree with existing configured origins; backend services were not restarted. Browser acceptance used synthetic HTTP account fixtures only, with no real account changes.
