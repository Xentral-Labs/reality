# Data Model: Separate MCP Runtime

## Summary

Feature 018 requires no new business tables, columns, indexes, object-storage objects,
or Alembic migration. It changes runtime ownership and configuration while reusing the
existing authoritative records below.

## Existing durable entities

### MCPAccessToken

Tenant-scoped credential authority administered through Web/API settings and verified
by the dedicated MCP runtime.

Relevant semantics:

- opaque token record identity;
- exactly one tenant authority;
- human-readable name and non-secret display prefix;
- SHA-256 token digest; clear text is never recoverable after creation;
- explicit allowed tool names or the existing all-tools marker;
- creation, last-use, and revocation timestamps;
- revoked records never authorize a later protected call.

No record is copied into an MCP-owned store. The token subject produced by successful
verification is the tenant authority used by every tool call.

### ChangeProposal

Existing tenant-scoped durable preview of a requested mutation.

Relevant semantics:

- created by mutation-oriented MCP/application tools without executing the mutation;
- retains exact tool name and arguments for review;
- remains proposed until a separately authorized approval or rejection;
- client disconnect does not delete or execute it;
- tenant-scoped listing allows reconciliation after an uncertain response.

### Canonical Tool Definition

Code/configuration contract rather than a database entity. One definition contains:

- stable exposed name and human description;
- structured input contract;
- access mode (`read`, `propose`, or `confirm`);
- canonical application handler adapter;
- group/label metadata used by settings;
- optional compatibility aliases only where already supported and tested.

HTTP MCP registration, allowlist validation, settings display, and internal Copilot
tool presentation derive from this definition. Startup rejects incomplete or duplicate
definitions.

### MCP Endpoint Configuration

Deployment configuration rather than tenant business data:

- exact public origin URL with the protocol served at `/`;
- internal bind host and port;
- production/local validation mode;
- runtime-specific database pool bounds;
- narrowly defined trusted external host/proxy behavior.

The public URL is never identity or authorization and is not stored per tenant.

### Runtime Health Result

Ephemeral operational result, not a business record:

- liveness: process can answer;
- readiness: database query, credential-verifier prerequisite, and canonical registry
  integrity are usable;
- bounded component status without credentials, tenant IDs, business payloads, or
  exception traces.

## Relationships

```text
configured public MCP endpoint
          |
          v
authenticated HTTP runtime
          |
          +-- verifies --> MCPAccessToken --authorizes--> tenant + tool
          |
          +-- adapts ----> Canonical Tool Definition
                                 |
                                 v
                         shared application service
                                 |
                                 +-- read result, or
                                 +-- ChangeProposal
```

## State transitions

### Credential

```text
created/active -> used (last-used audit update) -> revoked
```

Revoked is terminal for authorization. Feature 018 does not change this lifecycle.

### Proposal

Existing transitions remain authoritative. Transport timeout or disconnect is not a
proposal state transition.

### Runtime readiness

```text
not ready <-> ready
```

Readiness changes are observations of dependencies and registry integrity, not durable
business state.

## Validation rules

- Public MCP URL is absolute, has the required endpoint path, and follows production
  transport-security requirements.
- Bind host and port are independently valid and never inferred as authorization.
- Tool names are unique and every definition has one supported access mode and binding.
- Allowed tool names resolve through the canonical registry.
- Successful token subject is non-empty and is the only tenant source for MCP calls.
- Runtime pool bounds are positive, bounded deployment values and are reported in
  configuration validation without exposing database credentials.
- No migration may be introduced unless implementation discovers a separately reviewed
  requirement that changes this design artifact and spec.
