"""Consolidate thirteen cost output tables without changing logical identities.

Frozen DDL and exact-value parity make this migration independent of live models.
Compatibility views preserve existing SQL and mapped interfaces.
"""

from alembic import op
from sqlalchemy import text

revision = "0117_cost_projections"
down_revision = "0116_company_currency"
branch_labels = None
depends_on = None

STORAGE = [
    "cost_projection_generation",
    "cost_projection_inventory",
    "cost_projection_contribution",
    "cost_projection_publication",
]

FAMILIES = {
    "cost_inventory_generation": "cost_projection_generation",
    "cost_contribution_generation": "cost_projection_generation",
    "cost_generation": "cost_projection_generation",
    "cost_company_generation": "cost_projection_generation",
    "cost_inventory_snapshot": "cost_projection_inventory",
    "cost_inventory_row": "cost_projection_inventory",
    "cost_company_inventory_result": "cost_projection_inventory",
    "cost_contribution_snapshot": "cost_projection_contribution",
    "cost_contribution_row": "cost_projection_contribution",
    "cost_company_contribution_result": "cost_projection_contribution",
    "cost_inventory_publication": "cost_projection_publication",
    "cost_publication": "cost_projection_publication",
    "cost_company_publication": "cost_projection_publication",
}

COLUMNS = {
    "cost_inventory_generation": (
        "review_id",
        "assessment_revision_id",
        "algorithm_version",
        "completed_at",
        "output_hash",
        "tenant_id",
        "id",
    ),
    "cost_contribution_generation": (
        "action_id",
        "algorithm_version",
        "completed_at",
        "output_hash",
        "tenant_id",
        "id",
    ),
    "cost_generation": (
        "captured_basis_id",
        "kind",
        "algorithm_version",
        "scope_key",
        "state",
        "completed_at",
        "inventory_count",
        "contribution_count",
        "output_hash",
        "tenant_id",
        "id",
    ),
    "cost_company_generation": (
        "manifest_id",
        "algorithm_bundle",
        "scope_key",
        "state",
        "expected_work_count",
        "completed_work_count",
        "inventory_count",
        "contribution_count",
        "inventory_content_hash",
        "contribution_content_hash",
        "started_at",
        "completed_at",
        "tenant_id",
        "id",
    ),
    "cost_inventory_snapshot": (
        "generation_id",
        "remaining_quantity",
        "acquisition_value",
        "carrying_value",
        "tenant_id",
        "id",
    ),
    "cost_inventory_row": (
        "generation_id",
        "inventory_basis_member_id",
        "state",
        "currency",
        "base_unit",
        "method",
        "owner_party_id",
        "remaining_quantity",
        "acquisition_value",
        "carrying_value",
        "tenant_id",
        "id",
    ),
    "cost_company_inventory_result": (
        "generation_id",
        "inventory_input_id",
        "inventory_generation_id",
        "state",
        "result_fingerprint",
        "tenant_id",
        "id",
    ),
    "cost_contribution_snapshot": (
        "generation_id",
        "review_id",
        "goods_cost",
        "known_direct_selling_cost",
        "known_allocated_selling_cost",
        "selling_complete",
        "tenant_id",
        "id",
    ),
    "cost_contribution_row": (
        "generation_id",
        "contribution_basis_member_id",
        "state",
        "currency",
        "base_unit",
        "revenue",
        "goods_cost",
        "direct_selling_cost",
        "allocated_selling_cost",
        "tenant_id",
        "id",
    ),
    "cost_company_contribution_result": (
        "generation_id",
        "contribution_input_id",
        "contribution_generation_id",
        "review_id",
        "db1_state",
        "db2_state",
        "result_fingerprint",
        "tenant_id",
        "id",
    ),
    "cost_inventory_publication": ("review_id", "generation_id", "tenant_id", "id"),
    "cost_publication": ("scope_key", "generation_id", "tenant_id", "id"),
    "cost_company_publication": (
        "scope_key",
        "generation_id",
        "updated_at",
        "tenant_id",
        "id",
    ),
}

DEFAULTS = {
    "cost_inventory_generation": {"projection_family": "cost_inventory_generation"},
    "cost_contribution_generation": {
        "projection_family": "cost_contribution_generation"
    },
    "cost_generation": {"projection_family": "cost_generation"},
    "cost_company_generation": {"projection_family": "cost_company_generation"},
    "cost_inventory_snapshot": {
        "projection_family": "cost_inventory_snapshot",
        "generation_id_family": "cost_inventory_generation",
    },
    "cost_inventory_row": {
        "projection_family": "cost_inventory_row",
        "generation_id_family": "cost_generation",
    },
    "cost_company_inventory_result": {
        "projection_family": "cost_company_inventory_result",
        "generation_id_family": "cost_company_generation",
        "inventory_generation_id_family": "cost_inventory_generation",
    },
    "cost_contribution_snapshot": {
        "projection_family": "cost_contribution_snapshot",
        "generation_id_family": "cost_contribution_generation",
    },
    "cost_contribution_row": {
        "projection_family": "cost_contribution_row",
        "generation_id_family": "cost_generation",
    },
    "cost_company_contribution_result": {
        "projection_family": "cost_company_contribution_result",
        "generation_id_family": "cost_company_generation",
        "contribution_generation_id_family": "cost_contribution_generation",
    },
    "cost_inventory_publication": {
        "projection_family": "cost_inventory_publication",
        "generation_id_family": "cost_inventory_generation",
    },
    "cost_publication": {
        "projection_family": "cost_publication",
        "generation_id_family": "cost_generation",
    },
    "cost_company_publication": {
        "projection_family": "cost_company_publication",
        "generation_id_family": "cost_company_generation",
    },
}

