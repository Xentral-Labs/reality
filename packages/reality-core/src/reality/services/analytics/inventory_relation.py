"""Bounded canonical current inventory, at one row per article across all locations."""

from typing import Any

from sqlalchemy import Numeric, String, bindparam, column, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import TableValuedAlias

from reality.db.core import Commitment, CommitmentRevision, Item, Movement
from reality.services import core
from reality.services.analytics.traversal import TraversalRefused

MAX_INVENTORY_ITEMS = 20_000
MAX_INVENTORY_INPUTS = 100_000
# Commitment terms binds one identity per supplier promise in its bulk reads.
MAX_INVENTORY_COMMITMENTS = 20_000
INVENTORY_COLUMNS = {key: Numeric() for key in ("physical", "reserved", "available")}


def relation(
    session: Session,
    tenant_id: str,
    *,
    identities: set[str] | None = None,
    cache: dict[Any, Any] | None = None,
) -> TableValuedAlias:
    """Bound every family the canonical bulk derivation materializes in memory."""
    for model, maximum in (
        (Item, MAX_INVENTORY_ITEMS),
        (Movement, MAX_INVENTORY_INPUTS),
        (Commitment, MAX_INVENTORY_COMMITMENTS),
        (CommitmentRevision, MAX_INVENTORY_INPUTS),
    ):
        candidates = select(model.id).where(model.tenant_id == tenant_id)
        if model is Commitment:
            candidates = candidates.where(
                Commitment.type == "supplier_delivery", Commitment.status == "open"
            )
        if identities is not None and model is Item:
            candidates = candidates.where(Item.id.in_(identities))
        count = session.scalar(
            select(func.count()).select_from(candidates.limit(maximum + 1).subquery())
        )
        if count > maximum:
            raise TraversalRefused(
                "Current stock analysis exceeds its input limit; use the warehouse register.",
                "inventory_limit",
            )
    key = ("warehouse.inventory", None if identities is None else frozenset(identities))
    if cache is not None and key in cache:
        rows = cache[key]
    else:
        rows = core.inventory_rows(session, tenant_id, item_ids=identities)
        if cache is not None:
            cache[key] = rows
    return recordset(
        [
            {
                "item_id": row["item"].id,
                **{key: str(row[key]) for key in INVENTORY_COLUMNS},
            }
            for row in rows
        ]
    )


def recordset(data: list[dict[str, Any]]) -> TableValuedAlias:
    return (
        func.jsonb_to_recordset(bindparam("inventory_rows", data, type_=JSONB))
        .table_valued(
            column("item_id", String()),
            *[column(key, kind) for key, kind in INVENTORY_COLUMNS.items()],
        )
        .render_derived(name="inventory_current", with_types=True)
    )
