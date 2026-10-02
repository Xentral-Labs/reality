"""Share typed census membership with exact protected rollback (spec 327)."""

import sqlalchemy as sa
from alembic import op

revision = "0121_census_members"
down_revision = "0120_manifest_members"
branch_labels = None
depends_on = None

# Frozen actual predecessor and replacement DDL; no live model imports.
# Create unique keys before equivalent PKs, preserving predecessor FK index binding.
LEGACY_DDL = [
    "CREATE TABLE cost_company_census_movement (census_id character varying NOT NULL,movement_id character varying NOT NULL,observed_values jsonb NOT NULL,content_hash character varying(64) NOT NULL,id character varying NOT NULL,tenant_id character varying NOT NULL,CONSTRAINT ck_census_movement_hash CHECK ((length((content_hash)::text) = 64)),CONSTRAINT cost_company_census_movement_tenant_id_census_id_fkey FOREIGN KEY (tenant_id, census_id) REFERENCES cost_company_census(tenant_id, id),CONSTRAINT cost_company_census_movement_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenant(id),CONSTRAINT cost_company_census_movement_tenant_id_movement_id_fkey FOREIGN KEY (tenant_id, movement_id) REFERENCES movement(tenant_id, id))",
    "ALTER TABLE cost_company_census_movement ADD CONSTRAINT cost_company_census_movement_tenant_id_census_id_id_key UNIQUE (tenant_id, census_id, id)",
    "ALTER TABLE cost_company_census_movement ADD CONSTRAINT cost_company_census_movement_tenant_id_census_id_movement_i_key UNIQUE (tenant_id, census_id, movement_id)",
    "ALTER TABLE cost_company_census_movement ADD CONSTRAINT cost_company_census_movement_tenant_id_id_key UNIQUE (tenant_id, id)",
    "ALTER TABLE cost_company_census_movement ADD CONSTRAINT cost_company_census_movement_pkey PRIMARY KEY (tenant_id, id)",
    "CREATE INDEX ix_cost_company_census_movement_census_id ON public.cost_company_census_movement USING btree (census_id)",
    "CREATE INDEX ix_cost_company_census_movement_movement_id ON public.cost_company_census_movement USING btree (tenant_id, movement_id)",
    "CREATE TABLE cost_company_census_document (census_id character varying NOT NULL,document_id character varying NOT NULL,observed_values jsonb NOT NULL,content_hash character varying(64) NOT NULL,id character varying NOT NULL,tenant_id character varying NOT NULL,CONSTRAINT ck_census_document_hash CHECK ((length((content_hash)::text) = 64)),CONSTRAINT cost_company_census_document_tenant_id_census_id_fkey FOREIGN KEY (tenant_id, census_id) REFERENCES cost_company_census(tenant_id, id),CONSTRAINT cost_company_census_document_tenant_id_document_id_fkey FOREIGN KEY (tenant_id, document_id) REFERENCES document(tenant_id, id),CONSTRAINT cost_company_census_document_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenant(id))",
    "ALTER TABLE cost_company_census_document ADD CONSTRAINT cost_company_census_document_tenant_id_census_id_document_i_key UNIQUE (tenant_id, census_id, document_id)",
    "ALTER TABLE cost_company_census_document ADD CONSTRAINT cost_company_census_document_tenant_id_census_id_id_key UNIQUE (tenant_id, census_id, id)",
    "ALTER TABLE cost_company_census_document ADD CONSTRAINT cost_company_census_document_tenant_id_id_key UNIQUE (tenant_id, id)",
    "ALTER TABLE cost_company_census_document ADD CONSTRAINT cost_company_census_document_pkey PRIMARY KEY (tenant_id, id)",
    "CREATE INDEX ix_cost_company_census_document_census_id ON public.cost_company_census_document USING btree (census_id)",
    "CREATE INDEX ix_cost_company_census_document_document_id ON public.cost_company_census_document USING btree (tenant_id, document_id)",
    "CREATE TABLE cost_company_census_line (census_id character varying NOT NULL,document_line_id character varying NOT NULL,observed_values jsonb NOT NULL,content_hash character varying(64) NOT NULL,document_member_id character varying NOT NULL,id character varying NOT NULL,tenant_id character varying NOT NULL,CONSTRAINT ck_census_line_hash CHECK ((length((content_hash)::text) = 64)),CONSTRAINT cost_company_census_line_tenant_id_census_id_document_memb_fkey FOREIGN KEY (tenant_id, census_id, document_member_id) REFERENCES cost_company_census_document(tenant_id, census_id, id),CONSTRAINT cost_company_census_line_tenant_id_census_id_fkey FOREIGN KEY (tenant_id, census_id) REFERENCES cost_company_census(tenant_id, id),CONSTRAINT cost_company_census_line_tenant_id_document_line_id_fkey FOREIGN KEY (tenant_id, document_line_id) REFERENCES document_line(tenant_id, id),CONSTRAINT cost_company_census_line_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenant(id))",
    "ALTER TABLE cost_company_census_line ADD CONSTRAINT cost_company_census_line_tenant_id_census_id_document_line__key UNIQUE (tenant_id, census_id, document_line_id)",
    "ALTER TABLE cost_company_census_line ADD CONSTRAINT cost_company_census_line_tenant_id_census_id_id_key UNIQUE (tenant_id, census_id, id)",
    "ALTER TABLE cost_company_census_line ADD CONSTRAINT cost_company_census_line_tenant_id_id_key UNIQUE (tenant_id, id)",
    "ALTER TABLE cost_company_census_line ADD CONSTRAINT cost_company_census_line_pkey PRIMARY KEY (tenant_id, id)",
    "CREATE INDEX ix_cost_company_census_line_census_id ON public.cost_company_census_line USING btree (census_id)",
    "CREATE INDEX ix_cost_company_census_line_census_id_document_member_id ON public.cost_company_census_line USING btree (tenant_id, census_id, document_member_id)",
    "CREATE INDEX ix_cost_company_census_line_document_line_id ON public.cost_company_census_line USING btree (tenant_id, document_line_id)",
    "CREATE INDEX ix_cost_company_census_line_document_member_id ON public.cost_company_census_line USING btree (document_member_id)",
    "CREATE TABLE cost_company_census_source (census_id character varying NOT NULL,source_record_id character varying NOT NULL,observed_values jsonb NOT NULL,content_hash character varying(64) NOT NULL,interpretation_outcome_id character varying,id character varying NOT NULL,tenant_id character varying NOT NULL,CONSTRAINT ck_census_source_hash CHECK ((length((content_hash)::text) = 64)),CONSTRAINT cost_company_census_source_tenant_id_census_id_fkey FOREIGN KEY (tenant_id, census_id) REFERENCES cost_company_census(tenant_id, id),CONSTRAINT cost_company_census_source_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES tenant(id),CONSTRAINT cost_company_census_source_tenant_id_interpretation_outcom_fkey FOREIGN KEY (tenant_id, interpretation_outcome_id) REFERENCES interpretation_outcome(tenant_id, id),CONSTRAINT cost_company_census_source_tenant_id_source_record_id_fkey FOREIGN KEY (tenant_id, source_record_id) REFERENCES source_record(tenant_id, id))",
    "ALTER TABLE cost_company_census_source ADD CONSTRAINT cost_company_census_source_tenant_id_census_id_id_key UNIQUE (tenant_id, census_id, id)",
    "ALTER TABLE cost_company_census_source ADD CONSTRAINT cost_company_census_source_tenant_id_census_id_source_recor_key UNIQUE (tenant_id, census_id, source_record_id)",
    "ALTER TABLE cost_company_census_source ADD CONSTRAINT cost_company_census_source_tenant_id_id_key UNIQUE (tenant_id, id)",
    "ALTER TABLE cost_company_census_source ADD CONSTRAINT cost_company_census_source_pkey PRIMARY KEY (tenant_id, id)",
    "CREATE INDEX ix_cost_company_census_source_census_id ON public.cost_company_census_source USING btree (census_id)",
    "CREATE INDEX ix_cost_company_census_source_interpretation_outcome_id ON public.cost_company_census_source USING btree (tenant_id, interpretation_outcome_id)",
    "CREATE INDEX ix_cost_company_census_source_source_record_id ON public.cost_company_census_source USING btree (tenant_id, source_record_id)",
]

