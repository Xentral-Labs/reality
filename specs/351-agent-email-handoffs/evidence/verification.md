# Verification: Agent Email Handoffs

## Local evidence

- Spec policy and Ruff passed.
- Source-authored business-description audit: zero missing root descriptions/bindings.
- Focused PostgreSQL integration/contract suite: 143 passed, including migration
  chain, policy, graph completeness, MCP read/permission and blueprint adapters.
- Email-specific story and migration checks pass; repeat after final source/file
  refinements is recorded below and in CI.
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
The complete required suite is verified by the PR's GitHub quality gates, with
final conclusions recorded once those gates complete.

## Review

Original messages, files and reported outcomes remain Sources. Approval authorizes
an exact external instruction and does not imply successful sending or delivery.
Claims are authenticated and serialized; unresolved identical payloads cannot be
reproposed/claimed to bypass reconciliation. Outcome derivation uses only
executor-bound receipt links, not arbitrary caller-selected source labels.
New correspondence tables are explicitly deferred from graph analytics pending a
separate privacy/grain design; the operational evidence trail remains available.
