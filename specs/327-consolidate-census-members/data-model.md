# Data Model: Census Membership

## Retained entities and scope

Keep `cost_company_census` and all four original mapped classes. Add private physical
Table `cost_company_census_member` registered in Base metadata after original models,
before shared FK indexing. Mapped classes compile as four filtered exact-column views.

| Store field | Type / nullability | Meaning |
| --- | --- | --- |
| tenant_id, member_family, id | String, required | Family-qualified tenant/opaque PK |
| census_id | String, required | Original retained parent |
| observed_values | JSONB, required | Original lossless normalized captured observation |
| content_hash | String(64), required | Original retained member hash |
| movement_id / document_id / document_line_id / source_record_id | String, nullable individually | Exactly one family-selected real subject |
| document_member_id | String, line only, required for line | Original captured document within same census |
| interpretation_outcome_id | String, source only, nullable for source | Original optional outcome |
| document_member_identity | String, stored generated | id for document family, NULL otherwise |
| line_member_identity | String, stored generated | id for line family, NULL otherwise |

The two aliases expose existing IDs for old family-safe links; no received business
value or derived authority is created. They are never selected by logical interfaces.

## Keys, shape and relationships

- PK `(tenant_id,member_family,id)`. Closed non-null discriminator: movement/document/
  line/source. OR shape branches use explicit IS NULL/IS NOT NULL, so SQL UNKNOWN
  cannot admit missing required targets. Line requires document member; every other
  family prohibits it. Only source can have an outcome. Hash length stays 64.
- Four partial unique `(tenant_id,census_id,selected_subject)` keys preserve original
  family selection uniqueness. PK preserves old within-family tenant/id uniqueness.
- Ordinary UNIQUE `(tenant_id,census_id,document_member_identity)` and
  `(tenant_id,line_member_identity)` use default NULL-distinct semantics, not partial
  indexes and not NULLS NOT DISTINCT.
- Eight store FKs: tenant; tenant/census parent; four tenant-qualified real subject
  targets; tenant/outcome; self `(tenant_id,census_id,document_member_id)` to the
  document alias unique key. Default immediate/non-deferrable behavior stays original.
- Company contribution input retains `(tenant_id,census_line_id)` and points to
  `(tenant_id,line_member_identity)` in the backing store. No new consumer field.
- Preserve all FK actions and complete-key index coverage. Partial indexes do not
  count as unconditional lookup coverage. Parent lookup can use the document-alias
  unique key prefix; subject/outcome/self lookups need ordinary complete tuple indexes.

## Logical rows and hashes

Use captured original column order/sets, never SELECT *. Movement/document expose six
columns; line/source expose seven. Original observations and existing member/header
hash serializers remain untouched. Fixed-family INSERT routing returns only stored
original columns. Views do not expose discriminator, other-family NULLs or aliases.

## Lifecycle

Member writes: INSERT only while the same-tenant parent is building under FOR UPDATE;
UPDATE/DELETE always refused. Header building → sealed transition and sealed header
immutability remain original. Private backing BEFORE guard protects all physical
writes and uses only original ordinary fields, not generated aliases.

Store-owned function/trigger hooks create/drop with metadata and explicit dependencies;
header deployed guard/function is unchanged. Existing create_all does not install the
original header guard: metadata tests must distinguish that baseline from migrated
production-schema protection and cannot claim header parity from metadata alone.
Migration copying installs guards only after exact data/FK parity, before commit.

## Migration footprint

Four physical members → one store/four views. Actual predecessor schema and the incoming
company input FK name/action/indexes must be frozen from revision 0112. Downgrade restores
original tables and guards, including data captured after upgrade. No original column,
public discriminator, timestamp, digest, source amount or consumer row value changes.
