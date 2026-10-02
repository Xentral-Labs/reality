"""Typed retained census membership with original protected SQL interfaces."""

from sqlalchemy import (
    DDL,
    CheckConstraint,
    Column,
    Computed,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    String,
    Table,
    UniqueConstraint,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from reality.db.core import Base
from reality.db.schema_views import include_schema_object  # noqa: F401

STORE = "cost_company_census_member"
FAMILIES = {
    "movement": ("movement_id", "movement"),
    "document": ("document_id", "document"),
    "line": ("document_line_id", "document_line"),
    "source": ("source_record_id", "source_record"),
}
SUBJECTS = tuple(column for column, _ in FAMILIES.values())
storage = Table(
    STORE,
    Base.metadata,
    Column("tenant_id", String, nullable=False),
    Column("member_family", String, nullable=False),
    Column("id", String, nullable=False),
    Column("census_id", String, nullable=False),
    Column("observed_values", JSONB, nullable=False),
    Column("content_hash", String(64), nullable=False),
    *(Column(column, String) for column in SUBJECTS),
    Column("document_member_id", String),
    Column("interpretation_outcome_id", String),
    Column(
        "document_member_identity",
        String,
        Computed("CASE WHEN member_family='document' THEN id END", persisted=True),
    ),
    Column(
        "line_member_identity",
        String,
        Computed("CASE WHEN member_family='line' THEN id END", persisted=True),
    ),
    PrimaryKeyConstraint("tenant_id", "member_family", "id"),
    UniqueConstraint("tenant_id", "census_id", "document_member_identity"),
    UniqueConstraint("tenant_id", "line_member_identity"),
    ForeignKeyConstraint(["tenant_id"], ["tenant.id"]),
    ForeignKeyConstraint(
        ["tenant_id", "census_id"],
        ["cost_company_census.tenant_id", "cost_company_census.id"],
    ),
    *(
        ForeignKeyConstraint(
            ["tenant_id", column], [f"{target}.tenant_id", f"{target}.id"]
        )
        for column, target in FAMILIES.values()
    ),
    ForeignKeyConstraint(
        ["tenant_id", "interpretation_outcome_id"],
        ["interpretation_outcome.tenant_id", "interpretation_outcome.id"],
    ),
    ForeignKeyConstraint(
        ["tenant_id", "census_id", "document_member_id"],
        [
            f"{STORE}.tenant_id",
            f"{STORE}.census_id",
            f"{STORE}.document_member_identity",
        ],
    ),
    CheckConstraint("length(content_hash)=64", name="ck_census_member_hash"),
    CheckConstraint(
        " OR ".join(
            "(member_family='"
            + family
            + "' AND "
            + " AND ".join(
                f"{candidate} IS {'NOT ' if candidate == column else ''}NULL"
                for candidate in SUBJECTS
            )
            + f" AND document_member_id IS {'NOT ' if family == 'line' else ''}NULL"
            + (" AND interpretation_outcome_id IS NULL" if family != "source" else "")
            + ")"
            for family, (column, _) in FAMILIES.items()
        ),
        name="ck_census_member_shape",
    ),
)
for column in (*SUBJECTS, "interpretation_outcome_id"):
    Index(f"ix_{STORE}_{column}", storage.c.tenant_id, storage.c[column])
Index(
    f"ix_{STORE}_census_id_document_member_id",
    storage.c.tenant_id,
    storage.c.census_id,
    storage.c.document_member_id,
)

GUARD_DDL = [
    """CREATE FUNCTION public.guard_company_census_member_store() RETURNS trigger
    LANGUAGE plpgsql AS $$ DECLARE parent_state text; BEGIN
      IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'Company census members are immutable'; END IF;
      SELECT state INTO parent_state FROM public.cost_company_census
        WHERE tenant_id=NEW.tenant_id AND id=NEW.census_id FOR UPDATE;
      IF parent_state IS DISTINCT FROM 'building' THEN
        RAISE EXCEPTION 'Census member requires a building same-tenant census';
      END IF;
      RETURN NEW;
    END $$""",
    (
        f"CREATE TRIGGER guard_company_census_member BEFORE INSERT OR UPDATE OR DELETE ON {STORE} "
        "FOR EACH ROW EXECUTE FUNCTION public.guard_company_census_member_store()"
    ),
]
for sql in GUARD_DDL:
    event.listen(storage, "after_create", DDL(sql).execute_if(dialect="postgresql"))
event.listen(
    storage,
    "after_drop",
    DDL("DROP FUNCTION public.guard_company_census_member_store()").execute_if(
        dialect="postgresql"
    ),
)

VIEW_COLUMNS = {}
VIEW_DDL = {}
ROUTING_DDL = {}
for family, (column, _) in FAMILIES.items():
    Index(
        f"uq_census_member_{column}",
        storage.c.tenant_id,
        storage.c.census_id,
        storage.c[column],
        unique=True,
        postgresql_where=text(f"member_family='{family}'"),
    )
    name = "cost_company_census_" + family
    logical = Base.metadata.tables[name]
    columns = tuple(c.name for c in logical.c if c.name not in ("id", "tenant_id")) + (
        "id",
        "tenant_id",
    )
    VIEW_COLUMNS[name] = columns
    fields = ",".join(columns)
    view = (
        f"CREATE VIEW {name} AS SELECT {fields} FROM {STORE} "
        f"WHERE member_family='{family}' WITH LOCAL CHECK OPTION"
    )
    VIEW_DDL[name] = view
    logical.info["compatibility_view_sql"] = view
    logical.add_is_dependent_on(storage)
    function = "insert_" + name
    new_fields = ",".join("NEW." + field for field in columns)
    routing = [
        (
            f"CREATE FUNCTION public.{function}() RETURNS trigger LANGUAGE plpgsql AS $$ "
            f"BEGIN INSERT INTO public.{STORE} ({fields},member_family) "
            f"VALUES ({new_fields},'{family}') RETURNING {fields} INTO {new_fields}; RETURN NEW; END $$"
        ),
        (
            f"CREATE TRIGGER route_census_insert INSTEAD OF INSERT ON {name} "
            f"FOR EACH ROW EXECUTE FUNCTION public.{function}()"
        ),
    ]
    ROUTING_DDL[name] = routing
    for sql in routing:
        event.listen(logical, "after_create", DDL(sql).execute_if(dialect="postgresql"))
    event.listen(
        logical,
        "after_drop",
        DDL(f"DROP FUNCTION public.{function}()").execute_if(dialect="postgresql"),
    )
