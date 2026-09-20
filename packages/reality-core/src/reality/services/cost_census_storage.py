"""Atomic retained current discovery and bounded frozen-member inspection."""

import base64
import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session

from reality.db.core import now
from reality.db.cost_census import (
    CostCompanyCensus,
    CostCompanyCensusDocument,
    CostCompanyCensusLine,
    CostCompanyCensusMovement,
    CostCompanyCensusSource,
)
from reality.domain.cost_census import check_size, digest, normalize
from reality.services import core
from reality.services.cost_census import _capture

_FAMILIES = {
    "movement": (CostCompanyCensusMovement.__table__, "movement_id"),
    "document": (CostCompanyCensusDocument.__table__, "document_id"),
    "line": (CostCompanyCensusLine.__table__, "document_line_id"),
    "source": (CostCompanyCensusSource.__table__, "source_record_id"),
}
# Version 1 is an explicit allowlist: schema growth requires a capture-version review.
_FIELDS = {
    "movement": [
        "commitment_id",
        "event_count",
        "event_id",
        "event_sequence",
        "from_location_id",
        "handling_unit_id",
        "id",
        "item_id",
        "lot_id",
        "occurred_at",
        "quantity",
        "resolves_movement_id",
        "return_announcement_id",
        "scoped_item_id",
        "serial_unit_id",
        "shipment_package_id",
        "source_record_id",
        "tenant_id",
        "to_location_id",
        "type",
    ],
    "document": [
        "currency",
        "customer_reference",
        "document_date",
        "event_count",
        "event_id",
        "event_sequence",
        "gross_amount",
        "id",
        "number",
        "ordered_at",
        "party_id",
        "payment_term_id",
        "requested_delivery_at",
        "sales_channel",
        "ship_to_party_id",
        "source_record_id",
        "status",
        "tenant_id",
        "type",
    ],
    "line": [
        "billed_document_line_id",
        "description",
        "document_id",
        "gross_amount",
        "id",
        "item_id",
        "line_type",
        "payload",
        "price_list_entry_id",
        "promised_at",
        "quantity",
        "requested_at",
        "sku",
        "source_line_id",
        "tenant_id",
        "unit",
        "unit_price",
    ],
    "source": [
        "classification",
        "import_status",
        "outcome_id",
        "payload_hash",
        "received_at",
        "source_record_id",
        "version",
    ],
}
_HEADER = CostCompanyCensus.__table__
_CONTEXT = (
    "id",
    "tenant_id",
    "request_id",
    "request_hash",
    "effective_at",
    "observed_at",
    "snapshot_identity",
    "event_sequence",
    "input_schema_version",
)


