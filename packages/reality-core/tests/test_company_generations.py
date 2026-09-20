"""Financial company-generation storage keeps authority typed and tenant scoped."""

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

TABLES = {
    "cost_company_manifest",
    "cost_company_inventory_input",
    "cost_company_contribution_input",
    "cost_company_generation",
    "cost_company_inventory_result",
    "cost_company_contribution_result",
    "cost_company_publication",
}


def test_company_generation_metadata_has_exact_typed_boundary():
    from reality.db import company_generations  # noqa: F401
    from reality.db.core import Base

    assert TABLES <= set(Base.metadata.tables)
    manifest = Base.metadata.tables["cost_company_manifest"]
    assert {
        "census_id",
        "effective_at",
        "knowledge_at",
        "target_event_sequence",
        "inventory_algorithm_version",
        "contribution_algorithm_version",
        "scope_key",
        "population_digest",
        "inventory_count",
        "contribution_count",
        "header_gap_count",
        "source_gap_count",
        "gap_digest",
        "state",
        "sealed_at",
        "content_hash",
    } <= set(manifest.c.keys())
    assert manifest.c.gap_digest.type.length == 64
    assert manifest.c.population_digest.type.length == 64
    assert manifest.c.content_hash.type.length == 64
    for name in TABLES:
        table = Base.metadata.tables[name]
        assert "tenant_id" in table.c
        for foreign_key in table.foreign_key_constraints:
            if foreign_key.referred_table.name != "tenant":
                assert "tenant_id" in foreign_key.column_keys


def test_company_generation_constraints_bind_unknowns_gaps_and_scope():
    from reality.db.core import Base

    checks = {
        table_name: {
            constraint.name
            for constraint in Base.metadata.tables[table_name].constraints
            if isinstance(constraint, CheckConstraint)
        }
        for table_name in TABLES
    }
    assert {
        "ck_company_manifest_state",
        "ck_company_manifest_counts",
        "ck_company_manifest_hashes",
    } <= checks["cost_company_manifest"]
    assert (
        "ck_company_inventory_result_shape" in checks["cost_company_inventory_result"]
    )
    assert (
        "ck_company_contribution_result_shape"
        in checks["cost_company_contribution_result"]
    )
    publication = Base.metadata.tables["cost_company_publication"]
    assert any(
        isinstance(constraint, ForeignKeyConstraint)
        and tuple(constraint.column_keys) == ("tenant_id", "scope_key", "generation_id")
        for constraint in publication.constraints
    )
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(constraint.columns.keys()) == ("tenant_id", "scope_key")
        for constraint in publication.constraints
    )
