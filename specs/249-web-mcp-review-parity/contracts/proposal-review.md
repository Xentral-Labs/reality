# Proposal Review Contract

For one tenant-scoped opaque proposal ID the server returns identity, tool label, origin,
timestamps, lifecycle status, one review kind/destination, redacted stated input, persisted preview,
validation/refusal explanation, confirmation requirement, optional review token and stored receipt.

The client sends only proposal identity, explicit confirmation and the issued review token. It never
sends reconstructed application input. Unknown or cross-tenant IDs are not found. Retired tools may
be rejected but not approved. Specialized kinds never silently degrade to `common`.
