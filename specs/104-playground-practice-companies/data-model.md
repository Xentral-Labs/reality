# Data Model
PlaygroundRun.sandbox_kind is non-null temporary|practice; old rows default temporary.
Only temporary active rows are unique per owner. Existing tenant/run uniqueness stays.
Tenant.name stores the label; no duplicate run name. Own-company Party gets that name
in atomic synthetic setup. Other entities and financial/goods facts remain unchanged.
