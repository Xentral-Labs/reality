"""Typed shared cost outputs behind the existing logical SQL interfaces.

Logical model declarations remain the authoritative column/constraint contracts.
Their tables describe writable views; four storage tables compose those proven
contracts without introducing polymorphic business identities or JSON authority.
"""

from __future__ import annotations

from hashlib import sha256

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    String,
    Table,
    UniqueConstraint,
    event,
)

from reality.db.core import Base
from reality.db.schema_views import include_schema_object  # noqa: F401

STORAGE = {
    "cost_projection_generation": (
        "cost_inventory_generation",
        "cost_contribution_generation",
        "cost_generation",
        "cost_company_generation",
    ),
    "cost_projection_inventory": (
        "cost_inventory_snapshot",
        "cost_inventory_row",
        "cost_company_inventory_result",
    ),
    "cost_projection_contribution": (
        "cost_contribution_snapshot",
        "cost_contribution_row",
        "cost_company_contribution_result",
    ),
    "cost_projection_publication": (
        "cost_inventory_publication",
        "cost_publication",
        "cost_company_publication",
    ),
}
FAMILIES = {
    family: storage for storage, families in STORAGE.items() for family in families
}
VIEW_COLUMNS: dict[str, tuple[str, ...]] = {}
VIEW_DEFAULTS: dict[str, dict[str, str]] = {}


