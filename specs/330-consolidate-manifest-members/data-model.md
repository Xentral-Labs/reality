# Data Model: Receipt Manifest Members

## Physical store

`cost_manifest_member` has non-null String `tenant_id`, `member_family`, `id`, `manifest_id`; PK `(tenant_id, member_family, id)`; tenant FK and composite `(tenant_id, manifest_id)` FK to `cost_input_manifest`. All original ID and target types remain String with unchanged widths.

| Family (original logical name) | Required target column | Composite target FK |
| --- | --- | --- |
| cost_manifest_receipt | receipt_basis_id | cost_receipt_basis(tenant_id,id) |
| cost_manifest_component | component_basis_id | cost_component_basis(tenant_id,id) |
| cost_manifest_attribution | attribution_revision_id | cost_attribution_revision(tenant_id,id) |
| cost_manifest_correction | correction_basis_id | cost_correction_basis(tenant_id,id) |
| cost_manifest_replacement | replacement_id | cost_component_replacement(tenant_id,id) |

Each of the five target columns is nullable physically but a closed family CHECK requires the corresponding target and forbids the other four. Separate partial unique indexes enforce `(tenant_id, manifest_id, target_column)` per family. Original member PK identity is preserved within each family. Physical FK indexes lead with tenant and cover parent and target tuples, using existing index helper when possible; preserve practical original family-filtered manifest access paths.

## Logical resources

Each original view selects exactly its original columns from the shared store, filtered by its fixed family, WITH LOCAL CHECK OPTION. No family/routing column appears in the view. An INSTEAD OF INSERT trigger routes original columns and hidden family to the store and returns the inserted original values. Native updates/deletes preserve current behavior. Five ORM declarations retain their original columns and contract; view metadata depends on the physical table. Function/trigger creation and cleanup must work for full, repeated and selected metadata creation/drop.

## Authority and lifecycle

Keep all parent manifests, basis records, decisions, reviews, hashes and authorities unchanged. Receipt memberships have no new building/sealed admission or immutable-row guard. A manifest's recorded hash verifies its exact family-specific selected input IDs; physical member family is not part of historical digest serialization. No fields, timestamps or amount values are fabricated.

There are no incoming physical member FKs in the audited model; confirm in predecessor PostgreSQL before freezing migration. Populated per-family exact-column comparisons and exact original DDL rollback are mandatory.
