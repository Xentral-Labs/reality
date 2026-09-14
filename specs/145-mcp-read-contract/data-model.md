# Data and Read Models

No schema or authority changes. Existing Item.unit and DocumentLine.unit define distinct quantity bases. Commitments refer to items; reservations refer to commitments; movements and ledger entries retain existing provenance.

A response envelope, cursor and metadata are transient transport values, never business tables. Cursor: format version, tenant/read/filter digest, last opaque ordering key. Metadata: tenant, filters, UTC observed_at, read version, optional derivation version/local event sequence, explicit unknown upstream freshness, consistency/persistence declaration.

Balance rows group receivable/payable LedgerEntries by currency with Decimal arithmetic. Location stock reuses Movement minus active Reservation semantics via shared services; no stored balance or conversion.
