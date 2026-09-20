"""Bounded internal known subtotals over verified pinned replay, never a report engine."""

from decimal import Decimal

from sqlalchemy import Numeric, String, cast, column, func, select, values
from sqlalchemy.orm import Session

from reality.domain.contribution import CONTRIBUTION_TERMS
from reality.services import core
from reality.services.analytics.contribution_aggregates import (
    contribution_aggregate_columns,
)
from reality.services.cost_captured_basis import _replay
from reality.services.costing import _money

_INPUTS = ("revenue", "goods_cost", "direct_selling_cost", "allocated_selling_cost")
_STOCK = ("remaining_quantity", "acquisition_value", "carrying_value")


def _amount(value: str | None) -> Decimal | None:
    return Decimal(value) if value is not None else None


def _members(rows: list[dict], dimensions: tuple[str, ...], identity: str) -> dict:
    groups = {}
    for row in rows:
        key = tuple(row["result"][name] for name in dimensions)
        groups.setdefault(key, []).append(
            {identity: row[identity], "review_id": row["review_id"]}
        )
    return {
        key: sorted(members, key=lambda row: row[identity])
        for key, members in groups.items()
    }


def _inventory(session: Session, rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    dimensions = ("currency", "base_unit", "method", "owner_party_id")
    source = values(
        *(column(name, String) for name in dimensions),
        *(column(name, Numeric()) for name in _STOCK),
        name="verified_captured_inventory",
    ).data(
        [
            (
                *(row["result"][name] for name in dimensions),
                *(cast(_amount(row["result"][name]), Numeric()) for name in _STOCK),
            )
            for row in rows
        ]
    )
    keys = [source.c[name] for name in dimensions]
    statement = (
        select(
            *keys,
            func.count().label("required"),
            *(
                expression
                for name in _STOCK
                for expression in (
                    func.coalesce(func.sum(source.c[name]), 0).label(f"{name}_known"),
                    func.count(source.c[name]).label(f"{name}_covered"),
                )
            ),
        )
        .select_from(source)
        .group_by(*keys)
        .order_by(*keys)
    )
    members = _members(rows, dimensions, "item_id")
    result = []
    for row in session.execute(statement).mappings():
        result.append(
            {
                **{name: row[name] for name in dimensions},
                "members": members[tuple(row[name] for name in dimensions)],
                **{
                    label: {
                        "known": _money(row[f"{name}_known"]),
                        "total": None,
                        "required": row["required"],
                        "covered": row[f"{name}_covered"],
                    }
                    for label, name in (
                        ("remaining_quantity", "remaining_quantity"),
                        ("acquisition", "acquisition_value"),
                        ("carrying", "carrying_value"),
                    )
                },
            }
        )
    return result


def _contribution(session: Session, rows: list[dict]) -> list[dict]:
    if not rows:
        return []
    dimensions = ("currency", "base_unit")
    data = []
    for row in rows:
        result = row["result"]
        if result["profile"] != "commercial_v1":
            raise core.InvalidOperation("Unsupported captured contribution profile.")
        amounts = (
            result["trace"]["received_net"],
            result["trace"]["consumption"]["cost"],
            result["direct_selling_cost"],
            result["allocated_selling_cost"],
        )
        data.append(
            (
                *(result[name] for name in dimensions),
                *(
                    value
                    for amount in amounts
                    for value in (
                        cast(_amount(amount), Numeric()),
                        "reviewed" if amount is not None else "unknown",
                    )
                ),
            )
        )
    source = values(
        *(column(name, String) for name in dimensions),
        *(
            part
            for name in _INPUTS
            for part in (column(name, Numeric()), column(f"{name}_state", String))
        ),
        name="verified_captured_contribution",
    ).data(data)
    keys = [source.c[name] for name in dimensions]
    # Individually reviewed inputs support known subtotals. They do not establish the
    # jointly admitted company context needed for final totals or margin percentages.
    statement = (
        select(*keys, *contribution_aggregate_columns(source, reviewed=False))
        .select_from(source)
        .group_by(*keys)
        .order_by(*keys)
    )
    members = _members(rows, dimensions, "document_line_id")
    return [
        {
            **{name: row[name] for name in dimensions},
            "profile": "commercial_v1",
            "members": members[tuple(row[name] for name in dimensions)],
            **{
                name: {
                    "known": _money(row[f"{name}_known"]),
                    "total": _money(row[f"{name}_total"]),
                    **{
                        stat: row[f"{name}_{stat}"]
                        for stat in ("required", "covered", "evidenced", "provisional")
                    },
                }
                for name in CONTRIBUTION_TERMS
            },
            "db1_rate": _money(row["db1_rate"]),
            "db2_rate": _money(row["db2_rate"]),
        }
        for row in session.execute(statement).mappings()
    ]


def _groups(session: Session, inventory: list[dict], contribution: list[dict]) -> dict:
    """Internal trusted replay adapter; no API accepts these row arrays."""
    if len(inventory) + len(contribution) > 10:
        raise core.InvalidOperation("Captured summary subject limit exceeded.")
    for rows, key in ((inventory, "item_id"), (contribution, "document_line_id")):
        if len({row[key] for row in rows}) != len(rows) or any(
            (row["result"] is not None) != (row["state"] == "available_at_capture")
            for row in rows
        ):
            raise core.InvalidOperation("Invalid captured summary membership.")
    return {
        "inventory": _inventory(
            session, [row for row in inventory if row["result"] is not None]
        ),
        "contribution": _contribution(
            session, [row for row in contribution if row["result"] is not None]
        ),
    }


def _summary(session: Session, tenant: str, identity: str) -> dict:
    with session.no_autoflush:
        replay = _replay(session, tenant, identity)
        grouped = _groups(session, replay["inventory"], replay["contribution"])
        return {
            "state": "captured_known_subtotals",
            "algorithm_version": "captured-known-subtotals-v1",
            "basis": replay["captured_basis"],
            "inventory_groups": grouped["inventory"],
            "contribution_groups": grouped["contribution"],
            "group_coverage_scope": "available_subjects_only",
            "unavailable": {
                family: [
                    {key: row[key], "review_id": row["review_id"], "gaps": row["gaps"]}
                    for row in replay[family]
                    if row["result"] is None
                ]
                for family, key in (
                    ("inventory", "item_id"),
                    ("contribution", "document_line_id"),
                )
            },
            "details": {
                family: replay[family] for family in ("inventory", "contribution")
            },
            "publication_eligible": False,
            "persistence": {"business_writes": False, "projection_writes": False},
        }