def _register() -> None:
    logical = {name: Base.metadata.tables[name] for name in FAMILIES}
    for storage, families in STORAGE.items():
        originals = [logical[name] for name in families]
        columns = {c.name: c.type for table in originals for c in table.columns}
        columns["projection_family"] = String()
        extras: dict[str, dict[str, str]] = {}
        for table in originals:
            VIEW_COLUMNS[table.name] = tuple(table.c.keys())
            extras[table.name] = {"projection_family": table.name}
            for fk in table.foreign_key_constraints:
                target = fk.referred_table.name
                if target in FAMILIES:
                    reference = next(
                        e.parent.name for e in fk.elements if e.column.name == "id"
                    )
                    column = reference + "_family"
                    columns[column] = String()
                    extras[table.name][column] = target
        shared = Table(
            storage,
            Base.metadata,
            *(
                Column(
                    name,
                    typ,
                    nullable=name not in {"tenant_id", "id", "projection_family"},
                )
                for name, typ in columns.items()
            ),
            PrimaryKeyConstraint("tenant_id", "projection_family", "id"),
            info={"cost_projection_storage": True},
        )
        shared.append_constraint(
            CheckConstraint(
                "projection_family IN (" + ", ".join(repr(f) for f in families) + ")",
                name="ck_" + storage + "_family",
            )
        )
        used_fks: set[tuple] = set()
        used_unique: set[tuple] = set()
        for table in originals:
            name = table.name
            defaults = extras[name]
            VIEW_DEFAULTS[name] = defaults
            required = [f"{c.name} IS NOT NULL" for c in table.c if not c.nullable]
            required.extend(
                f"{column} = '{value}'" for column, value in defaults.items()
            )
            required.extend(f"{column} IS NOT NULL" for column in defaults)
            required.extend(
                f"{column} IS NULL"
                for column in (col.name for col in shared.c)
                if column not in table.c and column not in defaults
            )
            shared.append_constraint(
                CheckConstraint(
                    f"projection_family <> '{name}' OR ("
                    + " AND ".join(required)
                    + ")",
                    name="ck_" + name + "_projection_shape",
                )
            )
            for constraint in sorted(
                table.constraints,
                key=lambda item: (type(item).__name__, item.name or "", str(item)),
            ):
                if isinstance(constraint, CheckConstraint):
                    shared.append_constraint(
                        CheckConstraint(
                            f"projection_family <> '{name}' OR ({constraint.sqltext})",
                            name=constraint.name,
                        )
                    )
                elif isinstance(constraint, UniqueConstraint):
                    keys = tuple(c.name for c in constraint.columns)
                    scoped = (
                        "tenant_id",
                        "projection_family",
                        *[k for k in keys if k != "tenant_id"],
                    )
                    # Full keys support typed FKs; partial indexes preserve all
                    # family-specific uniqueness, including NULLS NOT DISTINCT.
                    if "id" in keys and scoped not in used_unique:
                        shared.append_constraint(
                            UniqueConstraint(
                                *scoped,
                                name="uq_proj_"
                                + sha256(
                                    (storage + ":" + ",".join(scoped)).encode()
                                ).hexdigest()[:16],
                            )
                        )
                        used_unique.add(scoped)
                    if set(keys) != {"tenant_id", "id"}:
                        options = constraint.dialect_options["postgresql"]
                        Index(
                            "uq_proj_"
                            + sha256(
                                (name + ":" + ",".join(keys)).encode()
                            ).hexdigest()[:16],
                            *(shared.c[k] for k in keys),
                            unique=True,
                            postgresql_where=shared.c.projection_family == name,
                            postgresql_nulls_not_distinct=options.get(
                                "nulls_not_distinct"
                            ),
                        )
                elif isinstance(constraint, ForeignKeyConstraint):
                    local = [e.parent.name for e in constraint.elements]
                    remote = [e.column.name for e in constraint.elements]
                    target = constraint.referred_table.name
                    if target in FAMILIES:
                        reference = next(
                            e.parent.name
                            for e in constraint.elements
                            if e.column.name == "id"
                        )
                        local.insert(1, reference + "_family")
                        remote.insert(1, "projection_family")
                        target = FAMILIES[target]
                    key = (tuple(local), target, tuple(remote))
                    if key not in used_fks:
                        shared.append_constraint(
                            ForeignKeyConstraint(
                                local,
                                [target + "." + column for column in remote],
                                name="fk_proj_"
                                + sha256(repr((storage, key)).encode()).hexdigest()[
                                    :16
                                ],
                            )
                        )
                        used_fks.add(key)
            for index in sorted(table.indexes, key=lambda item: item.name or ""):
                keys = tuple(column.name for column in index.columns)
                Index(
                    "ix_proj_"
                    + sha256((name + ":" + ",".join(keys)).encode()).hexdigest()[:16],
                    *(shared.c[key] for key in dict.fromkeys(("tenant_id", *keys))),
                    postgresql_where=shared.c.projection_family == name,
                )
            # Keep model mappings/columns and inspector links unchanged. Internal
            # routing constants belong to the SQL view only, never ORM fields.
            table.info["projection_view"] = True
            table.info["projection_storage"] = storage
            table.add_is_dependent_on(shared)
            names = ", ".join((*VIEW_COLUMNS[name], *defaults))
            sql = (
                f"CREATE VIEW {name} AS SELECT {names} FROM {storage} "
                f"WHERE projection_family = '{name}' WITH LOCAL CHECK OPTION"
            )
            for column, value in defaults.items():
                sql += (
                    f"; ALTER VIEW {name} ALTER COLUMN {column} SET DEFAULT '{value}'"
                )
            table.info["compatibility_view_sql"] = sql


_register()


def _install_guards(target, connection, **kwargs) -> None:
    from pathlib import Path

    from sqlalchemy import text

    # Metadata events also run for no-op and partial create_all calls. This is
    # test/schema support, never application startup DDL.
    if not all(
        connection.dialect.has_table(connection, name) for name in (*STORAGE, *FAMILIES)
    ):
        return
    import re

    sql = Path(__file__).with_name("cost_projection_guards.sql").read_text()
    triggers = list(re.finditer(r"CREATE TRIGGER (\w+) .*? ON (\w+) .*?;", sql))
    installed = set(
        connection.execute(
            text(
                "SELECT t.tgname,c.relname FROM pg_trigger t "
                "JOIN pg_class c ON c.oid=t.tgrelid "
                "JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname=current_schema() AND c.relname IN "
                "('cost_projection_generation','cost_projection_inventory',"
                "'cost_projection_contribution','cost_projection_publication')"
            )
        ).tuples()
    )
    missing = [match for match in triggers if (match[1], match[2]) not in installed]
    if missing:
        connection.exec_driver_sql(sql[: triggers[0].start()])
        for match in missing:
            connection.exec_driver_sql(match[0])


event.listen(Base.metadata, "after_create", _install_guards)
