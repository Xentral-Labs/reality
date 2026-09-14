# Data Model: Complete Chat and MCP Command Coverage

## Persistence impact

No schema changes are required. This feature composes existing entities and adds
configuration metadata only.

## Existing entities used

### Command catalog entry

Existing fields remain. Added metadata classifies each command as `eligible`,
`excluded`, or `blocked`, binds eligible commands to stable application tools, and
requires a reason for exclusions/blocks. Validation rejects missing, stale, duplicate,
or unjustified classifications.

### Application tool definition

Immutable code metadata holds stable name, description, access, strict input JSON
Schema, and handler. Mutation handlers cannot execute through the read path.

### ChangeProposal (`action` table)

Existing opaque ID, tenant, tool type, actor, status, input, output, and timestamps are
reused. State transitions are `proposed → executed` or `proposed → rejected`; terminal
states cannot replay. Proposal creation has no business effect and approval revalidates
tenant, authorization, and current state.

### SourceRecord → Document/DocumentLine → Commitment

Manual order payloads are stored losslessly as immutable SourceRecords. Documents and
lines are typed Evidence using opaque Party/Item relationships. Existing interpretation
derives sales or purchase Commitments. Documents gain no fulfillment/payment status.

### Other existing entities

Party/Role, Item, Location, PaymentTerm, pricing structures, HandlingUnit, Lot,
SerialUnit, Reservation, holds, Movement, LedgerEntry, SettlementAllocation,
SourceSystem/Capability, Membership, and Invitation retain their current fields and
shortest true links.

## Transactions, identity, and tenancy

- One approved proposal is one application transaction.
- Batch/location/order/finance operations succeed completely or leave no partial records.
- Persisted relationships use opaque IDs; human codes/numbers/names are display/search only.
- Every query is tenant scoped; foreign identities behave as not found.
