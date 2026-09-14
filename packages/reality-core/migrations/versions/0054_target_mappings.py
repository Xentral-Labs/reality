"""Add Finance-only external targets and reviewed mapping revisions."""

import sqlalchemy as sa
from alembic import op

revision = "0054_target_mappings"
down_revision = "0053_source_classification"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE accounting_target (
            id VARCHAR NOT NULL,
            tenant_id VARCHAR NOT NULL,
            namespace VARCHAR(200) NOT NULL,
            name VARCHAR(200) NOT NULL,
            state VARCHAR NOT NULL,
            revision INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (id),
            UNIQUE (tenant_id, id),
            UNIQUE (tenant_id, namespace),
            CONSTRAINT ck_accounting_target_values CHECK (state IN ('active','blocked') AND revision > 0 AND length(trim(namespace)) > 0 AND length(trim(name)) > 0),
            FOREIGN KEY(tenant_id) REFERENCES tenant (id)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_accounting_target_tenant_id ON accounting_target (tenant_id)"
    )
    op.execute(
        """
        CREATE TABLE accounting_target_reference (
            id VARCHAR NOT NULL,
            tenant_id VARCHAR NOT NULL,
            target_id VARCHAR NOT NULL,
            kind VARCHAR NOT NULL,
            code VARCHAR(200) NOT NULL,
            name VARCHAR(200) NOT NULL,
            state VARCHAR NOT NULL,
            revision INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(tenant_id, target_id) REFERENCES accounting_target (tenant_id, id),
            UNIQUE (tenant_id, target_id, kind, code),
            UNIQUE (tenant_id, target_id, id, kind),
            CONSTRAINT ck_accounting_reference_values CHECK (kind IN ('account','tax_code') AND state IN ('active','blocked') AND revision > 0 AND length(trim(code)) > 0 AND length(trim(name)) > 0),
            FOREIGN KEY(tenant_id) REFERENCES tenant (id)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_accounting_target_reference_tenant_id ON accounting_target_reference (tenant_id)"
    )
    op.execute(
        """
        CREATE TABLE finance_target_mapping_revision (
            id VARCHAR NOT NULL,
            tenant_id VARCHAR NOT NULL,
            target_id VARCHAR NOT NULL,
            mapping_kind VARCHAR NOT NULL,
            local_account_id VARCHAR,
            transaction_kind VARCHAR,
            case_reference_id VARCHAR,
            group_mode VARCHAR,
            group_reference_id VARCHAR,
            external_account_id VARCHAR NOT NULL,
            external_tax_code_id VARCHAR,
            case_kind VARCHAR NOT NULL,
            group_kind VARCHAR NOT NULL,
            account_kind VARCHAR NOT NULL,
            tax_kind VARCHAR NOT NULL,
            revision INTEGER NOT NULL,
            replaces_id VARCHAR,
            state VARCHAR NOT NULL,
            is_current BOOLEAN NOT NULL,
            configuration_snapshot JSONB NOT NULL,
            reason TEXT NOT NULL,
            actor_id VARCHAR,
            action_id VARCHAR NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (id),
            UNIQUE (tenant_id, id),
            FOREIGN KEY(tenant_id, target_id) REFERENCES accounting_target (tenant_id, id),
            FOREIGN KEY(tenant_id, replaces_id) REFERENCES finance_target_mapping_revision (tenant_id, id),
            FOREIGN KEY(tenant_id, local_account_id) REFERENCES subledger_account (tenant_id, id),
            FOREIGN KEY(tenant_id, case_reference_id, case_kind) REFERENCES finance_reference (tenant_id, id, kind),
            FOREIGN KEY(tenant_id, group_reference_id, group_kind) REFERENCES finance_reference (tenant_id, id, kind),
            FOREIGN KEY(tenant_id, target_id, external_account_id, account_kind) REFERENCES accounting_target_reference (tenant_id, target_id, id, kind),
            FOREIGN KEY(tenant_id, target_id, external_tax_code_id, tax_kind) REFERENCES accounting_target_reference (tenant_id, target_id, id, kind),
            CONSTRAINT ck_target_mapping_reference_kinds CHECK (case_kind = 'case_code' AND group_kind = 'coding_group' AND account_kind = 'account' AND tax_kind = 'tax_code'),
            CONSTRAINT ck_target_mapping_values CHECK (state IN ('active','blocked') AND revision > 0 AND length(trim(reason)) > 0),
            CONSTRAINT ck_target_mapping_shape CHECK ((mapping_kind = 'local_account' AND local_account_id IS NOT NULL AND transaction_kind IS NULL AND case_reference_id IS NULL AND group_mode IS NULL AND group_reference_id IS NULL AND external_tax_code_id IS NULL) OR (mapping_kind = 'case_routing' AND local_account_id IS NULL AND transaction_kind IS NOT NULL AND transaction_kind IN ('sales_invoice','supplier_invoice','credit_note','supplier_credit_note') AND case_reference_id IS NOT NULL AND group_mode IS NOT NULL AND ((group_mode = 'none' AND group_reference_id IS NULL) OR (group_mode = 'exact' AND group_reference_id IS NOT NULL)))),
            FOREIGN KEY(tenant_id) REFERENCES tenant (id),
            FOREIGN KEY(action_id) REFERENCES action (id)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_finance_target_mapping_revision_tenant_id ON finance_target_mapping_revision (tenant_id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_target_mapping_account_current ON finance_target_mapping_revision (tenant_id, target_id, local_account_id) WHERE mapping_kind = 'local_account' AND is_current"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_target_mapping_account_revision ON finance_target_mapping_revision (tenant_id, target_id, local_account_id, revision) WHERE mapping_kind = 'local_account'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_target_mapping_case_current ON finance_target_mapping_revision (tenant_id, target_id, transaction_kind, case_reference_id) WHERE mapping_kind = 'case_routing' AND group_mode = 'none' AND is_current"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_target_mapping_case_revision ON finance_target_mapping_revision (tenant_id, target_id, transaction_kind, case_reference_id, revision) WHERE mapping_kind = 'case_routing' AND group_mode = 'none'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_target_mapping_group_current ON finance_target_mapping_revision (tenant_id, target_id, transaction_kind, case_reference_id, group_reference_id) WHERE mapping_kind = 'case_routing' AND group_mode = 'exact' AND is_current"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_target_mapping_group_revision ON finance_target_mapping_revision (tenant_id, target_id, transaction_kind, case_reference_id, group_reference_id, revision) WHERE mapping_kind = 'case_routing' AND group_mode = 'exact'"
    )


def downgrade():
    for table in (
        "finance_target_mapping_revision",
        "accounting_target_reference",
        "accounting_target",
    ):
        if op.get_bind().scalar(sa.text(f"SELECT EXISTS (SELECT 1 FROM {table})")):
            raise RuntimeError(
                "Target configuration history exists; downgrade would discard decisions."
            )
    for table in (
        "finance_target_mapping_revision",
        "accounting_target_reference",
        "accounting_target",
    ):
        op.drop_table(table)
