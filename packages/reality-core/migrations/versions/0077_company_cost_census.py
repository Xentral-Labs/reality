"""Retained company discovery; never a financial approval (spec242)."""

from alembic import op
from sqlalchemy import text

revision = "0077_company_cost_census"
down_revision = "0076_contribution_generations"
branch_labels = None
depends_on = None

TABLES = [
    "cost_company_census",
    "cost_company_census_movement",
    "cost_company_census_document",
    "cost_company_census_line",
    "cost_company_census_source",
]
DDL = [
    "\nCREATE TABLE cost_company_census (\n\trequest_id VARCHAR(128) NOT NULL, \n\trequest_hash VARCHAR(64) NOT NULL, \n\teffective_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tobserved_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tsnapshot_identity VARCHAR NOT NULL, \n\tevent_sequence INTEGER NOT NULL, \n\tinput_schema_version INTEGER NOT NULL, \n\tstate VARCHAR NOT NULL, \n\tmovement_count INTEGER NOT NULL, \n\tdocument_count INTEGER NOT NULL, \n\tline_count INTEGER NOT NULL, \n\tsource_count INTEGER NOT NULL, \n\tcontent_hash VARCHAR(64) NOT NULL, \n\tsealed_at TIMESTAMP WITH TIME ZONE, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, request_id), \n\tCONSTRAINT ck_company_census_version CHECK (input_schema_version=1 AND event_sequence>=0 AND length(request_hash)=64 AND length(content_hash)=64), \n\tCONSTRAINT ck_company_census_state CHECK (state IN ('building','sealed') AND ((state='sealed') = (sealed_at IS NOT NULL))), \n\tCONSTRAINT ck_company_census_counts CHECK (movement_count>=0 AND document_count>=0 AND line_count>=0 AND source_count>=0 AND movement_count+document_count+line_count+source_count<=100000), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_company_census_tenant_id ON cost_company_census (tenant_id)",
    "\nCREATE TABLE cost_company_census_movement (\n\tcensus_id VARCHAR NOT NULL, \n\tmovement_id VARCHAR NOT NULL, \n\tobserved_values JSONB NOT NULL, \n\tcontent_hash VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, census_id, id), \n\tUNIQUE (tenant_id, census_id, movement_id), \n\tFOREIGN KEY(tenant_id, census_id) REFERENCES cost_company_census (tenant_id, id), \n\tFOREIGN KEY(tenant_id, movement_id) REFERENCES movement (tenant_id, id), \n\tCONSTRAINT ck_census_movement_hash CHECK (length(content_hash)=64), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_company_census_movement_census_id ON cost_company_census_movement (census_id)",
    "CREATE INDEX ix_cost_company_census_movement_movement_id ON cost_company_census_movement (movement_id)",
    "CREATE INDEX ix_cost_company_census_movement_tenant_id ON cost_company_census_movement (tenant_id)",
    "\nCREATE TABLE cost_company_census_document (\n\tcensus_id VARCHAR NOT NULL, \n\tdocument_id VARCHAR NOT NULL, \n\tobserved_values JSONB NOT NULL, \n\tcontent_hash VARCHAR(64) NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, census_id, id), \n\tUNIQUE (tenant_id, census_id, document_id), \n\tFOREIGN KEY(tenant_id, census_id) REFERENCES cost_company_census (tenant_id, id), \n\tFOREIGN KEY(tenant_id, document_id) REFERENCES document (tenant_id, id), \n\tCONSTRAINT ck_census_document_hash CHECK (length(content_hash)=64), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_company_census_document_census_id ON cost_company_census_document (census_id)",
    "CREATE INDEX ix_cost_company_census_document_document_id ON cost_company_census_document (document_id)",
    "CREATE INDEX ix_cost_company_census_document_tenant_id ON cost_company_census_document (tenant_id)",
    "\nCREATE TABLE cost_company_census_line (\n\tcensus_id VARCHAR NOT NULL, \n\tdocument_line_id VARCHAR NOT NULL, \n\tobserved_values JSONB NOT NULL, \n\tcontent_hash VARCHAR(64) NOT NULL, \n\tdocument_member_id VARCHAR NOT NULL, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, census_id, id), \n\tUNIQUE (tenant_id, census_id, document_line_id), \n\tFOREIGN KEY(tenant_id, census_id) REFERENCES cost_company_census (tenant_id, id), \n\tFOREIGN KEY(tenant_id, document_line_id) REFERENCES document_line (tenant_id, id), \n\tCONSTRAINT ck_census_line_hash CHECK (length(content_hash)=64), \n\tFOREIGN KEY(tenant_id, census_id, document_member_id) REFERENCES cost_company_census_document (tenant_id, census_id, id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_company_census_line_census_id ON cost_company_census_line (census_id)",
    "CREATE INDEX ix_cost_company_census_line_document_line_id ON cost_company_census_line (document_line_id)",
    "CREATE INDEX ix_cost_company_census_line_document_member_id ON cost_company_census_line (document_member_id)",
    "CREATE INDEX ix_cost_company_census_line_tenant_id ON cost_company_census_line (tenant_id)",
    "\nCREATE TABLE cost_company_census_source (\n\tcensus_id VARCHAR NOT NULL, \n\tsource_record_id VARCHAR NOT NULL, \n\tobserved_values JSONB NOT NULL, \n\tcontent_hash VARCHAR(64) NOT NULL, \n\tinterpretation_outcome_id VARCHAR, \n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, id), \n\tUNIQUE (tenant_id, census_id, id), \n\tUNIQUE (tenant_id, census_id, source_record_id), \n\tFOREIGN KEY(tenant_id, census_id) REFERENCES cost_company_census (tenant_id, id), \n\tFOREIGN KEY(tenant_id, source_record_id) REFERENCES source_record (tenant_id, id), \n\tCONSTRAINT ck_census_source_hash CHECK (length(content_hash)=64), \n\tFOREIGN KEY(tenant_id, interpretation_outcome_id) REFERENCES interpretation_outcome (tenant_id, id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenant (id)\n)\n\n",
    "CREATE INDEX ix_cost_company_census_source_census_id ON cost_company_census_source (census_id)",
    "CREATE INDEX ix_cost_company_census_source_interpretation_outcome_id ON cost_company_census_source (interpretation_outcome_id)",
    "CREATE INDEX ix_cost_company_census_source_source_record_id ON cost_company_census_source (source_record_id)",
    "CREATE INDEX ix_cost_company_census_source_tenant_id ON cost_company_census_source (tenant_id)",
]

