# Data Model: Chat Agent Decisions

## Decision

Add nullable `decided_via_channel` to the existing tenant-scoped ChangeProposal, with a database check permitting only `chat`.

| Settlement | Person ID | MCP token ID | Channel |
|---|---|---|---|
| Signed-in person | set | null | null |
| MCP token | null | set | null |
| Chat agent | null | null | `chat` |
| Historical/unknown | null | null | null |

Application behavior keeps modes mutually exclusive. Existing rows receive no backfill. `decided_at` remains required for any attribution to be reported.

## Lifecycle

Existing `proposed → executing → executed` and `proposed → rejected` transitions remain. Chat channel is written when settling and cleared if existing recovery restores `proposed`. Executed replay keeps the stored receipt and attribution. Executing remains an outcome requiring reconciliation.

## Relationships and tenancy

No relationship changes. Decision → BusinessEvent remains `business_event.action_id`. Interaction → decision remains supporting telemetry. All reads filter by tenant; foreign proposals remain undisclosed.

## Migration

Upgrade adds the nullable field and check without rewriting rows. Downgrade removes both. Historic unknown attribution cannot be reconstructed.
