"""Retain source-backed inventory write-down and recovery assessments."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "0086_carrying_value"
down_revision = "0085_commercial_matching"
branch_labels = None
depends_on = None

TABLES = [
    "cost_valuation_assessment_revision",
    "cost_valuation_assessment_part",
]


def link(local, target):
    return sa.ForeignKeyConstraint(
        ["tenant_id", local], [f"{target}.tenant_id", f"{target}.id"]
    )


def upgrade():
    op.create_table(
        TABLES[0],
        sa.Column("inventory_review_id", sa.String(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("supersedes_id", sa.String(), nullable=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("target_event_sequence", sa.Integer(), nullable=False),
        sa.Column("knowledge_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("introduced_event_id", sa.String(), nullable=False),
        sa.Column("action_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("input_schema_version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "inventory_review_id", "revision"),
        sa.UniqueConstraint("tenant_id", "supersedes_id"),
        link("inventory_review_id", "cost_inventory_review"),
        link("supersedes_id", TABLES[0]),
        link("introduced_event_id", "business_event"),
        link("action_id", "action"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.CheckConstraint(
            "revision>0 AND kind IN ('write_down','recovery') AND target_event_sequence>=0 AND input_schema_version=1",
            name="ck_valuation_assessment_revision",
        ),
        sa.CheckConstraint(
            "(kind='write_down' AND supersedes_id IS NULL) OR (kind='recovery' AND supersedes_id IS NOT NULL)",
            name="ck_valuation_assessment_predecessor",
        ),
        sa.CheckConstraint(
            "content_hash='building' OR length(content_hash)=64",
            name="ck_valuation_assessment_hash",
        ),
    )
    op.create_index(
        "ix_cost_valuation_assessment_revision_inventory_review_id",
        TABLES[0],
        ["inventory_review_id"],
    )
    op.create_table(
        TABLES[1],
        sa.Column("assessment_revision_id", sa.String(), nullable=False),
        sa.Column("inventory_member_id", sa.String(), nullable=False),
        sa.Column("evidence_source_record_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("assessed_value", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("input_schema_version", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint(
            "tenant_id", "assessment_revision_id", "inventory_member_id"
        ),
        link("assessment_revision_id", TABLES[0]),
        link("inventory_member_id", "cost_inventory_member"),
        link("evidence_source_record_id", "source_record"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.CheckConstraint(
            "quantity>0 AND assessed_value>=0 AND input_schema_version=1",
            name="ck_valuation_assessment_part",
        ),
    )
    op.create_index(
        "ix_cost_valuation_assessment_part_assessment_revision_id",
        TABLES[1],
        ["assessment_revision_id"],
    )
    op.drop_constraint(
        "cost_inventory_generation_tenant_id_review_id_algorithm_ver_key",
        "cost_inventory_generation",
        type_="unique",
    )
    op.add_column(
        "cost_inventory_generation",
        sa.Column("assessment_revision_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_inventory_generation_assessment",
        "cost_inventory_generation",
        TABLES[0],
        ["tenant_id", "assessment_revision_id"],
        ["tenant_id", "id"],
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_inventory_generation_basis ON cost_inventory_generation (tenant_id, review_id, assessment_revision_id, algorithm_version) NULLS NOT DISTINCT"
    )
    op.add_column(
        "cost_inventory_snapshot",
        sa.Column("carrying_value", sa.Numeric(18, 4), nullable=True),
    )
    op.create_check_constraint(
        "ck_inventory_snapshot_carrying",
        "cost_inventory_snapshot",
        "carrying_value IS NULL OR (carrying_value>=0 AND carrying_value<=acquisition_value)",
    )
    op.execute(
        """
        CREATE FUNCTION guard_valuation_assessment() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE parent_hash text;
        BEGIN
          IF TG_TABLE_NAME = 'cost_valuation_assessment_revision' THEN
            IF TG_OP = 'UPDATE'
               AND OLD.content_hash = 'building'
               AND length(NEW.content_hash) = 64
               AND (to_jsonb(OLD) - 'content_hash') = (to_jsonb(NEW) - 'content_hash')
            THEN RETURN NEW;
            END IF;
            RAISE EXCEPTION 'Valuation assessment revision is immutable';
          END IF;
          IF TG_OP <> 'INSERT' THEN
            RAISE EXCEPTION 'Valuation assessment part is immutable';
          END IF;
          SELECT content_hash INTO parent_hash FROM cost_valuation_assessment_revision
            WHERE tenant_id=NEW.tenant_id AND id=NEW.assessment_revision_id FOR UPDATE;
          IF parent_hash IS DISTINCT FROM 'building' THEN
            RAISE EXCEPTION 'Valuation assessment part requires a building same-tenant revision';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER guard_valuation_assessment_revision BEFORE UPDATE OR DELETE ON cost_valuation_assessment_revision FOR EACH ROW EXECUTE FUNCTION guard_valuation_assessment()"
    )
    op.execute(
        "CREATE TRIGGER guard_valuation_assessment_part BEFORE INSERT OR UPDATE OR DELETE ON cost_valuation_assessment_part FOR EACH ROW EXECUTE FUNCTION guard_valuation_assessment()"
    )


def downgrade():
    if op.get_bind().scalar(
        text("SELECT EXISTS (SELECT 1 FROM cost_valuation_assessment_revision)")
    ):
        raise RuntimeError("Cannot remove retained valuation assessment history.")
    op.drop_constraint(
        "ck_inventory_snapshot_carrying",
        "cost_inventory_snapshot",
        type_="check",
    )
    op.drop_column("cost_inventory_snapshot", "carrying_value")
    op.execute("DROP INDEX uq_inventory_generation_basis")
    op.drop_constraint(
        "fk_inventory_generation_assessment",
        "cost_inventory_generation",
        type_="foreignkey",
    )
    op.drop_column("cost_inventory_generation", "assessment_revision_id")
    op.create_unique_constraint(
        None,
        "cost_inventory_generation",
        ["tenant_id", "review_id", "algorithm_version"],
    )
    for name in reversed(TABLES):
        op.drop_table(name)
    op.execute("DROP FUNCTION guard_valuation_assessment()")
