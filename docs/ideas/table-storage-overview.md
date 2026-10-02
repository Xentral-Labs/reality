# Table storage overview and target structure

Date: 2026-10-02. Status: repository inventory and final assessment of five accepted consolidation slices.
Spec impact: none. This report documents existing model metadata, completed changes and future review candidates; it changes no behavior or schema.

## Result and scope

The five implemented changes remove **eighteen physical tables**. Integrated with main 0d485c12, SQLAlchemy metadata contains **150 physical tables and 25 compatibility views**, compared with 168 physical tables before these changes. Main added the independently reviewed `company_currency` table in spec 309. Earlier required PR checks passed; current-main revalidation is recorded in spec 327. This is a repository schema count, not a count of a running database, populated tables, or business objects. Alembic's migration bookkeeping is outside this application metadata count.

The original small Reality vocabulary remains the semantic core. Twelve business concepts do not imply twelve storage tables once exact received evidence, retained decisions, revisions, many-to-many relationships and execution history must be preserved. A generic Fact or Settings payload cannot replace those constraints merely by reducing the number of names.

| Accepted change | Original physical storage | Result | Net reduction |
| --- | --- | --- | --- |
| [331: cost projections](../../specs/331-consolidate-cost-projections/verification.md) | 13 cost output tables | 4 typed physical stores, 13 writable compatibility views | 9 |
| [332: default accounts](../../specs/332-integrate-account-defaults/verification.md) | `finance_role_destination` | Selection identity on existing `subledger_account`; read-only compatibility view | 1 |
| [324: Finance references](../../specs/324-consolidate-finance-references/verification.md) | `finance_reference`, `accounting_target_reference` | One `finance_reference_store`; two writable family-filtered views | 1 |
| [330: receipt manifest membership](../../specs/330-consolidate-manifest-members/verification.md) | Five receipt manifest member tables | One typed `cost_manifest_member` store; five writable exact-column views | 4 |
| [327: census membership](../../specs/327-consolidate-census-members/verification.md) | Four census member tables | One typed store; four exact-column guarded views | 3 |
| Total | 25 retired physical tables | 7 new physical stores; existing account storage reused | **18** |

These changes preserve opaque IDs, tenant scope, typed references, historical values and existing application interfaces. Populated upgrade/downgrade proofs and acceptance evidence are linked above. Spec 324 records composite backend acceptance of 5,343 passing cases and 10 existing skips, including the corrected static reporting audit and a separately passing benchmark; its historical full command itself had one static audit failure. No live migration or deployment is included. Historical logs predate this PR integration; the final PR checks verify the combined change.

## History: what can actually be attributed

The requested 34-day window starts around 2026-08-29. The current branch's reachable history begins with `3b7978c7`, the public release on 2026-09-14. Older August/September commits exist on other refs; their existence does not establish a before/after schema for this branch or prove that an addition was caused by Business Journey.

Parsing all Python database modules at the public baseline identifies 86 declared application tables. Of those, 83 remain physical and three are now compatibility views. The integrated model has 67 physical names absent from that baseline: 150 = 86 - 3 + 67. Seven of these are replacement stores introduced by these consolidations. Twenty-two later cost-output/member names are now views. There are no baseline names missing from both physical storage and compatibility views. This comparison establishes branch-baseline differences, not exact original creation dates or causal attribution to a Journey.

The Settings and mapping audits establish that the Finance catalogs, mappings, components, defaults and AI preferences already existed at that public baseline. They must not all be described as new Journey tables. Costing expanded after the baseline; `cost_policy_revision` entered the available branch history on September 20, dunning schedule rules on September 29, and item/location reorder rules on October 1. Exact earlier attribution requires comparing the appropriate earlier source lineage.

## Lean target structure

| Layer | Existing structure to reuse | Storage rule |
| --- | --- | --- |
| Received source | SourceRecord and existing source identities | Preserve external payloads losslessly; do not type every upstream field. |
| Evidence | Document/DocumentLine and received components | Store stated amounts and opaque evidence identity; do not add operational delivery or fulfillment state to documents. |
| Reality | Fact, Commitment, Reservation, Movement, LedgerEntry and true related identities | Keep observations separate from decisions. Use the shortest real relationship and tenant-qualified FKs. |
| Retained decisions | Existing mapping, assignment, policy and review revisions | Preserve confirmed revision, predecessor, exact snapshot and typed reference; consolidate only after proving common grain. |
| Catalogs and preferences | Shared Finance reference store; preferences on their actual owner | Reuse existing account/default storage. Extend existing tenant AI preference boundary only after another genuine preference use case is proven. |
| Derived outputs | Four cost projection stores and existing general projection storage | Share compatible output families while preserving captured generation, lifecycle and publication contracts. |
| Execution and security | Shared scheduled jobs, secrets, audit and source lifecycle | Reuse existing infrastructure; never hide permissions, claims, retries or secret references in ordinary Settings. |

