"""Share typed receipt manifest memberships, preserving original interfaces (spec 330)."""

import sqlalchemy as sa
from alembic import op

revision = "0120_manifest_members"
down_revision = "0119_finance_references"
branch_labels = None
depends_on = None

# Frozen predecessor and replacement DDL. No current model imports.
LEGACY_DDL = [
    "CREATE TABLE cost_manifest_receipt (manifest_id VARCHAR NOT NULL,receipt_basis_id VARCHAR NOT NULL,id VARCHAR NOT NULL,tenant_id VARCHAR NOT NULL,CONSTRAINT cost_manifest_receipt_pkey PRIMARY KEY (tenant_id,id),CONSTRAINT cost_manifest_receipt_tenant_id_manifest_id_receipt_basis_i_key UNIQUE (tenant_id,manifest_id,receipt_basis_id),CONSTRAINT cost_manifest_receipt_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenant (id),CONSTRAINT cost_manifest_receipt_tenant_id_manifest_id_fkey FOREIGN KEY (tenant_id,manifest_id) REFERENCES cost_input_manifest (tenant_id,id),CONSTRAINT cost_manifest_receipt_tenant_id_receipt_basis_id_fkey FOREIGN KEY (tenant_id,receipt_basis_id) REFERENCES cost_receipt_basis (tenant_id,id))",
    "CREATE INDEX ix_cost_manifest_receipt_manifest_id ON cost_manifest_receipt (manifest_id)",
    "CREATE INDEX ix_cost_manifest_receipt_receipt_basis_id ON cost_manifest_receipt (tenant_id,receipt_basis_id)",
    "CREATE TABLE cost_manifest_component (manifest_id VARCHAR NOT NULL,component_basis_id VARCHAR NOT NULL,id VARCHAR NOT NULL,tenant_id VARCHAR NOT NULL,CONSTRAINT cost_manifest_component_pkey PRIMARY KEY (tenant_id,id),CONSTRAINT cost_manifest_component_tenant_id_manifest_id_component_bas_key UNIQUE (tenant_id,manifest_id,component_basis_id),CONSTRAINT cost_manifest_component_tenant_id_component_basis_id_fkey FOREIGN KEY (tenant_id,component_basis_id) REFERENCES cost_component_basis (tenant_id,id),CONSTRAINT cost_manifest_component_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenant (id),CONSTRAINT cost_manifest_component_tenant_id_manifest_id_fkey FOREIGN KEY (tenant_id,manifest_id) REFERENCES cost_input_manifest (tenant_id,id))",
    "CREATE INDEX ix_cost_manifest_component_component_basis_id ON cost_manifest_component (tenant_id,component_basis_id)",
    "CREATE INDEX ix_cost_manifest_component_manifest_id ON cost_manifest_component (manifest_id)",
    "CREATE TABLE cost_manifest_attribution (manifest_id VARCHAR NOT NULL,attribution_revision_id VARCHAR NOT NULL,id VARCHAR NOT NULL,tenant_id VARCHAR NOT NULL,CONSTRAINT cost_manifest_attribution_pkey PRIMARY KEY (tenant_id,id),CONSTRAINT cost_manifest_attribution_tenant_id_manifest_id_attribution_key UNIQUE (tenant_id,manifest_id,attribution_revision_id),CONSTRAINT cost_manifest_attribution_tenant_id_attribution_revision_i_fkey FOREIGN KEY (tenant_id,attribution_revision_id) REFERENCES cost_attribution_revision (tenant_id,id),CONSTRAINT cost_manifest_attribution_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenant (id),CONSTRAINT cost_manifest_attribution_tenant_id_manifest_id_fkey FOREIGN KEY (tenant_id,manifest_id) REFERENCES cost_input_manifest (tenant_id,id))",
    "CREATE INDEX ix_cost_manifest_attribution_attribution_revision_id ON cost_manifest_attribution (tenant_id,attribution_revision_id)",
    "CREATE INDEX ix_cost_manifest_attribution_manifest_id ON cost_manifest_attribution (manifest_id)",
    "CREATE TABLE cost_manifest_correction (manifest_id VARCHAR NOT NULL,correction_basis_id VARCHAR NOT NULL,id VARCHAR NOT NULL,tenant_id VARCHAR NOT NULL,CONSTRAINT cost_manifest_correction_pkey PRIMARY KEY (tenant_id,id),CONSTRAINT cost_manifest_correction_tenant_id_manifest_id_correction_b_key UNIQUE (tenant_id,manifest_id,correction_basis_id),CONSTRAINT cost_manifest_correction_tenant_id_correction_basis_id_fkey FOREIGN KEY (tenant_id,correction_basis_id) REFERENCES cost_correction_basis (tenant_id,id),CONSTRAINT cost_manifest_correction_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenant (id),CONSTRAINT cost_manifest_correction_tenant_id_manifest_id_fkey FOREIGN KEY (tenant_id,manifest_id) REFERENCES cost_input_manifest (tenant_id,id))",
    "CREATE INDEX ix_cost_manifest_correction_correction_basis_id ON cost_manifest_correction (tenant_id,correction_basis_id)",
    "CREATE INDEX ix_cost_manifest_correction_manifest_id ON cost_manifest_correction (manifest_id)",
    "CREATE TABLE cost_manifest_replacement (manifest_id VARCHAR NOT NULL,replacement_id VARCHAR NOT NULL,id VARCHAR NOT NULL,tenant_id VARCHAR NOT NULL,CONSTRAINT cost_manifest_replacement_pkey PRIMARY KEY (tenant_id,id),CONSTRAINT cost_manifest_replacement_tenant_id_manifest_id_replacement_key UNIQUE (tenant_id,manifest_id,replacement_id),CONSTRAINT cost_manifest_replacement_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenant (id),CONSTRAINT cost_manifest_replacement_tenant_id_manifest_id_fkey FOREIGN KEY (tenant_id,manifest_id) REFERENCES cost_input_manifest (tenant_id,id),CONSTRAINT cost_manifest_replacement_tenant_id_replacement_id_fkey FOREIGN KEY (tenant_id,replacement_id) REFERENCES cost_component_replacement (tenant_id,id))",
    "CREATE INDEX ix_cost_manifest_replacement_manifest_id ON cost_manifest_replacement (manifest_id)",
    "CREATE INDEX ix_cost_manifest_replacement_replacement_id ON cost_manifest_replacement (tenant_id,replacement_id)",
]

