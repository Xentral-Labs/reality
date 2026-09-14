# Contract: Canonical MCP Tool Parity

## Single registry

Each externally visible tool is defined once with its name, description, structured
input, access mode, settings metadata, and application binding. These consumers derive
from that definition:

- dedicated HTTP MCP registration;
- token allowlist validation;
- company-settings tool catalog;
- internal Copilot model-tool schema;
- direct internal dispatch;
- contract/parity tests.

## Required parity checks

For every registry entry, tests compare:

1. exposed HTTP MCP name;
2. structured input schema and required/optional arguments;
3. access mode and permission scope;
4. direct dispatcher and HTTP result normalization;
5. tenant not-found behavior;
6. proposal-only or separately confirmed mutation behavior;
7. trace/opaque identifiers relevant to the result.

No HTTP MCP tool may exist outside the registry, and no registry entry may fail to bind
at startup.

## Internal Copilot

The Copilot gives the model schemas derived from the same registry and dispatches model
calls through the same binding with the Chat service's authorized tenant. Its client
policy may expose a narrower subset than an external token. It does not receive tenant
authority from model arguments and does not gain confirmation permission by being an
internal caller.

## Compatibility

Feature 018 does not intentionally rename tools or change schemas. Existing documented
legacy allowlist aliases remain only if the canonical validation contract already
supports them. Any incompatible tool change requires its own reviewed behavior change.
