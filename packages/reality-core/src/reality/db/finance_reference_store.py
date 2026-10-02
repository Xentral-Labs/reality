"""One typed Finance catalog store behind the original writable interfaces."""

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
    UniqueConstraint,
    text,
)

from reality.db.core import Base, UTCDateTime
from reality.db.schema_views import include_schema_object  # noqa: F401

INTERNAL = "kind IN ('cost_center','case_code','coding_group')"
EXTERNAL = "kind IN ('account','tax_code')"
STORE = "finance_reference_store"

storage = Table(
    STORE,
    Base.metadata,
    Column("id", String, nullable=False),
    Column("tenant_id", String, nullable=False),
    Column("kind", String, nullable=False),
    Column("code", String(200), nullable=False),
    Column("name", String(200), nullable=False),
    Column("state", String, nullable=False),
    Column("revision", Integer, nullable=False),
    Column("target_id", String),
    Column("created_at", UTCDateTime),
    Column("updated_at", UTCDateTime),
    PrimaryKeyConstraint("tenant_id", "id", "kind"),
    ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
    ForeignKeyConstraint(
        ["tenant_id", "target_id"],
        ["accounting_target.tenant_id", "accounting_target.id"],
    ),
    UniqueConstraint(
        "tenant_id", "target_id", "id", "kind", name="uq_reference_store_target_id"
    ),
    CheckConstraint(
        f"({INTERNAL} AND target_id IS NULL AND created_at IS NULL AND updated_at IS NULL AND length(code)<=100) OR ({EXTERNAL} AND target_id IS NOT NULL AND created_at IS NOT NULL AND updated_at IS NOT NULL)",
        name="ck_reference_store_shape",
    ),
    CheckConstraint(
        "state IN ('active','blocked') AND revision>0 AND length(trim(code))>0 AND length(trim(name))>0",
        name="ck_reference_store_values",
    ),
)
for family, predicate, code_columns in (
    ("internal", INTERNAL, ("tenant_id", "kind", "code")),
    ("external", EXTERNAL, ("tenant_id", "target_id", "kind", "code")),
):
    Index(
        f"uq_reference_store_{family}_id",
        storage.c.tenant_id,
        storage.c.id,
        unique=True,
        postgresql_where=text(predicate),
    )
    Index(
        f"uq_reference_store_{family}_code",
        *(storage.c[column] for column in code_columns),
        unique=True,
        postgresql_where=text(predicate),
    )

VIEW_COLUMNS = {}
VIEW_DDL = {}
for name, predicate in (
    ("finance_reference", INTERNAL),
    ("accounting_target_reference", EXTERNAL),
):
    logical = Base.metadata.tables[name]
    VIEW_COLUMNS[name] = tuple(logical.c.keys())
    sql = (
        f"CREATE VIEW {name} AS SELECT {','.join(VIEW_COLUMNS[name])} "
        f"FROM {STORE} WHERE {predicate} WITH LOCAL CHECK OPTION"
    )
    VIEW_DDL[name] = sql
    logical.info["compatibility_view_sql"] = sql
    logical.add_is_dependent_on(storage)

# Keep the original local key tuples. Their constrained kinds identify the family.
for table in list(Base.metadata.tables.values()):
    if table.name in VIEW_DDL:
        continue
    for constraint in list(table.foreign_key_constraints):
        if constraint.referred_table.name not in VIEW_DDL:
            continue
        local = [element.parent.name for element in constraint.elements]
        remote = [f"{STORE}.{element.column.name}" for element in constraint.elements]
        table.constraints.remove(constraint)
        for element in constraint.elements:
            table.foreign_keys.discard(element)
            element.parent.foreign_keys.discard(element)
        table.append_constraint(
            ForeignKeyConstraint(
                local,
                remote,
                name=constraint.name,
                ondelete=constraint.ondelete,
                onupdate=constraint.onupdate,
                deferrable=constraint.deferrable,
                initially=constraint.initially,
                match=constraint.match,
            )
        )
