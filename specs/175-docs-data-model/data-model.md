# Documentation model

`dataModels[]`: key (actual table), name, bilingual purpose/example/notes/derived guidance, fields, action IDs.
`fields[]`: name, type, nullable, default {kind,value}, bilingual meaning, references {table,column}[] extracted from actual foreign keys.
Defaults distinguish none, scalar, generated callable and server expression. Examples contain only actual fields, with illustrative opaque links and decimal strings. Derived descriptions never become stored fields.
No persistence or state transition changes.

## ERP expansion

Each documentation object also has one `group` key and bilingual `groupLabel`. The five groups partition 35 covered records. Types/defaults/nullability remain generated from SQLAlchemy; business group membership is documentation-only. Unknown related keys and ungrouped records fail generation. No persistent business fields were added.
