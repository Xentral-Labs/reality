# Plan

Constitution PASS: no schema, no new authority, no recomputation; the form keeps calling the canonical reference tools through the existing ChangeProposal path, tenant scope is enforced by the shared services, and tests precede implementation.

Layers: service (`reference_workspace.prepare_reference`, `reference_detail`) → adapter (`web/api.py` request model accepts typed JSON values) → web (`MasterDataCard.tsx`, `MasterDataPage.tsx`, localization). Domain services are untouched; `update_parties`, `update_items`, `update_locations` and their preview already accept every field.

Preparation gets a declarative field table per core family with normalisation rules (text, required text, choice, roles, currency, non-negative money, positive factor, non-negative count, flag, opaque reference). For updates the canonical record starts from the current editable values of the reviewed detail and overlays the request, so omitted fields are preserved and the stored intent is complete for review. Source identity is passed through; the shared source reference helper keeps the same SourceRecord when unchanged. Detail adds `payment_term_code`, `source_system` and `external_id` outside the revision snapshot.

Web: one field definition per family drives inputs, prefill, drafts and review labels; choices come from the existing `/suggestions/{kind}` endpoint. The register button becomes "Edit details".

Tests: service tests for full create/update per family, omitted-field preservation, role guard, invalid values, provenance behaviour and detail codes; API test for typed values; contract test for field coverage; browser script updated for the wider form. Rollback: revert the scoped commits; no data migration.
