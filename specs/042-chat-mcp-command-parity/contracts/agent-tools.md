# Agent Tool Contract

## Shared registry

MCP and managed Chat expose identical canonical definitions: stable name, label,
description, access class, group, strict input JSON Schema, and confirmation requirement.

## Reads

Reads execute immediately and create no proposal. Discovery accepts bounded query/limit
inputs and returns opaque IDs plus mutation-relevant current fields. Detail reads use
one opaque ID. Foreign-tenant and unknown records are indistinguishable.

Discovery covers Parties, Items, Locations, Documents/orders, Commitments, Movements,
handling identities, finance/pricing, sources, and governed membership records.

## Propose and approve

Mutation proposal response:

```json
{"proposal_id":"act_opaque","status":"proposed","requires_human_confirmation":true,"arguments":{},"preview":{}}
```

Proposal creation changes no business state. Approval input is
`{"proposal_id":"act_opaque","approved":true}` and returns the executed proposal,
stable tool name, and exact output. Approval derives tenant from authentication and
revalidates state. Membership additionally requires a current human owner. Reject,
stale, unauthorized, foreign-tenant, invalid, and replay paths produce no mutation.

## Orders

Sales/purchase inputs include type/direction, human number, date, currency, opaque
Party ID, optional opaque ship-to Party ID, and at least one line with opaque Item ID,
Decimal quantity, unit, and optional price/time. Preview contains the complete normalized
header and lines. Approval returns SourceRecord, Document, DocumentLine, and Commitment IDs.

## Compatibility

Existing tool names/shapes remain valid. New tools are additive. Existing MCP token
allowlists do not automatically receive new permissions.
