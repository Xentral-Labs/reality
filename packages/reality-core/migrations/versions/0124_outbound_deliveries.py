"""Planned outbound deliveries, their lines and their picks (spec 334).

Revision ID: 0124_outbound_deliveries
Revises: 0122_purchasing_depth
"""

import sqlalchemy as sa
from alembic import op

revision = "0124_outbound_deliveries"
down_revision = "0122_purchasing_depth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbound_delivery",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("recipient_party_id", sa.String(), nullable=True),
        sa.Column("staging_location_id", sa.String(), nullable=True),
        sa.Column("shipment_id", sa.String(), nullable=True),
        sa.Column("source_record_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "customer_id"], ["party.tenant_id", "party.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "recipient_party_id"], ["party.tenant_id", "party.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "staging_location_id"],
            ["location.tenant_id", "location.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "shipment_id"], ["shipment.tenant_id", "shipment.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_record_id"],
            ["source_record.tenant_id", "source_record.id"],
        ),
    )
    op.create_index("ix_outbound_delivery_tenant_id", "outbound_delivery", ["tenant_id"])
    for column in (
        "customer_id",
        "recipient_party_id",
        "staging_location_id",
        "source_record_id",
    ):
        op.create_index(
            f"ix_outbound_delivery_{column}",
            "outbound_delivery",
            ["tenant_id", column],
        )
    op.create_index(
        "uq_outbound_delivery_shipment",
        "outbound_delivery",
        ["tenant_id", "shipment_id"],
        unique=True,
    )
    op.create_table(
        "outbound_delivery_line",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("outbound_delivery_id", sa.String(), nullable=False),
        sa.Column("commitment_id", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "outbound_delivery_id"],
            ["outbound_delivery.tenant_id", "outbound_delivery.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "commitment_id"],
            ["commitment.tenant_id", "commitment.id"],
        ),
        sa.CheckConstraint("quantity > 0", name="ck_outbound_delivery_line_quantity"),
    )
    op.create_index(
        "ix_outbound_delivery_line_tenant_id", "outbound_delivery_line", ["tenant_id"]
    )
    op.create_index(
        "uq_outbound_delivery_line_commitment",
        "outbound_delivery_line",
        ["tenant_id", "outbound_delivery_id", "commitment_id"],
        unique=True,
    )
    op.create_index(
        "ix_outbound_delivery_line_commitment_id",
        "outbound_delivery_line",
        ["tenant_id", "commitment_id"],
    )
    op.create_table(
        "outbound_delivery_pick",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("outbound_delivery_line_id", sa.String(), nullable=False),
        sa.Column("movement_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "outbound_delivery_line_id"],
            ["outbound_delivery_line.tenant_id", "outbound_delivery_line.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "movement_id"], ["movement.tenant_id", "movement.id"]
        ),
        sa.CheckConstraint(
            "kind IN ('pick', 'put_back')", name="ck_outbound_delivery_pick_kind"
        ),
    )
    op.create_index(
        "ix_outbound_delivery_pick_tenant_id", "outbound_delivery_pick", ["tenant_id"]
    )
    op.create_index(
        "ix_outbound_delivery_pick_line_id",
        "outbound_delivery_pick",
        ["tenant_id", "outbound_delivery_line_id"],
    )
    op.create_index(
        "uq_outbound_delivery_pick_movement",
        "outbound_delivery_pick",
        ["tenant_id", "movement_id"],
        unique=True,
    )


def downgrade() -> None:
    planned = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM outbound_delivery"))
        .scalar()
    )
    if planned:
        raise RuntimeError(
            f"{planned} planned deliveries are recorded; they cannot be removed."
        )
    op.drop_table("outbound_delivery_pick")
    op.drop_table("outbound_delivery_line")
    op.drop_table("outbound_delivery")