STORE_DDL = [
    "\nCREATE TABLE cost_company_census_member (\n\ttenant_id VARCHAR NOT NULL, \n\tmember_family VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\tcensus_id VARCHAR NOT NULL, \n\tobserved_values JSONB NOT NULL, \n\tcontent_hash VARCHAR(64) NOT NULL, \n\tmovement_id VARCHAR, \n\tdocument_id VARCHAR, \n\tdocument_line_id VARCHAR, \n\tsource_record_id VARCHAR, \n\tdocument_member_id VARCHAR, \n\tinterpretation_outcome_id VARCHAR, \n\tdocument_member_identity VARCHAR GENERATED ALWAYS AS (CASE WHEN member_family='document' THEN id END) STORED, \n\tline_member_identity VARCHAR GENERATED ALWAYS AS (CASE WHEN member_family='line' THEN id END) STORED, \n\tPRIMARY KEY (tenant_id, member_family, id), \n\tUNIQUE (tenant_id, census_id, document_member_identity), \n\tUNIQUE (tenant_id, line_member_identity), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id), \n\tFOREIGN KEY(tenant_id, census_id) REFERENCES cost_company_census (tenant_id, id), \n\tFOREIGN KEY(tenant_id, movement_id) REFERENCES movement (tenant_id, id), \n\tFOREIGN KEY(tenant_id, document_id) REFERENCES document (tenant_id, id), \n\tFOREIGN KEY(tenant_id, document_line_id) REFERENCES document_line (tenant_id, id), \n\tFOREIGN KEY(tenant_id, source_record_id) REFERENCES source_record (tenant_id, id), \n\tFOREIGN KEY(tenant_id, interpretation_outcome_id) REFERENCES interpretation_outcome (tenant_id, id), \n\tFOREIGN KEY(tenant_id, census_id, document_member_id) REFERENCES cost_company_census_member (tenant_id, census_id, document_member_identity), \n\tCONSTRAINT ck_census_member_hash CHECK (length(content_hash)=64), \n\tCONSTRAINT ck_census_member_shape CHECK ((member_family='movement' AND movement_id IS NOT NULL AND document_id IS NULL AND document_line_id IS NULL AND source_record_id IS NULL AND document_member_id IS NULL AND interpretation_outcome_id IS NULL) OR (member_family='document' AND movement_id IS NULL AND document_id IS NOT NULL AND document_line_id IS NULL AND source_record_id IS NULL AND document_member_id IS NULL AND interpretation_outcome_id IS NULL) OR (member_family='line' AND movement_id IS NULL AND document_id IS NULL AND document_line_id IS NOT NULL AND source_record_id IS NULL AND document_member_id IS NOT NULL AND interpretation_outcome_id IS NULL) OR (member_family='source' AND movement_id IS NULL AND document_id IS NULL AND document_line_id IS NULL AND source_record_id IS NOT NULL AND document_member_id IS NULL))\n)\n\n",
    "CREATE INDEX ix_cost_company_census_member_census_id_document_member_id ON cost_company_census_member (tenant_id, census_id, document_member_id)",
    "CREATE INDEX ix_cost_company_census_member_document_id ON cost_company_census_member (tenant_id, document_id)",
    "CREATE INDEX ix_cost_company_census_member_document_line_id ON cost_company_census_member (tenant_id, document_line_id)",
    "CREATE INDEX ix_cost_company_census_member_interpretation_outcome_id ON cost_company_census_member (tenant_id, interpretation_outcome_id)",
    "CREATE INDEX ix_cost_company_census_member_movement_id ON cost_company_census_member (tenant_id, movement_id)",
    "CREATE INDEX ix_cost_company_census_member_source_record_id ON cost_company_census_member (tenant_id, source_record_id)",
    "CREATE UNIQUE INDEX uq_census_member_document_id ON cost_company_census_member (tenant_id, census_id, document_id) WHERE member_family='document'",
    "CREATE UNIQUE INDEX uq_census_member_document_line_id ON cost_company_census_member (tenant_id, census_id, document_line_id) WHERE member_family='line'",
    "CREATE UNIQUE INDEX uq_census_member_movement_id ON cost_company_census_member (tenant_id, census_id, movement_id) WHERE member_family='movement'",
    "CREATE UNIQUE INDEX uq_census_member_source_record_id ON cost_company_census_member (tenant_id, census_id, source_record_id) WHERE member_family='source'",
]

