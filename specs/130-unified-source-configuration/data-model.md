# Existing records only
SourceSystem: opaque id, tenant_id, normalized code, name, description, is_active.
SourceCapability: opaque id, tenant_id, source_system_id, source_type, target_type, is_active.
Existing integrations read adds interpreter_available and record counts. Browser stores only an unresolved action marker and its reviewed definition in sessionStorage by tenant. No database migration or operational record change.
