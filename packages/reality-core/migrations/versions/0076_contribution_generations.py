"""Disposable joint contribution observations (spec242); no financial authority."""

from alembic import op
from sqlalchemy import text

revision = "0076_contribution_generations"
down_revision = "0075_inventory_generations"
branch_labels = None
depends_on = None

TABLES = ["cost_contribution_generation", "cost_contribution_snapshot"]
DDL = [
    "\nCREATE TABLE cost_contribution_generation (\n\taction_id VARCHAR NOT NULL, \n\talgorithm_version VARCHAR NOT NULL, \n\tcompleted_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\toutput_hash VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, action_id, algorithm_version), \n\tFOREIGN KEY(tenant_id, action_id) REFERENCES action (tenant_id, id), \n\tCONSTRAINT ck_contribution_generation_version CHECK (algorithm_version='commercial-v1' AND length(output_hash)=64), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_contribution_generation_tenant_id ON cost_contribution_generation (tenant_id)",
    "\nCREATE TABLE cost_contribution_snapshot (\n\tgeneration_id VARCHAR NOT NULL, \n\treview_id VARCHAR NOT NULL, \n\tgoods_cost NUMERIC(18, 4) NOT NULL, \n\tknown_direct_selling_cost NUMERIC(18, 4), \n\tknown_allocated_selling_cost NUMERIC(18, 4), \n\tselling_complete BOOLEAN NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, generation_id, review_id), \n\tFOREIGN KEY(tenant_id, generation_id) REFERENCES cost_contribution_generation (tenant_id, id), \n\tFOREIGN KEY(tenant_id, review_id) REFERENCES cost_contribution_review (tenant_id, id), \n\tCONSTRAINT ck_contribution_snapshot_goods CHECK (goods_cost>=0), \n\tCONSTRAINT ck_contribution_snapshot_selling CHECK ((known_direct_selling_cost IS NULL) = (known_allocated_selling_cost IS NULL) AND (NOT selling_complete OR known_direct_selling_cost IS NOT NULL)), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_contribution_snapshot_tenant_id ON cost_contribution_snapshot (tenant_id)",
]


def upgrade():
    for statement in DDL:
        op.execute(statement)


def downgrade():
    if op.get_bind().scalar(
        text(
            "SELECT EXISTS (SELECT 1 FROM scheduled_job_run WHERE job_type='costing.contribution.refresh' AND status IN ('pending','running','retry','unresolved'))"
        )
    ):
        raise RuntimeError(
            "Cannot remove contribution caches with unfinished costing jobs."
        )
    for name in reversed(TABLES):
        op.drop_table(name)
