# Implementation Plan: Resource Metadata Lists Every Supported Scope

**Branch**: `382-resource-metadata-scopes` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

## Summary

`RealityServer.streamable_http_app` replaces the SDK's protected-resource metadata route
with one built by the SDK's `create_protected_resource_routes`, using
`sorted(SUPPORTED_SCOPES)`. `AuthSettings.required_scopes` stays `[REQUIRED_SCOPE]`.
`approve_interaction` adds `REQUIRED_SCOPE` to the derived scopes. No schema, migration or
client change.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Untouched. | PASS |
| Reality owns operational state | No business state involved. | PASS |
| Proven schema only | No table or column; `scopes` already stores a list. | PASS |
| Tenant + shared service boundaries | Grant creation stays in the shared service; the transport only publishes metadata. | PASS |
| Spec/test traceability | Each FR maps to a test below. | PASS |
| Explainable web behavior | Connected clients shows the true scope list. | PASS |
| Received values not recomputed | No business value involved. | PASS |
| Smallest coherent design | One route replaced with the SDK's own builder; one set member added. | PASS |

## Layer Changes

```text
packages/reality-core/src/reality/services/mcp_authorization.py  # REQUIRED_SCOPE; grants hold it
packages/reality-core/src/reality/mcp/server.py                   # publish SUPPORTED_SCOPES
packages/reality-core/tests/test_mcp_http_runtime.py               # FR-001
packages/reality-core/tests/test_mcp_oauth_service.py              # FR-002, FR-003
```

## Design

The SDK builds its routes in `streamable_http_app` and gives custom routes the lowest
precedence, so a custom route cannot shadow the metadata path. The override replaces the
one route at the same path and index, and fails loudly if an SDK upgrade stops registering
it. Required scopes and the 401/403 middleware are untouched.

Adding `reality:read` at approval, not at token resolution, keeps the existing invariant
that narrowing a stored grant's scopes removes tools.

## Test Strategy

1. Runtime: the resource metadata lists all three scopes, equal to the authorization server
   metadata; an unauthenticated call still answers 401 (FR-001).
2. Service: a grant of one proposal tool records `reality:propose reality:read`, the token
   response states both, and the principal permits only that tool (FR-002, FR-003).
3. Existing: the 403 `insufficient_scope` transport test and the scope-narrowing principal
   test keep passing unchanged.

Both new tests observed failing on `origin/main`.

## Rollback

Revert both changes. Grants approved meanwhile keep `reality:read`, which permits no extra
tool.

## Risks and Review

- **Risk**: an SDK upgrade changes the metadata route. **Mitigation**: the override raises
  if the route is missing, and the runtime test reads the published document.
- **Review focus**: whether `reality:read` should stay the transport minimum. The spec
  records the decision and its reason.

## Complexity Tracking

No constitutional exception is required.
