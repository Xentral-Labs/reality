# Data Model

No schema, migration or persisted state changes. Read Document → DocumentLine → Item and Document → Party; Reservation → Commitment → Document/Party; Movement → Commitment and named locations; Shipment → packages/movements/events; LedgerEntry → Document/Party and existing settlement relationships. All reads enforce tenant scope. The new preview sections are transient presentation, not business authority.