STORE_DDL = [
    "\nCREATE TABLE cost_manifest_member (\n\ttenant_id VARCHAR NOT NULL, \n\tmember_family VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\tmanifest_id VARCHAR NOT NULL, \n\treceipt_basis_id VARCHAR, \n\tcomponent_basis_id VARCHAR, \n\tattribution_revision_id VARCHAR, \n\tcorrection_basis_id VARCHAR, \n\treplacement_id VARCHAR, \n\tPRIMARY KEY (tenant_id, member_family, id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tFOREIGN KEY(tenant_id, manifest_id) REFERENCES cost_input_manifest (tenant_id, id), \n\tFOREIGN KEY(tenant_id, receipt_basis_id) REFERENCES cost_receipt_basis (tenant_id, id), \n\tFOREIGN KEY(tenant_id, component_basis_id) REFERENCES cost_component_basis (tenant_id, id), \n\tFOREIGN KEY(tenant_id, attribution_revision_id) REFERENCES cost_attribution_revision (tenant_id, id), \n\tFOREIGN KEY(tenant_id, correction_basis_id) REFERENCES cost_correction_basis (tenant_id, id), \n\tFOREIGN KEY(tenant_id, replacement_id) REFERENCES cost_component_replacement (tenant_id, id), \n\tCONSTRAINT ck_cost_manifest_member_shape CHECK ((member_family='cost_manifest_receipt' AND receipt_basis_id IS NOT NULL AND component_basis_id IS NULL AND attribution_revision_id IS NULL AND correction_basis_id IS NULL AND replacement_id IS NULL) OR (member_family='cost_manifest_component' AND receipt_basis_id IS NULL AND component_basis_id IS NOT NULL AND attribution_revision_id IS NULL AND correction_basis_id IS NULL AND replacement_id IS NULL) OR (member_family='cost_manifest_attribution' AND receipt_basis_id IS NULL AND component_basis_id IS NULL AND attribution_revision_id IS NOT NULL AND correction_basis_id IS NULL AND replacement_id IS NULL) OR (member_family='cost_manifest_correction' AND receipt_basis_id IS NULL AND component_basis_id IS NULL AND attribution_revision_id IS NULL AND correction_basis_id IS NOT NULL AND replacement_id IS NULL) OR (member_family='cost_manifest_replacement' AND receipt_basis_id IS NULL AND component_basis_id IS NULL AND attribution_revision_id IS NULL AND correction_basis_id IS NULL AND replacement_id IS NOT NULL))\n)\n\n",
    "CREATE INDEX ix_cost_manifest_member_attribution_revision_id ON cost_manifest_member (tenant_id, attribution_revision_id)",
    "CREATE INDEX ix_cost_manifest_member_component_basis_id ON cost_manifest_member (tenant_id, component_basis_id)",
    "CREATE INDEX ix_cost_manifest_member_correction_basis_id ON cost_manifest_member (tenant_id, correction_basis_id)",
    "CREATE INDEX ix_cost_manifest_member_manifest_id ON cost_manifest_member (tenant_id, manifest_id)",
    "CREATE INDEX ix_cost_manifest_member_receipt_basis_id ON cost_manifest_member (tenant_id, receipt_basis_id)",
    "CREATE INDEX ix_cost_manifest_member_replacement_id ON cost_manifest_member (tenant_id, replacement_id)",
    "CREATE UNIQUE INDEX uq_manifest_member_attribution_revision_id ON cost_manifest_member (tenant_id, manifest_id, attribution_revision_id) WHERE member_family='cost_manifest_attribution'",
    "CREATE UNIQUE INDEX uq_manifest_member_component_basis_id ON cost_manifest_member (tenant_id, manifest_id, component_basis_id) WHERE member_family='cost_manifest_component'",
    "CREATE UNIQUE INDEX uq_manifest_member_correction_basis_id ON cost_manifest_member (tenant_id, manifest_id, correction_basis_id) WHERE member_family='cost_manifest_correction'",
    "CREATE UNIQUE INDEX uq_manifest_member_receipt_basis_id ON cost_manifest_member (tenant_id, manifest_id, receipt_basis_id) WHERE member_family='cost_manifest_receipt'",
    "CREATE UNIQUE INDEX uq_manifest_member_replacement_id ON cost_manifest_member (tenant_id, manifest_id, replacement_id) WHERE member_family='cost_manifest_replacement'",
]

