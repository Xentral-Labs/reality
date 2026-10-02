# Compatibility contract

Existing list_accounts, initialize_accounts, create_account, update_account,
set_default_account, resolve_account and transaction_matrix signatures/results remain.
Default selection still requires active same-role same-tenant account; no default and
blocked/wrong-role resolution retain existing error codes and messages. Finance revisions,
confirmation and event behavior remain. Selection does not increment account revision.

Historical invoices/payments/postings retain their original account IDs. Current default
reads cause no writes or initialization. Legacy SQL SELECT exposes the exact four old
columns/opaque values; INSERT/UPDATE/DELETE are explicitly unsupported on that relation.
Write interfaces are the existing shared confirmed application services.

PostgreSQL uniqueness protects tenant-local destination identity and role selection.
Cross-tenant identifiers cannot resolve or be selected through the service boundary.
No command, tool, report vocabulary or UI operation is introduced.