SHARED_DDL = [
    "\nCREATE TABLE cost_projection_generation (\n\treview_id VARCHAR, \n\tassessment_revision_id VARCHAR, \n\talgorithm_version VARCHAR, \n\tcompleted_at TIMESTAMP WITH TIME ZONE, \n\toutput_hash VARCHAR(64), \n\ttenant_id VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\taction_id VARCHAR, \n\tcaptured_basis_id VARCHAR, \n\tkind VARCHAR, \n\tscope_key VARCHAR(64), \n\tstate VARCHAR, \n\tinventory_count INTEGER, \n\tcontribution_count INTEGER, \n\tmanifest_id VARCHAR, \n\talgorithm_bundle VARCHAR, \n\texpected_work_count INTEGER, \n\tcompleted_work_count INTEGER, \n\tinventory_content_hash VARCHAR(64), \n\tcontribution_content_hash VARCHAR(64), \n\tstarted_at TIMESTAMP WITH TIME ZONE, \n\tprojection_family VARCHAR NOT NULL, \n\tPRIMARY KEY (tenant_id, projection_family, id), \n\tCONSTRAINT ck_cost_projection_generation_family CHECK (projection_family IN ('cost_inventory_generation', 'cost_contribution_generation', 'cost_generation', 'cost_company_generation')), \n\tCONSTRAINT ck_cost_inventory_generation_projection_shape CHECK (projection_family <> 'cost_inventory_generation' OR (review_id IS NOT NULL AND algorithm_version IS NOT NULL AND completed_at IS NOT NULL AND output_hash IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_inventory_generation' AND projection_family IS NOT NULL AND action_id IS NULL AND captured_basis_id IS NULL AND kind IS NULL AND scope_key IS NULL AND state IS NULL AND inventory_count IS NULL AND contribution_count IS NULL AND manifest_id IS NULL AND algorithm_bundle IS NULL AND expected_work_count IS NULL AND completed_work_count IS NULL AND inventory_content_hash IS NULL AND contribution_content_hash IS NULL AND started_at IS NULL)), \n\tCONSTRAINT ck_inventory_generation_version CHECK (projection_family <> 'cost_inventory_generation' OR (algorithm_version='inventory-v1' AND length(output_hash)=64)), \n\tCONSTRAINT fk_proj_d8276ca5d52663bc FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT fk_proj_7fcbd2a6e0f61923 FOREIGN KEY(tenant_id, assessment_revision_id) REFERENCES cost_valuation_assessment_revision (tenant_id, id), \n\tCONSTRAINT fk_proj_a00830367d714d17 FOREIGN KEY(tenant_id, review_id) REFERENCES cost_inventory_review (tenant_id, id), \n\tCONSTRAINT uq_proj_620f4a84fe2d2153 UNIQUE (tenant_id, projection_family, id), \n\tCONSTRAINT uq_proj_ee9e9070b90a9c93 UNIQUE (tenant_id, projection_family, review_id, id), \n\tCONSTRAINT ck_cost_contribution_generation_projection_shape CHECK (projection_family <> 'cost_contribution_generation' OR (action_id IS NOT NULL AND algorithm_version IS NOT NULL AND completed_at IS NOT NULL AND output_hash IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_contribution_generation' AND projection_family IS NOT NULL AND review_id IS NULL AND assessment_revision_id IS NULL AND captured_basis_id IS NULL AND kind IS NULL AND scope_key IS NULL AND state IS NULL AND inventory_count IS NULL AND contribution_count IS NULL AND manifest_id IS NULL AND algorithm_bundle IS NULL AND expected_work_count IS NULL AND completed_work_count IS NULL AND inventory_content_hash IS NULL AND contribution_content_hash IS NULL AND started_at IS NULL)), \n\tCONSTRAINT ck_contribution_generation_version CHECK (projection_family <> 'cost_contribution_generation' OR (algorithm_version='commercial-v1' AND length(output_hash)=64)), \n\tCONSTRAINT fk_proj_8705ae2d4d3a10ff FOREIGN KEY(tenant_id, action_id) REFERENCES action (tenant_id, id), \n\tCONSTRAINT ck_cost_generation_projection_shape CHECK (projection_family <> 'cost_generation' OR (captured_basis_id IS NOT NULL AND kind IS NOT NULL AND algorithm_version IS NOT NULL AND scope_key IS NOT NULL AND state IS NOT NULL AND inventory_count IS NOT NULL AND contribution_count IS NOT NULL AND output_hash IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_generation' AND projection_family IS NOT NULL AND review_id IS NULL AND assessment_revision_id IS NULL AND action_id IS NULL AND manifest_id IS NULL AND algorithm_bundle IS NULL AND expected_work_count IS NULL AND completed_work_count IS NULL AND inventory_content_hash IS NULL AND contribution_content_hash IS NULL AND started_at IS NULL)), \n\tCONSTRAINT ck_cost_generation_counts CHECK (projection_family <> 'cost_generation' OR (inventory_count>=0 AND contribution_count>=0 AND inventory_count+contribution_count<=10)), \n\tCONSTRAINT ck_cost_generation_state CHECK (projection_family <> 'cost_generation' OR (state IN ('building','sealed') AND ((state='sealed') = (completed_at IS NOT NULL)))), \n\tCONSTRAINT ck_cost_generation_version CHECK (projection_family <> 'cost_generation' OR (kind='captured_review_selection_v1' AND algorithm_version='captured-report-v1' AND length(scope_key)=64 AND length(output_hash)=64)), \n\tCONSTRAINT fk_proj_0c0ab681b88cacc2 FOREIGN KEY(tenant_id, captured_basis_id) REFERENCES cost_captured_basis (tenant_id, id), \n\tCONSTRAINT uq_proj_7f6d90c7ceec7d61 UNIQUE (tenant_id, projection_family, scope_key, id), \n\tCONSTRAINT ck_cost_company_generation_projection_shape CHECK (projection_family <> 'cost_company_generation' OR (manifest_id IS NOT NULL AND algorithm_bundle IS NOT NULL AND scope_key IS NOT NULL AND state IS NOT NULL AND expected_work_count IS NOT NULL AND completed_work_count IS NOT NULL AND inventory_count IS NOT NULL AND contribution_count IS NOT NULL AND inventory_content_hash IS NOT NULL AND contribution_content_hash IS NOT NULL AND started_at IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_company_generation' AND projection_family IS NOT NULL AND review_id IS NULL AND assessment_revision_id IS NULL AND algorithm_version IS NULL AND output_hash IS NULL AND action_id IS NULL AND captured_basis_id IS NULL AND kind IS NULL)), \n\tCONSTRAINT ck_company_generation_counts CHECK (projection_family <> 'cost_company_generation' OR (expected_work_count>=0 AND completed_work_count>=0 AND completed_work_count<=expected_work_count AND inventory_count>=0 AND contribution_count>=0)), \n\tCONSTRAINT ck_company_generation_hashes CHECK (projection_family <> 'cost_company_generation' OR (length(scope_key)=64 AND length(inventory_content_hash)=64 AND length(contribution_content_hash)=64)), \n\tCONSTRAINT ck_company_generation_state CHECK (projection_family <> 'cost_company_generation' OR (state IN ('building','sealed') AND ((state='sealed') = (completed_at IS NOT NULL)))), \n\tCONSTRAINT fk_proj_e4071d410e4eeed6 FOREIGN KEY(tenant_id, manifest_id) REFERENCES cost_company_manifest (tenant_id, id)\n)\n\n",
    "\nCREATE TABLE cost_projection_inventory (\n\tgeneration_id VARCHAR, \n\tremaining_quantity NUMERIC(18, 4), \n\tacquisition_value NUMERIC(18, 4), \n\tcarrying_value NUMERIC(18, 4), \n\ttenant_id VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\tinventory_basis_member_id VARCHAR, \n\tstate VARCHAR, \n\tcurrency VARCHAR, \n\tbase_unit VARCHAR, \n\tmethod VARCHAR, \n\towner_party_id VARCHAR, \n\tinventory_input_id VARCHAR, \n\tinventory_generation_id VARCHAR, \n\tresult_fingerprint VARCHAR(64), \n\tprojection_family VARCHAR NOT NULL, \n\tgeneration_id_family VARCHAR, \n\tinventory_generation_id_family VARCHAR, \n\tPRIMARY KEY (tenant_id, projection_family, id), \n\tCONSTRAINT ck_cost_projection_inventory_family CHECK (projection_family IN ('cost_inventory_snapshot', 'cost_inventory_row', 'cost_company_inventory_result')), \n\tCONSTRAINT ck_cost_inventory_snapshot_projection_shape CHECK (projection_family <> 'cost_inventory_snapshot' OR (generation_id IS NOT NULL AND remaining_quantity IS NOT NULL AND acquisition_value IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_inventory_snapshot' AND generation_id_family = 'cost_inventory_generation' AND projection_family IS NOT NULL AND generation_id_family IS NOT NULL AND inventory_basis_member_id IS NULL AND state IS NULL AND currency IS NULL AND base_unit IS NULL AND method IS NULL AND owner_party_id IS NULL AND inventory_input_id IS NULL AND inventory_generation_id IS NULL AND result_fingerprint IS NULL AND inventory_generation_id_family IS NULL)), \n\tCONSTRAINT ck_inventory_snapshot_amounts CHECK (projection_family <> 'cost_inventory_snapshot' OR (remaining_quantity>=0 AND acquisition_value>=0 AND (carrying_value IS NULL OR (carrying_value>=0 AND carrying_value<=acquisition_value)))), \n\tCONSTRAINT fk_proj_26d5f76ecf4a6160 FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT fk_proj_a6fa4e90d23ca47d FOREIGN KEY(tenant_id, generation_id_family, generation_id) REFERENCES cost_projection_generation (tenant_id, projection_family, id), \n\tCONSTRAINT uq_proj_3548b445df33884a UNIQUE (tenant_id, projection_family, id), \n\tCONSTRAINT ck_cost_inventory_row_projection_shape CHECK (projection_family <> 'cost_inventory_row' OR (generation_id IS NOT NULL AND inventory_basis_member_id IS NOT NULL AND state IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_inventory_row' AND generation_id_family = 'cost_generation' AND projection_family IS NOT NULL AND generation_id_family IS NOT NULL AND inventory_input_id IS NULL AND inventory_generation_id IS NULL AND result_fingerprint IS NULL AND inventory_generation_id_family IS NULL)), \n\tCONSTRAINT ck_cost_inventory_row_amounts CHECK (projection_family <> 'cost_inventory_row' OR (remaining_quantity>=0 AND acquisition_value>=0 AND carrying_value>=0 AND carrying_value<=acquisition_value)), \n\tCONSTRAINT ck_cost_inventory_row_shape CHECK (projection_family <> 'cost_inventory_row' OR ((state='available_at_capture' AND currency IS NOT NULL AND base_unit IS NOT NULL AND method IS NOT NULL AND owner_party_id IS NOT NULL AND remaining_quantity IS NOT NULL AND acquisition_value IS NOT NULL) OR (state='unknown_at_capture' AND currency IS NULL AND base_unit IS NULL AND method IS NULL AND owner_party_id IS NULL AND remaining_quantity IS NULL AND acquisition_value IS NULL AND carrying_value IS NULL))), \n\tCONSTRAINT fk_proj_cbffd2e2019d2c06 FOREIGN KEY(tenant_id, inventory_basis_member_id) REFERENCES cost_captured_inventory_basis (tenant_id, id), \n\tCONSTRAINT fk_proj_62f886adfcb59458 FOREIGN KEY(tenant_id, owner_party_id) REFERENCES party (tenant_id, id), \n\tCONSTRAINT ck_cost_company_inventory_result_projection_shape CHECK (projection_family <> 'cost_company_inventory_result' OR (generation_id IS NOT NULL AND inventory_input_id IS NOT NULL AND state IS NOT NULL AND result_fingerprint IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_company_inventory_result' AND inventory_generation_id_family = 'cost_inventory_generation' AND generation_id_family = 'cost_company_generation' AND projection_family IS NOT NULL AND inventory_generation_id_family IS NOT NULL AND generation_id_family IS NOT NULL AND remaining_quantity IS NULL AND acquisition_value IS NULL AND carrying_value IS NULL AND inventory_basis_member_id IS NULL AND currency IS NULL AND base_unit IS NULL AND method IS NULL AND owner_party_id IS NULL)), \n\tCONSTRAINT ck_company_inventory_result_shape CHECK (projection_family <> 'cost_company_inventory_result' OR (state IN ('known','unknown') AND ((state='known') = (inventory_generation_id IS NOT NULL)) AND length(result_fingerprint)=64)), \n\tCONSTRAINT fk_proj_90bfd8c644f5d5ec FOREIGN KEY(tenant_id, inventory_input_id) REFERENCES cost_company_inventory_input (tenant_id, id), \n\tCONSTRAINT fk_proj_8412ef294c421ea9 FOREIGN KEY(tenant_id, inventory_generation_id_family, inventory_generation_id) REFERENCES cost_projection_generation (tenant_id, projection_family, id)\n)\n\n",
    "\nCREATE TABLE cost_projection_publication (\n\treview_id VARCHAR, \n\tgeneration_id VARCHAR, \n\ttenant_id VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\tscope_key VARCHAR(64), \n\tupdated_at TIMESTAMP WITH TIME ZONE, \n\tprojection_family VARCHAR NOT NULL, \n\tgeneration_id_family VARCHAR, \n\tPRIMARY KEY (tenant_id, projection_family, id), \n\tCONSTRAINT ck_cost_projection_publication_family CHECK (projection_family IN ('cost_inventory_publication', 'cost_publication', 'cost_company_publication')), \n\tCONSTRAINT ck_cost_inventory_publication_projection_shape CHECK (projection_family <> 'cost_inventory_publication' OR (review_id IS NOT NULL AND generation_id IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_inventory_publication' AND generation_id_family = 'cost_inventory_generation' AND projection_family IS NOT NULL AND generation_id_family IS NOT NULL AND scope_key IS NULL AND updated_at IS NULL)), \n\tCONSTRAINT fk_proj_f192b52e87f88512 FOREIGN KEY(tenant_id, generation_id_family, review_id, generation_id) REFERENCES cost_projection_generation (tenant_id, projection_family, review_id, id), \n\tCONSTRAINT fk_proj_c9737e91a331431d FOREIGN KEY(tenant_id, review_id) REFERENCES cost_inventory_review (tenant_id, id), \n\tCONSTRAINT fk_proj_e5194c9c0290ce32 FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT uq_proj_08fa86b60a94e302 UNIQUE (tenant_id, projection_family, id), \n\tCONSTRAINT ck_cost_publication_projection_shape CHECK (projection_family <> 'cost_publication' OR (scope_key IS NOT NULL AND generation_id IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_publication' AND generation_id_family = 'cost_generation' AND projection_family IS NOT NULL AND generation_id_family IS NOT NULL AND review_id IS NULL AND updated_at IS NULL)), \n\tCONSTRAINT fk_proj_337739278440c90e FOREIGN KEY(tenant_id, generation_id_family, scope_key, generation_id) REFERENCES cost_projection_generation (tenant_id, projection_family, scope_key, id), \n\tCONSTRAINT ck_cost_company_publication_projection_shape CHECK (projection_family <> 'cost_company_publication' OR (scope_key IS NOT NULL AND generation_id IS NOT NULL AND updated_at IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_company_publication' AND generation_id_family = 'cost_company_generation' AND projection_family IS NOT NULL AND generation_id_family IS NOT NULL AND review_id IS NULL))\n)\n\n",
    "\nCREATE TABLE cost_projection_contribution (\n\tgeneration_id VARCHAR, \n\treview_id VARCHAR, \n\tgoods_cost NUMERIC(18, 4), \n\tknown_direct_selling_cost NUMERIC(18, 4), \n\tknown_allocated_selling_cost NUMERIC(18, 4), \n\tselling_complete BOOLEAN, \n\ttenant_id VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\tcontribution_basis_member_id VARCHAR, \n\tstate VARCHAR, \n\tcurrency VARCHAR, \n\tbase_unit VARCHAR, \n\trevenue NUMERIC(18, 4), \n\tdirect_selling_cost NUMERIC(18, 4), \n\tallocated_selling_cost NUMERIC(18, 4), \n\tcontribution_input_id VARCHAR, \n\tcontribution_generation_id VARCHAR, \n\tdb1_state VARCHAR, \n\tdb2_state VARCHAR, \n\tresult_fingerprint VARCHAR(64), \n\tprojection_family VARCHAR NOT NULL, \n\tgeneration_id_family VARCHAR, \n\tcontribution_generation_id_family VARCHAR, \n\tPRIMARY KEY (tenant_id, projection_family, id), \n\tCONSTRAINT ck_cost_projection_contribution_family CHECK (projection_family IN ('cost_contribution_snapshot', 'cost_contribution_row', 'cost_company_contribution_result')), \n\tCONSTRAINT ck_cost_contribution_snapshot_projection_shape CHECK (projection_family <> 'cost_contribution_snapshot' OR (generation_id IS NOT NULL AND review_id IS NOT NULL AND goods_cost IS NOT NULL AND selling_complete IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_contribution_snapshot' AND generation_id_family = 'cost_contribution_generation' AND projection_family IS NOT NULL AND generation_id_family IS NOT NULL AND contribution_basis_member_id IS NULL AND state IS NULL AND currency IS NULL AND base_unit IS NULL AND revenue IS NULL AND direct_selling_cost IS NULL AND allocated_selling_cost IS NULL AND contribution_input_id IS NULL AND contribution_generation_id IS NULL AND db1_state IS NULL AND db2_state IS NULL AND result_fingerprint IS NULL AND contribution_generation_id_family IS NULL)), \n\tCONSTRAINT ck_contribution_snapshot_goods CHECK (projection_family <> 'cost_contribution_snapshot' OR (goods_cost>=0)), \n\tCONSTRAINT ck_contribution_snapshot_selling CHECK (projection_family <> 'cost_contribution_snapshot' OR ((known_direct_selling_cost IS NULL) = (known_allocated_selling_cost IS NULL) AND (NOT selling_complete OR known_direct_selling_cost IS NOT NULL))), \n\tCONSTRAINT fk_proj_47aec83d0f934044 FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT fk_proj_4bed6f9db3cea5ee FOREIGN KEY(tenant_id, generation_id_family, generation_id) REFERENCES cost_projection_generation (tenant_id, projection_family, id), \n\tCONSTRAINT fk_proj_c4652d80b61c6c14 FOREIGN KEY(tenant_id, review_id) REFERENCES cost_contribution_review (tenant_id, id), \n\tCONSTRAINT uq_proj_ba04d2e969fa09a6 UNIQUE (tenant_id, projection_family, id), \n\tCONSTRAINT ck_cost_contribution_row_projection_shape CHECK (projection_family <> 'cost_contribution_row' OR (generation_id IS NOT NULL AND contribution_basis_member_id IS NOT NULL AND state IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_contribution_row' AND generation_id_family = 'cost_generation' AND projection_family IS NOT NULL AND generation_id_family IS NOT NULL AND review_id IS NULL AND known_direct_selling_cost IS NULL AND known_allocated_selling_cost IS NULL AND selling_complete IS NULL AND contribution_input_id IS NULL AND contribution_generation_id IS NULL AND db1_state IS NULL AND db2_state IS NULL AND result_fingerprint IS NULL AND contribution_generation_id_family IS NULL)), \n\tCONSTRAINT ck_cost_contribution_row_goods CHECK (projection_family <> 'cost_contribution_row' OR (goods_cost>=0)), \n\tCONSTRAINT ck_cost_contribution_row_shape CHECK (projection_family <> 'cost_contribution_row' OR ((state='available_at_capture' AND currency IS NOT NULL AND base_unit IS NOT NULL AND revenue IS NOT NULL AND goods_cost IS NOT NULL) OR (state='unknown_at_capture' AND currency IS NULL AND base_unit IS NULL AND revenue IS NULL AND goods_cost IS NULL AND direct_selling_cost IS NULL AND allocated_selling_cost IS NULL))), \n\tCONSTRAINT fk_proj_d164495655efd5ed FOREIGN KEY(tenant_id, contribution_basis_member_id) REFERENCES cost_captured_contribution_basis (tenant_id, id), \n\tCONSTRAINT ck_cost_company_contribution_result_projection_shape CHECK (projection_family <> 'cost_company_contribution_result' OR (generation_id IS NOT NULL AND contribution_input_id IS NOT NULL AND db1_state IS NOT NULL AND db2_state IS NOT NULL AND result_fingerprint IS NOT NULL AND tenant_id IS NOT NULL AND id IS NOT NULL AND projection_family = 'cost_company_contribution_result' AND generation_id_family = 'cost_company_generation' AND contribution_generation_id_family = 'cost_contribution_generation' AND projection_family IS NOT NULL AND generation_id_family IS NOT NULL AND contribution_generation_id_family IS NOT NULL AND goods_cost IS NULL AND known_direct_selling_cost IS NULL AND known_allocated_selling_cost IS NULL AND selling_complete IS NULL AND contribution_basis_member_id IS NULL AND state IS NULL AND currency IS NULL AND base_unit IS NULL AND revenue IS NULL AND direct_selling_cost IS NULL AND allocated_selling_cost IS NULL)), \n\tCONSTRAINT ck_company_contribution_result_shape CHECK (projection_family <> 'cost_company_contribution_result' OR (db1_state IN ('known','unknown') AND db2_state IN ('known','unknown') AND NOT (db2_state='known' AND db1_state='unknown') AND ((db1_state='known') = (contribution_generation_id IS NOT NULL AND review_id IS NOT NULL)) AND length(result_fingerprint)=64)), \n\tCONSTRAINT fk_proj_277f4e517a19201c FOREIGN KEY(tenant_id, contribution_input_id) REFERENCES cost_company_contribution_input (tenant_id, id), \n\tCONSTRAINT fk_proj_20bd34ed94b5019d FOREIGN KEY(tenant_id, contribution_generation_id_family, contribution_generation_id) REFERENCES cost_projection_generation (tenant_id, projection_family, id)\n)\n\n",
    "CREATE INDEX ix_cost_projection_generation_assessment_revision_id ON cost_projection_generation (tenant_id, assessment_revision_id)",
    "CREATE INDEX ix_proj_899488f2055b5d84 ON cost_projection_generation (tenant_id, captured_basis_id) WHERE projection_family = 'cost_generation'",
    "CREATE INDEX ix_proj_8c9f2278c89d62a0 ON cost_projection_generation (tenant_id, manifest_id) WHERE projection_family = 'cost_company_generation'",
    "CREATE UNIQUE INDEX uq_proj_3e7420f74a9faf96 ON cost_projection_generation (tenant_id, action_id, algorithm_version) WHERE projection_family = 'cost_contribution_generation'",
    "CREATE UNIQUE INDEX uq_proj_463bb8a7e0f8106f ON cost_projection_generation (tenant_id, review_id, id) WHERE projection_family = 'cost_inventory_generation'",
    "CREATE UNIQUE INDEX uq_proj_969eb8bfdc822b6d ON cost_projection_generation (tenant_id, manifest_id, algorithm_bundle) WHERE projection_family = 'cost_company_generation'",
    "CREATE UNIQUE INDEX uq_proj_9f5ceeb7aed31c97 ON cost_projection_generation (tenant_id, scope_key, id) WHERE projection_family = 'cost_generation'",
    "CREATE UNIQUE INDEX uq_proj_b8ff221b01735d30 ON cost_projection_generation (tenant_id, scope_key, id) WHERE projection_family = 'cost_company_generation'",
    "CREATE UNIQUE INDEX uq_proj_e7c8a95b2e9e4613 ON cost_projection_generation (tenant_id, captured_basis_id, algorithm_version) WHERE projection_family = 'cost_generation'",
    "CREATE UNIQUE INDEX uq_proj_fe53f946c7a13eee ON cost_projection_generation (tenant_id, review_id, assessment_revision_id, algorithm_version) NULLS NOT DISTINCT WHERE projection_family = 'cost_inventory_generation'",
    "CREATE INDEX ix_cost_projection_inventory_generation_id_family_generation_id ON cost_projection_inventory (tenant_id, generation_id_family, generation_id)",
    "CREATE INDEX ix_cost_projection_inventory_inventory_basis_member_id ON cost_projection_inventory (tenant_id, inventory_basis_member_id)",
    "CREATE INDEX ix_cost_projection_inventory_inventory_generation_id_f_45a6a182 ON cost_projection_inventory (tenant_id, inventory_generation_id_family, inventory_generation_id)",
    "CREATE INDEX ix_cost_projection_inventory_inventory_input_id ON cost_projection_inventory (tenant_id, inventory_input_id)",
    "CREATE INDEX ix_cost_projection_inventory_owner_party_id ON cost_projection_inventory (tenant_id, owner_party_id)",
    "CREATE INDEX ix_proj_7f289483720ba048 ON cost_projection_inventory (tenant_id, generation_id, currency, base_unit, method, owner_party_id) WHERE projection_family = 'cost_inventory_row'",
    "CREATE INDEX ix_proj_bad991fbb69ef82b ON cost_projection_inventory (tenant_id, generation_id) WHERE projection_family = 'cost_inventory_row'",
    "CREATE INDEX ix_proj_ed85938b6d9e9810 ON cost_projection_inventory (tenant_id, generation_id) WHERE projection_family = 'cost_company_inventory_result'",
    "CREATE UNIQUE INDEX uq_proj_0ac95927848188c2 ON cost_projection_inventory (tenant_id, generation_id, inventory_input_id) WHERE projection_family = 'cost_company_inventory_result'",
    "CREATE UNIQUE INDEX uq_proj_0f000823b23b09d7 ON cost_projection_inventory (tenant_id, generation_id) WHERE projection_family = 'cost_inventory_snapshot'",
    "CREATE UNIQUE INDEX uq_proj_c35212bbebd12580 ON cost_projection_inventory (tenant_id, generation_id, inventory_basis_member_id) WHERE projection_family = 'cost_inventory_row'",
    "CREATE INDEX ix_cost_projection_publication_generation_id_family_re_96a94ad4 ON cost_projection_publication (tenant_id, generation_id_family, review_id, generation_id)",
    "CREATE INDEX ix_cost_projection_publication_generation_id_family_sc_95974279 ON cost_projection_publication (tenant_id, generation_id_family, scope_key, generation_id)",
    "CREATE INDEX ix_proj_5c3a16693d26c9d3 ON cost_projection_publication (tenant_id, generation_id) WHERE projection_family = 'cost_company_publication'",
    "CREATE INDEX ix_proj_b76a1d4f5fadf1de ON cost_projection_publication (tenant_id, generation_id) WHERE projection_family = 'cost_publication'",
    "CREATE UNIQUE INDEX uq_proj_5a0219fa674a7788 ON cost_projection_publication (tenant_id, scope_key) WHERE projection_family = 'cost_publication'",
    "CREATE UNIQUE INDEX uq_proj_6e0607d7626721c4 ON cost_projection_publication (tenant_id, scope_key) WHERE projection_family = 'cost_company_publication'",
    "CREATE UNIQUE INDEX uq_proj_7ef5bd307d1f931d ON cost_projection_publication (tenant_id, review_id) WHERE projection_family = 'cost_inventory_publication'",
    "CREATE INDEX ix_cost_projection_contribution_contribution_basis_member_id ON cost_projection_contribution (tenant_id, contribution_basis_member_id)",
    "CREATE INDEX ix_cost_projection_contribution_contribution_generatio_2bc9a1e9 ON cost_projection_contribution (tenant_id, contribution_generation_id_family, contribution_generation_id)",
    "CREATE INDEX ix_cost_projection_contribution_contribution_input_id ON cost_projection_contribution (tenant_id, contribution_input_id)",
    "CREATE INDEX ix_cost_projection_contribution_generation_id_family_g_b91e9488 ON cost_projection_contribution (tenant_id, generation_id_family, generation_id)",
    "CREATE INDEX ix_cost_projection_contribution_review_id ON cost_projection_contribution (tenant_id, review_id)",
    "CREATE INDEX ix_proj_24ef9b91acf308a8 ON cost_projection_contribution (tenant_id, generation_id) WHERE projection_family = 'cost_company_contribution_result'",
    "CREATE INDEX ix_proj_37ddabc6d149f219 ON cost_projection_contribution (tenant_id, generation_id) WHERE projection_family = 'cost_contribution_row'",
    "CREATE INDEX ix_proj_d99f535d7616c145 ON cost_projection_contribution (tenant_id, generation_id, currency, base_unit) WHERE projection_family = 'cost_contribution_row'",
    "CREATE UNIQUE INDEX uq_proj_3efbfc4ee9f38d01 ON cost_projection_contribution (tenant_id, generation_id, contribution_input_id) WHERE projection_family = 'cost_company_contribution_result'",
    "CREATE UNIQUE INDEX uq_proj_4c455bf081834837 ON cost_projection_contribution (tenant_id, generation_id, contribution_basis_member_id) WHERE projection_family = 'cost_contribution_row'",
    "CREATE UNIQUE INDEX uq_proj_fe45878a7ac98741 ON cost_projection_contribution (tenant_id, generation_id, review_id) WHERE projection_family = 'cost_contribution_snapshot'",
]

