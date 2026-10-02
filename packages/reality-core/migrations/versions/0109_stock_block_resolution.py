"""A stock block stays as stated; releases and scraps are its resolutions (spec 316).

Revision ID: 0109_stock_block_resolution
Revises: 0108_stock_block
"""

import json
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision = "0109_stock_block_resolution"
down_revision = "0108_stock_block"
branch_labels = None
depends_on = None

_KIND = {"released": "release", "scrapped": "scrap"}


def _fold(bind) -> None:
    """Fold each spec 304 split chain into its first block.

    A partial release or scrap closed a row for the part and continued the rest
    as a new row. The first row's quantity becomes the sum of the chain, which
    is what was stated, and every closed row becomes one resolution of it.
    """
    rows = (
        bind.execute(
            sa.text(
                "SELECT tenant_id, id, quantity, status, resolved_at, resolved_by, "
                "resolution_reason, previous_block_id, movement_id, created_at "
                "FROM stock_block"
            )
        )
        .mappings()
        .all()
    )
    following = {
        (row["tenant_id"], row["previous_block_id"]): row
        for row in rows
        if row["previous_block_id"]
    }
    for root in (row for row in rows if not row["previous_block_id"]):
        tenant = root["tenant_id"]
        chain = [root]
        while (tenant, chain[-1]["id"]) in following:
            chain.append(following[(tenant, chain[-1]["id"])])
        receipt = root["movement_id"]
        if root["status"] == "scrapped":
            # A whole scrap overwrote the receipt with its adjustment; the
            # block's creation event still names the receipt.
            payload = bind.execute(
                sa.text(
                    "SELECT payload FROM business_event WHERE tenant_id = :tenant "
                    "AND event_type = 'stock_block.created' AND subject_id = :block "
                    "ORDER BY sequence LIMIT 1"
                ),
                {"tenant": tenant, "block": root["id"]},
            ).scalar()
            receipt = json.loads(payload or "{}").get("movement_id")
        for row in chain:
            if row["status"] not in _KIND:
                continue
            bind.execute(
                sa.text(
                    "INSERT INTO stock_block_resolution (id, tenant_id, block_id, "
                    "kind, quantity, reason, resolved_at, resolved_by, movement_id) "
                    "VALUES (:id, :tenant, :block, :kind, :quantity, :reason, "
                    ":resolved_at, :resolved_by, :movement)"
                ),
                {
                    # The closed row's own id keeps its events pointing somewhere true.
                    "id": row["id"],
                    "tenant": tenant,
                    "block": root["id"],
                    "kind": _KIND[row["status"]],
                    "quantity": row["quantity"],
                    "reason": (row["resolution_reason"] or "").strip()
                    or "recorded before spec 316",
                    "resolved_at": row["resolved_at"] or row["created_at"],
                    "resolved_by": row["resolved_by"] or "human",
                    "movement": row["movement_id"]
                    if row["status"] == "scrapped"
                    else None,
                },
            )
        bind.execute(
            sa.text(
                "UPDATE stock_block SET quantity = :quantity, movement_id = :receipt "
                "WHERE tenant_id = :tenant AND id = :id"
            ),
            {
                "quantity": sum(
                    (Decimal(row["quantity"]) for row in chain), Decimal(0)
                ),
                "receipt": receipt,
                "tenant": tenant,
                "id": root["id"],
            },
        )
        for row in reversed(chain[1:]):
            bind.execute(
                sa.text(
                    "DELETE FROM stock_block WHERE tenant_id = :tenant AND id = :id"
                ),
                {"tenant": tenant, "id": row["id"]},
            )


def upgrade() -> None:
    op.create_table(
        "stock_block_resolution",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("block_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_by", sa.String(), nullable=False),
        sa.Column("movement_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "block_id"], ["stock_block.tenant_id", "stock_block.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "movement_id"],
            ["movement.tenant_id", "movement.id"],
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.CheckConstraint("quantity > 0", name="ck_stock_block_resolution_quantity"),
        sa.CheckConstraint(
            "kind IN ('release','scrap')", name="ck_stock_block_resolution_kind"
        ),
        sa.CheckConstraint(
            "btrim(reason) <> ''", name="ck_stock_block_resolution_reason"
        ),
        sa.CheckConstraint(
            "(kind = 'scrap') = (movement_id IS NOT NULL)",
            name="ck_stock_block_resolution_movement",
        ),
        sa.UniqueConstraint(
            "tenant_id", "movement_id", name="uq_stock_block_resolution_movement"
        ),
    )
    op.create_index(
        "ix_stock_block_resolution_tenant_id", "stock_block_resolution", ["tenant_id"]
    )
    op.create_index(
        "ix_stock_block_resolution_block_id",
        "stock_block_resolution",
        ["tenant_id", "block_id"],
    )
    op.create_index(
        "ix_stock_block_resolution_movement_id",
        "stock_block_resolution",
        ["tenant_id", "movement_id"],
    )
    _fold(op.get_bind())

    op.drop_index("ix_stock_block_item_location_status", table_name="stock_block")
    op.drop_index("ix_stock_block_previous_block_id", table_name="stock_block")
    op.drop_index("ix_stock_block_movement_id", table_name="stock_block")
    op.drop_constraint("ck_stock_block_status", "stock_block", type_="check")
    for column in (
        "previous_block_id",
        "status",
        "resolved_at",
        "resolved_by",
        "resolution_reason",
    ):
        op.drop_column("stock_block", column)
    op.alter_column("stock_block", "movement_id", new_column_name="receipt_movement_id")
    op.create_index(
        "ix_stock_block_item_location",
        "stock_block",
        ["tenant_id", "item_id", "location_id"],
    )
    op.create_index(
        "ix_stock_block_receipt_movement_id",
        "stock_block",
        ["tenant_id", "receipt_movement_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    resolved = bind.execute(
        sa.text("SELECT count(*) FROM stock_block_resolution")
    ).scalar()
    if resolved:
        raise RuntimeError(
            f"{resolved} stock block resolutions exist; they cannot be removed."
        )
    op.drop_index("ix_stock_block_receipt_movement_id", table_name="stock_block")
    op.drop_index("ix_stock_block_item_location", table_name="stock_block")
    op.alter_column("stock_block", "receipt_movement_id", new_column_name="movement_id")
    op.add_column(
        "stock_block",
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
    )
    op.alter_column("stock_block", "status", server_default=None)
    op.add_column("stock_block", sa.Column("resolved_at", sa.DateTime(timezone=True)))
    op.add_column("stock_block", sa.Column("resolved_by", sa.String()))
    op.add_column("stock_block", sa.Column("resolution_reason", sa.Text()))
    op.add_column("stock_block", sa.Column("previous_block_id", sa.String()))
    op.create_foreign_key(
        None,
        "stock_block",
        "stock_block",
        ["tenant_id", "previous_block_id"],
        ["tenant_id", "id"],
    )
    op.create_check_constraint(
        "ck_stock_block_status",
        "stock_block",
        "status IN ('active','released','scrapped')",
    )
    op.create_index(
        "ix_stock_block_item_location_status",
        "stock_block",
        ["tenant_id", "item_id", "location_id", "status"],
    )
    op.create_index(
        "ix_stock_block_previous_block_id",
        "stock_block",
        ["tenant_id", "previous_block_id"],
    )
    op.create_index(
        "ix_stock_block_movement_id", "stock_block", ["tenant_id", "movement_id"]
    )
    op.drop_table("stock_block_resolution")
