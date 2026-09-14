# Contract: Master Data Adapter Parity Proof

## Supported matrix

| Record family | Create | Update | Deactivate | Reactivate |
|---|---|---|---|---|
| Party | CLI, JSON API, Web | CLI, JSON API, Web | CLI, JSON API, Web | CLI, JSON API, Web |
| Item | CLI, JSON API, Web | CLI, JSON API, Web | CLI, JSON API, Web | CLI, JSON API, Web |
| Location | CLI, JSON API, Web | CLI, JSON API, Web | CLI, JSON API, Web | CLI, JSON API, Web |

The table represents 36 independently identified interface/operation/family cells.

## Adapter flow

```text
CLI command ───────────────┐
                           ├─> shared family service ─> PostgreSQL
Web action ─> JSON API ────┘
direct JSON API caller ────┘
```

Adapters may translate representations but may not persist directly or own business
normalization, validation, or lifecycle rules.

## Canonical success result

```text
family; scenario_alias; tenant_alias; business_fields; relationship_aliases;
roles; is_active; source_provenance?; historical_link_digest
```

Opaque IDs remain authoritative inside each tenant and become reviewed aliases only for
cross-run comparison. Generated times and presentation output are excluded.

## Failure result

```text
outcome: invalid | not_found
local_before == local_after
foreign_before == foreign_after
no_foreign_values_disclosed
```

Transport-specific status, exit code, and error display may differ.

## Product Web evidence

For each family, an executable structural contract inspects the actual register/modal
create and edit handlers plus lifecycle toggle, their real API-client method,
tenant-scoped HTTP route/body, and catch/error-rendering path. An unused helper does not
count. Backend HTTP/PostgreSQL parity proves resulting state and atomic rejection.

## Completion rule

Any missing cell/action, canonical difference, direct adapter persistence, partial
mutation, or foreign disclosure fails. Transport-only differences do not.