VIEW_DDL = [
    "CREATE VIEW cost_inventory_generation AS SELECT review_id, assessment_revision_id, algorithm_version, completed_at, output_hash, tenant_id, id, projection_family FROM cost_projection_generation WHERE projection_family = 'cost_inventory_generation' WITH LOCAL CHECK OPTION; ALTER VIEW cost_inventory_generation ALTER COLUMN projection_family SET DEFAULT 'cost_inventory_generation'",
    "CREATE VIEW cost_contribution_generation AS SELECT action_id, algorithm_version, completed_at, output_hash, tenant_id, id, projection_family FROM cost_projection_generation WHERE projection_family = 'cost_contribution_generation' WITH LOCAL CHECK OPTION; ALTER VIEW cost_contribution_generation ALTER COLUMN projection_family SET DEFAULT 'cost_contribution_generation'",
    "CREATE VIEW cost_generation AS SELECT captured_basis_id, kind, algorithm_version, scope_key, state, completed_at, inventory_count, contribution_count, output_hash, tenant_id, id, projection_family FROM cost_projection_generation WHERE projection_family = 'cost_generation' WITH LOCAL CHECK OPTION; ALTER VIEW cost_generation ALTER COLUMN projection_family SET DEFAULT 'cost_generation'",
    "CREATE VIEW cost_company_generation AS SELECT manifest_id, algorithm_bundle, scope_key, state, expected_work_count, completed_work_count, inventory_count, contribution_count, inventory_content_hash, contribution_content_hash, started_at, completed_at, tenant_id, id, projection_family FROM cost_projection_generation WHERE projection_family = 'cost_company_generation' WITH LOCAL CHECK OPTION; ALTER VIEW cost_company_generation ALTER COLUMN projection_family SET DEFAULT 'cost_company_generation'",
    "CREATE VIEW cost_inventory_snapshot AS SELECT generation_id, remaining_quantity, acquisition_value, carrying_value, tenant_id, id, projection_family, generation_id_family FROM cost_projection_inventory WHERE projection_family = 'cost_inventory_snapshot' WITH LOCAL CHECK OPTION; ALTER VIEW cost_inventory_snapshot ALTER COLUMN projection_family SET DEFAULT 'cost_inventory_snapshot'; ALTER VIEW cost_inventory_snapshot ALTER COLUMN generation_id_family SET DEFAULT 'cost_inventory_generation'",
    "CREATE VIEW cost_inventory_row AS SELECT generation_id, inventory_basis_member_id, state, currency, base_unit, method, owner_party_id, remaining_quantity, acquisition_value, carrying_value, tenant_id, id, projection_family, generation_id_family FROM cost_projection_inventory WHERE projection_family = 'cost_inventory_row' WITH LOCAL CHECK OPTION; ALTER VIEW cost_inventory_row ALTER COLUMN projection_family SET DEFAULT 'cost_inventory_row'; ALTER VIEW cost_inventory_row ALTER COLUMN generation_id_family SET DEFAULT 'cost_generation'",
    "CREATE VIEW cost_company_inventory_result AS SELECT generation_id, inventory_input_id, inventory_generation_id, state, result_fingerprint, tenant_id, id, projection_family, generation_id_family, inventory_generation_id_family FROM cost_projection_inventory WHERE projection_family = 'cost_company_inventory_result' WITH LOCAL CHECK OPTION; ALTER VIEW cost_company_inventory_result ALTER COLUMN projection_family SET DEFAULT 'cost_company_inventory_result'; ALTER VIEW cost_company_inventory_result ALTER COLUMN generation_id_family SET DEFAULT 'cost_company_generation'; ALTER VIEW cost_company_inventory_result ALTER COLUMN inventory_generation_id_family SET DEFAULT 'cost_inventory_generation'",
    "CREATE VIEW cost_contribution_snapshot AS SELECT generation_id, review_id, goods_cost, known_direct_selling_cost, known_allocated_selling_cost, selling_complete, tenant_id, id, projection_family, generation_id_family FROM cost_projection_contribution WHERE projection_family = 'cost_contribution_snapshot' WITH LOCAL CHECK OPTION; ALTER VIEW cost_contribution_snapshot ALTER COLUMN projection_family SET DEFAULT 'cost_contribution_snapshot'; ALTER VIEW cost_contribution_snapshot ALTER COLUMN generation_id_family SET DEFAULT 'cost_contribution_generation'",
    "CREATE VIEW cost_contribution_row AS SELECT generation_id, contribution_basis_member_id, state, currency, base_unit, revenue, goods_cost, direct_selling_cost, allocated_selling_cost, tenant_id, id, projection_family, generation_id_family FROM cost_projection_contribution WHERE projection_family = 'cost_contribution_row' WITH LOCAL CHECK OPTION; ALTER VIEW cost_contribution_row ALTER COLUMN projection_family SET DEFAULT 'cost_contribution_row'; ALTER VIEW cost_contribution_row ALTER COLUMN generation_id_family SET DEFAULT 'cost_generation'",
    "CREATE VIEW cost_company_contribution_result AS SELECT generation_id, contribution_input_id, contribution_generation_id, review_id, db1_state, db2_state, result_fingerprint, tenant_id, id, projection_family, generation_id_family, contribution_generation_id_family FROM cost_projection_contribution WHERE projection_family = 'cost_company_contribution_result' WITH LOCAL CHECK OPTION; ALTER VIEW cost_company_contribution_result ALTER COLUMN projection_family SET DEFAULT 'cost_company_contribution_result'; ALTER VIEW cost_company_contribution_result ALTER COLUMN generation_id_family SET DEFAULT 'cost_company_generation'; ALTER VIEW cost_company_contribution_result ALTER COLUMN contribution_generation_id_family SET DEFAULT 'cost_contribution_generation'",
    "CREATE VIEW cost_inventory_publication AS SELECT review_id, generation_id, tenant_id, id, projection_family, generation_id_family FROM cost_projection_publication WHERE projection_family = 'cost_inventory_publication' WITH LOCAL CHECK OPTION; ALTER VIEW cost_inventory_publication ALTER COLUMN projection_family SET DEFAULT 'cost_inventory_publication'; ALTER VIEW cost_inventory_publication ALTER COLUMN generation_id_family SET DEFAULT 'cost_inventory_generation'",
    "CREATE VIEW cost_publication AS SELECT scope_key, generation_id, tenant_id, id, projection_family, generation_id_family FROM cost_projection_publication WHERE projection_family = 'cost_publication' WITH LOCAL CHECK OPTION; ALTER VIEW cost_publication ALTER COLUMN projection_family SET DEFAULT 'cost_publication'; ALTER VIEW cost_publication ALTER COLUMN generation_id_family SET DEFAULT 'cost_generation'",
    "CREATE VIEW cost_company_publication AS SELECT scope_key, generation_id, updated_at, tenant_id, id, projection_family, generation_id_family FROM cost_projection_publication WHERE projection_family = 'cost_company_publication' WITH LOCAL CHECK OPTION; ALTER VIEW cost_company_publication ALTER COLUMN projection_family SET DEFAULT 'cost_company_publication'; ALTER VIEW cost_company_publication ALTER COLUMN generation_id_family SET DEFAULT 'cost_company_generation'",
]

