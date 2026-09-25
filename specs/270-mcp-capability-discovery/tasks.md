---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: One Way In to the Capability Catalog

**Input**: `spec.md`, `plan.md`, `research.md` and `contracts/capability_catalog.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes and resulting repository artifacts MUST be written in
English. Paths are relative to the repository root; `core/` abbreviates `packages/reality-core/`.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

`[P]` marks tasks that touch different files and may run in parallel. Every functional requirement
appears in at least one test task and one implementation or documentation task. Test tasks precede
the code they prove and are observed failing first. Every negative test carries a positive control,
so it cannot pass merely because the code under test does not exist yet.

## Phase 1: Specification and Design Gates

- [ ] T001 Confirm owner approval of scope in `specs/270-mcp-capability-discovery/spec.md`, in
  particular the non-goal that `tools/list` stays unfiltered per credential, and confirm no
  clarification markers remain
- [ ] T002 Confirm every Constitution Check row is PASS and that no schema, migration or dependency
  is introduced, in `specs/270-mcp-capability-discovery/plan.md`
- [ ] T003 Run the analysis pass across `specs/270-mcp-capability-discovery/` and resolve every
  CRITICAL or HIGH finding
- [ ] T004 Settle the public name `capability_catalog` for both the MCP tool and the application
  tool, and record it in `plan.md`; `capability_describe` keeps the per-tool answer

## Phase 2: Foundational — Catalog Access and the Service

**Goal**: the classification is readable cheaply and grouped by topic, before any adapter exists.

### Tests

- [ ] T005 [P] [FR-003] [FR-008] Add a failing test that every name in `MCP_TOOL_CATALOG` appears
  under at least one topic of the service's grouping, that the topic keys equal the eleven in
  `core/config/tool_catalog.json`, and that the eleven tools bound to several capability entries are
  counted once. Derive both sides from the catalog, never from a written list, in
  `core/tests/test_capability_catalog.py`
- [ ] T006 [P] [FR-007] Add a failing test that the narrow catalog accessor returns an isolated copy
  — mutating the result does not affect a second call — and that it does not deep-copy the other
  eighteen catalog sections. Positive control: `runtime_application_catalog()` still returns all
  nineteen, in `core/tests/test_capability_catalog.py`

### Implementation

- [ ] T007 [FR-007] Add a narrow accessor for the tool-catalog slice beside
  `runtime_application_catalog()` in `core/src/reality/catalogs.py`, so a discovery call does not pay
  the measured 45.5 ms full-catalog deep copy (research R5)
- [ ] T008 [FR-001] [FR-002] [FR-003] Add `core/src/reality/services/capability_catalog.py` with
  `topics()` and `capabilities(topic)`, shaped exactly as `contracts/capability_catalog.md`. The
  module reads the built classification and defines no vocabulary of its own; an unknown topic is
  refused by naming the topics that exist

## Phase 3: User Story 1 — An agent can ask what this company can do (P1)

**Independent test**: two calls from no arguments reach the five dunning tools under `payments`.

### Tests

- [ ] T009 [P] [FR-001] Add a failing test that the no-argument answer lists every topic with its
  key, label and capability and tool counts, and that it stays within the 697-byte order measured in
  research R3, in `core/tests/test_capability_catalog.py`
- [ ] T010 [P] [FR-002] Add a failing test that `topic="payments"` returns its capabilities with
  label, purpose, description and bound tools, and that the answer stays within the 9.4 KB measured
  for the largest topic. Negative control: an unknown topic is refused and the refusal names the
  eleven valid keys; positive control: a valid key next to it succeeds, in
  `core/tests/test_capability_catalog.py`
- [ ] T011 [P] [FR-001] [FR-002] [SC-001] Add a failing end-to-end test through the MCP runtime: no
  arguments, then one topic, reaches `finance_dunning_context`, `finance_dunning_notices`,
  `finance_dunning_notice`, `finance_dunning_record_propose` and `finance_dunning_reverse_propose`.
  This is the reported regression from research R7, in `core/tests/test_capability_catalog.py`
- [ ] T012 [P] [FR-006] Add a failing test that the server instructions built by
  `build_server` name the discovery tool, in `core/tests/test_ai_mcp.py`
- [ ] T013 [P] [FR-007] Add a failing test that the tool is declared `read`, carries
  `readOnlyHint` and not `destructiveHint`, is rejected by `run_read_tool`'s mutating guard only if
  it were ever marked mutating, and that its answer contains no tenant business record. Positive
  control: a business read tool in the same test does return tenant records, in
  `core/tests/test_capability_catalog.py`

### Implementation

- [ ] T014 [FR-001] [FR-002] [FR-007] Add the `_capability_catalog` handler and register
  `TOOLS["capability_catalog"]` as non-mutating in `core/src/reality/tools/application.py`, next to
  `_capability_describe`
- [ ] T015 [FR-001] [FR-002] Add the `MCPToolDefinition` for `capability_catalog` in the `Discovery`
  group with an optional `topic` argument, in `core/src/reality/mcp/catalog.py`
- [ ] T016 [FR-006] Extend the server instructions to name the tool as the entry point for
  discovering capabilities, in `core/src/reality/mcp/server.py`

## Phase 4: User Story 2 — "Not granted" is distinguishable from "does not exist" (P1)

**Independent test**: four credentials produce four different, named grant states.

### Tests

- [ ] T017 [P] [FR-004] Add failing service tests for the four cases of
  `contracts/capability_catalog.md`: no MCP principal reports `limits_tools: false` and every tool
  callable; a manual token holding a subset reports `not_in_token` for the rest; an interactive grant
  whose tool list omits a name reports `not_in_grant`; an interactive grant that names a `propose`
  tool but was granted only `reality:read` reports `scope_excluded`. Positive control in each case:
  a tool the same credential does hold is reported callable, in
  `core/tests/test_capability_catalog.py`
- [ ] T018 [P] [FR-004] Add a failing test that `scope_excluded` never appears for a manual token,
  because manual credentials model no access-class scopes (research R4). Positive control: the same
  tool under an interactive grant does produce `scope_excluded`, in
  `core/tests/test_capability_catalog.py`
- [ ] T019 [P] [FR-004] Add the honesty test: for each of the four credentials, every tool the
  answer marks callable is then dispatched through the MCP runtime and is not refused for permission
  reasons, and at least one tool marked not callable is refused. This is the assertion that keeps the
  answer from drifting away from `dispatch_mcp_tool`, in `core/tests/test_capability_catalog.py`
- [ ] T020 [P] [FR-004] Add a tenant-isolation test: a grant id belonging to another company is
  never read; the grant lookup is filtered by the principal's tenant and behaves as not found.
  Positive control: the own-tenant grant resolves, in `core/tests/tenant_isolation/` per that
  suite's conventions

### Implementation

- [ ] T021 [FR-004] Implement grant state in `core/src/reality/services/capability_catalog.py`:
  read `current_mcp_principal()`; for a manual credential use `principal.permits`; for an
  interactive one read the `mcp_client_grant` row for `(tenant_id, grant_id)` once per call and
  separate `not_in_grant` from `scope_excluded`; with no principal report no credential limit
- [ ] T022 [FR-004] Confirm by reading both sides that the service's rule and
  `dispatch_mcp_tool`'s two checks cannot diverge silently, and note in `plan.md` where each lives,
  so a later change to dispatch has one place to look

## Phase 5: User Story 3 — Findable under its business name (P3)

### Tests

- [ ] T023 [P] [FR-005] Add a failing test that a capability with a German label in
  `core/config/resource_catalog.yaml` carries it — `Mahnung erfassen` for
  `finance_dunning_record_propose` — and that one without carries `null` and the English label, which
  is not an error. Positive control: the English label is present in both cases, in
  `core/tests/test_capability_catalog.py`

### Implementation

- [ ] T024 [FR-005] Carry `labels.de` from the built classification into the answer in
  `core/src/reality/services/capability_catalog.py`; introduce no new strings and translate no tool
  name, description or schema

## Phase 6: Registration Gates

Each of these fails the build or an unrelated suite when it is missed; they are listed separately so
none is discovered by a red pipeline (research R6).

- [ ] T025 [P] [FR-008] Add `"capability_catalog": "evidence"` to `mcp_topics` and the name to
  `understand_tools` in `core/config/tool_catalog.json`
- [ ] T026 [P] [FR-007] Add `tool:capability_catalog` to the `application_boundaries` family and to
  its evidence operation list in `core/config/tenant_isolation_catalog.yaml`, beside
  `tool:capability_describe`
- [ ] T027 [P] [FR-008] Add the name to the agent-work resource's `match` pattern in
  `core/config/resource_catalog.yaml`, beside `capability_describe` and `business_records_discover`,
  and give it a German ERP label
- [ ] T028 [FR-007] Widen the capability-guidance exemption in `core/src/reality/catalogs.py` from
  the single literal `capability_describe` to a named set of catalog-about-capability tools, and add
  a test asserting the set holds only those two, so the exemption cannot become a hole a business
  read slips through, in `core/tests/test_application_catalog.py`
- [ ] T029 [P] [FR-008] Add `core/tests/test_capability_catalog.py` to `docs/SPEC_COVERAGE_MATRIX.md`
  under this spec's section
- [ ] T030 [FR-008] Run `make docs-generate` and commit the regenerated Tool Usage pages and
  `apps/docs/.vitepress/data/tool-usage.json`

## Phase 7: Surfaces That Inherit the Tool

- [ ] T031 [P] [FR-004] Add a test that chat's tool list gains the tool automatically, because
  `model_tool_schemas` returns every read and propose definition, and that in chat — where no MCP
  principal exists — the answer reports no credential limit. Positive control: the same call under a
  manual token does report limits, in `core/tests/test_mcp_chat.py`
- [ ] T032 No CLI command is added. `capability_describe` has none either, and the CLI exposes named
  business reads rather than the capability catalog. Record this decision in `plan.md` so it reads as
  a choice rather than an omission

## Phase 8: Verification

- [ ] T033 Run the focused suite: `pytest core/tests/test_capability_catalog.py
  core/tests/test_ai_mcp.py core/tests/test_mcp_chat.py`
- [ ] T034 Run the catalog and gate suite: `pytest core/tests/test_application_catalog.py
  core/tests/test_tool_catalog.py core/tests/test_reporting_graph_coverage.py
  core/tests/test_schema_indexes.py core/tests/tenant_isolation`
- [ ] T035 Run `make docs-catalog-check` and the repository's required lint and type gates; run
  `ruff` from `packages/reality-core` with `--no-cache`
- [ ] T036 Run the complete backend suite before calling the feature done, and record the evidence
  in `specs/270-mcp-capability-discovery/checklists/requirements.md`

## Requirement Coverage

| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T009, T011 | T008, T014, T015 |
| FR-002 | T010, T011 | T008, T014, T015 |
| FR-003 | T005 | T008 |
| FR-004 | T017, T018, T019, T020, T031 | T021, T022 |
| FR-005 | T023 | T024 |
| FR-006 | T012 | T016 |
| FR-007 | T006, T013, T028 | T007, T014, T026, T028 |
| FR-008 | T005 | T025, T027, T029, T030 |

## Dependencies

Phase 1 precedes everything. Phase 2 blocks Phases 3–5; the service is where the shape and the rule
live. Phase 3 and Phase 4 are independently deliverable: the entry point is useful before grant
state exists, and grant state has nothing to attach to without it, so Phase 3 goes first. Phase 5
depends only on Phase 2. Phase 6 may run in parallel with Phases 3–5 but must complete before any
suite in Phase 8 is believed. Phase 7 depends on Phases 3 and 4.
