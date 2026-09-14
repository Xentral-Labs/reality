# Implementation Plan: Sandbox read parity

## Technical Context
Python/SQLAlchemy/PostgreSQL shared services and FastAPI adapters. Existing get_tenant validates identity without a purpose restriction. No dependencies or schema changes.
## Constitution Check
All principles PASS before and after design: existing authority and shortest links unchanged; no schema; tenant queries and HTTP owner/admission boundaries retained; tests precede changes; no browser rules; Decimal/UTC untouched; source values untouched.
## Design
Replace ordinary-workspace guards only in reference_register, reference_detail, reference_proposal, warehouse_register, source_metadata_page, preview_item_import and the original CSV download route with existing get_tenant. Preserve require_ordinary_workspace itself and every mutation caller. Preview parses existing evidence without persistence. Preserve private temporary lesson HTTP allowlist and privileged credential/provider settings.
## Test plan and implementation order
Service regressions first, then adapters. Create a real ready Sandbox through company setup, populate it through canonical services and assert stable results and expected stock quantities with a SQL observer rejecting writes. Cover all master families, warehouse views, sources, proposals, CSV preview/download and foreign identifiers. Extend authenticated practice-company HTTP tests across reads and ownership/lifecycle failures. Run full backend, lint and spec checks. No frontend changes; existing web gates are unaffected.
## Rollout and rollback
Apply only the reviewed patch to the active integration; rebuild and recreate API/MCP/background services with root .env. No migration. Confirm the real demo reads against deployed service functions and HTTP/browser where available. Preserve local files before applying; revert scoped code and rebuild for rollback.
## Risks
Do not weaken mutation checks by editing the shared guard globally. Do not allow a tenant-scoped ID to resolve foreign data. Download materialization is evidence retrieval, not business mutation. Existing spec154 numbering collision is inherited and recorded if spec-check reports it.
