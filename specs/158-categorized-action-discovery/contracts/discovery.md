# Discovery Contract

The existing tenant-authorized application-reference response adds `discovery` with
`categories`, `command_groups`, and `entries`. Existing fields and execution endpoints
are unchanged. Each entry has exactly one `form` or `destination`. Forms correspond
to the finite ActionCard dispatch union. Placements specify page/record context strings.
Category paths are presentation metadata; permission and eligibility remain server-owned.
