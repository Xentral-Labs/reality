"""Bounded derived positions and explicit effective-date inputs for analysis."""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Numeric, String, bindparam, column, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import TableValuedAlias
from sqlalchemy.types import TypeEngine

from reality.db.core import (
    Base,
    Document,
    HandlingUnit,
    Item,
    LedgerEntry,
    LedgerReversal,
    Location,
    Lot,
    Movement,
    Party,
    PaymentTerm,
    Reservation,
    SerialUnit,
    SettlementAllocation,
)
from reality.db.opening import OpeningScope
from reality.services.analytics.budget import input_ceiling
from reality.services.analytics.traversal import ResolvedPath, TraversalRefused
from reality.services.finance.balances import party_balance_rows
from reality.services.inventory_positions import (
    inventory_detail_rows,
    position_identity,
)

BALANCE_COLUMNS = {
    "position_id": String(),
    "currency": String(),
    **{k: Numeric() for k in ("open", "credit", "balance")},
}
STOCK_COLUMNS = {
    "position_id": String(),
    **{
        k: String()
        for k in (
            "location_id",
            "lot_id",
            "serial_unit_id",
            "handling_unit_id",
            "location_name",
            "lot_name",
            "serial_unit_name",
            "handling_unit_name",
        )
    },
    **{k: Numeric() for k in ("physical", "reserved", "available")},
}
MAX_ROWS = 20_000


def snapshot_date(path: ResolvedPath) -> date | None:
    """Require one identical equality input for every historical alias, including EXISTS."""
    scopes = [(path.node_of, path.query.filter)] + [
        (test.node_of, (*path.query.filter, *test.conditions)) for test in path.exists
    ]
    selected = set()
    for nodes, conditions in scopes:
        for alias, name in nodes.items():
            if not (path.graph.nodes[name].derivation or "").endswith(".history"):
                continue
            filters = [c for c in conditions if c.field == f"{alias}.snapshot_date"]
            if not filters:
                raise TraversalRefused(
                    "Choose a snapshot date (end of the selected UTC day).",
                    "snapshot_date_required",
                )
            for condition in filters:
                try:
                    value = (
                        date.fromisoformat(condition.value)
                        if isinstance(condition.value, str)
                        else None
                    )
                    if (
                        condition.op != "eq"
                        or value is None
                        or value.isoformat() != condition.value
                        or value > datetime.now(UTC).date()
                    ):
                        raise ValueError()
                except (ValueError, TypeError):
                    raise TraversalRefused(
                        "Use one past or current calendar date for the snapshot.",
                        "invalid_snapshot_date",
                    ) from None
                selected.add(value)
    if len(selected) > 1:
        raise TraversalRefused(
            "All snapshot dates in one analysis must agree.", "invalid_snapshot_date"
        )
    return next(iter(selected), None)


def bounded(
    session: Session,
    tenant_id: str,
    models: tuple[type[Base], ...],
    anchor: tuple[type[Base], set[str]] | None = None,
) -> None:
    for model in models:
        candidates = select(model.id).where(model.tenant_id == tenant_id)
        if anchor and model is anchor[0]:
            candidates = candidates.where(model.id.in_(anchor[1]))
        candidates = candidates.limit(input_ceiling(MAX_ROWS) + 1)
        if session.scalar(
            select(func.count()).select_from(candidates.subquery())
        ) > input_ceiling(MAX_ROWS):
            raise TraversalRefused(
                "Position analysis exceeds its input limit; narrow the source in the operational register.",
                "position_limit",
            )


def recordset(
    data: list[dict[str, Any]],
    *,
    name: str,
    identity: str,
    columns: dict[str, TypeEngine],
) -> TableValuedAlias:
    return (
        func.jsonb_to_recordset(bindparam(name + "_rows", data, type_=JSONB))
        .table_valued(
            column(identity, String()), *[column(k, t) for k, t in columns.items()]
        )
        .render_derived(name=name, with_types=True)
    )


def relation(
    session: Session,
    tenant_id: str,
    *,
    name: str,
    identity: str,
    columns: dict[str, TypeEngine],
    side: str | None = None,
    snapshot: date | None = None,
    identities: set[str] | None = None,
    cache: dict[Any, Any] | None = None,
) -> TableValuedAlias:
    before = (
        datetime.combine(snapshot + timedelta(days=1), time(), UTC)
        if snapshot
        else None
    )
    key = (name, snapshot, None if identities is None else frozenset(identities))
    if cache is not None and key in cache:
        # The bounds and the opening-coverage refusals below depend only on the
        # tenant, the snapshot and these identities, so the stored answer is one
        # that already passed them in this request. Re-running them would ask the
        # same question of the same rows.
        return recordset(cache[key], name=name, identity=identity, columns=columns)
    if side:
        bounded(
            session,
            tenant_id,
            (
                Document,
                Party,
                LedgerEntry,
                LedgerReversal,
                SettlementAllocation,
                OpeningScope,
                PaymentTerm,
            ),
            (Party, identities) if identities is not None else None,
        )
        if snapshot and session.scalar(
            select(OpeningScope.id)
            .where(
                OpeningScope.tenant_id == tenant_id,
                OpeningScope.direction.like(side + "_%"),
                OpeningScope.cutover_date > snapshot,
            )
            .limit(1)
        ):
            raise TraversalRefused(
                "The snapshot precedes retained opening coverage.",
                "history_unavailable",
            )
        rows = [
            {
                "party_id": row["party_id"],
                "position_id": position_identity(
                    tenant_id, side, row["party_id"], row["currency"]
                ),
                **{k: row[k] for k in ("currency", "open", "credit", "balance")},
            }
            for row in party_balance_rows(
                session,
                tenant_id,
                side=side,
                as_of=cache.get("moment") if cache is not None else None,
                effective_before=before,
                party_ids=identities,
                cache=cache,
            )
        ]
    else:
        bounded(
            session,
            tenant_id,
            (Item, Movement, Reservation, Location, Lot, SerialUnit, HandlingUnit),
            (Item, identities) if identities is not None else None,
        )
        if before and session.scalar(
            select(Movement.id)
            .where(
                Movement.tenant_id == tenant_id,
                Movement.type == "opening_stock",
                Movement.occurred_at >= before,
            )
            .limit(1)
        ):
            raise TraversalRefused(
                "The snapshot precedes retained opening stock.", "history_unavailable"
            )
        rows = inventory_detail_rows(
            session, tenant_id, effective_before=before, item_ids=identities
        )
    data = [
        {
            **{k: str(v) if isinstance(v, Decimal) else v for k, v in row.items()},
            **({"snapshot_date": snapshot.isoformat()} if snapshot else {}),
        }
        for row in rows
    ]
    if cache is not None:
        cache[key] = data
    return recordset(data, name=name, identity=identity, columns=columns)
