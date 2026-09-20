"""Retain append-only partial commercial match revisions and exact parts."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "0085_commercial_matching"
down_revision = "0084_inventory_ownership_parts"
branch_labels = None
depends_on = None

TABLES = [
    "cost_commercial_match_revision",
    "cost_commercial_inventory_part",
    "cost_commercial_direct_part",
]


def link(local, target):
    return sa.ForeignKeyConstraint(
        ["tenant_id", local], [f"{target}.tenant_id", f"{target}.id"]
    )


def upgrade():
    op.create_table(
        TABLES[0],
        sa.Column("document_line_id", sa.String(), nullable=False),
        sa.Column("order_line_id", sa.String(), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("supersedes_id", sa.String(), nullable=True),
        sa.Column("stated_net", sa.Numeric(18, 4), nullable=False),
        sa.Column("stated_quantity", sa.Numeric(18, 4), nullable=True),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("base_unit", sa.String(), nullable=True),
        sa.Column("evidence_hash", sa.String(64), nullable=False),
        sa.Column("goods_cost_disposition", sa.String(), nullable=False),
        sa.Column("profile", sa.String(), nullable=False),
        sa.Column("introduced_event_id", sa.String(), nullable=False),
        sa.Column("action_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("input_schema_version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "document_line_id", "revision"),
        sa.UniqueConstraint("tenant_id", "supersedes_id"),
        link("document_line_id", "document_line"),
        link("order_line_id", "document_line"),
        link("supersedes_id", TABLES[0]),
        link("introduced_event_id", "business_event"),
        link("action_id", "action"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.CheckConstraint(
            "revision>0 AND stated_quantity<>0 AND profile='commercial_v1' AND input_schema_version=1",
            name="ck_commercial_match_revision",
        ),
        sa.CheckConstraint(
            "goods_cost_disposition IN ('inventory','direct_evidence','not_applicable','unresolved')",
            name="ck_commercial_match_disposition",
        ),
        sa.CheckConstraint(
            "content_hash='building' OR length(content_hash)=64",
            name="ck_commercial_match_hash",
        ),
    )
    op.create_index(
        "ix_cost_commercial_match_revision_document_line_id",
        TABLES[0],
        ["document_line_id"],
    )
    op.create_table(
        TABLES[1],
        sa.Column("match_revision_id", sa.String(), nullable=False),
        sa.Column("inventory_member_id", sa.String(), nullable=False),
        sa.Column("original_issue_member_id", sa.String(), nullable=True),
        sa.Column("entry_movement_basis_id", sa.String(), nullable=False),
        sa.Column("receipt_movement_basis_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("input_schema_version", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint(
            "tenant_id",
            "match_revision_id",
            "inventory_member_id",
            "entry_movement_basis_id",
            "receipt_movement_basis_id",
        ),
        link("match_revision_id", TABLES[0]),
        link("inventory_member_id", "cost_inventory_member"),
        link("original_issue_member_id", "cost_inventory_member"),
        link("entry_movement_basis_id", "cost_movement_basis"),
        link("receipt_movement_basis_id", "cost_movement_basis"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.CheckConstraint(
            "quantity>0 AND input_schema_version=1",
            name="ck_commercial_inventory_part",
        ),
    )
    op.create_index(
        "ix_cost_commercial_inventory_part_match_revision_id",
        TABLES[1],
        ["match_revision_id"],
    )
    op.create_table(
        TABLES[2],
        sa.Column("match_revision_id", sa.String(), nullable=False),
        sa.Column("attribution_revision_id", sa.String(), nullable=False),
        sa.Column("input_role", sa.String(), nullable=False),
        sa.Column("input_schema_version", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint(
            "tenant_id", "match_revision_id", "attribution_revision_id", "input_role"
        ),
        link("match_revision_id", TABLES[0]),
        link("attribution_revision_id", "cost_attribution_revision"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.CheckConstraint(
            "input_role IN ('service_input','shipping_input','kit_input','production_input') AND input_schema_version=1",
            name="ck_commercial_direct_part",
        ),
    )
    op.create_index(
        "ix_cost_commercial_direct_part_match_revision_id",
        TABLES[2],
        ["match_revision_id"],
    )
    op.execute(
        """
        CREATE FUNCTION guard_commercial_matching() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE parent_hash text;
        BEGIN
          IF TG_TABLE_NAME = 'cost_commercial_match_revision' THEN
            IF TG_OP = 'UPDATE'
               AND OLD.content_hash = 'building'
               AND length(NEW.content_hash) = 64
               AND (to_jsonb(OLD) - 'content_hash') = (to_jsonb(NEW) - 'content_hash')
            THEN RETURN NEW;
            END IF;
            RAISE EXCEPTION 'Commercial match revision is immutable';
          END IF;
          IF TG_OP <> 'INSERT' THEN
            RAISE EXCEPTION 'Commercial match part is immutable';
          END IF;
          SELECT content_hash INTO parent_hash FROM cost_commercial_match_revision
            WHERE tenant_id=NEW.tenant_id AND id=NEW.match_revision_id FOR UPDATE;
          IF parent_hash IS DISTINCT FROM 'building' THEN
            RAISE EXCEPTION 'Commercial match part requires a building same-tenant revision';
          END IF;
          RETURN NEW;
        END $$
        """
    )
    op.execute(
        "CREATE TRIGGER guard_commercial_match_revision BEFORE UPDATE OR DELETE ON cost_commercial_match_revision FOR EACH ROW EXECUTE FUNCTION guard_commercial_matching()"
    )
    for name in TABLES[1:]:
        op.execute(
            f"CREATE TRIGGER guard_commercial_match_part BEFORE INSERT OR UPDATE OR DELETE ON {name} FOR EACH ROW EXECUTE FUNCTION guard_commercial_matching()"
        )


def downgrade():
    if op.get_bind().scalar(
        text("SELECT EXISTS (SELECT 1 FROM cost_commercial_match_revision)")
    ):
        raise RuntimeError("Cannot remove retained commercial matching history.")
    for name in reversed(TABLES):
        op.drop_table(name)
    op.execute("DROP FUNCTION guard_commercial_matching()")
