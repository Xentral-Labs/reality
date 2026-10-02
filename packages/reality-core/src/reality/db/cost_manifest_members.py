"""Typed receipt-manifest membership behind the five original SQL interfaces."""

from sqlalchemy import (
    DDL,
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    String,
    Table,
    event,
    text,
)

from reality.db.core import Base
from reality.db.schema_views import include_schema_object  # noqa: F401

STORE = "cost_manifest_member"
FAMILIES = {
    "cost_manifest_receipt": ("receipt_basis_id", "cost_receipt_basis"),
    "cost_manifest_component": ("component_basis_id", "cost_component_basis"),
    "cost_manifest_attribution": (
        "attribution_revision_id",
        "cost_attribution_revision",
    ),
    "cost_manifest_correction": ("correction_basis_id", "cost_correction_basis"),
    "cost_manifest_replacement": ("replacement_id", "cost_component_replacement"),
}
TARGET_COLUMNS = tuple(column for column, _ in FAMILIES.values())
storage = Table(
    STORE,
    Base.metadata,
    Column("tenant_id", String, nullable=False),
    Column("member_family", String, nullable=False),
    Column("id", String, nullable=False),
    Column("manifest_id", String, nullable=False),
    *(Column(column, String) for column in TARGET_COLUMNS),
    PrimaryKeyConstraint("tenant_id", "member_family", "id"),
    ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
    ForeignKeyConstraint(
        ["tenant_id", "manifest_id"],
        ["cost_input_manifest.tenant_id", "cost_input_manifest.id"],
    ),
    *(
        ForeignKeyConstraint(
            ["tenant_id", column], [f"{target}.tenant_id", f"{target}.id"]
        )
        for column, target in FAMILIES.values()
    ),
    CheckConstraint(
        " OR ".join(
            "(member_family='"
            + family
            + "' AND "
            + " AND ".join(
                f"{candidate} IS {'NOT ' if candidate == column else ''}NULL"
                for candidate in TARGET_COLUMNS
            )
            + ")"
            for family, (column, _) in FAMILIES.items()
        ),
        name="ck_cost_manifest_member_shape",
    ),
)
# Family partial uniqueness cannot support a parent FK check over every family.
Index("ix_cost_manifest_member_manifest_id", storage.c.tenant_id, storage.c.manifest_id)
VIEW_DDL = {}
VIEW_COLUMNS = {}
ROUTING_DDL = {}
for family, (column, _) in FAMILIES.items():
    Index(
        f"uq_manifest_member_{column}",
        storage.c.tenant_id,
        storage.c.manifest_id,
        storage.c[column],
        unique=True,
        postgresql_where=text(f"member_family='{family}'"),
    )
    logical = Base.metadata.tables[family]
    columns = tuple(logical.c.keys())
    VIEW_COLUMNS[family] = columns
    view = (
        f"CREATE VIEW {family} AS SELECT {','.join(columns)} "
        f"FROM {STORE} WHERE member_family='{family}' WITH LOCAL CHECK OPTION"
    )
    VIEW_DDL[family] = view
    logical.info["compatibility_view_sql"] = view
    logical.add_is_dependent_on(storage)
    # Fixed relation/column names and invoker rights. Only inserts need routing;
    # automatic view updates/deletes retain the original direct-write contract.
    function = f"insert_{family}"
    fields = ",".join(columns)
    new_fields = ",".join(f"NEW.{field}" for field in columns)
    routing = [
        (
            f"CREATE FUNCTION public.{function}() RETURNS trigger LANGUAGE plpgsql AS $$ "
            f"BEGIN INSERT INTO public.{STORE} ({fields},member_family) "
            f"VALUES ({new_fields},'{family}') RETURNING {fields} INTO {new_fields}; "
            "RETURN NEW; END $$"
        ),
        (
            f"CREATE TRIGGER route_manifest_insert INSTEAD OF INSERT ON {family} "
            f"FOR EACH ROW EXECUTE FUNCTION public.{function}()"
        ),
    ]
    ROUTING_DDL[family] = routing
    for sql in routing:
        event.listen(logical, "after_create", DDL(sql).execute_if(dialect="postgresql"))
    event.listen(
        logical,
        "after_drop",
        DDL(f"DROP FUNCTION public.{function}()").execute_if(dialect="postgresql"),
    )
