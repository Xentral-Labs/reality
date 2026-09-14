# Verification: Seven MCP Read Improvements

Date: 2026-09-08. Base: origin/main at 2183b88. Branch: 145-mcp-read-contract.
Implementation is isolated from the owner's existing checkout. No deployment,
remote business mutation, schema change, dependency change or merge is included.

## Design gates

Owner approved all seven product decisions before implementation. Specification,
plan, requirement checklist and task analysis cover all nine functional and three
domain requirements. Constitution checks PASS; no unresolved clarification or
critical analysis finding. The final review preserves that scope.

## Test-first evidence and corrections

The initial new contract suite failed on missing pages, currency grouping,
location/unit fields and closed-order explanation (12 failures, 2 passes). The
ambiguous-number fixture was adjusted to create distinct retained documents
instead of triggering the existing manual-order deduplication contract. The
first implemented contract suite passed all 14 tests.

Coverage was then expanded to 20 contract tests: real reservation effects by
location, unit disagreement, live cursor boundaries, signed/zero balances,
foreign-tenant stock and postings, and mixed open/closed order lines. All 20 pass.
The existing MCP server test now verifies the actual serialized page envelope,
not only a matching text fragment. Existing internal list consumers remain
covered by the application, projection and tenant-isolation suites.

The first full run exposed missing tenant-isolation catalog registrations and
spec-coverage entries; both were added with executable evidence. A source-code
inspection test also ran while source line positions were being formatted. The
final full run uses fixed source files. Fixture-only failures during additional
test development were corrected through the existing public business services.

## Quality results

- Focused new contracts: 20 passed.
- Ruff (`cd packages/reality-core && ruff check .`): PASS.
- Specification policy (`make spec-check`): PASS.
- Frontend: formatting PASS, 39 tests PASS, production build PASS, all four
  translation audits PASS. Existing bundle-size advisories are non-failing.
- Documentation: formatting PASS, 45 tests PASS, production build PASS.
- Generated English/German MCP reference updated from the executable catalog;
  unrelated pre-existing command/event reference drift was left out.
- Public site: untouched; its PR quality gate is conditional on site/workflow changes.
- Final full PostgreSQL/backend/migration suite: **1817 passed, 7 skipped in
  170.61 seconds** (`python -m pytest -n 2 --dist loadscope -q -ra --tb=short`).
  All seven skips are existing retired server-rendered UI cases covered by
  React/JSON API boundaries; no new feature test is skipped.
- Final diff review and `git diff --check`: PASS. All fourteen implementation
  tasks are complete after the required checks passed.

## Review and operational limits

No migrations or new dependencies. All quantities/money use existing Decimal
semantics; source evidence is read without rewriting it. Shared services enforce
tenant filters and reference checks. New diagnostics suppress autoflush and do
not write or commit business/projection records; authentication telemetry remains
separate. Existing cache-based list callers remain supported.

Public MCP list clients must adopt `records`/`next_cursor`/`has_more` or explicitly
request legacy lists. Finance always returns separate currency rows. No FX/unit
conversion, upstream freshness guarantee or point-in-time snapshot is introduced.
Operational pages bound the response but still derive the relevant tenant state
in full. This is not a large-tenant query optimization or analytics platform.

A human merge/deployment review remains separate from the completed local
implementation and verification.
