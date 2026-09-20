"""Retain exact financial company inputs and disposable generation membership."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "0080_company_generations"
down_revision = "0079_captured_report"
branch_labels = None
depends_on = None

TABLES = (
    "cost_company_manifest",
    "cost_company_inventory_input",
    "cost_company_contribution_input",
    "cost_company_generation",
    "cost_company_inventory_result",
    "cost_company_contribution_result",
    "cost_company_publication",
)


def tenant_columns():
    return (
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
    )


def upgrade():
    op.create_table(
        "cost_company_manifest",
        sa.Column("census_id", sa.String(), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("knowledge_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("target_event_sequence", sa.Integer(), nullable=False),
        sa.Column("inventory_algorithm_version", sa.String(), nullable=False),
        sa.Column("contribution_algorithm_version", sa.String(), nullable=False),
        sa.Column("scope_key", sa.String(64), nullable=False),
        sa.Column("population_digest", sa.String(64), nullable=False),
        sa.Column("inventory_count", sa.Integer(), nullable=False),
        sa.Column("contribution_count", sa.Integer(), nullable=False),
        sa.Column("header_gap_count", sa.Integer(), nullable=False),
        sa.Column("source_gap_count", sa.Integer(), nullable=False),
        sa.Column("gap_digest", sa.String(64), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("sealed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        *tenant_columns(),
        sa.UniqueConstraint("tenant_id", "scope_key", "content_hash"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "census_id"],
            ["cost_company_census.tenant_id", "cost_company_census.id"],
        ),
        sa.CheckConstraint(
            "state IN ('building','sealed') AND ((state='sealed') = (sealed_at IS NOT NULL))",
            name="ck_company_manifest_state",
        ),
        sa.CheckConstraint(
            "target_event_sequence>=0 AND inventory_count>=0 AND contribution_count>=0 AND header_gap_count>=0 AND source_gap_count>=0",
            name="ck_company_manifest_counts",
        ),
        sa.CheckConstraint(
            "length(scope_key)=64 AND length(population_digest)=64 AND length(gap_digest)=64 AND length(content_hash)=64",
            name="ck_company_manifest_hashes",
        ),
    )
    op.create_index(
        "ix_cost_company_manifest_census_id", "cost_company_manifest", ["census_id"]
    )
    op.create_index(
        "ix_cost_company_manifest_tenant_id", "cost_company_manifest", ["tenant_id"]
    )

    op.create_table(
        "cost_company_inventory_input",
        sa.Column("manifest_id", sa.String(), nullable=False),
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("review_id", sa.String(), nullable=True),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("support_state", sa.String(), nullable=False),
        *tenant_columns(),
        sa.UniqueConstraint("tenant_id", "manifest_id", "id"),
        sa.UniqueConstraint("tenant_id", "manifest_id", "item_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "manifest_id"],
            ["cost_company_manifest.tenant_id", "cost_company_manifest.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "item_id"], ["item.tenant_id", "item.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "review_id"],
            ["cost_inventory_review.tenant_id", "cost_inventory_review.id"],
        ),
        sa.CheckConstraint(
            "support_state IN ('known','unknown') AND ((support_state='known') = (review_id IS NOT NULL)) AND length(input_fingerprint)=64",
            name="ck_company_inventory_input_shape",
        ),
    )
    for column in ("tenant_id", "manifest_id", "item_id", "review_id"):
        op.create_index(
            f"ix_cost_company_inventory_input_{column}",
            "cost_company_inventory_input",
            [column],
        )

    op.create_table(
        "cost_company_contribution_input",
        sa.Column("manifest_id", sa.String(), nullable=False),
        sa.Column("census_line_id", sa.String(), nullable=False),
        sa.Column("review_id", sa.String(), nullable=True),
        sa.Column("inventory_review_id", sa.String(), nullable=True),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("db1_state", sa.String(), nullable=False),
        sa.Column("db2_state", sa.String(), nullable=False),
        *tenant_columns(),
        sa.UniqueConstraint("tenant_id", "manifest_id", "id"),
        sa.UniqueConstraint("tenant_id", "manifest_id", "census_line_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "manifest_id"],
            ["cost_company_manifest.tenant_id", "cost_company_manifest.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "census_line_id"],
            ["cost_company_census_line.tenant_id", "cost_company_census_line.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "review_id"],
            ["cost_contribution_review.tenant_id", "cost_contribution_review.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "inventory_review_id"],
            ["cost_inventory_review.tenant_id", "cost_inventory_review.id"],
        ),
        sa.CheckConstraint(
            "db1_state IN ('known','unknown') AND db2_state IN ('known','unknown') AND NOT (db2_state='known' AND db1_state='unknown') AND ((db1_state='known') = (review_id IS NOT NULL)) AND length(input_fingerprint)=64",
            name="ck_company_contribution_input_shape",
        ),
    )
    for column in (
        "tenant_id",
        "manifest_id",
        "census_line_id",
        "review_id",
        "inventory_review_id",
    ):
        op.create_index(
            f"ix_cost_company_contribution_input_{column}",
            "cost_company_contribution_input",
            [column],
        )

    op.create_table(
        "cost_company_generation",
        sa.Column("manifest_id", sa.String(), nullable=False),
        sa.Column("algorithm_bundle", sa.String(), nullable=False),
        sa.Column("scope_key", sa.String(64), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("expected_work_count", sa.Integer(), nullable=False),
        sa.Column("completed_work_count", sa.Integer(), nullable=False),
        sa.Column("inventory_count", sa.Integer(), nullable=False),
        sa.Column("contribution_count", sa.Integer(), nullable=False),
        sa.Column("inventory_content_hash", sa.String(64), nullable=False),
        sa.Column("contribution_content_hash", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *tenant_columns(),
        sa.UniqueConstraint("tenant_id", "scope_key", "id"),
        sa.UniqueConstraint("tenant_id", "manifest_id", "algorithm_bundle"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "manifest_id"],
            ["cost_company_manifest.tenant_id", "cost_company_manifest.id"],
        ),
        sa.CheckConstraint(
            "state IN ('building','sealed') AND ((state='sealed') = (completed_at IS NOT NULL))",
            name="ck_company_generation_state",
        ),
        sa.CheckConstraint(
            "expected_work_count>=0 AND completed_work_count>=0 AND completed_work_count<=expected_work_count AND inventory_count>=0 AND contribution_count>=0",
            name="ck_company_generation_counts",
        ),
        sa.CheckConstraint(
            "length(scope_key)=64 AND length(inventory_content_hash)=64 AND length(contribution_content_hash)=64",
            name="ck_company_generation_hashes",
        ),
    )
    for column in ("tenant_id", "manifest_id"):
        op.create_index(
            f"ix_cost_company_generation_{column}",
            "cost_company_generation",
            [column],
        )

    op.create_table(
        "cost_company_inventory_result",
        sa.Column("generation_id", sa.String(), nullable=False),
        sa.Column("inventory_input_id", sa.String(), nullable=False),
        sa.Column("inventory_generation_id", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("result_fingerprint", sa.String(64), nullable=False),
        *tenant_columns(),
        sa.UniqueConstraint("tenant_id", "generation_id", "inventory_input_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "generation_id"],
            ["cost_company_generation.tenant_id", "cost_company_generation.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "inventory_input_id"],
            [
                "cost_company_inventory_input.tenant_id",
                "cost_company_inventory_input.id",
            ],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "inventory_generation_id"],
            ["cost_inventory_generation.tenant_id", "cost_inventory_generation.id"],
        ),
        sa.CheckConstraint(
            "state IN ('known','unknown') AND ((state='known') = (inventory_generation_id IS NOT NULL)) AND length(result_fingerprint)=64",
            name="ck_company_inventory_result_shape",
        ),
    )
    for column in (
        "tenant_id",
        "generation_id",
        "inventory_input_id",
        "inventory_generation_id",
    ):
        op.create_index(
            f"ix_cost_company_inventory_result_{column}",
            "cost_company_inventory_result",
            [column],
        )

    op.create_table(
        "cost_company_contribution_result",
        sa.Column("generation_id", sa.String(), nullable=False),
        sa.Column("contribution_input_id", sa.String(), nullable=False),
        sa.Column("contribution_generation_id", sa.String(), nullable=True),
        sa.Column("review_id", sa.String(), nullable=True),
        sa.Column("db1_state", sa.String(), nullable=False),
        sa.Column("db2_state", sa.String(), nullable=False),
        sa.Column("result_fingerprint", sa.String(64), nullable=False),
        *tenant_columns(),
        sa.UniqueConstraint("tenant_id", "generation_id", "contribution_input_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "generation_id"],
            ["cost_company_generation.tenant_id", "cost_company_generation.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "contribution_input_id"],
            [
                "cost_company_contribution_input.tenant_id",
                "cost_company_contribution_input.id",
            ],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "contribution_generation_id"],
            [
                "cost_contribution_generation.tenant_id",
                "cost_contribution_generation.id",
            ],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "review_id"],
            ["cost_contribution_review.tenant_id", "cost_contribution_review.id"],
        ),
        sa.CheckConstraint(
            "db1_state IN ('known','unknown') AND db2_state IN ('known','unknown') AND NOT (db2_state='known' AND db1_state='unknown') AND ((db1_state='known') = (contribution_generation_id IS NOT NULL AND review_id IS NOT NULL)) AND length(result_fingerprint)=64",
            name="ck_company_contribution_result_shape",
        ),
    )
    for column in (
        "tenant_id",
        "generation_id",
        "contribution_input_id",
        "contribution_generation_id",
        "review_id",
    ):
        op.create_index(
            f"ix_cost_company_contribution_result_{column}",
            "cost_company_contribution_result",
            [column],
        )

    op.create_table(
        "cost_company_publication",
        sa.Column("scope_key", sa.String(64), nullable=False),
        sa.Column("generation_id", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        *tenant_columns(),
        sa.UniqueConstraint("tenant_id", "scope_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "scope_key", "generation_id"],
            [
                "cost_company_generation.tenant_id",
                "cost_company_generation.scope_key",
                "cost_company_generation.id",
            ],
        ),
    )
    for column in ("tenant_id", "generation_id"):
        op.create_index(
            f"ix_cost_company_publication_{column}",
            "cost_company_publication",
            [column],
        )

    op.execute(
        """
        CREATE FUNCTION guard_company_generation_storage() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE parent_state text; manifest_state text; n integer; m integer;
        BEGIN
          IF TG_TABLE_NAME='cost_company_manifest' THEN
            IF TG_OP='INSERT' AND NEW.state<>'building' THEN
              RAISE EXCEPTION 'Company manifest starts building';
            END IF;
            IF TG_OP='UPDATE' AND (OLD.state='sealed' OR NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.census_id<>OLD.census_id OR NEW.scope_key<>OLD.scope_key) THEN
              RAISE EXCEPTION 'Sealed company manifest or identity is immutable';
            END IF;
            RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
          END IF;
          IF TG_TABLE_NAME='cost_company_generation' THEN
            IF TG_OP='INSERT' THEN
              SELECT state INTO manifest_state FROM cost_company_manifest WHERE tenant_id=NEW.tenant_id AND id=NEW.manifest_id;
              IF NEW.state<>'building' OR manifest_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Generation requires sealed manifest'; END IF;
            ELSIF TG_OP='UPDATE' THEN
              IF OLD.state='sealed' OR NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.manifest_id<>OLD.manifest_id OR NEW.scope_key<>OLD.scope_key THEN RAISE EXCEPTION 'Sealed company generation or identity is immutable'; END IF;
              IF NEW.state='sealed' THEN
                SELECT count(*) INTO n FROM cost_company_inventory_result WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;
                SELECT count(*) INTO m FROM cost_company_contribution_result WHERE tenant_id=NEW.tenant_id AND generation_id=NEW.id;
                IF n<>NEW.inventory_count OR m<>NEW.contribution_count OR NEW.completed_work_count<>NEW.expected_work_count THEN RAISE EXCEPTION 'Company generation membership is incomplete'; END IF;
              END IF;
            END IF;
            RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
          END IF;
          IF TG_TABLE_NAME='cost_company_publication' THEN
            IF TG_OP='UPDATE' AND (NEW.id<>OLD.id OR NEW.tenant_id<>OLD.tenant_id OR NEW.scope_key<>OLD.scope_key) THEN RAISE EXCEPTION 'Company publication scope is immutable'; END IF;
            SELECT state INTO parent_state FROM cost_company_generation WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id AND scope_key=NEW.scope_key FOR UPDATE;
            IF parent_state IS DISTINCT FROM 'sealed' THEN RAISE EXCEPTION 'Company publication requires sealed generation'; END IF;
            RETURN NEW;
          END IF;
          IF TG_TABLE_NAME IN ('cost_company_inventory_input','cost_company_contribution_input') THEN
            IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Company manifest members are immutable'; END IF;
            SELECT state INTO manifest_state FROM cost_company_manifest WHERE tenant_id=NEW.tenant_id AND id=NEW.manifest_id FOR UPDATE;
            IF manifest_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Company input requires building manifest'; END IF;
            RETURN NEW;
          END IF;
          IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'Company generation members are immutable'; END IF;
          SELECT state INTO parent_state FROM cost_company_generation WHERE tenant_id=NEW.tenant_id AND id=NEW.generation_id FOR UPDATE;
          IF parent_state IS DISTINCT FROM 'building' THEN RAISE EXCEPTION 'Company result requires building generation'; END IF;
          RETURN NEW;
        END $$
        """
    )
    for name in TABLES:
        operations = (
            "INSERT OR UPDATE"
            if name == "cost_company_publication"
            else "INSERT OR UPDATE OR DELETE"
        )
        op.execute(
            f"CREATE TRIGGER guard_company_generation_row BEFORE {operations} ON {name} FOR EACH ROW EXECUTE FUNCTION guard_company_generation_storage()"
        )


def downgrade():
    bind = op.get_bind()
    if any(
        bind.scalar(text(f"SELECT EXISTS (SELECT 1 FROM {name})")) for name in TABLES
    ):
        raise RuntimeError("Discard company generation history before downgrade.")
    for name in reversed(TABLES):
        op.drop_table(name)
    op.execute("DROP FUNCTION guard_company_generation_storage()")
