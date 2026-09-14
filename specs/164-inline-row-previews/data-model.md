# Data Model: Inline Row Previews

No business or persistence entity is added or changed.

## Presentation state

- **Register identity**: current page/tab/filter context.
- **Record identity**: opaque ID of the expanded tenant-scoped record.
- **Preview kind**: existing Inspector record kind when applicable.
- **State**: collapsed, loading, loaded, or failed.
- **Disclosure control reference**: transient browser reference used to restore focus.

State transitions: `collapsed → loading → loaded | failed → collapsed`.

Opening a second record closes the prior record. Tenant, route, tab, page, search, family, and material-filter changes close stale state. Nothing is persisted.
