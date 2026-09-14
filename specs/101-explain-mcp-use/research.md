# Research: Explain MCP Use

## Decision: Keep the landing page at connection-summary depth

**Rationale**: The surrounding agent-context visual already establishes operational value. A second five-column capability showcase interrupts that story and gives implementation detail the visual weight of a product pillar. A compact bridge answers how an agent connects and delegates concrete jobs to the canonical guide.

**Alternatives considered**: Keeping the five job cards was rejected because the guide and generated catalog own that detail. Removing MCP entirely was rejected because customers still need a discoverable connection path from the landing page.

## Decision: Document the implemented bearer-token connection honestly

**Rationale**: Reality currently exposes authenticated Streamable HTTP with tenant-scoped, hashed, revocable bearer tokens and per-tool allowlists. OAuth flows are not implemented.

**Alternatives considered**: Named one-click client instructions were rejected because client interfaces change and some clients require OAuth.

## Decision: Add one bilingual guide under API & Tools

**Rationale**: This is the canonical area for external agent interfaces and keeps setup separate from conceptual capability guidance.

**Alternatives considered**: Expanding company-settings documentation alone was rejected because it is not a discoverable end-to-end connection journey.
