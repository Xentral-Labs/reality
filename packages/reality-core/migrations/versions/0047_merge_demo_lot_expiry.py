"""Join scheduled demo setup and existing lot expiry without rewriting either branch."""
revision = "0047_merge_demo_lot_expiry"
down_revision = ("0046_company_setup_demo", "0045_lot_expiry")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
