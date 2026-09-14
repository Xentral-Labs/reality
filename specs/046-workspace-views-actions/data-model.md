# Data Model: Workspace Views and Actions

This feature adds no PostgreSQL entities. It introduces validated, version-controlled application metadata.

## WorkspaceDefinition

- `key`: one of `company`, `operations`, `warehouse`, `finance`, `data`.
- `label`: canonical English workspace label.
- `view_keys`: ordered, non-duplicated ViewDefinition references.
- `action_keys`: ordered, non-duplicated ActionDefinition references.

Every key is unique, all five workspaces exist exactly once, and every reference resolves.

## ViewDefinition

- `key`: stable presentation identity.
- `label`: canonical Web noun.
- `route`: existing Product Web route.
- `kind`: `authoritative_register` or `materialized_projection`.
- `projection`: registered materialization name, required only for a materialized Projection.
- `description`: supporting business purpose.

Keys and route/label pairs are unique. Materialized references resolve in the Projection catalog; authoritative views do not claim Projection identity.

## ActionDefinition

- `key`: stable presentation identity.
- `label`: business verb phrase.
- `command`: existing Command catalog service key.
- `target_route`: canonical register opened after success.
- `confirmation`: `summary` or `server_preview`.
- `prerequisites`: stable empty-state hints.
- `result_kind`: existing Inspector kind when a single result is inspectable.

The command and route resolve, the command declares the Web adapter, every mutation has confirmation, and snapshot-sensitive correction uses `server_preview`.

## Runtime relationships

```text
WorkspaceDefinition -> ordered ViewDefinition and ActionDefinition references
ViewDefinition(materialized) -> Projection catalog materialization
ActionDefinition -> Command catalog service -> explicit API -> shared service -> Reality
```

These are metadata references, not foreign keys or tenant business records.
# Searchable Action Launcher Amendment

`Action definition` creates no tenant or business state. Workspace order determines both the first two directly visible actions and the complete launcher order; no second promotion classification is stored.
