"""Add first-slice operational coordination (spec 371)."""

import sqlalchemy as sa
from alembic import op

revision = "0144_operational_cases"
down_revision = "0143_intake_review_mandates"
branch_labels = None
depends_on = None

# Frozen PostgreSQL DDL; never import evolving runtime models in a migration.
DDL = (
    "CREATE TABLE operational_case (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tkind VARCHAR NOT NULL, \n\torder_document_id VARCHAR, \n\treturn_announcement_id VARCHAR, \n\tpolicy_version INTEGER NOT NULL, \n\tcontrol_mode VARCHAR NOT NULL, \n\tcontrol_revision INTEGER NOT NULL, \n\ttakeover_user_id VARCHAR, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (tenant_id, id), \n\tFOREIGN KEY(tenant_id, order_document_id) REFERENCES document (tenant_id, id), \n\tFOREIGN KEY(tenant_id, return_announcement_id) REFERENCES return_announcement (tenant_id, id), \n\tUNIQUE (tenant_id, order_document_id), \n\tUNIQUE (tenant_id, return_announcement_id), \n\tCONSTRAINT ck_case_anchor CHECK ((kind = 'order_fulfillment' AND order_document_id IS NOT NULL AND return_announcement_id IS NULL) OR (kind = 'customer_return' AND order_document_id IS NULL AND return_announcement_id IS NOT NULL)), \n\tCONSTRAINT ck_case_control CHECK (control_mode IN ('automation', 'human')), \n\tCONSTRAINT ck_case_revision CHECK (control_revision >= 1 AND policy_version = 1), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tFOREIGN KEY(takeover_user_id) REFERENCES app_user (id)\n)",
    "CREATE INDEX ix_operational_case_takeover_user_id ON operational_case (takeover_user_id)",
    "CREATE TABLE case_commitment_link (\n\ttenant_id VARCHAR NOT NULL, \n\tcase_id VARCHAR NOT NULL, \n\tcommitment_id VARCHAR NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (tenant_id, case_id, commitment_id), \n\tFOREIGN KEY(tenant_id, case_id) REFERENCES operational_case (tenant_id, id), \n\tFOREIGN KEY(tenant_id, commitment_id) REFERENCES commitment (tenant_id, id)\n)",
    "CREATE INDEX ix_case_commitment_link_commitment_id ON case_commitment_link (tenant_id, commitment_id)",
    "CREATE TABLE case_proposal_link (\n\ttenant_id VARCHAR NOT NULL, \n\tcase_id VARCHAR NOT NULL, \n\tproposal_id VARCHAR NOT NULL, \n\tbound_control_revision INTEGER NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (tenant_id, case_id, proposal_id), \n\tFOREIGN KEY(tenant_id, case_id) REFERENCES operational_case (tenant_id, id), \n\tFOREIGN KEY(tenant_id, proposal_id) REFERENCES action (tenant_id, id), \n\tCONSTRAINT ck_case_binding_revision CHECK (bound_control_revision >= 1)\n)",
    "CREATE INDEX ix_case_proposal_link_proposal_id ON case_proposal_link (tenant_id, proposal_id)",
    "CREATE TABLE case_adoption (\n\ttenant_id VARCHAR NOT NULL, \n\tdecision_id VARCHAR NOT NULL, \n\tpolicy_version INTEGER NOT NULL, \n\tcapture_sequence BIGINT NOT NULL, \n\tselected_order_ids JSONB NOT NULL, \n\tselected_return_ids JSONB NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (tenant_id), \n\tFOREIGN KEY(tenant_id, decision_id) REFERENCES action (tenant_id, id), \n\tCONSTRAINT ck_case_adoption_boundary CHECK (capture_sequence >= 0 AND policy_version = 1), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)",
    "CREATE INDEX ix_case_adoption_decision_id ON case_adoption (tenant_id, decision_id)",
    "CREATE TABLE case_consumer_checkpoint (\n\ttenant_id VARCHAR NOT NULL, \n\tpolicy_version INTEGER NOT NULL, \n\tincorporated_sequence BIGINT NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (tenant_id, policy_version), \n\tCONSTRAINT ck_case_checkpoint CHECK (incorporated_sequence >= 0 AND policy_version = 1), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)",
)


def upgrade():
    for statement in DDL:
        op.execute(statement)


def downgrade():
    if (
        op.get_bind()
        .execute(sa.text("SELECT EXISTS (SELECT 1 FROM case_adoption)"))
        .scalar()
    ):
        raise RuntimeError(
            "Preserve actual operational case control history; disable automation and review before schema removal."
        )
    op.drop_table("case_consumer_checkpoint")
    op.drop_table("case_adoption")
    op.drop_table("case_proposal_link")
    op.drop_table("case_commitment_link")
    op.drop_table("operational_case")
