# Implementation Plan (Draft): Unattended Refresh for Interactive MCP Grants

**Branch**: `385-unattended-mcp-refresh` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Status**: Draft for the owner's decision (spec D-1 to D-3). No code in this pull request.

## Sketch, assuming options 1 and 3

All changes stay in `packages/reality-core/src/reality/services/mcp_authorization.py`:

- **Sliding window.** In `rotate_refresh_token`, the replacement's `refresh_expires_at`
  becomes `now() + REFRESH_IDLE`, then `min(..., grant.created_at + REFRESH_CEILING)` when a
  ceiling is set, instead of `min(current.refresh_expires_at, now() + REFRESH_TTL)`.
  `exchange_code` keeps `now() + REFRESH_IDLE`.
- **Grace.** In the reuse branch, load the replacement under the same lock. If
  `now() - current.rotated_at <= REUSE_GRACE`, the replacement has `last_used_at IS NULL`,
  is not rotated and not revoked, then revoke the replacement with a marker and issue a new
  one chained from `current`. Otherwise revoke the family as today. A credential revoked by
  the grace path, presented again, takes the family-revocation branch.
- **Marker.** Distinguishing "revoked by grace" needs one bounded value per credential. The
  smallest option is a nullable `revoke_reason` column on `mcp_user_credential` (migration),
  or reusing `replaced_by_id` on the revoked replacement to point at its successor, which
  needs no schema. The plan prefers the no-schema option if review accepts the overloaded
  meaning; otherwise the column.
- **Inventory.** `_grant_view` adds the current credential's `refresh_expires_at`.

## Constitution Check *(blocking gate, provisional)*

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Untouched. | PASS |
| Reality owns operational state | No business state. | PASS |
| Proven schema only | No schema if the no-schema marker is accepted; otherwise one nullable column justified by FR-004. | PASS (pending marker choice) |
| Tenant + shared service boundaries | Service-only change; every query keeps `(tenant_id, grant_id)` scope. | PASS |
| Spec/test traceability | Tests below map to every FR. | PASS |
| Explainable web behavior | Connected clients shows the window's end. | PASS |
| Received values not recomputed | No business value. | PASS |
| Smallest coherent design | Two branches in one function; option 2 deferred. | PASS |

## Tests to write first

Service tests with a frozen clock: day-29 and day-58 rotations succeed; idle expiry refused;
ceiling refused; membership loss refused; grace retry succeeds once and revokes the unused
replacement; used replacement still revokes the family; grace window elapsed revokes the
family; presenting a grace-revoked replacement revokes the family; concurrent refresh with
the same token takes one path each.

## Security review focus

- The sliding window extends a stolen refresh token's life only while the attacker keeps
  using it, and each use rotates, so the legitimate client's next refresh is reuse and
  ends the family. That detection is unchanged.
- The grace path's window is the only new exposure: an attacker presenting a stolen,
  just-rotated token within 60 seconds, before the legitimate client used its replacement,
  wins that family. The legitimate client's next use of its now-revoked replacement then
  revokes the family (FR-004), so the takeover is detected on the next refresh.

## Rollback

Restore the capped expiry and the unconditional reuse branch. Credentials issued with a
longer window keep it until their next rotation; revoking grants is available in settings.
