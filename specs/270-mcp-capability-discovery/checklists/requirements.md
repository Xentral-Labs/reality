# Specification Quality Checklist: One Way In to the Capability Catalog

**Purpose**: Validate specification completeness and quality before implementation
**Created**: 2026-09-25
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details in the specification
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] Every functional requirement maps to a test task and an implementation task
      (`tasks.md`, Requirement Coverage)
- [x] User scenarios cover the primary flows
- [x] Measurable outcomes are reachable from the planned design
- [x] Product scope approved by the owner (2026-09-25, before implementation)

## Verification Evidence

Filled in as the work lands. A row stays open while its check is red.

| Gate | Command | Result |
|---|---|---|
| Focused suite | `pytest core/tests/test_capability_catalog.py` | 15 passed |
| MCP surfaces | `pytest core/tests/test_ai_mcp.py core/tests/test_mcp_chat.py core/tests/test_mcp_oauth_service.py core/tests/test_mcp_read_contract.py` | passed |
| Catalog and registration gates | `pytest core/tests/test_application_catalog.py core/tests/test_tool_catalog.py core/tests/test_reporting_graph_coverage.py core/tests/test_schema_indexes.py core/tests/tenant_isolation` | 130 passed, 2 skipped (with the MCP suites above) |
| Generated documentation | `make docs-generate`, then `make docs-catalog-check` once the output is committed | regenerated; the check diffs against the commit |
| Lint | `ruff check . --no-cache` and `ruff format` from `packages/reality-core` | all checks passed |
| Complete backend suite | full `pytest` run | running locally; CI runs it on the pull request |

## Notes

- The owner approved scope on 2026-09-25, including the non-goal that `tools/list` stays
  unfiltered per credential, and implementation followed.
- One planned rule was wrong and was inverted during implementation: `approve_interaction`
  refuses tools outside the requested scopes, so a grant can never name a tool whose access class
  its scopes exclude. `tasks.md` Implementation Notes and `research.md` R4 carry the correction.
- The analysis pass (T003) has not been run as a separate step; the review that would have found
  the scope-rule error found it during implementation instead, and it is recorded rather than
  quietly fixed.
