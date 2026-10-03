"""Receipt and shipment deviations: wrong items, substitutes, advised quantities (spec 338).

Revision ID: 0130_receipt_deviations
Revises: 0128_outbound_deliveries
"""

import sqlalchemy as sa
from alembic import op

revision = "0130_receipt_deviations"
down_revision = "0128_outbound_deliveries"
branch_labels = None
depends_on = None

TABLES = ("shipment_advice_line", "commitment_substitute", "misdelivery")


def upgrade() -> None:
    op.create_table(
        "misdelivery",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("movement_id", sa.String(), nullable=False),
        sa.Column("commitment_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "movement_id"], ["movement.tenant_id", "movement.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        sa.UniqueConstraint("tenant_id", "movement_id", name="uq_misdelivery_movement"),
    )
    op.create_index("ix_misdelivery_tenant_id", "misdelivery", ["tenant_id"])
    op.create_index(
        "ix_misdelivery_commitment_id", "misdelivery", ["tenant_id", "commitment_id"]
    )

    op.create_table(
        "commitment_substitute",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("commitment_id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "item_id"], ["item.tenant_id", "item.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "commitment_id",
            "item_id",
            name="uq_commitment_substitute_commitment_item",
        ),
        sa.CheckConstraint(
            "btrim(reason) <> ''", name="ck_commitment_substitute_reason"
        ),
    )
    op.create_index(
        "ix_commitment_substitute_tenant_id", "commitment_substitute", ["tenant_id"]
    )
    op.create_index(
        "ix_commitment_substitute_item_id",
        "commitment_substitute",
        ["tenant_id", "item_id"],
    )
    op.create_index(
        "ix_commitment_substitute_source_record_id",
        "commitment_substitute",
        ["tenant_id", "source_record_id"],
    )

    op.create_table(
        "shipment_advice_line",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("shipment_id", sa.String(), nullable=False),
        sa.Column("commitment_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "shipment_id"], ["shipment.tenant_id", "shipment.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "shipment_id",
            "commitment_id",
            name="uq_shipment_advice_line_shipment_commitment",
        ),
        sa.CheckConstraint("quantity > 0", name="ck_shipment_advice_line_quantity"),
    )
    op.create_index(
        "ix_shipment_advice_line_tenant_id", "shipment_advice_line", ["tenant_id"]
    )
    op.create_index(
        "ix_shipment_advice_line_commitment_id",
        "shipment_advice_line",
        ["tenant_id", "commitment_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    for table in TABLES:
        held = bind.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar()
        if held:
            raise RuntimeError(
                f"{held} {table} rows are recorded; they cannot be removed."
            )
    for table in TABLES:
        op.drop_table(table)
