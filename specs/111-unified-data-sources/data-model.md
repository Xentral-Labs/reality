# Data model

No persistence changes. SourceSystem scoped code matches the existing SourceRecord.source_system origin. SourceRecord ID denotes one immutable version and links to its predecessor through supersedes_source_record_id. ImportJob uniquely links tenant/source ID and supplies raw job status. Document.source_record_id is the exact provenance filter. Existing shortest links are retained; no duplicate FKs or derived statuses.