## Retain now and review next

| Family | Current recommendation | Reason / next proof |
| --- | --- | --- |
| Source and target mapping revisions, cost policy revisions | Retain typed decision families | Different routing grains, current-selection keys and historical references. Two mapping families might save one table, but require a broad sparse union; lower priority. |
| Financial components and assignment revisions/parts | Retain | Common opaque component identity across document and line owners; exact assignments and multi-row allocation amounts need real FK targets. A replacement identity registry cancels the saving. |
| Accounting targets and Finance state | Retain | Identified external destination and mutation lock/revision are distinct authorities, not preferences. |
| Dunning rules and item/location reorder rules | Retain typed rules | Business logic acts on fees, days, quantities and location-specific grain. Facts do not represent selected rules. |
| AI settings | Retain current boundary | Replacing the only simple tenant preference table with one generic Settings table saves zero. Preserve secret FK and owner/redaction contracts if later generalized. |
| Remaining costing basis, census, captured membership and review tables | Retain pending a separate reviewed use case | The [costing audit](cost-storage-consolidation.md) led to spec 330 for receipt manifest membership. Other candidate families retain different incoming FKs and sealed lifecycle contracts. |
| Scheduling, source lifecycle, access/security, chat and onboarding | Retain in this assessment | Technical and lifecycle identities are not evidence that the Reality vocabulary is wrong. No safe further consolidation has been proven here. |
| Operational extensions: dunning, collections, returns, stock blocks and supply assignments | Retain pending separate domain review | A table-count audit alone does not prove equivalence to existing Commitment/Movement/Action. Any removal requires service/relationship/history analysis. |

The [census membership assessment](census-storage-consolidation.md) records spec 327: four member families share one store, saving three physical tables. Generated typed identities preserve both incoming links; physical admission protects immutable capture history. Populated PostgreSQL rollback and CI acceptance evidence are recorded in the specification. This report does not authorize a generic business-object registry, additional Settings table or further migration.

## Complete repository inventory

The following names are exhaustive for the metadata snapshot inspected on this date. “Added” means absent from the September 14 branch baseline; it does not mean caused by Business Journey. Keeping a name in this inventory is not an individual migration safety proof.

### Physical names absent from the branch baseline (67)

- `company_currency`
- `analysis_request`
- `collection_handover`
- `collection_handover_invoice`
- `cost_attribution_part`
- `cost_attribution_revision`
- `cost_captured_basis`
- `cost_captured_contribution_basis`
- `cost_captured_inventory_basis`
- `cost_commercial_direct_part`
- `cost_commercial_inventory_part`
- `cost_commercial_match_revision`
- `cost_company_census`
- `cost_company_census_member`
- `cost_company_contribution_input`
- `cost_company_inventory_input`
- `cost_company_manifest`
- `cost_component_basis`
- `cost_component_replacement`
- `cost_contribution_review`
- `cost_conversion_basis_revision`
- `cost_correction_basis`
- `cost_input_manifest`
- `cost_inventory_member`
- `cost_inventory_ownership_part`
- `cost_inventory_review`
- `cost_manifest_member`
- `cost_movement_basis`
- `cost_opening_basis`
- `cost_ownership_revision`
- `cost_policy_revision`
- `cost_projection_contribution`
- `cost_projection_generation`
- `cost_projection_inventory`
- `cost_projection_publication`
- `cost_receipt_basis`
- `cost_revenue_match_basis`
- `cost_scope_review`
- `cost_scope_review_category`
- `cost_selling_attribution_part`
- `cost_selling_review_category`
- `cost_selling_review_member`
- `cost_valuation_assessment_part`
- `cost_valuation_assessment_revision`
- `customer_exchange`
- `customer_item_number`
- `delivery_rule`
- `down_payment_offset`
- `dunning_notice`
- `dunning_notice_invoice`
- `dunning_schedule_level`
- `finance_reference_store`
- `interaction`
- `item_reorder_point`
- `journey_proposal`
- `journey_proposal_vote`
- `mcp_authorization_interaction`
- `mcp_client_grant`
- `mcp_user_credential`
- `party_email_address`
- `payment_return`
- `stock_block`
- `stock_block_resolution`
- `stock_count`
- `stock_count_line`
- `supply_assignment`
- `tenant_event_progress`

### Baseline physical names retained (83)

