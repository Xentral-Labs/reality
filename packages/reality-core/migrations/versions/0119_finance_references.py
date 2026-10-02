"""Consolidate typed Finance catalogs without changing logical contracts (spec 324)."""

import sqlalchemy as sa
from alembic import op

revision = "0119_finance_references"
down_revision = "0118_account_defaults"
branch_labels = None
depends_on = None

# Frozen revision-0110 DDL and incoming constraint inventory; no live ORM imports.
LEGACY_DDL = [
    "\nCREATE TABLE finance_reference (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tkind VARCHAR NOT NULL, \n\tcode VARCHAR(100) NOT NULL, \n\tname VARCHAR(200) NOT NULL, \n\tstate VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tPRIMARY KEY (tenant_id, id), \n\tCONSTRAINT uq_finance_reference_kind_id UNIQUE (tenant_id, id, kind), \n\tCONSTRAINT uq_finance_reference_code UNIQUE (tenant_id, kind, code), \n\tCONSTRAINT ck_finance_reference_kind CHECK (kind IN ('cost_center','case_code','coding_group')), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tCONSTRAINT ck_finance_reference_state CHECK (state IN ('active','blocked')), \n\tCONSTRAINT ck_finance_reference_revision CHECK (revision > 0), \n\tCONSTRAINT ck_finance_reference_labels CHECK (length(trim(code)) > 0 AND length(trim(name)) > 0)\n)\n\n",
    "CREATE INDEX ix_finance_reference_tenant_id ON finance_reference (tenant_id)",
    "\nCREATE TABLE accounting_target_reference (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\ttarget_id VARCHAR NOT NULL, \n\tkind VARCHAR NOT NULL, \n\tcode VARCHAR(200) NOT NULL, \n\tname VARCHAR(200) NOT NULL, \n\tstate VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (tenant_id, id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tUNIQUE (tenant_id, target_id, id, kind), \n\tFOREIGN KEY(tenant_id, target_id) REFERENCES accounting_target (tenant_id, id), \n\tUNIQUE (tenant_id, target_id, kind, code), \n\tCONSTRAINT ck_accounting_reference_values CHECK (kind IN ('account','tax_code') AND state IN ('active','blocked') AND revision > 0 AND length(trim(code)) > 0 AND length(trim(name)) > 0)\n)\n\n",
    "CREATE INDEX ix_accounting_target_reference_tenant_id ON accounting_target_reference (tenant_id)",
]
STORE_DDL = [
    "\nCREATE TABLE finance_reference_store (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tkind VARCHAR NOT NULL, \n\tcode VARCHAR(200) NOT NULL, \n\tname VARCHAR(200) NOT NULL, \n\tstate VARCHAR NOT NULL, \n\trevision INTEGER NOT NULL, \n\ttarget_id VARCHAR, \n\tcreated_at TIMESTAMP WITH TIME ZONE, \n\tupdated_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (tenant_id, id, kind), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tFOREIGN KEY(tenant_id, target_id) REFERENCES accounting_target (tenant_id, id), \n\tCONSTRAINT uq_reference_store_target_id UNIQUE (tenant_id, target_id, id, kind), \n\tCONSTRAINT ck_reference_store_shape CHECK ((kind IN ('cost_center','case_code','coding_group') AND target_id IS NULL AND created_at IS NULL AND updated_at IS NULL AND length(code)<=100) OR (kind IN ('account','tax_code') AND target_id IS NOT NULL AND created_at IS NOT NULL AND updated_at IS NOT NULL)), \n\tCONSTRAINT ck_reference_store_values CHECK (state IN ('active','blocked') AND revision>0 AND length(trim(code))>0 AND length(trim(name))>0)\n)\n\n",
    "CREATE UNIQUE INDEX uq_reference_store_external_code ON finance_reference_store (tenant_id, target_id, kind, code) WHERE kind IN ('account','tax_code')",
    "CREATE UNIQUE INDEX uq_reference_store_external_id ON finance_reference_store (tenant_id, id) WHERE kind IN ('account','tax_code')",
    "CREATE UNIQUE INDEX uq_reference_store_internal_code ON finance_reference_store (tenant_id, kind, code) WHERE kind IN ('cost_center','case_code','coding_group')",
    "CREATE UNIQUE INDEX uq_reference_store_internal_id ON finance_reference_store (tenant_id, id) WHERE kind IN ('cost_center','case_code','coding_group')",
]
INCOMING = [
    [
        "component_assignment_part",
        "fk_assignment_part_center",
        "FOREIGN KEY (tenant_id, cost_center_reference_id, reference_kind) REFERENCES finance_reference(tenant_id, id, kind)",
        "finance_reference",
    ],
    [
        "component_assignment_revision",
        "fk_assignment_case",
        "FOREIGN KEY (tenant_id, case_reference_id, case_kind) REFERENCES finance_reference(tenant_id, id, kind)",
        "finance_reference",
    ],
    [
        "component_assignment_revision",
        "fk_assignment_group",
        "FOREIGN KEY (tenant_id, group_reference_id, group_kind) REFERENCES finance_reference(tenant_id, id, kind)",
        "finance_reference",
    ],
    [
        "finance_target_mapping_revision",
        "finance_target_mapping_revis_tenant_id_target_id_external_fkey1",
        "FOREIGN KEY (tenant_id, target_id, external_tax_code_id, tax_kind) REFERENCES accounting_target_reference(tenant_id, target_id, id, kind)",
        "accounting_target_reference",
    ],
    [
        "finance_target_mapping_revision",
        "finance_target_mapping_revisi_tenant_id_case_reference_id__fkey",
        "FOREIGN KEY (tenant_id, case_reference_id, case_kind) REFERENCES finance_reference(tenant_id, id, kind)",
        "finance_reference",
    ],
    [
        "finance_target_mapping_revision",
        "finance_target_mapping_revisi_tenant_id_group_reference_id_fkey",
        "FOREIGN KEY (tenant_id, group_reference_id, group_kind) REFERENCES finance_reference(tenant_id, id, kind)",
        "finance_reference",
    ],
    [
        "finance_target_mapping_revision",
        "finance_target_mapping_revisi_tenant_id_target_id_external_fkey",
        "FOREIGN KEY (tenant_id, target_id, external_account_id, account_kind) REFERENCES accounting_target_reference(tenant_id, target_id, id, kind)",
        "accounting_target_reference",
    ],
    [
        "source_classification_mapping_revision",
        "fk_source_mapping_reference",
        "FOREIGN KEY (tenant_id, reference_id, field_kind) REFERENCES finance_reference(tenant_id, id, kind)",
        "finance_reference",
    ],
]
VIEW_DDL = {
    "finance_reference": "CREATE VIEW finance_reference AS SELECT id,tenant_id,kind,code,name,state,revision FROM finance_reference_store WHERE kind IN ('cost_center','case_code','coding_group') WITH LOCAL CHECK OPTION",
    "accounting_target_reference": "CREATE VIEW accounting_target_reference AS SELECT id,tenant_id,target_id,kind,code,name,state,revision,created_at,updated_at FROM finance_reference_store WHERE kind IN ('account','tax_code') WITH LOCAL CHECK OPTION",
}
COLUMNS = {
    "finance_reference": (
        "id",
        "tenant_id",
        "kind",
        "code",
        "name",
        "state",
        "revision",
    ),
    "accounting_target_reference": (
        "id",
        "tenant_id",
        "target_id",
        "kind",
        "code",
        "name",
        "state",
        "revision",
        "created_at",
        "updated_at",
    ),
}


