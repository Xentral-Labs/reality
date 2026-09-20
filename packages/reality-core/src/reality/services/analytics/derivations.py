"""The fixed allowlist of canonical read-time analysis derivations."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.sql.selectable import FromClause
from sqlalchemy.types import TypeEngine

from reality.services.analytics import (
    contribution_relation,
    costing_relation,
    finance_relation,
    inventory_relation,
)


@dataclass(frozen=True)
class Derivation:
    table: str
    identity: str
    columns: dict[str, TypeEngine]
    read: Callable[..., FromClause | tuple[FromClause, dict[str, Any]]]
    recordset: Callable[[list[dict[str, Any]]], FromClause]
    anchor_key: str = "id"
    canonical: bool = False


REGISTRY = {
    "costing.contribution": Derivation(
        "cost_contribution_snapshot",
        "snapshot_id",
        contribution_relation.CONTRIBUTION_COLUMNS,
        contribution_relation.report_relation,
        contribution_relation.empty_relation,
        canonical=True,
    ),
    "costing.inventory": Derivation(
        "cost_inventory_snapshot",
        "snapshot_id",
        costing_relation.INVENTORY_COLUMNS,
        costing_relation.report_relation,
        costing_relation.empty_relation,
        canonical=True,
    ),
    "finance.aging": Derivation(
        "document",
        "document_id",
        finance_relation.FINANCE_COLUMNS,
        finance_relation.relation,
        finance_relation.recordset,
    ),
    "warehouse.inventory": Derivation(
        "item",
        "item_id",
        inventory_relation.INVENTORY_COLUMNS,
        inventory_relation.relation,
        inventory_relation.recordset,
    ),
}


def columns_for(derivation: str | None) -> dict[str, TypeEngine]:
    return REGISTRY[derivation].columns if derivation else {}


def _register_positions() -> None:
    from functools import partial

    from sqlalchemy import Date

    from reality.services.analytics import position_relations as positions

    for kind, table, identity, side, columns in (
        ("customer", "party", "party_id", "customer", positions.BALANCE_COLUMNS),
        ("supplier", "party", "party_id", "supplier", positions.BALANCE_COLUMNS),
        ("stock", "item", "item_id", None, positions.STOCK_COLUMNS),
    ):
        for history in (False, True):
            key = f"positions.{kind}" + (".history" if history else "")
            declared = dict(columns)
            if history:
                declared["snapshot_date"] = Date()
                if kind == "stock":
                    declared.pop("reserved")
                    declared.pop("available")
            args = {
                "name": key.replace(".", "_"),
                "identity": identity,
                "columns": declared,
            }
            REGISTRY[key] = Derivation(
                table,
                identity,
                declared,
                partial(positions.relation, side=side, **args),
                partial(positions.recordset, **args),
            )


_register_positions()
