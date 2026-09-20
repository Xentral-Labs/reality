"""Internal captured report cache: immutable outputs, scoped CAS and bounded reads."""

import base64
import json
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session

from reality.db.captured_report import (
    CostContributionRow,
    CostGeneration,
    CostInventoryRow,
    CostPublication,
)
from reality.db.core import now
from reality.db.cost_captured_basis import (
    CostCapturedBasis,
    CostCapturedContributionBasis,
    CostCapturedInventoryBasis,
)
from reality.db.cost_census import CostCompanyCensus
from reality.domain.captured_report import (
    ALGORITHM,
    KIND,
    CapturedPublication,
    decide,
    scope_key,
)
from reality.domain.cost_census import digest, normalize
from reality.services import core, cost_captured_basis
from reality.services.business_locks import lock_delivery_state
from reality.services.cost_captured_summary import _groups
from reality.services.costing import _sequence

G = CostGeneration.__table__
P = CostPublication.__table__
FAMILIES = {
    "inventory": (
        CostInventoryRow.__table__,
        CostCapturedInventoryBasis.__table__,
        "inventory_basis_member_id",
        "item_id",
    ),
    "contribution": (
        CostContributionRow.__table__,
        CostCapturedContributionBasis.__table__,
        "contribution_basis_member_id",
        "document_line_id",
    ),
}


def _clean(session: Session, isolation: str | None = None) -> None:
    if session.new or session.dirty or session.deleted:
        raise core.InvalidOperation("Captured reports require a clean session.")
    if isolation and session.connection().get_isolation_level() != isolation:
        raise core.InvalidOperation(f"Captured report operation requires {isolation}.")


def _id() -> str:
    return "cgr_" + uuid4().hex


def _amount(value: str | None) -> Decimal | None:
    if value is None:
        return None
    result = Decimal(value)
    if (
        not result.is_finite()
        or abs(result) >= Decimal(100000000000000)
        or result != result.quantize(Decimal("0.0001"))
    ):
        raise core.InvalidOperation(
            "Captured amount exceeds exact NUMERIC(18,4) support."
        )
    return result


