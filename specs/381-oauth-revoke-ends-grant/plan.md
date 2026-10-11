# Implementation Plan: Revoking a Refresh Token Ends Its Grant

**Branch**: `381-oauth-revoke-ends-grant` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

## Summary

`revoke_credential_token` calls the existing `revoke_grant(reason="client_revoked")` when the
supplied token is a refresh token of the grant, or the access token of the grant's current
(not yet replaced) credential row. Otherwise it keeps revoking the one row. `revoke_grant`
accepts `actor_user_id=None`, because no human revoked the grant. Three UI labels are added
for the new reason. No schema, migration or endpoint change.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Untouched; no business record is read or written. | PASS |
| Reality owns operational state | No business state involved. | PASS |
| Proven schema only | No table, column or migration; `revoke_reason` is an existing bounded string. | PASS |
| Tenant + shared service boundaries | The adapter is unchanged; the service reuses `revoke_grant`, which is tenant-scoped by `(tenant_id, grant_id)` from the matched credential. | PASS |
| Spec/test traceability | Every FR maps to a test below. | PASS |
| Explainable web behavior | Connected clients shows the true state and a labelled reason. | PASS |
| Received values not recomputed | No business value is involved. | PASS |
| Smallest coherent design | One branch in one function, reusing the settings path. | PASS |

## Layer Changes

```text
packages/reality-core/src/reality/services/mcp_authorization.py
  revoke_credential_token   # refresh token or current access token -> revoke_grant
  revoke_grant              # actor_user_id may be None
apps/web/src/localization.tsx  # client_revoked label in de, nl, es
packages/reality-core/tests/test_mcp_oauth_service.py   # FR-001..FR-004
packages/reality-core/tests/test_mcp_oauth_http.py      # FR-001, FR-003 over HTTP
```

## Design

The current credential row is the one with `replaced_by_id IS NULL`. Its refresh token is
the only one that can renew the grant, and it shares the row with the current access
token, so revoking either leaves a grant that can never be used again. Ending the grant in
that case makes the inventory true rather than adding a new state. An older row's access
token carries no renewal power, so revoking it stays narrow.

Revoking an already rotated refresh token also ends the grant. Presenting a replaced refresh
token to the token endpoint already revokes the whole family as suspected reuse; revocation
follows the same fail-closed reading.

## Test Strategy

1. Service: revoke the newest refresh token after one rotation; the grant is listed revoked
   with `client_revoked`, no human revoker, both access tokens refused, the refresh token
   refused, and a repeat revocation changes nothing (FR-001, FR-003, FR-004).
2. Service: revoking the rotated refresh token ends the grant (FR-001).
3. Service: revoking the current access token ends the grant; revoking the rotated access
   token ends only itself and the grant renews (FR-002, with positive control).
4. Service: an unknown token changes nothing (FR-004).
5. HTTP: `/oauth/revoke` with the refresh token answers `{}` and the inventory shows the
   grant revoked; a refresh exchange answers `invalid_grant` (FR-001, FR-003, FR-004).

All observed failing on `origin/main` before the change, except the two positive controls.

## Rollback

Revert the service branch and labels. Grants already revoked with `client_revoked` stay
revoked, which is the state the client asked for.

## Risks and Review

- **Risk**: a client that revokes only its access token on logout now ends its grant.
  **Mitigation**: that row's refresh token was already unusable; the grant could not be
  renewed before this change either. RFC 7009 permits revoking the grant in this case.
- **Review focus**: that `client_revoked` reaches no consumer that enumerates reasons
  strictly. The web renders the reason through its translation lookup only.

## Complexity Tracking

No constitutional exception is required.