COLUMNS = {
    "cost_company_census_movement": (
        "census_id",
        "movement_id",
        "observed_values",
        "content_hash",
        "id",
        "tenant_id",
    ),
    "cost_company_census_document": (
        "census_id",
        "document_id",
        "observed_values",
        "content_hash",
        "id",
        "tenant_id",
    ),
    "cost_company_census_line": (
        "census_id",
        "document_line_id",
        "observed_values",
        "content_hash",
        "document_member_id",
        "id",
        "tenant_id",
    ),
    "cost_company_census_source": (
        "census_id",
        "source_record_id",
        "observed_values",
        "content_hash",
        "interpretation_outcome_id",
        "id",
        "tenant_id",
    ),
}

VIEW_DDL = {
    "cost_company_census_movement": "CREATE VIEW cost_company_census_movement AS SELECT census_id,movement_id,observed_values,content_hash,id,tenant_id FROM cost_company_census_member WHERE member_family='movement' WITH LOCAL CHECK OPTION",
    "cost_company_census_document": "CREATE VIEW cost_company_census_document AS SELECT census_id,document_id,observed_values,content_hash,id,tenant_id FROM cost_company_census_member WHERE member_family='document' WITH LOCAL CHECK OPTION",
    "cost_company_census_line": "CREATE VIEW cost_company_census_line AS SELECT census_id,document_line_id,observed_values,content_hash,document_member_id,id,tenant_id FROM cost_company_census_member WHERE member_family='line' WITH LOCAL CHECK OPTION",
    "cost_company_census_source": "CREATE VIEW cost_company_census_source AS SELECT census_id,source_record_id,observed_values,content_hash,interpretation_outcome_id,id,tenant_id FROM cost_company_census_member WHERE member_family='source' WITH LOCAL CHECK OPTION",
}