GUARD = """
CREATE FUNCTION guard_company_census() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE parent_state text;
BEGIN
  IF TG_TABLE_NAME = 'cost_company_census' THEN
    IF OLD.state = 'sealed' THEN
      RAISE EXCEPTION 'Sealed company census is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
  END IF;
  IF TG_OP <> 'INSERT' THEN
    RAISE EXCEPTION 'Company census members are immutable';
  END IF;
  SELECT state INTO parent_state FROM cost_company_census
    WHERE tenant_id=NEW.tenant_id AND id=NEW.census_id FOR UPDATE;
  IF parent_state IS DISTINCT FROM 'building' THEN
    RAISE EXCEPTION 'Census member requires a building same-tenant census';
  END IF;
  RETURN NEW;
END $$
"""


def upgrade():
    for statement in DDL:
        op.execute(statement)
    op.execute(GUARD)
    op.execute(
        "CREATE TRIGGER guard_company_census_header BEFORE UPDATE OR DELETE ON cost_company_census FOR EACH ROW EXECUTE FUNCTION guard_company_census()"
    )
    for name in TABLES[1:]:
        op.execute(
            f"CREATE TRIGGER guard_company_census_member BEFORE INSERT OR UPDATE OR DELETE ON {name} FOR EACH ROW EXECUTE FUNCTION guard_company_census()"
        )


def downgrade():
    if op.get_bind().scalar(text("SELECT EXISTS (SELECT 1 FROM cost_company_census)")):
        raise RuntimeError("Cannot remove retained company census history.")
    for name in reversed(TABLES):
        op.drop_table(name)
    op.execute("DROP FUNCTION guard_company_census()")
