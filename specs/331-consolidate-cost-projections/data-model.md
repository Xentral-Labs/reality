# Data model: shared cost projections

Four physical tables replace thirteen output tables. All source, decision and input
entities retain their existing schema. The original thirteen names are logical writable
views, not stored data. The view layer preserves family grain for all SQL and ORM readers.

| Table | Families |
|---|---|
| cost_projection_generation | cost_inventory_generation, cost_contribution_generation, cost_generation, cost_company_generation |
| cost_projection_inventory | cost_inventory_snapshot, cost_inventory_row, cost_company_inventory_result |
| cost_projection_contribution | cost_contribution_snapshot, cost_contribution_row, cost_company_contribution_result |
| cost_projection_publication | cost_inventory_publication, cost_publication, cost_company_publication |

Each table is keyed by tenant_id, projection_family and original id. The family uses
the original logical name, retaining record-type namespaces without identity translation.
Family-specific numeric, timestamp, scope and input columns keep their original types.
Fields absent from a family are null and constrained to be absent. Required fields and
original checks apply conditionally to the matching family. Unknown is never coerced to zero.

Foreign keys targeting shared outputs include a typed family discriminator. External
input references retain composite tenant FKs. Partial indexes isolate family uniqueness;
publication FKs also include original review or scope identity. Views supply internal
family/link constants with defaults and WITH LOCAL CHECK OPTION, forbidding reassignment.

Lifecycle remains building → sealed for captured/company generations. Rows are admitted
only against the correct building parent and exact captured membership. Sealed identity
and results remain immutable. Publication requires a sealed matching scope. Inventory
and contribution preserve their existing completed-generation admission and service guards.