def _header(session: Session, tenant: str, identity: str) -> dict:
    row = (
        session.execute(
            select(_HEADER).where(
                _HEADER.c.tenant_id == tenant, _HEADER.c.id == identity
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise core.NotFound("Company census not found.")
    result = dict(row)
    if (
        result["state"] != "sealed"
        or result["input_schema_version"] != 1
        or result["sealed_at"] is None
    ):
        raise core.InvalidOperation("Company census is not a supported sealed capture.")
    return result


def _summary(header: dict) -> dict:
    return {**normalize(header), "publication_eligible": False}


def _member_hash(row: dict) -> str:
    return digest({key: value for key, value in row.items() if key != "content_hash"})


def _content_hash(header: dict, members: dict) -> str:
    return digest(
        {
            "context": {key: header[key] for key in _CONTEXT},
            "counts": {family: header[f"{family}_count"] for family in _FAMILIES},
            "members": {
                family: sorted((row["id"], row["content_hash"]) for row in rows)
                for family, rows in members.items()
            },
        }
    )


def _retain(
    session: Session,
    tenant: str,
    effective_at: datetime,
    *,
    request_id: str,
    max_records: int = 100_000,
) -> dict:
    if session.new or session.dirty or session.deleted:
        raise core.InvalidOperation("Company census capture requires a clean session.")
    if (
        not isinstance(request_id, str)
        or not request_id.strip()
        or len(request_id) > 128
    ):
        raise core.InvalidOperation("Invalid company census request identity.")
    if not isinstance(effective_at, datetime) or effective_at.utcoffset() is None:
        raise core.InvalidOperation(
            "Company census requires an aware effective cutoff."
        )
    if type(max_records) is not int or not 1 <= max_records <= 100_000:
        raise core.InvalidOperation("Invalid company census record limit.")
    if session.connection().get_isolation_level() != "REPEATABLE READ":
        raise core.InvalidOperation("Company census requires REPEATABLE READ.")
    with session.no_autoflush:
        core.get_tenant(session, tenant)
        requested = digest(
            {"effective_at": effective_at, "version": 1, "max_records": max_records}
        )
        prior = session.execute(
            select(_HEADER.c.id, _HEADER.c.request_hash).where(
                _HEADER.c.tenant_id == tenant, _HEADER.c.request_id == request_id
            )
        ).one_or_none()
        if prior is not None:
            if prior.request_hash != requested:
                raise core.InvalidOperation("Company census request arguments changed.")
            _verify(session, tenant, prior.id)
            return _summary(_header(session, tenant, prior.id))
        records = {}
        discovery = _capture(
            session, tenant, effective_at, max_records=max_records, _records=records
        )
        context = discovery["context"]
        header = {
            "id": "cns_" + uuid4().hex,
            "tenant_id": tenant,
            "request_id": request_id,
            "request_hash": requested,
            "effective_at": effective_at.astimezone(UTC),
            "observed_at": datetime.fromisoformat(context["observed_at"]),
            "snapshot_identity": context["snapshot"],
            "event_sequence": context["event_sequence"],
            "input_schema_version": 1,
            "state": "building",
            "sealed_at": None,
            **{f"{family}_count": len(records[family]) for family in _FAMILIES},
        }
        members, documents, total = {}, {}, 0
        for family, (_, reference) in _FAMILIES.items():
            members[family] = []
            for record in records[family]:
                if set(record) != set(_FIELDS[family]):
                    raise core.InvalidOperation(
                        "Unsupported census observation schema."
                    )
                row = {
                    "id": "cns_" + uuid4().hex,
                    "tenant_id": tenant,
                    "census_id": header["id"],
                    reference: record["source_record_id"]
                    if family == "source"
                    else record["id"],
                    "observed_values": normalize(record),
                }
                if family == "document":
                    documents[record["id"]] = row["id"]
                elif family == "line":
                    if record["document_id"] not in documents:
                        raise core.InvalidOperation(
                            "Census line has an unavailable header."
                        )
                    row["document_member_id"] = documents[record["document_id"]]
                elif family == "source":
                    row["interpretation_outcome_id"] = record["outcome_id"]
                try:
                    total = check_size(row, total=total)
                except ValueError as error:
                    raise core.InvalidOperation(str(error)) from error
                row["content_hash"] = _member_hash(row)
                members[family].append(row)
        header["content_hash"] = _content_hash(header, members)
        # Savepoint protects callers that catch a write error and later commit.
        with session.begin_nested():
            session.execute(insert(_HEADER).values(**header))
            for family, (table, _) in _FAMILIES.items():
                for start in range(0, len(members[family]), 500):
                    session.execute(insert(table), members[family][start : start + 500])
            session.execute(
                update(_HEADER)
                .where(_HEADER.c.tenant_id == tenant, _HEADER.c.id == header["id"])
                .values(state="sealed", sealed_at=now())
            )
            _verify(session, tenant, header["id"])
        return _summary(_header(session, tenant, header["id"]))


def _get(session: Session, tenant: str, identity: str) -> dict:
    with session.no_autoflush:
        return _summary(_header(session, tenant, identity))


def _check_member(row: dict) -> None:
    if row["content_hash"] != _member_hash(row):
        raise core.InvalidOperation("Company census member integrity mismatch.")


def _verify(
    session: Session, tenant: str, identity: str, *, _records: dict | None = None
) -> dict:
    with session.no_autoflush:
        header = _header(session, tenant, identity)
        members, count, total = {}, 0, 0
        for family, (table, _) in _FAMILIES.items():
            rows = [
                dict(row)
                for row in session.execute(
                    select(table)
                    .where(table.c.tenant_id == tenant, table.c.census_id == identity)
                    .limit(100_001 - count)
                ).mappings()
            ]
            count += len(rows)
            if count > 100_000 or len(rows) != header[f"{family}_count"]:
                raise core.InvalidOperation("Company census membership count mismatch.")
            for row in rows:
                _check_member(row)
                try:
                    total = check_size(
                        {
                            key: value
                            for key, value in row.items()
                            if key != "content_hash"
                        },
                        total=total,
                    )
                except ValueError as error:
                    raise core.InvalidOperation(str(error)) from error
            members[family] = rows
        if header["content_hash"] != _content_hash(header, members):
            raise core.InvalidOperation("Company census content integrity mismatch.")
        if _records is not None:
            _records.update(members)
        return {
            "id": identity,
            "verified": True,
            "publication_eligible": False,
            "counts": {family: len(rows) for family, rows in members.items()},
        }


def _members(
    session: Session,
    tenant: str,
    identity: str,
    *,
    family: str,
    limit: int = 100,
    cursor: str | None = None,
) -> dict:
    with session.no_autoflush:
        _header(session, tenant, identity)
        if family not in _FAMILIES:
            raise core.InvalidOperation("Unsupported census member family.")
        if type(limit) is not int or not 1 <= limit <= 500:
            raise core.InvalidOperation("Census member page limit must be 1–500.")
        last = None
        if cursor is not None:
            try:
                if not isinstance(cursor, str) or len(cursor) > 2048:
                    raise ValueError
                decoded = json.loads(base64.urlsafe_b64decode(cursor))
                if (
                    not isinstance(decoded, list)
                    or len(decoded) != 4
                    or decoded[:3] != [tenant, identity, family]
                    or not isinstance(decoded[3], str)
                ):
                    raise ValueError
                last = decoded[3]
            except (ValueError, TypeError, UnicodeError) as error:
                raise core.InvalidOperation("Invalid census member cursor.") from error
        table, _ = _FAMILIES[family]
        query = select(table).where(
            table.c.tenant_id == tenant, table.c.census_id == identity
        )
        if last is not None:
            query = query.where(table.c.id > last)
        rows = [
            dict(row)
            for row in session.execute(
                query.order_by(table.c.id).limit(limit + 1)
            ).mappings()
        ]
        for row in rows:
            _check_member(row)
        next_cursor = (
            base64.urlsafe_b64encode(
                json.dumps([tenant, identity, family, rows[limit - 1]["id"]]).encode()
            ).decode()
            if len(rows) > limit
            else None
        )
        return {
            "census_id": identity,
            "family": family,
            "members": normalize(rows[:limit]),
            "next_cursor": next_cursor,
            "whole_capture_verified": False,
        }