LEGACY_DDL = (
    "\nCREATE TABLE cost_company_generation (\n\tmanifest_id VARCHAR NOT NULL, \n\talgorithm_bundle VARCHAR NOT NULL, \n\tscope_key VARCHAR(64) NOT NULL, \n\tstate VARCHAR NOT NULL, \n\texpected_work_count INTEGER NOT NULL, \n\tcompleted_work_count INTEGER NOT NULL, \n\tinventory_count INTEGER NOT NULL, \n\tcontribution_count INTEGER NOT NULL, \n\tinventory_content_hash VARCHAR(64) NOT NULL, \n\tcontribution_content_hash VARCHAR(64) NOT NULL, \n\tstarted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tcompleted_at TIMESTAMP WITH TIME ZONE, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_company_generation_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_company_generation_tenant_id_manifest_id_fkey FOREIGN KEY(tenant_id, manifest_id) REFERENCES cost_company_manifest (tenant_id, id), \n\tCONSTRAINT cost_company_generation_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT cost_company_generation_tenant_id_manifest_id_algorithm_bun_key UNIQUE NULLS DISTINCT (tenant_id, manifest_id, algorithm_bundle), \n\tCONSTRAINT cost_company_generation_tenant_id_scope_key_id_key UNIQUE NULLS DISTINCT (tenant_id, scope_key, id), \n\tCONSTRAINT ck_company_generation_counts CHECK (expected_work_count >= 0 AND completed_work_count >= 0 AND completed_work_count <= expected_work_count AND inventory_count >= 0 AND contribution_count >= 0), \n\tCONSTRAINT ck_company_generation_hashes CHECK (length(scope_key::text) = 64 AND length(inventory_content_hash::text) = 64 AND length(contribution_content_hash::text) = 64), \n\tCONSTRAINT ck_company_generation_state CHECK ((state IN ('building','sealed')) AND (state::text = 'sealed'::text) = (completed_at IS NOT NULL))\n)\n",
    "\nCREATE TABLE cost_contribution_generation (\n\taction_id VARCHAR NOT NULL, \n\talgorithm_version VARCHAR NOT NULL, \n\tcompleted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\toutput_hash VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_contribution_generation_tenant_id_action_id_fkey FOREIGN KEY(tenant_id, action_id) REFERENCES action (tenant_id, id), \n\tCONSTRAINT cost_contribution_generation_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_contribution_generation_tenant_id_action_id_algorithm__key UNIQUE NULLS DISTINCT (tenant_id, action_id, algorithm_version), \n\tCONSTRAINT cost_contribution_generation_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT ck_contribution_generation_version CHECK (algorithm_version::text = 'commercial-v1'::text AND length(output_hash::text) = 64)\n)\n",
    "\nCREATE TABLE cost_generation (\n\tcaptured_basis_id VARCHAR NOT NULL, \n\tkind VARCHAR NOT NULL, \n\talgorithm_version VARCHAR NOT NULL, \n\tscope_key VARCHAR(64) NOT NULL, \n\tstate VARCHAR NOT NULL, \n\tcompleted_at TIMESTAMP WITH TIME ZONE, \n\tinventory_count INTEGER NOT NULL, \n\tcontribution_count INTEGER NOT NULL, \n\toutput_hash VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_generation_tenant_id_captured_basis_id_fkey FOREIGN KEY(tenant_id, captured_basis_id) REFERENCES cost_captured_basis (tenant_id, id), \n\tCONSTRAINT cost_generation_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_generation_tenant_id_captured_basis_id_algorithm_versi_key UNIQUE NULLS DISTINCT (tenant_id, captured_basis_id, algorithm_version), \n\tCONSTRAINT cost_generation_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT cost_generation_tenant_id_scope_key_id_key UNIQUE NULLS DISTINCT (tenant_id, scope_key, id), \n\tCONSTRAINT ck_cost_generation_counts CHECK (inventory_count >= 0 AND contribution_count >= 0 AND (inventory_count + contribution_count) <= 10), \n\tCONSTRAINT ck_cost_generation_state CHECK ((state IN ('building','sealed')) AND (state::text = 'sealed'::text) = (completed_at IS NOT NULL)), \n\tCONSTRAINT ck_cost_generation_version CHECK (kind::text = 'captured_review_selection_v1'::text AND algorithm_version::text = 'captured-report-v1'::text AND length(scope_key::text) = 64 AND length(output_hash::text) = 64)\n)\n",
    "\nCREATE TABLE cost_company_publication (\n\tscope_key VARCHAR(64) NOT NULL, \n\tgeneration_id VARCHAR NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_company_publication_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_company_publication_tenant_id_scope_key_generation_id_fkey FOREIGN KEY(tenant_id, scope_key, generation_id) REFERENCES cost_company_generation (tenant_id, scope_key, id), \n\tCONSTRAINT cost_company_publication_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT cost_company_publication_tenant_id_scope_key_key UNIQUE NULLS DISTINCT (tenant_id, scope_key)\n)\n",
    "\nCREATE TABLE cost_publication (\n\tscope_key VARCHAR(64) NOT NULL, \n\tgeneration_id VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_publication_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_publication_tenant_id_scope_key_generation_id_fkey FOREIGN KEY(tenant_id, scope_key, generation_id) REFERENCES cost_generation (tenant_id, scope_key, id), \n\tCONSTRAINT cost_publication_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT cost_publication_tenant_id_scope_key_key UNIQUE NULLS DISTINCT (tenant_id, scope_key)\n)\n",
    "\nCREATE TABLE cost_inventory_generation (\n\treview_id VARCHAR NOT NULL, \n\talgorithm_version VARCHAR NOT NULL, \n\tcompleted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\toutput_hash VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tassessment_revision_id VARCHAR, \n\tCONSTRAINT cost_inventory_generation_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_inventory_generation_tenant_id_review_id_fkey FOREIGN KEY(tenant_id, review_id) REFERENCES cost_inventory_review (tenant_id, id), \n\tCONSTRAINT fk_inventory_generation_assessment FOREIGN KEY(tenant_id, assessment_revision_id) REFERENCES cost_valuation_assessment_revision (tenant_id, id), \n\tCONSTRAINT cost_inventory_generation_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT cost_inventory_generation_tenant_id_review_id_id_key UNIQUE NULLS DISTINCT (tenant_id, review_id, id), \n\tCONSTRAINT ck_inventory_generation_version CHECK (algorithm_version::text = 'inventory-v1'::text AND length(output_hash::text) = 64)\n)\n",
    "\nCREATE TABLE cost_inventory_row (\n\tgeneration_id VARCHAR NOT NULL, \n\tinventory_basis_member_id VARCHAR NOT NULL, \n\tstate VARCHAR NOT NULL, \n\tcurrency VARCHAR, \n\tbase_unit VARCHAR, \n\tmethod VARCHAR, \n\towner_party_id VARCHAR, \n\tremaining_quantity NUMERIC(18, 4), \n\tacquisition_value NUMERIC(18, 4), \n\tcarrying_value NUMERIC(18, 4), \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_inventory_row_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_inventory_row_tenant_id_generation_id_fkey FOREIGN KEY(tenant_id, generation_id) REFERENCES cost_generation (tenant_id, id), \n\tCONSTRAINT cost_inventory_row_tenant_id_inventory_basis_member_id_fkey FOREIGN KEY(tenant_id, inventory_basis_member_id) REFERENCES cost_captured_inventory_basis (tenant_id, id), \n\tCONSTRAINT cost_inventory_row_tenant_id_owner_party_id_fkey FOREIGN KEY(tenant_id, owner_party_id) REFERENCES party (tenant_id, id), \n\tCONSTRAINT cost_inventory_row_tenant_id_generation_id_inventory_basis__key UNIQUE NULLS DISTINCT (tenant_id, generation_id, inventory_basis_member_id), \n\tCONSTRAINT cost_inventory_row_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT ck_cost_inventory_row_amounts CHECK (remaining_quantity >= 0::numeric AND acquisition_value >= 0::numeric AND carrying_value >= 0::numeric AND carrying_value <= acquisition_value), \n\tCONSTRAINT ck_cost_inventory_row_shape CHECK (state::text = 'available_at_capture'::text AND currency IS NOT NULL AND base_unit IS NOT NULL AND method IS NOT NULL AND owner_party_id IS NOT NULL AND remaining_quantity IS NOT NULL AND acquisition_value IS NOT NULL OR state::text = 'unknown_at_capture'::text AND currency IS NULL AND base_unit IS NULL AND method IS NULL AND owner_party_id IS NULL AND remaining_quantity IS NULL AND acquisition_value IS NULL AND carrying_value IS NULL)\n)\n",
    "\nCREATE TABLE cost_company_inventory_result (\n\tgeneration_id VARCHAR NOT NULL, \n\tinventory_input_id VARCHAR NOT NULL, \n\tinventory_generation_id VARCHAR, \n\tstate VARCHAR NOT NULL, \n\tresult_fingerprint VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_company_inventory_result_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_company_inventory_result_tenant_id_generation_id_fkey FOREIGN KEY(tenant_id, generation_id) REFERENCES cost_company_generation (tenant_id, id), \n\tCONSTRAINT cost_company_inventory_result_tenant_id_inventory_generati_fkey FOREIGN KEY(tenant_id, inventory_generation_id) REFERENCES cost_inventory_generation (tenant_id, id), \n\tCONSTRAINT cost_company_inventory_result_tenant_id_inventory_input_id_fkey FOREIGN KEY(tenant_id, inventory_input_id) REFERENCES cost_company_inventory_input (tenant_id, id), \n\tCONSTRAINT cost_company_inventory_result_tenant_id_generation_id_inven_key UNIQUE NULLS DISTINCT (tenant_id, generation_id, inventory_input_id), \n\tCONSTRAINT cost_company_inventory_result_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT ck_company_inventory_result_shape CHECK ((state IN ('known','unknown')) AND (state::text = 'known'::text) = (inventory_generation_id IS NOT NULL) AND length(result_fingerprint::text) = 64)\n)\n",
    "\nCREATE TABLE cost_inventory_publication (\n\treview_id VARCHAR NOT NULL, \n\tgeneration_id VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_inventory_publication_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_inventory_publication_tenant_id_review_id_fkey FOREIGN KEY(tenant_id, review_id) REFERENCES cost_inventory_review (tenant_id, id), \n\tCONSTRAINT cost_inventory_publication_tenant_id_review_id_generation__fkey FOREIGN KEY(tenant_id, review_id, generation_id) REFERENCES cost_inventory_generation (tenant_id, review_id, id), \n\tCONSTRAINT cost_inventory_publication_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT cost_inventory_publication_tenant_id_review_id_key UNIQUE NULLS DISTINCT (tenant_id, review_id)\n)\n",
    "\nCREATE TABLE cost_inventory_snapshot (\n\tgeneration_id VARCHAR NOT NULL, \n\tremaining_quantity NUMERIC(18, 4) NOT NULL, \n\tacquisition_value NUMERIC(18, 4) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tcarrying_value NUMERIC(18, 4), \n\tCONSTRAINT cost_inventory_snapshot_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_inventory_snapshot_tenant_id_generation_id_fkey FOREIGN KEY(tenant_id, generation_id) REFERENCES cost_inventory_generation (tenant_id, id), \n\tCONSTRAINT cost_inventory_snapshot_tenant_id_generation_id_key UNIQUE NULLS DISTINCT (tenant_id, generation_id), \n\tCONSTRAINT cost_inventory_snapshot_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT ck_inventory_snapshot_amounts CHECK (remaining_quantity >= 0::numeric AND acquisition_value >= 0::numeric), \n\tCONSTRAINT ck_inventory_snapshot_carrying CHECK (carrying_value IS NULL OR carrying_value >= 0::numeric AND carrying_value <= acquisition_value)\n)\n",
    "\nCREATE TABLE cost_contribution_snapshot (\n\tgeneration_id VARCHAR NOT NULL, \n\treview_id VARCHAR NOT NULL, \n\tgoods_cost NUMERIC(18, 4) NOT NULL, \n\tknown_direct_selling_cost NUMERIC(18, 4), \n\tknown_allocated_selling_cost NUMERIC(18, 4), \n\tselling_complete BOOLEAN NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_contribution_snapshot_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_contribution_snapshot_tenant_id_generation_id_fkey FOREIGN KEY(tenant_id, generation_id) REFERENCES cost_contribution_generation (tenant_id, id), \n\tCONSTRAINT cost_contribution_snapshot_tenant_id_review_id_fkey FOREIGN KEY(tenant_id, review_id) REFERENCES cost_contribution_review (tenant_id, id), \n\tCONSTRAINT cost_contribution_snapshot_tenant_id_generation_id_review_i_key UNIQUE NULLS DISTINCT (tenant_id, generation_id, review_id), \n\tCONSTRAINT cost_contribution_snapshot_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT ck_contribution_snapshot_goods CHECK (goods_cost >= 0::numeric), \n\tCONSTRAINT ck_contribution_snapshot_selling CHECK ((known_direct_selling_cost IS NULL) = (known_allocated_selling_cost IS NULL) AND (NOT selling_complete OR known_direct_selling_cost IS NOT NULL))\n)\n",
    "\nCREATE TABLE cost_company_contribution_result (\n\tgeneration_id VARCHAR NOT NULL, \n\tcontribution_input_id VARCHAR NOT NULL, \n\tcontribution_generation_id VARCHAR, \n\treview_id VARCHAR, \n\tdb1_state VARCHAR NOT NULL, \n\tdb2_state VARCHAR NOT NULL, \n\tresult_fingerprint VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_company_contribution_res_tenant_id_contribution_gener_fkey FOREIGN KEY(tenant_id, contribution_generation_id) REFERENCES cost_contribution_generation (tenant_id, id), \n\tCONSTRAINT cost_company_contribution_res_tenant_id_contribution_input_fkey FOREIGN KEY(tenant_id, contribution_input_id) REFERENCES cost_company_contribution_input (tenant_id, id), \n\tCONSTRAINT cost_company_contribution_result_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_company_contribution_result_tenant_id_generation_id_fkey FOREIGN KEY(tenant_id, generation_id) REFERENCES cost_company_generation (tenant_id, id), \n\tCONSTRAINT cost_company_contribution_result_tenant_id_review_id_fkey FOREIGN KEY(tenant_id, review_id) REFERENCES cost_contribution_review (tenant_id, id), \n\tCONSTRAINT cost_company_contribution_res_tenant_id_generation_id_contr_key UNIQUE NULLS DISTINCT (tenant_id, generation_id, contribution_input_id), \n\tCONSTRAINT cost_company_contribution_result_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT ck_company_contribution_result_shape CHECK ((db1_state IN ('known','unknown')) AND (db2_state IN ('known','unknown')) AND NOT (db2_state::text = 'known'::text AND db1_state::text = 'unknown'::text) AND (db1_state::text = 'known'::text) = (contribution_generation_id IS NOT NULL AND review_id IS NOT NULL) AND length(result_fingerprint::text) = 64)\n)\n",
    "\nCREATE TABLE cost_contribution_row (\n\tgeneration_id VARCHAR NOT NULL, \n\tcontribution_basis_member_id VARCHAR NOT NULL, \n\tstate VARCHAR NOT NULL, \n\tcurrency VARCHAR, \n\tbase_unit VARCHAR, \n\trevenue NUMERIC(18, 4), \n\tgoods_cost NUMERIC(18, 4), \n\tdirect_selling_cost NUMERIC(18, 4), \n\tallocated_selling_cost NUMERIC(18, 4), \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tCONSTRAINT cost_contribution_row_tenant_id_contribution_basis_member__fkey FOREIGN KEY(tenant_id, contribution_basis_member_id) REFERENCES cost_captured_contribution_basis (tenant_id, id), \n\tCONSTRAINT cost_contribution_row_tenant_id_fkey FOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT cost_contribution_row_tenant_id_generation_id_fkey FOREIGN KEY(tenant_id, generation_id) REFERENCES cost_generation (tenant_id, id), \n\tCONSTRAINT cost_contribution_row_tenant_id_generation_id_contribution__key UNIQUE NULLS DISTINCT (tenant_id, generation_id, contribution_basis_member_id), \n\tCONSTRAINT cost_contribution_row_tenant_id_id_key UNIQUE NULLS DISTINCT (tenant_id, id), \n\tCONSTRAINT ck_cost_contribution_row_goods CHECK (goods_cost >= 0::numeric), \n\tCONSTRAINT ck_cost_contribution_row_shape CHECK (state::text = 'available_at_capture'::text AND currency IS NOT NULL AND base_unit IS NOT NULL AND revenue IS NOT NULL AND goods_cost IS NOT NULL OR state::text = 'unknown_at_capture'::text AND currency IS NULL AND base_unit IS NULL AND revenue IS NULL AND goods_cost IS NULL AND direct_selling_cost IS NULL AND allocated_selling_cost IS NULL)\n)\n",
    "CREATE INDEX ix_cost_company_generation_manifest_id ON cost_company_generation (manifest_id)",
    "CREATE INDEX ix_cost_generation_captured_basis_id ON cost_generation (captured_basis_id)",
    "CREATE INDEX ix_cost_company_publication_generation_id ON cost_company_publication (generation_id)",
    "CREATE INDEX ix_cost_company_publication_scope_key_generation_id ON cost_company_publication (tenant_id, scope_key, generation_id)",
    "CREATE INDEX ix_cost_publication_generation_id ON cost_publication (generation_id)",
    "CREATE INDEX ix_cost_publication_scope_key_generation_id ON cost_publication (tenant_id, scope_key, generation_id)",
    "CREATE INDEX ix_cost_inventory_generation_assessment_revision_id ON cost_inventory_generation (tenant_id, assessment_revision_id)",
    "CREATE UNIQUE INDEX uq_inventory_generation_basis ON cost_inventory_generation (tenant_id, review_id, assessment_revision_id, algorithm_version) NULLS NOT DISTINCT",
    "CREATE INDEX ix_cost_inventory_group ON cost_inventory_row (tenant_id, generation_id, currency, base_unit, method, owner_party_id)",
    "CREATE INDEX ix_cost_inventory_row_generation_id ON cost_inventory_row (generation_id)",
    "CREATE INDEX ix_cost_inventory_row_inventory_basis_member_id ON cost_inventory_row (tenant_id, inventory_basis_member_id)",
    "CREATE INDEX ix_cost_inventory_row_owner_party_id ON cost_inventory_row (tenant_id, owner_party_id)",
    "CREATE INDEX ix_cost_company_inventory_result_generation_id ON cost_company_inventory_result (generation_id)",
    "CREATE INDEX ix_cost_company_inventory_result_inventory_generation_id ON cost_company_inventory_result (tenant_id, inventory_generation_id)",
    "CREATE INDEX ix_cost_company_inventory_result_inventory_input_id ON cost_company_inventory_result (tenant_id, inventory_input_id)",
    "CREATE INDEX ix_cost_inventory_publication_review_id_generation_id ON cost_inventory_publication (tenant_id, review_id, generation_id)",
    "CREATE INDEX ix_cost_contribution_snapshot_review_id ON cost_contribution_snapshot (tenant_id, review_id)",
    "CREATE INDEX ix_cost_company_contribution_result_contribution_generation_id ON cost_company_contribution_result (tenant_id, contribution_generation_id)",
    "CREATE INDEX ix_cost_company_contribution_result_contribution_input_id ON cost_company_contribution_result (tenant_id, contribution_input_id)",
    "CREATE INDEX ix_cost_company_contribution_result_generation_id ON cost_company_contribution_result (generation_id)",
    "CREATE INDEX ix_cost_company_contribution_result_review_id ON cost_company_contribution_result (tenant_id, review_id)",
    "CREATE INDEX ix_cost_contribution_group ON cost_contribution_row (tenant_id, generation_id, currency, base_unit)",
    "CREATE INDEX ix_cost_contribution_row_contribution_basis_member_id ON cost_contribution_row (tenant_id, contribution_basis_member_id)",
    "CREATE INDEX ix_cost_contribution_row_generation_id ON cost_contribution_row (generation_id)",
)

