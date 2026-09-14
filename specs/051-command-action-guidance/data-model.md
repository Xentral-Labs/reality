# Data Model: Command Action Guidance

No persisted entity or migration is introduced.

## Command

- `service`: stable shared application-service name.
- `effect`: required non-empty canonical business explanation for a classified workspace Action.

## Composed Workspace Action

- Existing fields: `key`, `label`, `command`, `target_route`, `confirmation`, `prerequisites`, optional `result_kind`.
- Derived field: `description`, copied from the referenced Command effect during validation.
- Invariant: a classified Action cannot be composed when its Command effect is missing or blank.

## State transitions

None. This metadata does not alter business state or mutation lifecycle.
