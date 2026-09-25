# Implementation Plan: MCP Permission Ceiling Follows the Catalog

**Branch**: `271-mcp-permission-ceiling` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Delete the 200-name ceiling on interactive consent rather than raise it, because a normalized
permission list is a set of distinct catalog names and can never be longer than the catalog
([research.md](research.md) R2). Then make the two grant paths refuse alike: map the shared
validation's `ValueError` to a stated refusal, which today escapes the consent endpoint as a server
error (R3). Pin the relationship with a test that approves every eligible tool, reading the count
from the catalog.

No schema, no migration, no dependency, and no client change — the existing web request helper
already surfaces a string `detail` (R4).

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI, Pydantic v2 (unchanged)
**Storage**: None. `mcp_client_grant.allowed_tools` already has only a non-empty check constraint
**Testing**: pytest — OAuth HTTP and service suites, plus a parity proof across both grant paths
**Project Type**: web adapter and shared validation; no browser change
**Constraints**: zero permissions by default, explicit review of change-capable permissions and
human confirmation all stay exactly as they are
**Scale/Scope**: 180 tools today, 20 below the current ceiling

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Untouched. Permission validation reaches no Source, Document or Reality record. | PASS |
| Reality owns operational state | No business state is read or written. | PASS |
| Proven schema only | No table, column or migration. One literal is deleted. | PASS |
| Tenant + shared service boundaries | Both grant paths keep calling the same shared validation; the adapter only maps its refusal to a status. No ORM write moves. | PASS |
| Spec/test traceability | Every FR maps to a test below. | PASS |
| Explainable web behavior | A refused authorization stops reading as a server fault and names its cause. No business rule enters the browser. | PASS |
| Received values not recomputed | No business value is involved. | PASS |
| Smallest coherent design | The change is a deletion plus one exception mapping. Alternatives rejected in research R5. | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/
  web/mcp_authorization.py     # Approval.allowed_tools drops max_length;
                               #   approve() maps ValueError to a stated 400
  mcp/catalog.py               # validate_tool_permissions: the refusal messages become the
                               #   single statement of why a list is refused (wording only)
packages/reality-core/tests/
  test_mcp_oauth_http.py       # full eligible list accepted; unknown name states its cause
  test_mcp_oauth_service.py    # duplicates normalize; the wildcard stays one entry
  test_mcp_permission_parity.py# NEW: both grant paths accept and refuse the same lists
```

**Structure Decision**: shared validation stays the only place that decides what a permission list
may contain; the two adapters differ only in their status code, and after this change not even in
their message.

## Design

### The ceiling is deleted, not moved

`validate_tool_permissions` resolves legacy aliases, collapses duplicates and rejects any name
outside the catalog. What survives is a set of distinct catalog names, whose length is bounded by
the catalog by construction. `Approval.allowed_tools` keeps `min_length=1` and loses `max_length`,
which also matches its sibling `MCPTokenWrite.allowed_tools`, and the spec's "measure after
normalization" is met by there being no second measurement left to run too early.

### Both paths refuse alike

`approve()` catches `NotFound` and `InvalidOperation` today, so the `ValueError` that
`validate_tool_permissions` raises for an unknown name escapes as a 500. It gains a `ValueError`
arm answering **400** with `str(error)` — 400 rather than 409 because it is malformed input and
because that is exactly what `post_mcp_token` already answers for the same exception.

The three refusals then read as sentences: an unknown tool name, an empty selection, and tools
exceeding the requested scopes. The browser needs no change: its request helper surfaces a string
`detail` (research R4).

### What keeps the ceiling from coming back

One test approves every tool the requested scopes make eligible, with the expected count read from
the catalog at test time. It fails the moment any layer reintroduces a bound the catalog has
outgrown, which is the check that was missing when the 200 was written.

## Test Strategy

Written before the change, in this order:

1. **The full list is accepted (FR-001, FR-006, FR-007)** — approve with every eligible tool for
   each combination of supported scopes; the count comes from the catalog, never from the test.
   Observed failing first by temporarily asserting against a ceiling below the catalog size.
2. **Normalization is not pre-empted (FR-002)** — a list repeating a name and using a legacy alias
   is accepted and stored once. Positive control: the same list without duplicates stores the same
   grant.
3. **Refusals state their cause (FR-004, FR-005)** — an unknown name answers 400 with the name in
   the body, not 500; an empty list stays refused; tools outside the requested scopes keep their
   existing sentence. Positive control: a valid list in the same test is accepted.
4. **Both paths agree (FR-003)** — the same four lists submitted to interactive approval and to
   manual token creation produce the same acceptance and the same message.
5. **Gates** — the OAuth suites, the catalog suites, `ruff` from `packages/reality-core` with
   `--no-cache`, and the complete backend suite.

## Rollback

Revert the model field, the exception arm and the tests. Nothing is stored, no credential changes
meaning, and no migration is involved. Grants issued while the change is live remain valid, because
what they contain is unchanged — only which submissions are accepted.

## Risks and Review

- **Risk**: removing a bound looks like removing a safeguard. **Mitigation**: research R2 shows the
  membership rule is the real bound; the test in step 1 states it, and R5 records why a transport
  guard was considered and rejected.
- **Risk**: 400 versus 409 diverges from the router's other refusals. **Mitigation**: 409 is used
  there for state conflicts; this is malformed input, and the manual path already answers 400.
- **Risk**: a wildcard list slipping into an interactive grant. **Mitigation**: unchanged —
  `approve_interaction` refuses `*` explicitly, and a test keeps that.
- **Review focus**: that no other layer holds a second permission-length literal, and that the
  refusal messages do not disclose anything about a company the caller cannot already see.

## Complexity Tracking

No constitutional exception is required. The change removes a literal and adds one exception arm.
