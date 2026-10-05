# Compatibility and readiness

Status retains adopted=true and can_adopt=false; enabled is product policy, coverage_ready
means bounded historical scans completed and consumer caught up. migration_ready=false
and upgrade error explain missing schema. rollout_provenance=platform_version and
rollout_version=377 distinguish historical owner adoption. GET performs no backfill.
The deprecated adoption service remains owner-authenticated and confirmed; retries
acknowledge default policy without creating decisions or modifying historical adoption.
Selections are validated against same-company canonical records. Guard schema absence
fails explicitly with case_schema_not_ready rather than disabling case checks.

Status reads use existing tenant-surface access for owned sandbox companies. They
report can_control=false there; business-member control authority and private/archived
surface restrictions remain authoritative. Reading default policy grants no takeover rights.
