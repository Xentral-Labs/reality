"""Normalize payment terms into tenant-scoped master data.

Revision ID: 0009_payment_terms
Revises: 0008_utc_timestamps
"""

import uuid

import sqlalchemy as sa
from alembic import op

revision = "0009_payment_terms"
down_revision = "0008_utc_timestamps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "payment_term" not in inspector.get_table_names():
        op.create_table(
            "payment_term",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("due_days", sa.Integer(), nullable=False),
            sa.Column(
                "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
            ),
            sa.Column("source_record_id", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
            sa.ForeignKeyConstraint(["source_record_id"], ["source_record.id"]),
            sa.UniqueConstraint("tenant_id", "code"),
        )
        op.create_index("ix_payment_term_tenant_id", "payment_term", ["tenant_id"])
    for table in ("party", "document"):
        columns = {column["name"] for column in sa.inspect(connection).get_columns(table)}
        if "payment_term_id" not in columns:
            op.add_column(
                table, sa.Column("payment_term_id", sa.String(), nullable=True)
            )

    rows = connection.execute(
        sa.text(
            "SELECT tenant_id, payment_term_code FROM party WHERE payment_term_code <> '' "
            "UNION SELECT tenant_id, payment_term_code FROM document "
            "WHERE payment_term_code <> ''"
        )
    ).fetchall()
    for tenant_id, code in rows:
        term_id = connection.execute(
            sa.text(
                "SELECT id FROM payment_term WHERE tenant_id=:tenant AND code=:code"
            ),
            {"tenant": tenant_id, "code": code},
        ).scalar() or f"ptm_{uuid.uuid4().hex[:10]}"
        suffix = code.rsplit("_", 1)[-1]
        if not connection.execute(
            sa.text("SELECT 1 FROM payment_term WHERE id=:id"), {"id": term_id}
        ).scalar():
            connection.execute(
                sa.text(
                    "INSERT INTO payment_term "
                    "(id, tenant_id, code, name, due_days, is_active) "
                    "VALUES (:id, :tenant, :code, :name, :days, true)"
                ),
                {
                    "id": term_id,
                    "tenant": tenant_id,
                    "code": code,
                    "name": code.replace("_", " ").title(),
                    "days": int(suffix) if suffix.isdigit() else 0,
                },
            )
        for table in ("party", "document"):
            connection.execute(
                sa.text(
                    f"UPDATE {table} SET payment_term_id=:id "
                    "WHERE tenant_id=:tenant AND payment_term_code=:code"
                ),
                {"id": term_id, "tenant": tenant_id, "code": code},
            )

    with op.batch_alter_table("party") as batch:
        batch.create_foreign_key(
            "fk_party_payment_term", "payment_term", ["payment_term_id"], ["id"]
        )
        batch.drop_column("payment_term_code")
    with op.batch_alter_table("document") as batch:
        batch.create_foreign_key(
            "fk_document_payment_term", "payment_term", ["payment_term_id"], ["id"]
        )
        batch.drop_column("payment_term_code")


def downgrade() -> None:
    with op.batch_alter_table("document") as batch:
        batch.add_column(
            sa.Column("payment_term_code", sa.String(), nullable=False, server_default="")
        )
    with op.batch_alter_table("party") as batch:
        batch.add_column(
            sa.Column("payment_term_code", sa.String(), nullable=False, server_default="")
        )
    connection = op.get_bind()
    for table in ("party", "document"):
        connection.execute(
            sa.text(
                f"UPDATE {table} SET payment_term_code=(SELECT code FROM payment_term "
                f"WHERE payment_term.id={table}.payment_term_id) "
                "WHERE payment_term_id IS NOT NULL"
            )
        )
    with op.batch_alter_table("document") as batch:
        batch.drop_constraint("fk_document_payment_term", type_="foreignkey")
        batch.drop_column("payment_term_id")
    with op.batch_alter_table("party") as batch:
        batch.drop_constraint("fk_party_payment_term", type_="foreignkey")
        batch.drop_column("payment_term_id")
    op.drop_index("ix_payment_term_tenant_id", table_name="payment_term")
    op.drop_table("payment_term")
