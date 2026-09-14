"""Join existing Playground and main histories without rewriting deployed revisions."""

revision = "0041_playground_main_merge"
down_revision = ("0039_learning_playground", "0040_commitment_revisions")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
