"""Retain approved captured-review selection independently of disposable outputs."""

from alembic import op
from sqlalchemy import text

revision = "0078_captured_cost_basis"
down_revision = "0077_company_cost_census"
branch_labels = None
depends_on = None

TABLES = [
    "cost_captured_basis",
    "cost_captured_inventory_basis",
    "cost_captured_contribution_basis",
]

DDL = [
    "\nCREATE TABLE cost_captured_basis (\n\tcensus_id VARCHAR NOT NULL, \n\trequest_id VARCHAR(128) NOT NULL, \n\trequest_hash VARCHAR(64) NOT NULL, \n\tbasis_version VARCHAR NOT NULL, \n\tstate VARCHAR NOT NULL, \n\tsealed_at TIMESTAMP WITH TIME ZONE, \n\tinventory_count INTEGER NOT NULL, \n\tcontribution_count INTEGER NOT NULL, \n\tbasis_digest VARCHAR(64) NOT NULL, \n\tobservations JSONB NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, request_id), \n\tFOREIGN KEY(tenant_id, census_id) REFERENCES cost_company_census (tenant_id, id), \n\tCONSTRAINT ck_captured_basis_version CHECK (basis_version='captured-review-basis-v2' AND length(request_hash)=64 AND length(basis_digest)=64), \n\tCONSTRAINT ck_captured_basis_state CHECK (state IN ('building','sealed') AND ((state='sealed') = (sealed_at IS NOT NULL))), \n\tCONSTRAINT ck_captured_basis_counts CHECK (inventory_count>=0 AND contribution_count>=0 AND inventory_count+contribution_count<=10), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_captured_basis_census_id ON cost_captured_basis (census_id)",
    "CREATE INDEX ix_cost_captured_basis_tenant_id ON cost_captured_basis (tenant_id)",
    "\nCREATE TABLE cost_captured_inventory_basis (\n\tbasis_id VARCHAR NOT NULL, \n\titem_id VARCHAR NOT NULL, \n\treview_id VARCHAR, \n\tobservations JSONB NOT NULL, \n\tcontent_hash VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, basis_id, item_id), \n\tFOREIGN KEY(tenant_id, basis_id) REFERENCES cost_captured_basis (tenant_id, id), \n\tFOREIGN KEY(tenant_id, item_id) REFERENCES item (tenant_id, id), \n\tFOREIGN KEY(tenant_id, review_id) REFERENCES cost_inventory_review (tenant_id, id), \n\tCONSTRAINT ck_captured_inventory_hash CHECK (length(content_hash)=64), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_captured_inventory_basis_basis_id ON cost_captured_inventory_basis (basis_id)",
    "CREATE INDEX ix_cost_captured_inventory_basis_item_id ON cost_captured_inventory_basis (item_id)",
    "CREATE INDEX ix_cost_captured_inventory_basis_review_id ON cost_captured_inventory_basis (review_id)",
    "CREATE INDEX ix_cost_captured_inventory_basis_tenant_id ON cost_captured_inventory_basis (tenant_id)",
    "\nCREATE TABLE cost_captured_contribution_basis (\n\tbasis_id VARCHAR NOT NULL, \n\tdocument_line_id VARCHAR NOT NULL, \n\treview_id VARCHAR, \n\tobservations JSONB NOT NULL, \n\tcontent_hash VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, basis_id, document_line_id), \n\tFOREIGN KEY(tenant_id, basis_id) REFERENCES cost_captured_basis (tenant_id, id), \n\tFOREIGN KEY(tenant_id, document_line_id) REFERENCES document_line (tenant_id, id), \n\tFOREIGN KEY(tenant_id, review_id) REFERENCES cost_contribution_review (tenant_id, id), \n\tCONSTRAINT ck_captured_contribution_hash CHECK (length(content_hash)=64), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_captured_contribution_basis_basis_id ON cost_captured_contribution_basis (basis_id)",
    "CREATE INDEX ix_cost_captured_contribution_basis_document_line_id ON cost_captured_contribution_basis (document_line_id)",
    "CREATE INDEX ix_cost_captured_contribution_basis_review_id ON cost_captured_contribution_basis (review_id)",
    "CREATE INDEX ix_cost_captured_contribution_basis_tenant_id ON cost_captured_contribution_basis (tenant_id)",
]

GUARD = """
CREATE FUNCTION guard_captured_basis() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent_state text;
BEGIN
  IF TG_TABLE_NAME = 'cost_captured_basis' THEN
    IF OLD.state = 'sealed' THEN
      RAISE EXCEPTION 'Sealed captured basis is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
  END IF;
  IF TG_OP <> 'INSERT' THEN
    RAISE EXCEPTION 'Captured basis members are immutable';
  END IF;
  SELECT state INTO parent_state FROM cost_captured_basis
    WHERE tenant_id=NEW.tenant_id AND id=NEW.basis_id FOR UPDATE;
  IF parent_state IS DISTINCT FROM 'building' THEN
    RAISE EXCEPTION 'Captured basis member requires a building same-tenant basis';
  END IF;
  RETURN NEW;
END $$
"""


def upgrade():
    for statement in DDL:
        op.execute(statement)
    op.execute(GUARD)
    op.execute(
        "CREATE TRIGGER guard_captured_basis_header BEFORE UPDATE OR DELETE ON cost_captured_basis FOR EACH ROW EXECUTE FUNCTION guard_captured_basis()"
    )
    for name in TABLES[1:]:
        op.execute(
            f"CREATE TRIGGER guard_captured_basis_member BEFORE INSERT OR UPDATE OR DELETE ON {name} FOR EACH ROW EXECUTE FUNCTION guard_captured_basis()"
        )


def downgrade():
    if op.get_bind().scalar(text("SELECT EXISTS (SELECT 1 FROM cost_captured_basis)")):
        raise RuntimeError("Cannot remove retained captured basis history.")
    for name in reversed(TABLES):
        op.drop_table(name)
    op.execute("DROP FUNCTION guard_captured_basis()")
