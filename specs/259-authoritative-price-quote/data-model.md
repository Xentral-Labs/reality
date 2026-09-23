# Data Model

No persistent model changes. The feature reads existing `PartyPriceList`, `PartyGroupMember`,
`PartyGroupPriceList`, `PriceList`, and `PriceListEntry` records through `resolve_price`.

`PriceResult` gains non-persistent provenance values: `assignment_id`, optional `party_group_id`,
and `evaluated_at`.
