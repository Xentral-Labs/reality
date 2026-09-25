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
- [ ] One specification statement is wrong and is corrected by T002: the consent screen shows
      `Reality API returned 422`, not the generic completion failure the Context section claims
- [ ] Product scope approved by the owner (pending; the specification is `Draft`)

## Verification Evidence

Filled in as the work lands. A row stays open while its check is red.

| Gate | Command | Result |
|---|---|---|
| Focused suite | `pytest core/tests/test_mcp_oauth_http.py core/tests/test_mcp_oauth_service.py core/tests/test_mcp_permission_parity.py` | open |
| Catalog and isolation gates | `pytest core/tests/test_application_catalog.py core/tests/test_tool_catalog.py core/tests/tenant_isolation` | open |
| Lint | `ruff check . --no-cache` and `ruff format` from `packages/reality-core` | open |
| Complete backend suite | full `pytest` run | open |
| No second literal | repository search for a permission-length bound (T021) | open |

## Notes

- The plan deletes the ceiling rather than raising it. A normalized permission list is a set of
  distinct catalog names, so its length is bounded by the catalog by construction and a separate
  cap cannot fire for a valid list (`research.md` R2). Approving that reading is part of T001.
- Research found a second defect the specification only half-saw: an unknown tool name escapes the
  consent endpoint as a 500, because `approve()` does not catch the `ValueError` that the shared
  validation raises (`research.md` R3). FR-004 covers it and T014 fixes it.
