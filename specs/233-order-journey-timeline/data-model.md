# Read model

No stored entities change. SalesOrderOption has opaque id, number and party label. JourneyPage has optional order, events (existing TimelineEvent), edges, has_more and next/forward sequence information. Edge endpoints are `{kind,id}` and a relation label. Events retain distinct recorded_at and occurred_at.

Membership: Document(sales_order) → DocumentLine; Commitment → DocumentLine or document-level Document; Reservation/Movement → Commitment; LedgerEntry → Document; Fact → one exact scoped member. SourceRecord references are terminal and may contribute provenance events only. Facts do not recursively expand facts or arbitrary polymorphic graphs. All subqueries constrain tenant_id.

Edges are present only for actual held links of loaded subjects. Unloaded parents may appear as inspectable references but never receive a fabricated chart point. No human number is used as identity, no grouping is persisted and no source values are recalculated.

Posting-group events are included through held LedgerEntry.posting_group_id for the root document. The group event remains one event; links to its entries do not fabricate per-entry events.