def _lock():
    op.execute(
        "LOCK TABLE finance_reference,accounting_target_reference,component_assignment_part,component_assignment_revision,source_classification_mapping_revision,finance_target_mapping_revision IN ACCESS EXCLUSIVE MODE"
    )


def _verify(bind):
    for name, columns in COLUMNS.items():
        fields = ",".join(columns)
        predicate = (
            "kind IN ('cost_center','case_code','coding_group')"
            if name == "finance_reference"
            else "kind IN ('account','tax_code')"
        )
        legacy = f"SELECT {fields} FROM {name}"
        shared = f"SELECT {fields} FROM finance_reference_store WHERE {predicate}"
        if bind.scalar(
            sa.text(
                f"SELECT EXISTS (({legacy} EXCEPT {shared}) UNION ALL ({shared} EXCEPT {legacy}))"
            )
        ):
            raise RuntimeError(
                f"Catalog parity failed for {name}; original transaction retained."
            )


def _redirect(shared):
    for table, name, definition, target in INCOMING:
        op.execute(f'ALTER TABLE {table} DROP CONSTRAINT "{name}"')
        if shared:
            definition = definition.replace(
                f"REFERENCES {target}(", "REFERENCES finance_reference_store("
            )
        op.execute(f'ALTER TABLE {table} ADD CONSTRAINT "{name}" {definition}')


def upgrade():
    bind = op.get_bind()
    _lock()
    for sql in STORE_DDL:
        op.execute(sql)
    for name, columns in COLUMNS.items():
        fields = ",".join(columns)
        op.execute(
            f"INSERT INTO finance_reference_store ({fields}) SELECT {fields} FROM {name}"
        )
    _verify(bind)
    _redirect(True)
    for name in COLUMNS:
        op.drop_table(name)
        op.execute(VIEW_DDL[name])


def downgrade():
    bind = op.get_bind()
    _lock()
    for name in COLUMNS:
        op.execute(f"DROP VIEW {name}")
    for sql in LEGACY_DDL:
        op.execute(sql)
    for name, columns in COLUMNS.items():
        fields = ",".join(columns)
        predicate = (
            "kind IN ('cost_center','case_code','coding_group')"
            if name == "finance_reference"
            else "kind IN ('account','tax_code')"
        )
        op.execute(
            f"INSERT INTO {name} ({fields}) SELECT {fields} FROM finance_reference_store WHERE {predicate}"
        )
    _verify(bind)
    _redirect(False)
    op.drop_table("finance_reference_store")