LEGACY_ORDER = [
    "cost_company_generation",
    "cost_contribution_generation",
    "cost_generation",
    "cost_company_publication",
    "cost_publication",
    "cost_inventory_generation",
    "cost_inventory_row",
    "cost_company_inventory_result",
    "cost_inventory_publication",
    "cost_inventory_snapshot",
    "cost_contribution_snapshot",
    "cost_company_contribution_result",
    "cost_contribution_row",
]

GUARDS = "-- Shared physical output lifecycle; logical views own no business rules.\n\nCREATE OR REPLACE FUNCTION guard_cost_projection_captured() RETURNS trigger LANGUAGE plpgsql AS $$\nDECLARE parent_state text; parent_basis text; member_basis text; n integer; m integer;\nBEGIN\n IF COALESCE(NEW.projection_family, OLD.projection_family) = 'cost_generation' THEN\n  IF TG_OP = 'INSERT' THEN\n   IF NEW.state <> 'building' OR NOT EXISTS (\n    SELECT 1 FROM cost_captured_basis WHERE tenant_id=NEW.tenant_id\n    AND id=NEW.captured_basis_id AND state='sealed') THEN\n    RAISE EXCEPTION 'A report starts building from a sealed retained basis';\n   END IF;\n   RETURN NEW;\n  END IF;\n  IF TG_OP = 'DELETE' THEN\n   IF EXISTS (SELECT 1 FROM cost_publication WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id) THEN\n    RAISE EXCEPTION 'Published report cannot be discarded';\n   END IF;\n   DELETE FROM cost_inventory_row WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id;\n   DELETE FROM cost_contribution_row WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id;\n   RETURN OLD;\n  END IF;\n  IF OLD.state='sealed' OR NEW.tenant_id<>OLD.tenant_id OR NEW.id<>OLD.id\n    OR NEW.captured_basis_id<>OLD.captured_basis_id OR NEW.scope_key<>OLD.scope_key THEN\n   RAISE EXCEPTION 'Sealed report or report identity is immutable';\n  END IF;\n  IF NEW.state='sealed' THEN\n   SELECT count(*) INTO n FROM cost_inventory_row WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;\n   SELECT count(*) INTO m FROM cost_contribution_row WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;\n   IF n<>NEW.inventory_count OR m<>NEW.contribution_count OR NOT EXISTS (\n    SELECT 1 FROM cost_captured_basis WHERE tenant_id=NEW.tenant_id AND id=NEW.captured_basis_id\n    AND inventory_count=n AND contribution_count=m) THEN\n    RAISE EXCEPTION 'Report membership is incomplete';\n   END IF;\n  END IF;\n  RETURN NEW;\n END IF;\n IF COALESCE(NEW.projection_family, OLD.projection_family)='cost_publication' THEN\n  IF TG_OP='UPDATE' AND (OLD.tenant_id<>NEW.tenant_id OR OLD.scope_key<>NEW.scope_key OR OLD.id<>NEW.id) THEN\n   RAISE EXCEPTION 'Publication scope is immutable';\n  END IF;\n  SELECT state INTO parent_state FROM cost_generation WHERE tenant_id=NEW.tenant_id\n   AND id=NEW.generation_id AND scope_key=NEW.scope_key FOR UPDATE;\n  IF parent_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Publication requires sealed matching scope'; END IF;\n  RETURN NEW;\n END IF;\n IF TG_OP='DELETE' AND pg_trigger_depth()=2 THEN RETURN OLD; END IF;\n IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Report rows are immutable'; END IF;\n SELECT state,captured_basis_id INTO parent_state,parent_basis FROM cost_generation\n  WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id FOR UPDATE;\n IF parent_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Report row requires building generation'; END IF;\n IF COALESCE(NEW.projection_family, OLD.projection_family)='cost_inventory_row' THEN\n  SELECT basis_id INTO member_basis FROM cost_captured_inventory_basis\n   WHERE tenant_id=NEW.tenant_id AND id=NEW.inventory_basis_member_id;\n ELSE\n  SELECT basis_id INTO member_basis FROM cost_captured_contribution_basis\n   WHERE tenant_id=NEW.tenant_id AND id=NEW.contribution_basis_member_id;\n END IF;\n IF member_basis IS DISTINCT FROM parent_basis THEN RAISE EXCEPTION 'Report member belongs to another basis'; END IF;\n RETURN NEW;\nEND $$;\n\nCREATE OR REPLACE FUNCTION guard_cost_projection_company() RETURNS trigger LANGUAGE plpgsql AS $$\n        DECLARE parent_state text; manifest_state text; n integer; m integer;\n        BEGIN\n          IF COALESCE(NEW.projection_family, OLD.projection_family)='cost_company_manifest' THEN\n            IF TG_OP='INSERT' AND NEW.state<>'building' THEN\n              RAISE EXCEPTION 'Company manifest starts building';\n            END IF;\n            IF TG_OP='UPDATE' AND (OLD.state='sealed' OR NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.census_id<>OLD.census_id OR NEW.scope_key<>OLD.scope_key) THEN\n              RAISE EXCEPTION 'Sealed company manifest or identity is immutable';\n            END IF;\n            RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;\n          END IF;\n          IF COALESCE(NEW.projection_family, OLD.projection_family)='cost_company_generation' THEN\n            IF TG_OP='INSERT' THEN\n              SELECT state INTO manifest_state FROM cost_company_manifest WHERE tenant_id=NEW.tenant_id AND id=NEW.manifest_id;\n              IF NEW.state<>'building' OR manifest_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Generation requires sealed manifest'; END IF;\n            ELSIF TG_OP='UPDATE' THEN\n              IF OLD.state='sealed' OR NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.manifest_id<>OLD.manifest_id OR NEW.scope_key<>OLD.scope_key THEN RAISE EXCEPTION 'Sealed company generation or identity is immutable'; END IF;\n              IF NEW.state='sealed' THEN\n                SELECT count(*) INTO n FROM cost_company_inventory_result WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;\n                SELECT count(*) INTO m FROM cost_company_contribution_result WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;\n                IF n<>NEW.inventory_count OR m<>NEW.contribution_count OR NEW.completed_work_count<>NEW.expected_work_count THEN RAISE EXCEPTION 'Company generation membership is incomplete'; END IF;\n              END IF;\n            END IF;\n            RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;\n          END IF;\n          IF COALESCE(NEW.projection_family, OLD.projection_family)='cost_company_publication' THEN\n            IF TG_OP='UPDATE' AND (NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.scope_key<>OLD.scope_key) THEN RAISE EXCEPTION 'Company publication scope is immutable'; END IF;\n            SELECT state INTO parent_state FROM cost_company_generation WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id AND scope_key=NEW.scope_key FOR UPDATE;\n            IF parent_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Company publication requires sealed generation'; END IF;\n            RETURN NEW;\n          END IF;\n          IF COALESCE(NEW.projection_family, OLD.projection_family) IN ('cost_company_inventory_input','cost_company_contribution_input') THEN\n            IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Company manifest members are immutable'; END IF;\n            SELECT state INTO manifest_state FROM cost_company_manifest WHERE tenant_id=NEW.tenant_id AND id=NEW.manifest_id FOR UPDATE;\n            IF manifest_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Company input requires building manifest'; END IF;\n            RETURN NEW;\n          END IF;\n          IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Company generation members are immutable'; END IF;\n          SELECT state INTO parent_state FROM cost_company_generation WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id FOR UPDATE;\n          IF parent_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Company result requires building generation'; END IF;\n          RETURN NEW;\n        END $$;\n\nCREATE OR REPLACE FUNCTION guard_cost_projection_identity() RETURNS trigger LANGUAGE plpgsql AS $$\nBEGIN\n IF (NEW.tenant_id,NEW.projection_family,NEW.id) IS DISTINCT FROM (OLD.tenant_id,OLD.projection_family,OLD.id) THEN\n  RAISE EXCEPTION 'Cost projection identity is immutable';\n END IF;\n RETURN NEW;\nEND $$;\n\nCREATE TRIGGER guard_projection_identity BEFORE UPDATE ON cost_projection_generation FOR EACH ROW EXECUTE FUNCTION guard_cost_projection_identity();\n\nCREATE TRIGGER guard_projection_identity BEFORE UPDATE ON cost_projection_inventory FOR EACH ROW EXECUTE FUNCTION guard_cost_projection_identity();\n\nCREATE TRIGGER guard_projection_identity BEFORE UPDATE ON cost_projection_contribution FOR EACH ROW EXECUTE FUNCTION guard_cost_projection_identity();\n\nCREATE TRIGGER guard_projection_identity BEFORE UPDATE ON cost_projection_publication FOR EACH ROW EXECUTE FUNCTION guard_cost_projection_identity();\n\nCREATE TRIGGER guard_cost_generation_insert BEFORE INSERT ON cost_projection_generation FOR EACH ROW WHEN (NEW.projection_family = 'cost_generation') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_generation_update BEFORE UPDATE ON cost_projection_generation FOR EACH ROW WHEN (NEW.projection_family = 'cost_generation') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_generation_delete BEFORE DELETE ON cost_projection_generation FOR EACH ROW WHEN (OLD.projection_family = 'cost_generation') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_inventory_row_insert BEFORE INSERT ON cost_projection_inventory FOR EACH ROW WHEN (NEW.projection_family = 'cost_inventory_row') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_inventory_row_update BEFORE UPDATE ON cost_projection_inventory FOR EACH ROW WHEN (NEW.projection_family = 'cost_inventory_row') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_inventory_row_delete BEFORE DELETE ON cost_projection_inventory FOR EACH ROW WHEN (OLD.projection_family = 'cost_inventory_row') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_contribution_row_insert BEFORE INSERT ON cost_projection_contribution FOR EACH ROW WHEN (NEW.projection_family = 'cost_contribution_row') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_contribution_row_update BEFORE UPDATE ON cost_projection_contribution FOR EACH ROW WHEN (NEW.projection_family = 'cost_contribution_row') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_contribution_row_delete BEFORE DELETE ON cost_projection_contribution FOR EACH ROW WHEN (OLD.projection_family = 'cost_contribution_row') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_publication_insert BEFORE INSERT ON cost_projection_publication FOR EACH ROW WHEN (NEW.projection_family = 'cost_publication') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_publication_update BEFORE UPDATE ON cost_projection_publication FOR EACH ROW WHEN (NEW.projection_family = 'cost_publication') EXECUTE FUNCTION guard_cost_projection_captured();\n\nCREATE TRIGGER guard_cost_company_generation_insert BEFORE INSERT ON cost_projection_generation FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_generation') EXECUTE FUNCTION guard_cost_projection_company();\n\nCREATE TRIGGER guard_cost_company_generation_update BEFORE UPDATE ON cost_projection_generation FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_generation') EXECUTE FUNCTION guard_cost_projection_company();\n\nCREATE TRIGGER guard_cost_company_generation_delete BEFORE DELETE ON cost_projection_generation FOR EACH ROW WHEN (OLD.projection_family = 'cost_company_generation') EXECUTE FUNCTION guard_cost_projection_company();\n\nCREATE TRIGGER guard_cost_company_inventory_result_insert BEFORE INSERT ON cost_projection_inventory FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_inventory_result') EXECUTE FUNCTION guard_cost_projection_company();\n\nCREATE TRIGGER guard_cost_company_inventory_result_update BEFORE UPDATE ON cost_projection_inventory FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_inventory_result') EXECUTE FUNCTION guard_cost_projection_company();\n\nCREATE TRIGGER guard_cost_company_inventory_result_delete BEFORE DELETE ON cost_projection_inventory FOR EACH ROW WHEN (OLD.projection_family = 'cost_company_inventory_result') EXECUTE FUNCTION guard_cost_projection_company();\n\nCREATE TRIGGER guard_cost_company_contribution_result_insert BEFORE INSERT ON cost_projection_contribution FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_contribution_result') EXECUTE FUNCTION guard_cost_projection_company();\n\nCREATE TRIGGER guard_cost_company_contribution_result_update BEFORE UPDATE ON cost_projection_contribution FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_contribution_result') EXECUTE FUNCTION guard_cost_projection_company();\n\nCREATE TRIGGER guard_cost_company_contribution_result_delete BEFORE DELETE ON cost_projection_contribution FOR EACH ROW WHEN (OLD.projection_family = 'cost_company_contribution_result') EXECUTE FUNCTION guard_cost_projection_company();\n\nCREATE TRIGGER guard_cost_company_publication_insert BEFORE INSERT ON cost_projection_publication FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_publication') EXECUTE FUNCTION guard_cost_projection_company();\n\nCREATE TRIGGER guard_cost_company_publication_update BEFORE UPDATE ON cost_projection_publication FOR EACH ROW WHEN (NEW.projection_family = 'cost_company_publication') EXECUTE FUNCTION guard_cost_projection_company();\n"

