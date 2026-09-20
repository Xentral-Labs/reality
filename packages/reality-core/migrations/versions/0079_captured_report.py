"""Disposable fixed captured reports; no financial authority or historical manifest."""

from alembic import op
from sqlalchemy import text

revision = "0079_captured_report"
down_revision = "0078_captured_cost_basis"
branch_labels = None
depends_on = None

TABLES = [
    "cost_generation",
    "cost_inventory_row",
    "cost_contribution_row",
    "cost_publication",
]
DDL = [
    "\nCREATE TABLE cost_generation (\n\tcaptured_basis_id VARCHAR NOT NULL, \n\tkind VARCHAR NOT NULL, \n\talgorithm_version VARCHAR NOT NULL, \n\tscope_key VARCHAR(64) NOT NULL, \n\tstate VARCHAR NOT NULL, \n\tcompleted_at TIMESTAMP WITH TIME ZONE, \n\tinventory_count INTEGER NOT NULL, \n\tcontribution_count INTEGER NOT NULL, \n\toutput_hash VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, scope_key, id), \n\tUNIQUE (tenant_id, captured_basis_id, algorithm_version), \n\tFOREIGN KEY(tenant_id, captured_basis_id) REFERENCES cost_captured_basis (tenant_id, id), \n\tCONSTRAINT ck_cost_generation_version CHECK (kind='captured_review_selection_v1' AND algorithm_version='captured-report-v1' AND length(scope_key)=64 AND length(output_hash)=64), \n\tCONSTRAINT ck_cost_generation_state CHECK (state IN ('building','sealed') AND ((state='sealed') = (completed_at IS NOT NULL))), \n\tCONSTRAINT ck_cost_generation_counts CHECK (inventory_count>=0 AND contribution_count>=0 AND inventory_count+contribution_count<=10), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_generation_captured_basis_id ON cost_generation (captured_basis_id)",
    "CREATE INDEX ix_cost_generation_tenant_id ON cost_generation (tenant_id)",
    "\nCREATE TABLE cost_inventory_row (\n\tgeneration_id VARCHAR NOT NULL, \n\tinventory_basis_member_id VARCHAR NOT NULL, \n\tstate VARCHAR NOT NULL, \n\tcurrency VARCHAR, \n\tbase_unit VARCHAR, \n\tmethod VARCHAR, \n\towner_party_id VARCHAR, \n\tremaining_quantity NUMERIC(18, 4), \n\tacquisition_value NUMERIC(18, 4), \n\tcarrying_value NUMERIC(18, 4), \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, generation_id, inventory_basis_member_id), \n\tFOREIGN KEY(tenant_id, generation_id) REFERENCES cost_generation (tenant_id, id), \n\tFOREIGN KEY(tenant_id, inventory_basis_member_id) REFERENCES cost_captured_inventory_basis (tenant_id, id), \n\tFOREIGN KEY(tenant_id, owner_party_id) REFERENCES party (tenant_id, id), \n\tCONSTRAINT ck_cost_inventory_row_shape CHECK ((state='available_at_capture' AND currency IS NOT NULL AND base_unit IS NOT NULL AND method IS NOT NULL AND owner_party_id IS NOT NULL AND remaining_quantity IS NOT NULL AND acquisition_value IS NOT NULL) OR (state='unknown_at_capture' AND currency IS NULL AND base_unit IS NULL AND method IS NULL AND owner_party_id IS NULL AND remaining_quantity IS NULL AND acquisition_value IS NULL AND carrying_value IS NULL)), \n\tCONSTRAINT ck_cost_inventory_row_amounts CHECK (remaining_quantity>=0 AND acquisition_value>=0 AND carrying_value>=0 AND carrying_value<=acquisition_value), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_inventory_group ON cost_inventory_row (tenant_id, generation_id, currency, base_unit, method, owner_party_id)",
    "CREATE INDEX ix_cost_inventory_row_generation_id ON cost_inventory_row (generation_id)",
    "CREATE INDEX ix_cost_inventory_row_inventory_basis_member_id ON cost_inventory_row (inventory_basis_member_id)",
    "CREATE INDEX ix_cost_inventory_row_owner_party_id ON cost_inventory_row (owner_party_id)",
    "CREATE INDEX ix_cost_inventory_row_tenant_id ON cost_inventory_row (tenant_id)",
    "\nCREATE TABLE cost_contribution_row (\n\tgeneration_id VARCHAR NOT NULL, \n\tcontribution_basis_member_id VARCHAR NOT NULL, \n\tstate VARCHAR NOT NULL, \n\tcurrency VARCHAR, \n\tbase_unit VARCHAR, \n\trevenue NUMERIC(18, 4), \n\tgoods_cost NUMERIC(18, 4), \n\tdirect_selling_cost NUMERIC(18, 4), \n\tallocated_selling_cost NUMERIC(18, 4), \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, generation_id, contribution_basis_member_id), \n\tFOREIGN KEY(tenant_id, generation_id) REFERENCES cost_generation (tenant_id, id), \n\tFOREIGN KEY(tenant_id, contribution_basis_member_id) REFERENCES cost_captured_contribution_basis (tenant_id, id), \n\tCONSTRAINT ck_cost_contribution_row_shape CHECK ((state='available_at_capture' AND currency IS NOT NULL AND base_unit IS NOT NULL AND revenue IS NOT NULL AND goods_cost IS NOT NULL) OR (state='unknown_at_capture' AND currency IS NULL AND base_unit IS NULL AND revenue IS NULL AND goods_cost IS NULL AND direct_selling_cost IS NULL AND allocated_selling_cost IS NULL)), \n\tCONSTRAINT ck_cost_contribution_row_goods CHECK (goods_cost>=0), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_contribution_group ON cost_contribution_row (tenant_id, generation_id, currency, base_unit)",
    "CREATE INDEX ix_cost_contribution_row_contribution_basis_member_id ON cost_contribution_row (contribution_basis_member_id)",
    "CREATE INDEX ix_cost_contribution_row_generation_id ON cost_contribution_row (generation_id)",
    "CREATE INDEX ix_cost_contribution_row_tenant_id ON cost_contribution_row (tenant_id)",
    "\nCREATE TABLE cost_publication (\n\tscope_key VARCHAR(64) NOT NULL, \n\tgeneration_id VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, scope_key), \n\tFOREIGN KEY(tenant_id, scope_key, generation_id) REFERENCES cost_generation (tenant_id, scope_key, id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_publication_generation_id ON cost_publication (generation_id)",
    "CREATE INDEX ix_cost_publication_tenant_id ON cost_publication (tenant_id)",
]

