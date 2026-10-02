# Data Model

`finance_reference_store`: tenant_id, id, kind, code varchar(200), name varchar(200), state, revision, nullable target_id/created_at/updated_at.

- Primary key (tenant_id,id,kind).
- Internal kinds cost_center/case_code/coding_group: target/timestamps NULL, code length <=100.
- External kinds account/tax_code: target/timestamps NOT NULL; FK (tenant,target) to accounting_target.
- State active/blocked; revision >0; nonempty trimmed code/name.
- Partial unique (tenant,id) separately for the internal and external kind sets.
- Partial unique internal (tenant,kind,code); external (tenant,target,kind,code).
- Unique (tenant,target,id,kind) supplies original external FK target.

Logical `finance_reference` exposes original seven columns, filtered to internal kinds with LOCAL CHECK OPTION. Logical `accounting_target_reference` exposes original ten columns, filtered to external kinds with LOCAL CHECK OPTION. No new public columns or internal timestamps.

Eight incoming FK constraints retain their original local tuple shapes: six tenant/id/kind relationships and two tenant/target/id/kind relationships. Their disjoint, constrained kind columns prohibit crossing catalog families.