- `access_admission_counter`
- `access_application`
- `accounting_target`
- `action`
- `ai_settings`
- `analytics_report`
- `app_user`
- `business_event`
- `chat_message`
- `chat_session`
- `commitment`
- `commitment_hold`
- `commitment_revision`
- `company_invitation`
- `component_assignment_part`
- `component_assignment_revision`
- `demo_data_connection`
- `document`
- `document_line`
- `email_verification_code`
- `fact`
- `finance_state`
- `finance_target_mapping_revision`
- `financial_component`
- `handling_unit`
- `import_job`
- `interpretation_outcome`
- `interpretation_record_reference`
- `interpretation_rule`
- `invitation_delivery`
- `item`
- `ledger_entry`
- `ledger_reversal`
- `location`
- `lot`
- `mcp_access_token`
- `movement`
- `movement_correction`
- `opening_item_detail`
- `opening_scope`
- `ordinary_company_creation`
- `party`
- `party_group`
- `party_group_member`
- `party_group_price_list`
- `party_hold`
- `party_price_list`
- `party_role`
- `payment_term`
- `playground_run`
- `playground_step`
- `price_list`
- `price_list_entry`
- `projection_checkpoint`
- `projection_row`
- `reality_gap`
- `reality_gap_entry`
- `reservation`
- `return_announcement`
- `rule_interpretation_outcome`
- `scheduled_job`
- `scheduled_job_run`
- `secret`
- `secret_audit_event`
- `security_audit_event`
- `serial_unit`
- `settlement_allocation`
- `shipment`
- `shipment_event`
- `shipment_event_supersession`
- `shipment_package`
- `source_artifact`
- `source_capability`
- `source_classification_mapping_revision`
- `source_record`
- `source_stream`
- `source_system`
- `storyline_package`
- `storyline_trace_entry`
- `subledger_account`
- `tenant`
- `tenant_membership`
- `user_session`

### Compatibility views (25; no independent stored rows)

- `accounting_target_reference`
- `cost_company_census_document`
- `cost_company_census_line`
- `cost_company_census_movement`
- `cost_company_census_source`
- `cost_company_contribution_result`
- `cost_company_generation`
- `cost_company_inventory_result`
- `cost_company_publication`
- `cost_contribution_generation`
- `cost_contribution_row`
- `cost_contribution_snapshot`
- `cost_generation`
- `cost_inventory_generation`
- `cost_inventory_publication`
- `cost_inventory_row`
- `cost_inventory_snapshot`
- `cost_manifest_attribution`
- `cost_manifest_component`
- `cost_manifest_correction`
- `cost_manifest_receipt`
- `cost_manifest_replacement`
- `cost_publication`
- `finance_reference`
- `finance_role_destination`

## Reproduction and supporting audits

Inventory method: import `reality.db.core.Base` with an unused PostgreSQL URL (metadata registration only, no database connection), enumerate `Base.metadata.tables`, and classify a table as a logical compatibility view when `table.info["compatibility_view_sql"]` is present. Baseline method: read all `packages/reality-core/src/reality/db/*.py` files through `git show 3b7978c7:<path>` and collect literal `__tablename__` declarations and literal first arguments to `Table(...)` with Python AST. Reconcile retained, added, view and absent name sets as described above. This counts the working tree, including accepted migrations not yet deployed.

- [Settings assessment](settings-storage-consolidation.md): owner scopes, operational rules, default-account reuse and why a generic preference table presently saves zero.
- [Mapping/reference assessment](mapping-storage-consolidation.md): detailed retained grain and typed relationship constraints.
- [Data model](../DATA_MODEL.md) and [architecture](../ARCHITECTURE.md): implemented storage boundaries.

Validation: inventory set/count reconciliation and `make spec-check`; `git diff --check`. No new runtime behavior, catalog entry or generated documentation input was changed, so this report does not require another backend run or catalog regeneration.

## Subsequent costing audit

The [remaining costing assessment](cost-storage-consolidation.md) preserves the historical pre-manifest inventory of 47 physical cost tables. Its recommended five-to-one receipt-manifest member slice is now implemented in spec 330, saving four more physical tables. The earlier four slices reduced physical storage by fifteen; the historical pre-census costing inventory had 43 physical tables. The integrated model now has 40 physical cost tables; cumulative reduction is eighteen.

Historical local manifest acceptance (now spec 330): 5,383 unique backend cases passed with 10 skips (complete suite plus unchanged serial benchmark); docs/Web/catalog gates passed. The [verification record](../../specs/330-consolidate-manifest-members/verification.md) preserves frozen source hashes, prior failures and final logs. Historical inventory files remain dated snapshots rather than live-database counts.
