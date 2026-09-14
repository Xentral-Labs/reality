# Presentation data

Provider: stable catalog ID, original display name, category, translated purpose, intended areas. Fixed catalog only.
Draft: opaque browser-generated ID, provider ID, name, selected area IDs, optional related shop name. Session-only under user/tenant key; no source-system FK is invented. Only state is preparation. No timestamps or connection health. Invalid stored drafts are rejected. Existing domain unchanged.
