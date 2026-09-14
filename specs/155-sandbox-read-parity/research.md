# Audit and design decisions

Decision: reuse get_tenant on business reads rather than broaden require_ordinary_workspace. Rationale: the latter is also used by mutation preparation and confirmation. No new authorization helper is needed.

Affected reads: Warehouse stock/reservations/movements; master-data customer/supplier/item/location registers and detail; master-data proposal detail; source systems and records; item CSV preview and original download.

Retained restrictions: master-data preparation/confirmation, CSV staging/preparation, delivery action preparation, source installation and writes, secrets/MCP credentials/provider execution, private quick lessons and not-ready/foreign Sandbox admission. These are not the business read regression. Existing shared-company authorization already admits normal routes for active practice companies.

Repository-wide audit covers require_ordinary_workspace, tenant.purpose/playground branches, require_business_operation and require_core_operation. Most remaining calls protect persistence or credentials. Tests and final review document any additional findings.

The merged main tree contained two spec154 directories. Rename the register-empty-state documentation to spec156 (spec155 is this fix); no runtime change. This resolves the inherited spec-policy failure without weakening the check.

Manual document correction snapshots and price-list reads use tenant-scoped reads without the ordinary-workspace guard; no change is needed there.
