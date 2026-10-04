# Verification

Date: 2026-10-04. Scope: spec 364 FR-001–006 / DR-001–003.

## Local evidence

- Test-first run: 10 failures, 48 passes against the new regressions before production
  changes. The initial Playground fixture incorrectly attempted changing immutable
  tenant purpose; corrected to the real confirmed practice-company creation service.
- Final focused PostgreSQL suite: 67 passed in 8.92s across demo workflow, real HTTP MCP,
  both provider security loops and lesson companion. Includes valid legacy preparation,
  zero reservation until the separate reviewed decision, execution, replay and staleness.
- Full Python Ruff: passed.
- Catalog generation: passed; public MCP descriptions and generated references updated.
- Documentation reference unit tests: 16 passed.
- Documentation formatting: passed.
- Broad compatibility rerun on implementation head: 1,107 passed, one existing skip.
- Documentation Node contract tests: 145 passed; generated catalog freshness passed.
- First complete GitHub run found two failures in `test_ai_mcp.py` and one Finance
  owner-handoff expectation: the existing flat
  nested schema contract and an old exact Web/projection handoff expectation. Reused the
  existing reference resolver and updated the exact expected MCP contract, preserving
  the original decision policy; actual authenticated HTTP tests now cover inline nested
  enum/required constraints. Direct application-read names now resolve through the
  existing bound handler metadata, including Finance context; no Finance logic changes.
  Corrected focused suite including Finance/AI adapters: 100 passed, two existing skips
  in 7.24s. Complete required implementation-head gates passed as recorded below.

Fixtures create isolated PostgreSQL databases. No user company, credential, source control,
local deployment, outbound message or real shipment is changed by these coding tests.
Fake provider transport establishes retained context and enforced access, not live answer
accuracy. Actual authenticated HTTP tools/list and handler calls are covered.

## Review

Shared tenant-scoped services remain authoritative. No migration or domain relationship
change. Fresh ordinary practice reservations retain their delivery snapshot under the
existing lock; authored lesson context remains transaction-bound and separate. Reads do
not prepare or refresh proposals. Original execution receipt strings remain unchanged;
callable MCP guidance is an adapter observation. Human decision and credential permission
remain separate. Scope excludes Finance allocation, third-party scheduling/rights and
storage diagnostics. PR is not merged or deployed by this work.

## Complete required Quality workflow

Implementation head: `5188a470fe0ff3ba798fc5a670b0879b14101b43`.
Run: https://github.com/Xentral-Labs/reality/actions/runs/37225649462.
All 24 configured checks completed successfully: four full PostgreSQL shards and their
aggregate, eight actual live browser journeys, frontend, docs, specification and configured
browser-script jobs. No failing test, gate, ratchet or permission was bypassed.

A registry-only verification audit inspected 29 declared bases and returned 27 callable
MCP reads. The two bases without a registered MCP equivalent (`document_register`,
`timeline`) remain explicitly unavailable; they are not presented as tools.

The documentation closeout changes only task, verification and self-review metadata;
production and test code remain identical to the validated implementation head. Final
closeout-head checks are authoritative on https://github.com/Xentral-Labs/reality/pull/370
and must also complete successfully before the agent reports the PR green. No merge or
deployment is part of this work.