RESTORE_GUARDS = [
    "\nCREATE OR REPLACE FUNCTION guard_captured_report() RETURNS trigger LANGUAGE plpgsql AS $$\nDECLARE parent_state text; parent_basis text; member_basis text; n integer; m integer;\nBEGIN\n IF TG_TABLE_NAME = 'cost_generation' THEN\n  IF TG_OP = 'INSERT' THEN\n   IF NEW.state <> 'building' OR NOT EXISTS (\n    SELECT 1 FROM cost_captured_basis WHERE tenant_id=NEW.tenant_id\n    AND id=NEW.captured_basis_id AND state='sealed') THEN\n    RAISE EXCEPTION 'A report starts building from a sealed retained basis';\n   END IF;\n   RETURN NEW;\n  END IF;\n  IF TG_OP = 'DELETE' THEN\n   IF EXISTS (SELECT 1 FROM cost_publication WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id) THEN\n    RAISE EXCEPTION 'Published report cannot be discarded';\n   END IF;\n   DELETE FROM cost_inventory_row WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id;\n   DELETE FROM cost_contribution_row WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id;\n   RETURN OLD;\n  END IF;\n  IF OLD.state='sealed' OR NEW.tenant_id<>OLD.tenant_id OR NEW.id<>OLD.id\n    OR NEW.captured_basis_id<>OLD.captured_basis_id OR NEW.scope_key<>OLD.scope_key THEN\n   RAISE EXCEPTION 'Sealed report or report identity is immutable';\n  END IF;\n  IF NEW.state='sealed' THEN\n   SELECT count(*) INTO n FROM cost_inventory_row WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;\n   SELECT count(*) INTO m FROM cost_contribution_row WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;\n   IF n<>NEW.inventory_count OR m<>NEW.contribution_count OR NOT EXISTS (\n    SELECT 1 FROM cost_captured_basis WHERE tenant_id=NEW.tenant_id AND id=NEW.captured_basis_id\n    AND inventory_count=n AND contribution_count=m) THEN\n    RAISE EXCEPTION 'Report membership is incomplete';\n   END IF;\n  END IF;\n  RETURN NEW;\n END IF;\n IF TG_TABLE_NAME='cost_publication' THEN\n  IF TG_OP='UPDATE' AND (OLD.tenant_id<>NEW.tenant_id OR OLD.scope_key<>NEW.scope_key OR OLD.id<>NEW.id) THEN\n   RAISE EXCEPTION 'Publication scope is immutable';\n  END IF;\n  SELECT state INTO parent_state FROM cost_generation WHERE tenant_id=NEW.tenant_id\n   AND id=NEW.generation_id AND scope_key=NEW.scope_key FOR UPDATE;\n  IF parent_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Publication requires sealed matching scope'; END IF;\n  RETURN NEW;\n END IF;\n IF TG_OP='DELETE' AND pg_trigger_depth()=2 THEN RETURN OLD; END IF;\n IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Report rows are immutable'; END IF;\n SELECT state,captured_basis_id INTO parent_state,parent_basis FROM cost_generation\n  WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id FOR UPDATE;\n IF parent_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Report row requires building generation'; END IF;\n IF TG_TABLE_NAME='cost_inventory_row' THEN\n  SELECT basis_id INTO member_basis FROM cost_captured_inventory_basis\n   WHERE tenant_id=NEW.tenant_id AND id=NEW.inventory_basis_member_id;\n ELSE\n  SELECT basis_id INTO member_basis FROM cost_captured_contribution_basis\n   WHERE tenant_id=NEW.tenant_id AND id=NEW.contribution_basis_member_id;\n END IF;\n IF member_basis IS DISTINCT FROM parent_basis THEN RAISE EXCEPTION 'Report member belongs to another basis'; END IF;\n RETURN NEW;\nEND $$\n",
    "\n        CREATE OR REPLACE FUNCTION guard_company_generation_storage() RETURNS trigger LANGUAGE plpgsql AS $$\n        DECLARE parent_state text; manifest_state text; n integer; m integer;\n        BEGIN\n          IF TG_TABLE_NAME='cost_company_manifest' THEN\n            IF TG_OP='INSERT' AND NEW.state<>'building' THEN\n              RAISE EXCEPTION 'Company manifest starts building';\n            END IF;\n            IF TG_OP='UPDATE' AND (OLD.state='sealed' OR NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.census_id<>OLD.census_id OR NEW.scope_key<>OLD.scope_key) THEN\n              RAISE EXCEPTION 'Sealed company manifest or identity is immutable';\n            END IF;\n            RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;\n          END IF;\n          IF TG_TABLE_NAME='cost_company_generation' THEN\n            IF TG_OP='INSERT' THEN\n              SELECT state INTO manifest_state FROM cost_company_manifest WHERE tenant_id=NEW.tenant_id AND id=NEW.manifest_id;\n              IF NEW.state<>'building' OR manifest_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Generation requires sealed manifest'; END IF;\n            ELSIF TG_OP='UPDATE' THEN\n              IF OLD.state='sealed' OR NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.manifest_id<>OLD.manifest_id OR NEW.scope_key<>OLD.scope_key THEN RAISE EXCEPTION 'Sealed company generation or identity is immutable'; END IF;\n              IF NEW.state='sealed' THEN\n                SELECT count(*) INTO n FROM cost_company_inventory_result WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;\n                SELECT count(*) INTO m FROM cost_company_contribution_result WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;\n                IF n<>NEW.inventory_count OR m<>NEW.contribution_count OR NEW.completed_work_count<>NEW.expected_work_count THEN RAISE EXCEPTION 'Company generation membership is incomplete'; END IF;\n              END IF;\n            END IF;\n            RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;\n          END IF;\n          IF TG_TABLE_NAME='cost_company_publication' THEN\n            IF TG_OP='UPDATE' AND (NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.scope_key<>OLD.scope_key) THEN RAISE EXCEPTION 'Company publication scope is immutable'; END IF;\n            SELECT state INTO parent_state FROM cost_company_generation WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id AND scope_key=NEW.scope_key FOR UPDATE;\n            IF parent_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Company publication requires sealed generation'; END IF;\n            RETURN NEW;\n          END IF;\n          IF TG_TABLE_NAME IN ('cost_company_inventory_input','cost_company_contribution_input') THEN\n            IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Company manifest members are immutable'; END IF;\n            SELECT state INTO manifest_state FROM cost_company_manifest WHERE tenant_id=NEW.tenant_id AND id=NEW.manifest_id FOR UPDATE;\n            IF manifest_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Company input requires building manifest'; END IF;\n            RETURN NEW;\n          END IF;\n          IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Company generation members are immutable'; END IF;\n          SELECT state INTO parent_state FROM cost_company_generation WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id FOR UPDATE;\n          IF parent_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Company result requires building generation'; END IF;\n          RETURN NEW;\n        END $$\n        ",
    "CREATE TRIGGER guard_captured_report_row BEFORE INSERT OR UPDATE OR DELETE ON cost_generation FOR EACH ROW EXECUTE FUNCTION guard_captured_report()",
    "CREATE TRIGGER guard_company_generation_row BEFORE INSERT OR UPDATE OR DELETE ON cost_company_generation FOR EACH ROW EXECUTE FUNCTION guard_company_generation_storage()",
    "CREATE TRIGGER guard_captured_report_row BEFORE INSERT OR UPDATE OR DELETE ON cost_inventory_row FOR EACH ROW EXECUTE FUNCTION guard_captured_report()",
    "CREATE TRIGGER guard_company_generation_row BEFORE INSERT OR UPDATE OR DELETE ON cost_company_inventory_result FOR EACH ROW EXECUTE FUNCTION guard_company_generation_storage()",
    "CREATE TRIGGER guard_captured_report_row BEFORE INSERT OR UPDATE OR DELETE ON cost_contribution_row FOR EACH ROW EXECUTE FUNCTION guard_captured_report()",
    "CREATE TRIGGER guard_company_generation_row BEFORE INSERT OR UPDATE OR DELETE ON cost_company_contribution_result FOR EACH ROW EXECUTE FUNCTION guard_company_generation_storage()",
    "CREATE TRIGGER guard_captured_report_row BEFORE INSERT OR UPDATE ON cost_publication FOR EACH ROW EXECUTE FUNCTION guard_captured_report()",
    "CREATE TRIGGER guard_company_generation_row BEFORE INSERT OR UPDATE ON cost_company_publication FOR EACH ROW EXECUTE FUNCTION guard_company_generation_storage()",
]


