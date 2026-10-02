# Data model

`subledger_account.default_destination_id`: nullable String; omitted when unset and loaded on demand. Null means
not selected. Non-null is the exact opaque ID previously held by finance_role_destination.
Unique tenant/marker key permits equal IDs across tenants. Partial unique tenant/role
key permits multiple non-default accounts but at most one selected account per role.
No additional table, business FK, Boolean, source pointer or JSON value is introduced.

Existing account columns, revisions, FinanceState and LedgerEntry references remain.
A default switch moves the marker under existing lock, clearing/flushing before setting.
Blocked selected accounts remain selected; the existing resolver refuses their use.

The four-column old relation is a read-only DISTINCT view over marked accounts. ORM
logical fields remain identical; no production mutation persists its mapped objects.
Migration locks, validates role agreement, copies and verifies exact mappings; rollback
restores frozen old DDL and original IDs before removing the marker.