GUARD = """
CREATE FUNCTION guard_captured_report() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent_state text; parent_basis text; member_basis text; n integer; m integer;
BEGIN
 IF TG_TABLE_NAME = 'cost_generation' THEN
  IF TG_OP = 'INSERT' THEN
   IF NEW.state <> 'building' OR NOT EXISTS (
    SELECT 1 FROM cost_captured_basis WHERE tenant_id=NEW.tenant_id
    AND id=NEW.captured_basis_id AND state='sealed') THEN
    RAISE EXCEPTION 'A report starts building from a sealed retained basis';
   END IF;
   RETURN NEW;
  END IF;
  IF TG_OP = 'DELETE' THEN
   IF EXISTS (SELECT 1 FROM cost_publication WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id) THEN
    RAISE EXCEPTION 'Published report cannot be discarded';
   END IF;
   DELETE FROM cost_inventory_row WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id;
   DELETE FROM cost_contribution_row WHERE tenant_id=OLD.tenant_id AND generation_id=OLD.id;
   RETURN OLD;
  END IF;
  IF OLD.state='sealed' OR NEW.tenant_id<>OLD.tenant_id OR NEW.id<>OLD.id
    OR NEW.captured_basis_id<>OLD.captured_basis_id OR NEW.scope_key<>OLD.scope_key THEN
   RAISE EXCEPTION 'Sealed report or report identity is immutable';
  END IF;
  IF NEW.state='sealed' THEN
   SELECT count(*) INTO n FROM cost_inventory_row WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;
   SELECT count(*) INTO m FROM cost_contribution_row WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;
   IF n<>NEW.inventory_count OR m<>NEW.contribution_count OR NOT EXISTS (
    SELECT 1 FROM cost_captured_basis WHERE tenant_id=NEW.tenant_id AND id=NEW.captured_basis_id
    AND inventory_count=n AND contribution_count=m) THEN
    RAISE EXCEPTION 'Report membership is incomplete';
   END IF;
  END IF;
  RETURN NEW;
 END IF;
 IF TG_TABLE_NAME='cost_publication' THEN
  IF TG_OP='UPDATE' AND (OLD.tenant_id<>NEW.tenant_id OR OLD.scope_key<>NEW.scope_key OR OLD.id<>NEW.id) THEN
   RAISE EXCEPTION 'Publication scope is immutable';
  END IF;
  SELECT state INTO parent_state FROM cost_generation WHERE tenant_id=NEW.tenant_id
   AND id=NEW.generation_id AND scope_key=NEW.scope_key FOR UPDATE;
  IF parent_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Publication requires sealed matching scope'; END IF;
  RETURN NEW;
 END IF;
 IF TG_OP='DELETE' AND pg_trigger_depth()=2 THEN RETURN OLD; END IF;
 IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Report rows are immutable'; END IF;
 SELECT state,captured_basis_id INTO parent_state,parent_basis FROM cost_generation
  WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id FOR UPDATE;
 IF parent_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Report row requires building generation'; END IF;
 IF TG_TABLE_NAME='cost_inventory_row' THEN
  SELECT basis_id INTO member_basis FROM cost_captured_inventory_basis
   WHERE tenant_id=NEW.tenant_id AND id=NEW.inventory_basis_member_id;
 ELSE
  SELECT basis_id INTO member_basis FROM cost_captured_contribution_basis
   WHERE tenant_id=NEW.tenant_id AND id=NEW.contribution_basis_member_id;
 END IF;
 IF member_basis IS DISTINCT FROM parent_basis THEN RAISE EXCEPTION 'Report member belongs to another basis'; END IF;
 RETURN NEW;
END $$
"""


def upgrade():
    for statement in DDL:
        op.execute(statement)
    op.execute(GUARD)
    for name in TABLES:
        operations = (
            "INSERT OR UPDATE"
            if name == "cost_publication"
            else "INSERT OR UPDATE OR DELETE"
        )
        op.execute(
            f"CREATE TRIGGER guard_captured_report_row BEFORE {operations} ON {name} FOR EACH ROW EXECUTE FUNCTION guard_captured_report()"
        )


def downgrade():
    if op.get_bind().scalar(text("SELECT EXISTS (SELECT 1 FROM cost_generation)")):
        raise RuntimeError("Discard captured report caches before downgrade.")
    for name in reversed(TABLES):
        op.drop_table(name)
    op.execute("DROP FUNCTION guard_captured_report()")
