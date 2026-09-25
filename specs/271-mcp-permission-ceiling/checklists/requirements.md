# Specification Quality Checklist: MCP Permission Ceiling Follows the Catalog

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
- [x] The wrong specification statement is corrected (T002): the consent screen showed
      `Reality API returned 422`, not the generic completion failure the Context section claimed
- [x] Product scope approved by the owner (2026-09-25, before implementation)

## Verification Evidence

Filled in as the work lands. A row stays open while its check is red.

| Gate | Command | Result |
|---|---|---|
| Focused suite | `pytest core/tests/test_mcp_oauth_http.py core/tests/test_mcp_permission_parity.py` | 24 + 5 passed |
| Focused suite observed failing first | the bound lowered to 5 and the `ValueError` arm removed | 4 failed for the two intended reasons, then restored |
| Catalog, isolation and MCP gates | `pytest core/tests/test_mcp_oauth_service.py core/tests/test_application_catalog.py core/tests/test_tool_catalog.py core/tests/tenant_isolation core/tests/test_ai_mcp.py core/tests/test_decision_trail_mcp.py` (with the focused suite) | 135 passed, 2 skipped |
| Lint | `ruff check . --no-cache` and `ruff format` from `packages/reality-core` | all checks passed |
| Complete backend suite | full `pytest` run | running; CI runs it on the pull request |
| No second literal | repository search for a permission-length bound (T021) | none; the only nearby bound caps the scope string |

## Notes

- The plan deletes the ceiling rather than raising it. A normalized permission list is a set of
  distinct catalog names, so its length is bounded by the catalog by construction and a separate
  cap cannot fire for a valid list (`research.md` R2). Approving that reading is part of T001.
- Research found a second defect the specification only half-saw: an unknown tool name escaped the
  consent endpoint as a 500, because `approve()` did not catch the `ValueError` that the shared
  validation raises (`research.md` R3). FR-004 covers it and T014 fixed it.
- Implementation found a third: an empty selection was a pydantic 422 on the interactive path and a
  stated 400 on the manual one. `min_length=1` came off `Approval.allowed_tools` as well, so both
  paths now give the same sentence. Recorded under `tasks.md` Implementation Notes.
