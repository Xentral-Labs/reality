"""Add physical shipments, packages, and append-only tracking events."""

import sqlalchemy as sa
from alembic import op

revision = "0056_physical_shipments"
down_revision = "0055_demo_settlement_schedule"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shipment",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column(
            "counterparty_id", sa.String(), sa.ForeignKey("party.id"), nullable=False
        ),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "direction IN ('inbound', 'outbound')", name="ck_shipment_direction"
        ),
        sa.CheckConstraint(
            "purpose IN ('customer_delivery', 'supplier_delivery', 'customer_return', 'supplier_return')",
            name="ck_shipment_purpose",
        ),
    )
    op.create_index("ix_shipment_tenant_id", "shipment", ["tenant_id"])
    op.create_index(
        "ix_shipment_tenant_direction_created",
        "shipment",
        ["tenant_id", "direction", "created_at"],
    )
    op.create_index(
        "ix_shipment_tenant_purpose_created",
        "shipment",
        ["tenant_id", "purpose", "created_at"],
    )
    op.create_index(
        "ix_shipment_tenant_counterparty", "shipment", ["tenant_id", "counterparty_id"]
    )
    op.create_table(
        "shipment_package",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "shipment_id", sa.String(), sa.ForeignKey("shipment.id"), nullable=False
        ),
        sa.Column("carrier", sa.String()),
        sa.Column("tracking_number", sa.String()),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_shipment_package_tenant_id", "shipment_package", ["tenant_id"])
    op.create_index(
        "ix_shipment_package_tenant_shipment",
        "shipment_package",
        ["tenant_id", "shipment_id"],
    )
    op.create_index(
        "ix_shipment_package_tenant_carrier_tracking",
        "shipment_package",
        ["tenant_id", "carrier", "tracking_number"],
    )
    op.create_table(
        "shipment_event",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "shipment_id", sa.String(), sa.ForeignKey("shipment.id"), nullable=False
        ),
        sa.Column(
            "shipment_package_id", sa.String(), sa.ForeignKey("shipment_package.id")
        ),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("reporter_type", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True)),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location_text", sa.String()),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id")),
        sa.Column("external_event_id", sa.String()),
        sa.CheckConstraint(
            "event_type IN ('announced', 'handed_over', 'in_transit', 'delivered', 'delivery_exception', 'received')",
            name="ck_shipment_event_type",
        ),
        sa.CheckConstraint(
            "reporter_type IN ('company', 'counterparty', 'carrier', 'integration')",
            name="ck_shipment_event_reporter",
        ),
    )
    op.create_index("ix_shipment_event_tenant_id", "shipment_event", ["tenant_id"])
    op.create_index(
        "ix_shipment_event_tenant_shipment",
        "shipment_event",
        ["tenant_id", "shipment_id", "recorded_at"],
    )
    op.create_index(
        "ix_shipment_event_tenant_package",
        "shipment_event",
        ["tenant_id", "shipment_package_id", "recorded_at"],
    )
    op.create_index(
        "ix_shipment_event_tenant_external",
        "shipment_event",
        ["tenant_id", "external_event_id"],
    )
    op.create_table(
        "shipment_event_supersession",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column(
            "superseded_event_id",
            sa.String(),
            sa.ForeignKey("shipment_event.id"),
            nullable=False,
        ),
        sa.Column(
            "replacement_event_id", sa.String(), sa.ForeignKey("shipment_event.id")
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actor_context", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("source_record_id", sa.String(), sa.ForeignKey("source_record.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "superseded_event_id"),
    )
    op.create_index(
        "ix_shipment_event_supersession_tenant_id",
        "shipment_event_supersession",
        ["tenant_id"],
    )
    op.add_column(
        "movement", sa.Column("shipment_package_id", sa.String(), nullable=True)
    )
    op.create_foreign_key(
        "fk_movement_shipment_package",
        "movement",
        "shipment_package",
        ["shipment_package_id"],
        ["id"],
    )
    op.create_index(
        "ix_movement_shipment_package_id", "movement", ["shipment_package_id"]
    )


def downgrade():
    op.drop_index("ix_movement_shipment_package_id", table_name="movement")
    op.drop_constraint("fk_movement_shipment_package", "movement", type_="foreignkey")
    op.drop_column("movement", "shipment_package_id")
    op.drop_table("shipment_event_supersession")
    op.drop_table("shipment_event")
    op.drop_table("shipment_package")
    op.drop_table("shipment")
