"""Retain source-backed unit and currency conversion revisions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "0087_cost_conversion"
down_revision = "0086_carrying_value"
branch_labels = None
depends_on = None

TABLE = "cost_conversion_basis_revision"


def link(local, target):
    return sa.ForeignKeyConstraint(
        ["tenant_id", local], [f"{target}.tenant_id", f"{target}.id"]
    )


def upgrade():
    op.create_table(
        TABLE,
        sa.Column("evidence_source_record_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("from_code", sa.String(), nullable=False),
        sa.Column("to_code", sa.String(), nullable=False),
        sa.Column("numerator", sa.Numeric(28, 12), nullable=False),
        sa.Column("denominator", sa.Numeric(28, 12), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("supersedes_id", sa.String(), nullable=True),
        sa.Column("introduced_event_id", sa.String(), nullable=False),
        sa.Column("action_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("input_schema_version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "kind", "from_code", "to_code", "revision"),
        sa.UniqueConstraint("tenant_id", "supersedes_id"),
        link("evidence_source_record_id", "source_record"),
        link("supersedes_id", TABLE),
        link("introduced_event_id", "business_event"),
        link("action_id", "action"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.CheckConstraint(
            "revision>0 AND kind IN ('unit','currency') AND from_code<>to_code AND numerator>0 AND denominator>0 AND input_schema_version=1",
            name="ck_cost_conversion_basis",
        ),
        sa.CheckConstraint(
            "content_hash='building' OR length(content_hash)=64",
            name="ck_cost_conversion_hash",
        ),
    )
    op.add_column(
        "cost_attribution_part",
        sa.Column("conversion_basis_revision_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_cost_attribution_part_conversion",
        "cost_attribution_part",
        TABLE,
        ["tenant_id", "conversion_basis_revision_id"],
        ["tenant_id", "id"],
    )
    op.add_column(
        "cost_selling_attribution_part",
        sa.Column("conversion_basis_revision_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_cost_selling_part_conversion",
        "cost_selling_attribution_part",
        TABLE,
        ["tenant_id", "conversion_basis_revision_id"],
        ["tenant_id", "id"],
    )
    op.execute(
        f"""
        CREATE FUNCTION guard_cost_conversion() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'Cost conversion revision is immutable';
        END $$;
        CREATE TRIGGER guard_cost_conversion_revision
          BEFORE UPDATE OR DELETE ON {TABLE}
          FOR EACH ROW EXECUTE FUNCTION guard_cost_conversion();
        """
    )


def downgrade():
    connection = op.get_bind()
    if connection.scalar(text(f"SELECT EXISTS (SELECT 1 FROM {TABLE})")):
        raise RuntimeError("Cannot remove retained cost conversion history.")
    for part in ("cost_attribution_part", "cost_selling_attribution_part"):
        if connection.scalar(
            text(
                f"SELECT EXISTS (SELECT 1 FROM {part} WHERE conversion_basis_revision_id IS NOT NULL)"
            )
        ):
            raise RuntimeError("Cannot remove retained cost conversion links.")
    op.drop_constraint(
        "fk_cost_selling_part_conversion",
        "cost_selling_attribution_part",
        type_="foreignkey",
    )
    op.drop_column("cost_selling_attribution_part", "conversion_basis_revision_id")
    op.drop_constraint(
        "fk_cost_attribution_part_conversion",
        "cost_attribution_part",
        type_="foreignkey",
    )
    op.drop_column("cost_attribution_part", "conversion_basis_revision_id")
    op.drop_table(TABLE)
    op.execute("DROP FUNCTION guard_cost_conversion()")
