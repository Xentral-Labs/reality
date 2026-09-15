# Decisions

Existing account-wide dispatch audit and AppUser lock are reusable. Reject resetting
usage or advancing reset timestamps: both destroy consumption meaning. Reuse audit
records rather than introducing a second quota ledger. Security events are separate
from business event catalogs; no public command/view/MCP schema change.
