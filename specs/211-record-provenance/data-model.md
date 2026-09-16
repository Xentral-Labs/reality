# Data Model

Two nullable columns are added to `source_system`, and nothing else changes.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `base_url` | text | yes | Absolute `https` address of the external system's own interface for this configured instance. Configuration, not a credential and not an endpoint that is ever called. |
| `connector_code` | string | yes | The catalog connector shell this instance was installed from. Null for systems created by hand or for existing instances the backfill cannot resolve unambiguously. It is the only association between an instance and a connector, for address templates and for the existing instance grouping alike. |

No column is added to `source_record`, and no operational table changes. `source_record_id` on Party, Item, Location, Document, Commitment, Shipment, ShipmentPackage, ShipmentEvent, Movement, ReturnAnnouncement, LedgerEntry, Fact and BusinessEvent is read as it stands.

Reads used by the feature, all tenant-scoped:
- record → `source_record_id` → `SourceRecord` for identity, version and payload;
- `SourceRecord.source_system` → `SourceSystem.code` for name, base address and connector shell, where a configured system still exists under that code;
- `SourceRecord` → `ImportJob` and the terminal `InterpretationOutcome` for import state and classification, in detail context only;
- `SourceRecord.id` → the operational tables carrying that `source_record_id`, for produced-record links, bounded;
- record → its `Fact` rows → their distinct `source_record_id` values, for contributing-source disclosure in detail context only.

The external link is composed at read time from `SourceSystem.base_url`, the connector's relative template for the record's `source_type`, and the encoded `external_id`. It is never stored, never written to a business record, and carries no authority. `SourceRecord` remains immutable, and the retained payload is displayed verbatim.

The migration adds two nullable columns and backfills `connector_code` once, applying only the association rules already in force: an instance code equal to a connector code resolves to that connector; otherwise the description prefix resolves it, evaluated longest catalog name first and accepted only when exactly one connector matches; anything else stays null. The backfill introduces no new rule and no guess. After it, `connector_shells` reads the column and the description-prefix test is removed, which also ends the present double association between prefix-sharing connector names.

Downgrade drops both columns. Configured addresses are the only stored value lost; the connector association returns to being inferred, as it is today.