FAMILIES = {
    "cost_manifest_receipt": "receipt_basis_id",
    "cost_manifest_component": "component_basis_id",
    "cost_manifest_attribution": "attribution_revision_id",
    "cost_manifest_correction": "correction_basis_id",
    "cost_manifest_replacement": "replacement_id",
}

COLUMNS = {
    "cost_manifest_receipt": ("manifest_id", "receipt_basis_id", "tenant_id", "id"),
    "cost_manifest_component": ("manifest_id", "component_basis_id", "tenant_id", "id"),
    "cost_manifest_attribution": (
        "manifest_id",
        "attribution_revision_id",
        "tenant_id",
        "id",
    ),
    "cost_manifest_correction": (
        "manifest_id",
        "correction_basis_id",
        "tenant_id",
        "id",
    ),
    "cost_manifest_replacement": ("manifest_id", "replacement_id", "tenant_id", "id"),
}

VIEW_DDL = {
    "cost_manifest_receipt": "CREATE VIEW cost_manifest_receipt AS SELECT manifest_id,receipt_basis_id,tenant_id,id FROM cost_manifest_member WHERE member_family='cost_manifest_receipt' WITH LOCAL CHECK OPTION",
    "cost_manifest_component": "CREATE VIEW cost_manifest_component AS SELECT manifest_id,component_basis_id,tenant_id,id FROM cost_manifest_member WHERE member_family='cost_manifest_component' WITH LOCAL CHECK OPTION",
    "cost_manifest_attribution": "CREATE VIEW cost_manifest_attribution AS SELECT manifest_id,attribution_revision_id,tenant_id,id FROM cost_manifest_member WHERE member_family='cost_manifest_attribution' WITH LOCAL CHECK OPTION",
    "cost_manifest_correction": "CREATE VIEW cost_manifest_correction AS SELECT manifest_id,correction_basis_id,tenant_id,id FROM cost_manifest_member WHERE member_family='cost_manifest_correction' WITH LOCAL CHECK OPTION",
    "cost_manifest_replacement": "CREATE VIEW cost_manifest_replacement AS SELECT manifest_id,replacement_id,tenant_id,id FROM cost_manifest_member WHERE member_family='cost_manifest_replacement' WITH LOCAL CHECK OPTION",
}

