# Contract: Catalog Resources

Canonical files are `backend/config/command_catalog.yaml`,
`business_event_catalog.yaml`, `projection_catalog.yaml`, and `fact_catalog.yaml`.
Each has `version` and one category. The Command file owns parameter descriptions.
Consumers use the composed loader. It rejects missing categories, duplicates, invalid
cross-references, and implementation drift.