RESTORE_PRIMARY_KEYS = [
    "ALTER TABLE cost_company_generation ADD CONSTRAINT cost_company_generation_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_contribution_generation ADD CONSTRAINT cost_contribution_generation_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_generation ADD CONSTRAINT cost_generation_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_company_publication ADD CONSTRAINT cost_company_publication_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_publication ADD CONSTRAINT cost_publication_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_inventory_generation ADD CONSTRAINT cost_inventory_generation_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_inventory_row ADD CONSTRAINT cost_inventory_row_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_company_inventory_result ADD CONSTRAINT cost_company_inventory_result_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_inventory_publication ADD CONSTRAINT cost_inventory_publication_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_inventory_snapshot ADD CONSTRAINT cost_inventory_snapshot_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_contribution_snapshot ADD CONSTRAINT cost_contribution_snapshot_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_company_contribution_result ADD CONSTRAINT cost_company_contribution_result_pkey PRIMARY KEY (tenant_id,id)",
    "ALTER TABLE cost_contribution_row ADD CONSTRAINT cost_contribution_row_pkey PRIMARY KEY (tenant_id,id)",
]


def _verify(bind, logical, storage, columns):
    selected = ", ".join(columns)
    shared = f"SELECT {selected} FROM {storage} WHERE projection_family='{logical}'"
    original = f"SELECT {selected} FROM {logical}"
    mismatch = bind.scalar(
        text(
            f"SELECT EXISTS (({original} EXCEPT {shared}) UNION ALL ({shared} EXCEPT {original}))"
        )
    )
    if mismatch:
        raise RuntimeError(
            f"Cost projection parity failed for {logical}; storage retained."
        )


