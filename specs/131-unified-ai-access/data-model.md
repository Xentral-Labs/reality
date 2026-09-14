# Existing data only
AISettings references the tenant secret vault. MCPAccessToken stores opaque id, tenant, name, hash, prefix, explicit allowlist and timestamps. No schema change. New UI's unresolved session marker stores only random attempt ID and action kind. Clear API keys and token values remain transient component state; they are never part of stored review metadata.
