"""Add account-scoped Business Journey Guide proposals and votes.

Revision ID: 0100_business_journey_proposals
Revises: 0099_payment_term_prepayment
"""

import sqlalchemy as sa
from alembic import op

revision = "0100_business_journey_proposals"
down_revision = "0099_payment_term_prepayment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "journey_proposal",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("creator_account_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("business_question", sa.String(1000), nullable=False),
        sa.Column("expected_outcome", sa.String(2000), nullable=False),
        sa.Column("process_area", sa.String(32), nullable=False),
        sa.Column("business_context", sa.String(1000), nullable=False),
        sa.Column("normalized_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), server_default="proposed", nullable=False),
        sa.Column("public_rationale", sa.String(2000), nullable=False),
        sa.Column("available_journey_id", sa.String(3), nullable=True),
        sa.Column("reviewed_by_account_id", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["creator_account_id"], ["app_user.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_account_id"], ["app_user.id"]),
        sa.CheckConstraint(
            "status IN ('proposed', 'under_review', 'planned', 'in_progress', "
            "'available', 'declined', 'out_of_scope')",
            name="ck_journey_proposal_status",
        ),
        sa.CheckConstraint(
            "process_area IN ('orders', 'availability', 'payments', 'shipping', "
            "'invoicing', 'returns', 'purchasing', 'receiving', 'payables', "
            "'warehouse', 'products', 'commerce', 'b2b', 'finance', "
            "'master_data', 'sources', 'time', 'combined')",
            name="ck_journey_proposal_process_area",
        ),
    )
    op.create_index("ix_journey_proposal_creator", "journey_proposal", ["creator_account_id"])
    op.create_index("ix_journey_proposal_status", "journey_proposal", ["status"])
    op.create_index("ix_journey_proposal_process", "journey_proposal", ["process_area"])
    op.create_index("ix_journey_proposal_fingerprint", "journey_proposal", ["normalized_fingerprint"])
    op.create_index("ix_journey_proposal_reviewer", "journey_proposal", ["reviewed_by_account_id"])
    op.create_table(
        "journey_proposal_vote",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("proposal_id", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["proposal_id"], ["journey_proposal.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["app_user.id"]),
        sa.UniqueConstraint("proposal_id", "account_id", name="uq_journey_proposal_vote_account"),
    )
    op.create_index("ix_journey_proposal_vote_proposal", "journey_proposal_vote", ["proposal_id"])
    op.create_index("ix_journey_proposal_vote_account", "journey_proposal_vote", ["account_id"])


def downgrade() -> None:
    op.drop_table("journey_proposal_vote")
    op.drop_table("journey_proposal")
