"""Disposable retained-inventory publications (spec242); no financial authority."""

from alembic import op
from sqlalchemy import text

revision = "0075_inventory_generations"
down_revision = "0074_selling_costs"
branch_labels = None
depends_on = None

TABLES = [
    "cost_inventory_generation",
    "cost_inventory_snapshot",
    "cost_inventory_publication",
]
DDL = [
    "\nCREATE TABLE cost_inventory_generation (\n\treview_id VARCHAR NOT NULL, \n\talgorithm_version VARCHAR NOT NULL, \n\tcompleted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\toutput_hash VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, review_id, id), \n\tUNIQUE (tenant_id, review_id, algorithm_version), \n\tFOREIGN KEY(tenant_id, review_id) REFERENCES cost_inventory_review (tenant_id, id), \n\tCONSTRAINT ck_inventory_generation_version CHECK (algorithm_version='inventory-v1' AND length(output_hash)=64), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_inventory_generation_tenant_id ON cost_inventory_generation (tenant_id)",
    "\nCREATE TABLE cost_inventory_snapshot (\n\tgeneration_id VARCHAR NOT NULL, \n\tremaining_quantity NUMERIC(18, 4) NOT NULL, \n\tacquisition_value NUMERIC(18, 4) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, generation_id), \n\tFOREIGN KEY(tenant_id, generation_id) REFERENCES cost_inventory_generation (tenant_id, id), \n\tCONSTRAINT ck_inventory_snapshot_amounts CHECK (remaining_quantity>=0 AND acquisition_value>=0), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_inventory_snapshot_tenant_id ON cost_inventory_snapshot (tenant_id)",
    "\nCREATE TABLE cost_inventory_publication (\n\treview_id VARCHAR NOT NULL, \n\tgeneration_id VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, review_id), \n\tFOREIGN KEY(tenant_id, review_id) REFERENCES cost_inventory_review (tenant_id, id), \n\tFOREIGN KEY(tenant_id, review_id, generation_id) REFERENCES cost_inventory_generation (tenant_id, review_id, id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_inventory_publication_tenant_id ON cost_inventory_publication (tenant_id)",
]


def upgrade():
    for statement in DDL:
        op.execute(statement)


def downgrade():
    if op.get_bind().scalar(
        text(
            "SELECT EXISTS (SELECT 1 FROM scheduled_job_run WHERE job_type='costing.inventory.refresh' AND status IN ('pending','running','retry','unresolved'))"
        )
    ):
        raise RuntimeError(
            "Cannot remove inventory caches with unfinished costing jobs."
        )
    for name in reversed(TABLES):
        op.drop_table(name)