ROUTING_DDL = {
    "cost_company_census_movement": [
        "CREATE FUNCTION public.insert_cost_company_census_movement() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN INSERT INTO public.cost_company_census_member (census_id,movement_id,observed_values,content_hash,id,tenant_id,member_family) VALUES (NEW.census_id,NEW.movement_id,NEW.observed_values,NEW.content_hash,NEW.id,NEW.tenant_id,'movement') RETURNING census_id,movement_id,observed_values,content_hash,id,tenant_id INTO NEW.census_id,NEW.movement_id,NEW.observed_values,NEW.content_hash,NEW.id,NEW.tenant_id; RETURN NEW; END $$",
        "CREATE TRIGGER route_census_insert INSTEAD OF INSERT ON cost_company_census_movement FOR EACH ROW EXECUTE FUNCTION public.insert_cost_company_census_movement()",
    ],
    "cost_company_census_document": [
        "CREATE FUNCTION public.insert_cost_company_census_document() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN INSERT INTO public.cost_company_census_member (census_id,document_id,observed_values,content_hash,id,tenant_id,member_family) VALUES (NEW.census_id,NEW.document_id,NEW.observed_values,NEW.content_hash,NEW.id,NEW.tenant_id,'document') RETURNING census_id,document_id,observed_values,content_hash,id,tenant_id INTO NEW.census_id,NEW.document_id,NEW.observed_values,NEW.content_hash,NEW.id,NEW.tenant_id; RETURN NEW; END $$",
        "CREATE TRIGGER route_census_insert INSTEAD OF INSERT ON cost_company_census_document FOR EACH ROW EXECUTE FUNCTION public.insert_cost_company_census_document()",
    ],
    "cost_company_census_line": [
        "CREATE FUNCTION public.insert_cost_company_census_line() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN INSERT INTO public.cost_company_census_member (census_id,document_line_id,observed_values,content_hash,document_member_id,id,tenant_id,member_family) VALUES (NEW.census_id,NEW.document_line_id,NEW.observed_values,NEW.content_hash,NEW.document_member_id,NEW.id,NEW.tenant_id,'line') RETURNING census_id,document_line_id,observed_values,content_hash,document_member_id,id,tenant_id INTO NEW.census_id,NEW.document_line_id,NEW.observed_values,NEW.content_hash,NEW.document_member_id,NEW.id,NEW.tenant_id; RETURN NEW; END $$",
        "CREATE TRIGGER route_census_insert INSTEAD OF INSERT ON cost_company_census_line FOR EACH ROW EXECUTE FUNCTION public.insert_cost_company_census_line()",
    ],
    "cost_company_census_source": [
        "CREATE FUNCTION public.insert_cost_company_census_source() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN INSERT INTO public.cost_company_census_member (census_id,source_record_id,observed_values,content_hash,interpretation_outcome_id,id,tenant_id,member_family) VALUES (NEW.census_id,NEW.source_record_id,NEW.observed_values,NEW.content_hash,NEW.interpretation_outcome_id,NEW.id,NEW.tenant_id,'source') RETURNING census_id,source_record_id,observed_values,content_hash,interpretation_outcome_id,id,tenant_id INTO NEW.census_id,NEW.source_record_id,NEW.observed_values,NEW.content_hash,NEW.interpretation_outcome_id,NEW.id,NEW.tenant_id; RETURN NEW; END $$",
        "CREATE TRIGGER route_census_insert INSTEAD OF INSERT ON cost_company_census_source FOR EACH ROW EXECUTE FUNCTION public.insert_cost_company_census_source()",
    ],
}

