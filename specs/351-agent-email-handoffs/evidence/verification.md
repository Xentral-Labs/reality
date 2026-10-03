# Verification: Agent Email Handoffs

## Local evidence

- Spec policy and Ruff passed.
- Source-authored business-description audit: zero missing root descriptions/bindings.
- Focused PostgreSQL integration/contract suite: 143 passed, including migration
  chain, policy, graph completeness, MCP read/permission and blueprint adapters.
- Final email-specific stories and migration checks: 18 passed.
- After both main integrations, email, migration, application/discovery catalogs
  and agent registry contracts: 77 passed.
- CI integration fixes (MCP schema shape, canonical frontend fixture and explicit
  Chat read/propose restriction): 49 passed, 2 unchanged skips.
- Product documentation: 145 JavaScript contracts, Python reference tests,
  formatting and production build passed.
- Web test suite: 462 passed. The sandbox initially refused Python fixture
  subprocesses (EPERM); the same suite passed with the approved test execution.
- All four-language i18n audits passed; web build passed.
- Browser acceptance: full outgoing text/BCC, safe HTML and original evidence/file
  navigation passed.
- Generated Tool Usage and Product Advisor knowledge refreshed.

## Full-suite execution

An initial local parallel run was stopped after 1,111 passing tests because its
migration workers exceeded the disposable PostgreSQL container's default lock
capacity. That interrupted run is not a full-suite pass. The container's
max_locks_per_transaction was raised to 1024; focused migration tests then passed.
The complete required suite passed on commit
`c80f845bc9a86fb3f93e121a5cdf16cd4975523c`:

- [Quality gates run 949](https://github.com/Xentral-Labs/reality/actions/runs/37147333752):
  all 22 jobs passed, including all four PostgreSQL shards (1,462 + 1,438 +
  1,801 + 1,316 = 6,017 passed; 10 existing skips), frontend, documentation,
  seven browser-script shards and six live-browser journeys.
- [Installer run 218](https://github.com/Xentral-Labs/reality/actions/runs/37147333749):
  script and end-to-end jobs passed.
- [PR #332](https://github.com/Xentral-Labs/reality/pull/332) records the live
  checks for the final documentation-only completion commit as well.

Both merged main updates were incorporated, catalogs regenerated and the email
migration placed after the latest supplier-item-number migration. The first CI
attempt found three registry/fixture contract mismatches; those were corrected,
verified locally and passed in the complete rerun. No unresolved review findings
were present at completion.

## Review

Original messages, files and reported outcomes remain Sources. Approval authorizes
an exact external instruction and does not imply successful sending or delivery.
Claims are authenticated and serialized; unresolved identical payloads cannot be
reproposed/claimed to bypass reconciliation. Outcome derivation uses only
executor-bound receipt links, not arbitrary caller-selected source labels.
New correspondence tables are explicitly deferred from graph analytics pending a
separate privacy/grain design; the operational evidence trail remains available.