def _header(session: Session, tenant: str, identity: str) -> dict:
    b, c = CostCapturedBasis.__table__, CostCompanyCensus.__table__
    row = (
        session.execute(
            select(
                G,
                b.c.observations.label("basis_observations"),
                b.c.basis_digest,
                c.c.effective_at,
                c.c.observed_at,
                c.c.event_sequence,
            )
            .join(b, (b.c.tenant_id == tenant) & (b.c.id == G.c.captured_basis_id))
            .join(c, (c.c.tenant_id == tenant) & (c.c.id == b.c.census_id))
            .where(G.c.tenant_id == tenant, G.c.id == identity)
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise core.NotFound("Captured report not found.")
    result = dict(row)
    if (
        result["state"] != "sealed"
        or result["algorithm_version"] != ALGORITHM
        or result["kind"] != KIND
        or result["scope_key"] != scope_key(tenant, result["effective_at"])
    ):
        raise core.InvalidOperation("Captured report is unsealed or unsupported.")
    return result


def _stored(
    session: Session, tenant: str, identity: str, basis: str
) -> tuple[dict, dict]:
    content, details = {}, {}
    for family, (table, members, key, subject) in FAMILIES.items():
        rows = (
            session.execute(
                select(
                    table,
                    members.c[subject],
                    members.c.review_id,
                    members.c.observations.label("member_observations"),
                )
                .join(
                    members,
                    (members.c.tenant_id == tenant)
                    & (members.c.id == table.c[key])
                    & (members.c.basis_id == basis),
                )
                .where(table.c.tenant_id == tenant, table.c.generation_id == identity)
                .order_by(table.c[key])
                .limit(11)
            )
            .mappings()
            .all()
        )
        if len(rows) > 10:
            raise core.InvalidOperation("Captured report exceeds subject bounds.")
        content[family] = [
            {
                name: normalize(row[name])
                for name in tuple(table.c.keys())
                if name not in {"id", "tenant_id", "generation_id"}
            }
            for row in rows
        ]
        details[family] = [
            {
                **part,
                subject: row[subject],
                "review_id": row["review_id"],
                "basis": row["member_observations"],
            }
            for part, row in zip(content[family], rows, strict=True)
        ]
    return content, details


def _verified(session: Session, tenant: str, identity: str) -> tuple[dict, dict]:
    header = _header(session, tenant, identity)
    content, details = _stored(session, tenant, identity, header["captured_basis_id"])
    if (
        any(len(content[family]) != header[f"{family}_count"] for family in FAMILIES)
        or sum(map(len, content.values())) > 10
        or digest(content) != header["output_hash"]
    ):
        raise core.InvalidOperation("Captured report output integrity mismatch.")
    return header, details


def _metadata(header: dict) -> dict:
    return {
        "generation_id": header["id"],
        "basis_id": header["captured_basis_id"],
        "scope_key": header["scope_key"],
        "output_hash": header["output_hash"],
        "kind": KIND,
        "algorithm_version": ALGORITHM,
        "financial_publication_eligible": False,
    }


def _build(session: Session, tenant: str, basis_id: str) -> dict:
    _clean(session, "REPEATABLE READ")
    with session.no_autoflush, session.begin_nested():
        # Serialize against the immutable input row. Concurrent RR losers retry in a
        # fresh caller transaction; unique basis/algorithm prevents duplicate outputs.
        b = CostCapturedBasis.__table__
        if (
            session.scalar(
                select(b.c.id)
                .where(b.c.tenant_id == tenant, b.c.id == basis_id)
                .with_for_update()
            )
            is None
        ):
            raise core.NotFound("Captured basis not found.")
        prior = session.scalar(
            select(G.c.id).where(
                G.c.tenant_id == tenant,
                G.c.captured_basis_id == basis_id,
                G.c.algorithm_version == ALGORITHM,
            )
        )
        if prior:
            return _metadata(_verified(session, tenant, prior)[0])
        replay = cost_captured_basis._replay(session, tenant, basis_id)
        basis = replay["captured_basis"]
        context = basis["context"]
        identity = _id()
        expected = {}
        from datetime import datetime

        effective = datetime.fromisoformat(context["effective_at"])
        session.execute(
            insert(G).values(
                id=identity,
                tenant_id=tenant,
                captured_basis_id=basis_id,
                kind=KIND,
                algorithm_version=ALGORITHM,
                scope_key=scope_key(tenant, effective),
                state="building",
                inventory_count=len(replay["inventory"]),
                contribution_count=len(replay["contribution"]),
                output_hash="0" * 64,
            )
        )
        for family, (table, members, key, subject) in FAMILIES.items():
            mapping = dict(
                session.execute(
                    select(members.c[subject], members.c.id).where(
                        members.c.tenant_id == tenant, members.c.basis_id == basis_id
                    )
                ).all()
            )
            if set(mapping) != {row[subject] for row in replay[family]}:
                raise core.InvalidOperation("Captured membership mismatch.")
            parts = []
            for row in replay[family]:
                result = row["result"]
                part = {
                    name: None
                    for name in tuple(table.c.keys())
                    if name not in {"id", "tenant_id", "generation_id"}
                }
                part.update({key: mapping[row[subject]], "state": row["state"]})
                if result is not None:
                    part.update(
                        currency=result["currency"], base_unit=result["base_unit"]
                    )
                    if family == "inventory":
                        part.update(
                            method=result["method"],
                            owner_party_id=result["owner_party_id"],
                        )
                        for name in (
                            "remaining_quantity",
                            "acquisition_value",
                            "carrying_value",
                        ):
                            part[name] = _amount(result[name])
                    else:
                        if result["profile"] != "commercial_v1":
                            raise core.InvalidOperation(
                                "Unsupported commercial profile."
                            )
                        part.update(
                            revenue=_amount(result["trace"]["received_net"]),
                            goods_cost=_amount(result["trace"]["consumption"]["cost"]),
                            direct_selling_cost=_amount(result["direct_selling_cost"]),
                            allocated_selling_cost=_amount(
                                result["allocated_selling_cost"]
                            ),
                        )
                session.execute(
                    insert(table).values(
                        id=_id(), tenant_id=tenant, generation_id=identity, **part
                    )
                )
                parts.append(normalize(part))
            expected[family] = sorted(parts, key=lambda row: row[key])
        actual, _ = _stored(session, tenant, identity, basis_id)
        if actual != expected:
            raise core.InvalidOperation(
                "Persisted report differs from canonical replay."
            )
        session.execute(
            update(G)
            .where(G.c.tenant_id == tenant, G.c.id == identity)
            .values(state="sealed", completed_at=now(), output_hash=digest(actual))
        )
        return _metadata(_verified(session, tenant, identity)[0])


def _publication(header: dict) -> CapturedPublication:
    return CapturedPublication(
        tenant_id=header["tenant_id"],
        generation_id=header["id"],
        basis_id=header["captured_basis_id"],
        scope_key=header["scope_key"],
        effective_at=header["effective_at"],
        event_sequence=header["event_sequence"],
    )


def _publish(
    session: Session, tenant: str, identity: str, previous: str | None
) -> dict:
    _clean(session, "READ COMMITTED")
    with session.no_autoflush, session.begin_nested():
        lock_delivery_state(session, tenant)
        session.execute(
            select(G.c.id)
            .where(G.c.tenant_id == tenant, G.c.id == identity)
            .with_for_update()
        )
        header, _ = _verified(session, tenant, identity)
        pointer = (
            session.execute(
                select(P)
                .where(P.c.tenant_id == tenant, P.c.scope_key == header["scope_key"])
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )
        prior = (
            _verified(session, tenant, pointer["generation_id"])[0] if pointer else None
        )
        try:
            result = decide(
                tenant,
                _publication(header),
                _publication(prior) if prior else None,
                previous,
                _sequence(session, tenant),
            )
        except ValueError as error:
            raise core.InvalidOperation(str(error)) from error
        if result["change_pointer"]:
            if pointer:
                session.execute(
                    update(P)
                    .where(P.c.tenant_id == tenant, P.c.id == pointer["id"])
                    .values(generation_id=identity)
                )
            else:
                session.execute(
                    insert(P).values(
                        id=_id(),
                        tenant_id=tenant,
                        scope_key=header["scope_key"],
                        generation_id=identity,
                    )
                )
        return result


def _replay_shape(family: str, rows: list[dict]) -> list[dict]:
    shaped = []
    for row in rows:
        result = None
        if row["state"] == "available_at_capture":
            result = dict(row)
            if family == "contribution":
                result.update(
                    profile="commercial_v1",
                    trace={
                        "received_net": row["revenue"],
                        "consumption": {"cost": row["goods_cost"]},
                    },
                )
        shaped.append({**row, "result": result})
    return shaped


def _page(
    rows: list[dict], identity: str, family: str, cursor: str | None, size: int
) -> dict:
    key = FAMILIES[family][2]
    after = None
    if cursor is not None:
        try:
            value = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if (
                not isinstance(value, list)
                or len(value) != 3
                or value[:2] != [identity, family]
                or not isinstance(value[2], str)
            ):
                raise ValueError
            after = value[2]
            if after not in {row[key] for row in rows}:
                raise ValueError
        except (ValueError, TypeError, UnicodeError) as error:
            raise core.InvalidOperation("Invalid captured report cursor.") from error
    remaining = [row for row in rows if after is None or row[key] > after]
    page = remaining[:size]
    next_cursor = (
        base64.urlsafe_b64encode(
            json.dumps([identity, family, page[-1][key]]).encode()
        ).decode()
        if len(remaining) > size
        else None
    )
    return {"rows": page, "total": len(rows), "next_cursor": next_cursor}


def _report(
    session: Session,
    tenant: str,
    identity: str,
    *,
    page_size: int = 50,
    inventory_cursor: str | None = None,
    contribution_cursor: str | None = None,
) -> dict:
    _clean(session)
    if type(page_size) is not int or not 1 <= page_size <= 100:
        raise core.InvalidOperation("Page size must be between 1 and 100.")
    if any(
        cursor is not None and (not isinstance(cursor, str) or len(cursor) > 1024)
        for cursor in (inventory_cursor, contribution_cursor)
    ):
        raise core.InvalidOperation("Invalid captured report cursor.")
    with session.no_autoflush:
        header, details = _verified(session, tenant, identity)
        groups = _groups(
            session,
            _replay_shape("inventory", details["inventory"]),
            _replay_shape("contribution", details["contribution"]),
        )
        cursor = _sequence(session, tenant)
        return {
            **_metadata(header),
            "context": {
                key: normalize(header[key])
                for key in ("effective_at", "observed_at", "event_sequence")
            },
            "basis": {
                "id": header["captured_basis_id"],
                "digest": header["basis_digest"],
                **header["basis_observations"],
            },
            "freshness": "ready" if cursor == header["event_sequence"] else "pending",
            "groups": groups,
            "group_coverage_scope": "available_subjects_only",
            "inventory": _page(
                details["inventory"], identity, "inventory", inventory_cursor, page_size
            ),
            "contribution": _page(
                details["contribution"],
                identity,
                "contribution",
                contribution_cursor,
                page_size,
            ),
        }


def _discard(session: Session, tenant: str, identity: str) -> None:
    _clean(session, "READ COMMITTED")
    with session.no_autoflush, session.begin_nested():
        lock_delivery_state(session, tenant)
        if (
            session.scalar(
                select(G.c.id)
                .where(G.c.tenant_id == tenant, G.c.id == identity)
                .with_for_update()
            )
            is None
        ):
            raise core.NotFound("Captured report not found.")
        if session.scalar(
            select(P.c.id).where(P.c.tenant_id == tenant, P.c.generation_id == identity)
        ):
            raise core.InvalidOperation("Published report cannot be discarded.")
        session.execute(delete(G).where(G.c.tenant_id == tenant, G.c.id == identity))