GUARD_DDL = [
    "CREATE FUNCTION public.guard_company_census_member_store() RETURNS trigger\n    LANGUAGE plpgsql AS $$ DECLARE parent_state text; BEGIN\n      IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'Company census members are immutable'; END IF;\n      SELECT state INTO parent_state FROM public.cost_company_census\n        WHERE tenant_id=NEW.tenant_id AND id=NEW.census_id FOR UPDATE;\n      IF parent_state IS DISTINCT FROM 'building' THEN\n        RAISE EXCEPTION 'Census member requires a building same-tenant census';\n      END IF;\n      RETURN NEW;\n    END $$",
    "CREATE TRIGGER guard_company_census_member BEFORE INSERT OR UPDATE OR DELETE ON cost_company_census_member FOR EACH ROW EXECUTE FUNCTION public.guard_company_census_member_store()",
]

LEGACY_TRIGGERS = [
    "CREATE TRIGGER guard_company_census_member BEFORE INSERT OR DELETE OR UPDATE ON public.cost_company_census_document FOR EACH ROW EXECUTE FUNCTION guard_company_census()",
    "CREATE TRIGGER guard_company_census_member BEFORE INSERT OR DELETE OR UPDATE ON public.cost_company_census_line FOR EACH ROW EXECUTE FUNCTION guard_company_census()",
    "CREATE TRIGGER guard_company_census_member BEFORE INSERT OR DELETE OR UPDATE ON public.cost_company_census_movement FOR EACH ROW EXECUTE FUNCTION guard_company_census()",
    "CREATE TRIGGER guard_company_census_member BEFORE INSERT OR DELETE OR UPDATE ON public.cost_company_census_source FOR EACH ROW EXECUTE FUNCTION guard_company_census()",
]

CONSUMER_FK = "cost_company_contribution_input_tenant_id_census_line_id_fkey"

ORIGINAL_FK = "FOREIGN KEY (tenant_id, census_line_id) REFERENCES cost_company_census_line(tenant_id, id)"

SHARED_FK = "FOREIGN KEY (tenant_id, census_line_id) REFERENCES cost_company_census_member(tenant_id, line_member_identity)"


def _lock(shared=False):
    names = ["cost_company_census", *COLUMNS, "cost_company_contribution_input"]
    if shared:
        names.append("cost_company_census_member")
    op.execute("LOCK TABLE " + ",".join(sorted(names)) + " IN ACCESS EXCLUSIVE MODE")


def _verify(bind):
    for name, columns in COLUMNS.items():
        fields = ",".join(columns)
        family = name.removeprefix("cost_company_census_")
        original = f"SELECT {fields} FROM {name}"
        shared = f"SELECT {fields} FROM cost_company_census_member WHERE member_family='{family}'"
        if bind.scalar(
            sa.text(
                f"SELECT EXISTS(({original} EXCEPT {shared}) UNION ALL ({shared} EXCEPT {original}))"
            )
        ):
            raise RuntimeError(f"Census member parity failed: {name}")


def _redirect(definition):
    op.drop_constraint(
        CONSUMER_FK, "cost_company_contribution_input", type_="foreignkey"
    )
    op.execute(
        f"ALTER TABLE cost_company_contribution_input ADD CONSTRAINT {CONSUMER_FK} {definition}"
    )


def upgrade():
    bind = op.get_bind()
    _lock()
    for sql in STORE_DDL:
        op.execute(sql)
    # Captured documents precede lines; guards admit building captures only and
    # therefore are installed after exact sealed-history copy/parity.
    for name, columns in COLUMNS.items():
        fields = ",".join(columns)
        family = name.removeprefix("cost_company_census_")
        op.execute(
            f"INSERT INTO cost_company_census_member ({fields},member_family) SELECT {fields},'{family}' FROM {name}"
        )
    _verify(bind)
    _redirect(SHARED_FK)
    for name in reversed(COLUMNS):
        op.drop_table(name)
    for name in COLUMNS:
        op.execute(VIEW_DDL[name])
        for sql in ROUTING_DDL[name]:
            op.execute(sql)
    for sql in GUARD_DDL:
        op.execute(sql)


def downgrade():
    bind = op.get_bind()
    _lock(shared=True)
    for name in reversed(COLUMNS):
        op.execute(f"DROP VIEW {name}")
        op.execute(f"DROP FUNCTION public.insert_{name}()")
    for sql in LEGACY_DDL:
        op.execute(sql)
    for name, columns in COLUMNS.items():
        fields = ",".join(columns)
        family = name.removeprefix("cost_company_census_")
        op.execute(
            f"INSERT INTO {name} ({fields}) SELECT {fields} FROM cost_company_census_member WHERE member_family='{family}'"
        )
    _verify(bind)
    _redirect(ORIGINAL_FK)
    for sql in LEGACY_TRIGGERS:
        op.execute(sql)
    op.drop_table("cost_company_census_member")
    op.execute("DROP FUNCTION public.guard_company_census_member_store()")
