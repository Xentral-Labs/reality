# Research: MCP Permission Ceiling Follows the Catalog

**Branch**: `269-permission-ceiling-plan` | **Date**: 2026-09-25

Measured and read against `main` at `8d08b95f`, not recalled.

## R1 — The ceiling and the headroom

`Approval.allowed_tools` in `core/src/reality/web/mcp_authorization.py` is
`Field(min_length=1, max_length=200)`. The catalog holds **180** tools (106 propose, 71 read,
2 confirm) after spec 270 merged, leaving **20** additions of headroom. `interaction_view` preselects
every eligible tool, so the *default* consent submission is the full list and the failure needs no
unusual user behaviour.

`MCPTokenWrite.allowed_tools` in `core/src/reality/web/api.py` has no length bound at all. The two
paths that grant the same permissions already disagree, and the repository's own precedent for this
field is therefore "no transport bound".

## R2 — The ceiling is not the wrong size; it is unnecessary

`validate_tool_permissions` (`core/src/reality/mcp/catalog.py`) normalizes before anything else:
resolves the 4 legacy aliases, collapses duplicates through `dict.fromkeys`, returns `["*"]` for a
wildcard, and rejects any name outside `MCP_TOOL_NAMES`.

A normalized list is therefore a set of distinct names drawn from the catalog, so its length can
never exceed the catalog's. A separate length cap cannot fire for a valid list and can only fire for
an invalid one that the membership rule would reject anyway.

**Consequence**: the fix is to delete the literal, not to raise it or recompute it. The bound becomes
a consequence of the membership rule, which is what "derived from the catalog" means here. The
spec's FR-002 — measure after normalization — is then satisfied because there is no second
measurement left to happen too early.

## R3 — An unknown tool name is a 500 today

`approve_interaction` calls `validate_tool_permissions` first, which raises `ValueError` for an
unknown name. The web `approve()` handler catches `NotFound` (404) and `InvalidOperation` (409) and
nothing else, so the `ValueError` escapes as an unhandled server error.

Probed rather than assumed, by calling the service with one invented name:

```text
RAISED: ValueError - Unknown MCP tools: no_such_tool
```

The manual token endpoint does not have this defect: `post_mcp_token` catches
`(NotFound, ValueError)` and answers 400 with `str(error)`.

**Consequence**: the asymmetry in FR-003 is not only the length bound. One path already states its
refusal and the other returns a server error for the same input.

## R4 — What the consent screen shows

`request()` in `apps/web/src/api.ts` reads `detail` when it is a string, or `detail.message`, and
otherwise throws `APIError("Reality API returned <status>")`. `OAuthAuthorization.tsx` renders
`reason.message`.

So a refusal today shows:

| Refusal | Status | What the owner reads |
|---|---|---|
| More than 200 names | 422, `detail` is FastAPI's error list | `Reality API returned 422` |
| Unknown tool name | 500 | `Reality API returned 500` |
| Tools exceed requested scopes | 409, string detail | The stated sentence |

There is no `RequestValidationError` handler in `core/src/reality/web/app.py`, so the 422 body keeps
its default list shape and cannot be surfaced.

**Correction to the specification**: the spec says the consent page renders its generic
"Authorization could not be completed". It does not — that string is the fallback for a non-`Error`
rejection, and an `APIError` carries the message above. Equally unactionable, differently worded;
the specification is corrected with this plan.

**Consequence**: mapping the refusal to a status with a string `detail` is enough for the existing
client to show it. No client change is needed for FR-005.

## R5 — Alternatives considered and rejected

- **Raise the ceiling.** Moves the same failure 20 merges further out and keeps a number nobody
  maintains.
- **Derive the ceiling from the catalog size.** Correct but pointless: R2 shows the check cannot
  fire for a valid list.
- **Keep a generous transport bound as a denial-of-service guard.** Rejected for now: the sibling
  field on the manual token path has none, the endpoint is authenticated and owner-scoped, and
  adding a guard to one of the two paths would recreate the asymmetry this feature removes.
