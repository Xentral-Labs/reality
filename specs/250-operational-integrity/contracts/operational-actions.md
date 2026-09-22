# Contract: Operational Integrity Actions

All identifiers are opaque and tenant-scoped. Propose/review never mutates Reality. Confirmation requires the exact current review token and eligible principal and remains unavailable to model selection.

## Return disposition

Intent contains return movement, disposition, quantity, optional destination and reason. Tracking IDs are never caller-selected. Review exposes arrival identity/location and before/after quantities. Receipt identifies proposal, source, resolving movement, inherited identities, and original return.

## Commitment revision

Intent contains commitment, at least one date or positive quantity, optional note, statement time, source, and optional retained allocations expressed as opaque reservation ID plus retained quantity. Review exposes original/effective/revised terms, fulfilled/open/reserved quantities, exact release/retention effects, or eligible choices when explicit selection is required. Confirmation refuses missing, foreign, stale, duplicated, over-limit, or identity-altering selections. Receipt identifies revision, released reservations, retained replacements when any, event, and before/after observations.

## Commitment cancellation

Intent contains commitment, required non-blank reason, and optional source. Review exposes direction, item, exact location, effective/fulfilled/open quantity, active reservations/holds, and states that stock and Document do not change. Receipt identifies cancellation event, cancelled remainder, retained fulfilment, releases, reason, and links.

## Proposal outcome and reconciliation

Detail distinguishes proposal lifecycle, execution verification, applied effect, fresh observation/error, remaining work, and safe next action. Known pre-effect refusal is not executing. Genuine uncertainty remains executing/unresolved. Reconciliation settles only tenant/action/intent-correlated evidence and never retries.

## Interface parity

MCP/Chat expose propose, detail/status, and reconciliation through canonical tools. Web uses the same review/confirm flow. CLI/API are thin adapters. One parity matrix proves equivalent normalized intent, review, receipt, state, and explanation across all five interfaces. No interface writes domain records directly.