ROUTING_DDL = {
    "cost_manifest_receipt": [
        "CREATE FUNCTION public.insert_cost_manifest_receipt() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN INSERT INTO public.cost_manifest_member (manifest_id,receipt_basis_id,tenant_id,id,member_family) VALUES (NEW.manifest_id,NEW.receipt_basis_id,NEW.tenant_id,NEW.id,'cost_manifest_receipt') RETURNING manifest_id,receipt_basis_id,tenant_id,id INTO NEW.manifest_id,NEW.receipt_basis_id,NEW.tenant_id,NEW.id; RETURN NEW; END $$",
        "CREATE TRIGGER route_manifest_insert INSTEAD OF INSERT ON cost_manifest_receipt FOR EACH ROW EXECUTE FUNCTION public.insert_cost_manifest_receipt()",
    ],
    "cost_manifest_component": [
        "CREATE FUNCTION public.insert_cost_manifest_component() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN INSERT INTO public.cost_manifest_member (manifest_id,component_basis_id,tenant_id,id,member_family) VALUES (NEW.manifest_id,NEW.component_basis_id,NEW.tenant_id,NEW.id,'cost_manifest_component') RETURNING manifest_id,component_basis_id,tenant_id,id INTO NEW.manifest_id,NEW.component_basis_id,NEW.tenant_id,NEW.id; RETURN NEW; END $$",
        "CREATE TRIGGER route_manifest_insert INSTEAD OF INSERT ON cost_manifest_component FOR EACH ROW EXECUTE FUNCTION public.insert_cost_manifest_component()",
    ],
    "cost_manifest_attribution": [
        "CREATE FUNCTION public.insert_cost_manifest_attribution() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN INSERT INTO public.cost_manifest_member (manifest_id,attribution_revision_id,tenant_id,id,member_family) VALUES (NEW.manifest_id,NEW.attribution_revision_id,NEW.tenant_id,NEW.id,'cost_manifest_attribution') RETURNING manifest_id,attribution_revision_id,tenant_id,id INTO NEW.manifest_id,NEW.attribution_revision_id,NEW.tenant_id,NEW.id; RETURN NEW; END $$",
        "CREATE TRIGGER route_manifest_insert INSTEAD OF INSERT ON cost_manifest_attribution FOR EACH ROW EXECUTE FUNCTION public.insert_cost_manifest_attribution()",
    ],
    "cost_manifest_correction": [
        "CREATE FUNCTION public.insert_cost_manifest_correction() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN INSERT INTO public.cost_manifest_member (manifest_id,correction_basis_id,tenant_id,id,member_family) VALUES (NEW.manifest_id,NEW.correction_basis_id,NEW.tenant_id,NEW.id,'cost_manifest_correction') RETURNING manifest_id,correction_basis_id,tenant_id,id INTO NEW.manifest_id,NEW.correction_basis_id,NEW.tenant_id,NEW.id; RETURN NEW; END $$",
        "CREATE TRIGGER route_manifest_insert INSTEAD OF INSERT ON cost_manifest_correction FOR EACH ROW EXECUTE FUNCTION public.insert_cost_manifest_correction()",
    ],
    "cost_manifest_replacement": [
        "CREATE FUNCTION public.insert_cost_manifest_replacement() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN INSERT INTO public.cost_manifest_member (manifest_id,replacement_id,tenant_id,id,member_family) VALUES (NEW.manifest_id,NEW.replacement_id,NEW.tenant_id,NEW.id,'cost_manifest_replacement') RETURNING manifest_id,replacement_id,tenant_id,id INTO NEW.manifest_id,NEW.replacement_id,NEW.tenant_id,NEW.id; RETURN NEW; END $$",
        "CREATE TRIGGER route_manifest_insert INSTEAD OF INSERT ON cost_manifest_replacement FOR EACH ROW EXECUTE FUNCTION public.insert_cost_manifest_replacement()",
    ],
}


def _lock():
    op.execute("LOCK TABLE " + ",".join(FAMILIES) + " IN ACCESS EXCLUSIVE MODE")


def _verify(bind):
    for family, columns in COLUMNS.items():
        fields = ",".join(columns)
        original = f"SELECT {fields} FROM {family}"
        shared = (
            f"SELECT {fields} FROM cost_manifest_member WHERE member_family='{family}'"
        )
        different = bind.scalar(
            sa.text(
                f"SELECT EXISTS(({original} EXCEPT {shared}) UNION ALL ({shared} EXCEPT {original}))"
            )
        )
        if different:
            raise RuntimeError(f"Manifest member parity failed: {family}")


def upgrade():
    bind = op.get_bind()
    _lock()
    for sql in STORE_DDL:
        op.execute(sql)
    for family, columns in COLUMNS.items():
        fields = ",".join(columns)
        op.execute(
            f"INSERT INTO cost_manifest_member ({fields},member_family) SELECT {fields},'{family}' FROM {family}"
        )
    _verify(bind)
    for family in FAMILIES:
        op.drop_table(family)
        op.execute(VIEW_DDL[family])
        for sql in ROUTING_DDL[family]:
            op.execute(sql)


def downgrade():
    bind = op.get_bind()
    _lock()
    for family in FAMILIES:
        op.execute(f"DROP VIEW {family}")
        op.execute(f"DROP FUNCTION public.insert_{family}()")
    for sql in LEGACY_DDL:
        op.execute(sql)
    for family, columns in COLUMNS.items():
        fields = ",".join(columns)
        op.execute(
            f"INSERT INTO {family} ({fields}) SELECT {fields} FROM cost_manifest_member WHERE member_family='{family}'"
        )
    _verify(bind)
    op.drop_table("cost_manifest_member")
