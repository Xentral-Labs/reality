# Complete Read Capability Guidance

Agents should not discover public reads from schemas and then invent their semantic
meaning. Every public business read needs one canonical description of its data basis,
freshness, limitations, proof boundary, unknown conditions, and safe next step.

The bounded completion slice covers the six remaining public business reads. The
`capability_describe` meta-read describes these capabilities and does not describe
itself. No new business read, projection, table, or authority mechanism is introduced.