def upgrade():
    bind = op.get_bind()
    # Freeze all original output families before copying: a concurrent legacy
    # write must not commit between parity verification and table retirement.
    op.execute("LOCK TABLE " + ", ".join(LEGACY_ORDER) + " IN ACCESS EXCLUSIVE MODE")
    for sql in SHARED_DDL:
        op.execute(sql)
    for logical in LEGACY_ORDER:
        columns = list(COLUMNS[logical])
        constants = DEFAULTS[logical]
        destination = ", ".join([*columns, *constants])
        values = ", ".join([*columns, *(f"'{v}'" for v in constants.values())])
        op.execute(
            f"INSERT INTO {FAMILIES[logical]} ({destination}) SELECT {values} FROM {logical}"
        )
        _verify(bind, logical, FAMILIES[logical], columns)
    for logical in reversed(LEGACY_ORDER):
        op.drop_table(logical)
    for sql in VIEW_DDL:
        op.execute(sql)
    op.execute(GUARDS)


def downgrade():
    bind = op.get_bind()
    # Lock the logical interfaces first, as application writers do, and their
    # backing storage before restoring the old physical namespaces.
    op.execute("LOCK TABLE " + ", ".join(LEGACY_ORDER) + " IN ACCESS EXCLUSIVE MODE")
    for logical in reversed(LEGACY_ORDER):
        op.execute(f"DROP VIEW {logical}")
    for sql in LEGACY_DDL:
        op.execute(sql)
    # Original foreign keys predate the tenant-scoped primary keys (0088).
    # Bind them to the original tenant/id UNIQUE keys first, so an older
    # downgrade can replace primary keys without breaking these references.
    for sql in RESTORE_PRIMARY_KEYS:
        op.execute(sql)
    for logical in LEGACY_ORDER:
        columns = list(COLUMNS[logical])
        selected = ", ".join(columns)
        op.execute(
            f"INSERT INTO {logical} ({selected}) SELECT {selected} FROM {FAMILIES[logical]} WHERE projection_family='{logical}'"
        )
        _verify(bind, logical, FAMILIES[logical], columns)
    for storage in reversed(STORAGE):
        op.drop_table(storage)
    for function in (
        "guard_cost_projection_captured",
        "guard_cost_projection_company",
        "guard_cost_projection_identity",
    ):
        op.execute(f"DROP FUNCTION {function}()")
    for sql in RESTORE_GUARDS:
        op.execute(sql)
