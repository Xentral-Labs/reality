"""Atomic captured-basis retention and explicit pinned financial replay."""

from uuid import uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session

from reality.db.contribution import CostContributionReview, CostRevenueMatchBasis
from reality.db.core import BusinessEvent, now
from reality.db.cost_captured_basis import (
    CostCapturedBasis,
    CostCapturedContributionBasis,
    CostCapturedInventoryBasis,
)
from reality.db.inventory_costing import (
    CostInventoryMember,
    CostInventoryReview,
    CostPolicyRevision,
)
from reality.domain.cost_captured_basis import (
    BASIS_BYTES,
    MEMBER_BYTES,
    verify_captured_basis,
)
from reality.domain.cost_census import digest, normalize
from reality.services import core
from reality.services.cost_census_storage import _header as census_header
from reality.services.cost_census_storage import _verify

_HEADER = CostCapturedBasis.__table__
_FAMILIES = {
    "inventory": (CostCapturedInventoryBasis.__table__, "item_id"),
    "contribution": (CostCapturedContributionBasis.__table__, "document_line_id"),
}
_OBSERVATIONS = {
    "state",
    "review_content_hash",
    "knowledge_at",
    "policy_id",
    "profile_revision_id",
    "inventory_review_id",
    "result_digest",
    "historical_result_digest",
    "gaps",
    "freshness_proof",
}
_VERSION = "captured-review-basis-v2"


def _transaction(session: Session) -> None:
    if session.new or session.dirty or session.deleted:
        raise core.InvalidOperation("Captured basis requires a clean session.")
    if session.connection().get_isolation_level() != "REPEATABLE READ":
        raise core.InvalidOperation("Captured basis requires REPEATABLE READ.")


def _invalid() -> None:
    raise core.InvalidOperation(
        "Captured basis content or dependency digest is invalid."
    )


def _selected(
    session: Session, tenant: str, family: str, subject: str, member: dict, cursor: int
):
    identity = member["review_id"]
    if identity is None:
        if member["state"] != "unknown_at_capture" or any(
            member[key] is not None
            for key in (
                "review_content_hash",
                "knowledge_at",
                "policy_id",
                "profile_revision_id",
                "inventory_review_id",
                "result_digest",
                "historical_result_digest",
            )
        ):
            _invalid()
        return None
    event = BusinessEvent.__table__
    if family == "inventory":
        review, relation = CostInventoryReview.__table__, CostPolicyRevision.__table__
        query = (
            select(review)
            .join(
                relation,
                (relation.c.tenant_id == tenant)
                & (relation.c.id == review.c.policy_id),
            )
            .where(relation.c.item_id == subject)
        )
        sequence = review.c.target_event_sequence
    else:
        review, relation = (
            CostContributionReview.__table__,
            CostRevenueMatchBasis.__table__,
        )
        query = (
            select(review, relation.c.item_id)
            .join(
                relation,
                (relation.c.tenant_id == tenant)
                & (relation.c.id == review.c.revenue_basis_id),
            )
            .where(relation.c.document_line_id == subject)
        )
        sequence = review.c.event_sequence
    row = (
        session.execute(
            query.join(
                event,
                (event.c.tenant_id == tenant)
                & (event.c.id == review.c.introduced_event_id),
            ).where(
                review.c.tenant_id == tenant,
                review.c.id == identity,
                event.c.sequence <= cursor,
                sequence == event.c.sequence,
            )
        )
        .mappings()
        .one_or_none()
    )
    if (
        row is None
        or row["content_hash"] != member["review_content_hash"]
        or normalize(row["knowledge_at"]) != member["knowledge_at"]
    ):
        _invalid()
    if family == "inventory":
        if (
            row["policy_id"] != member["policy_id"]
            or member["profile_revision_id"] is not None
            or member["inventory_review_id"] is not None
        ):
            _invalid()
    else:
        table = CostInventoryMember.__table__
        linked = session.scalar(
            select(table.c.review_id).where(
                table.c.tenant_id == tenant, table.c.id == row["inventory_member_id"]
            )
        )
        if (
            member["profile_revision_id"] != identity
            or member["inventory_review_id"] != linked
            or member["policy_id"] is not None
        ):
            _invalid()
    return dict(row)


def _read(
    session: Session, tenant: str, identity: str, *, _reviews: dict | None = None
) -> dict:
    _transaction(session)
    with session.no_autoflush:
        header = (
            session.execute(
                select(_HEADER).where(
                    _HEADER.c.tenant_id == tenant, _HEADER.c.id == identity
                )
            )
            .mappings()
            .one_or_none()
        )
        if header is None:
            raise core.NotFound("Captured cost basis not found.")
        if (
            header["state"] != "sealed"
            or header["sealed_at"] is None
            or header["basis_version"] != _VERSION
            or set(header["observations"]) != {"coverage", "coverage_scope", "gaps"}
        ):
            _invalid()
        records = {}
        _verify(session, tenant, header["census_id"], _records=records)
        census = census_header(session, tenant, header["census_id"])
        expected = {
            "inventory": {
                row["observed_values"]["item_id"] for row in records["movement"]
            },
            "contribution": {row["document_line_id"] for row in records["line"]},
        }
        content = {
            "version": header["basis_version"],
            "context": {
                "census_id": census["id"],
                "census_content_hash": census["content_hash"],
                **{
                    key: census[key]
                    for key in (
                        "tenant_id",
                        "effective_at",
                        "observed_at",
                        "snapshot_identity",
                        "event_sequence",
                    )
                },
            },
            **header["observations"],
        }
        for family, (table, key) in _FAMILIES.items():
            rows = (
                session.execute(
                    select(table)
                    .where(table.c.tenant_id == tenant, table.c.basis_id == identity)
                    .order_by(table.c[key])
                    .limit(11)
                )
                .mappings()
                .all()
            )
            if (
                len(rows) != header[f"{family}_count"]
                or len(rows) > 10
                or {row[key] for row in rows} != expected[family]
            ):
                _invalid()
            content[family] = []
            if _reviews is not None:
                _reviews[family] = {}
            for row in rows:
                if (
                    set(row["observations"]) != _OBSERVATIONS
                    or digest({k: v for k, v in row.items() if k != "content_hash"})
                    != row["content_hash"]
                ):
                    _invalid()
                member = {
                    key: row[key],
                    "review_id": row["review_id"],
                    **row["observations"],
                }
                selected = _selected(
                    session, tenant, family, row[key], member, census["event_sequence"]
                )
                content[family].append(member)
                if _reviews is not None:
                    _reviews[family][row[key]] = selected
        result = normalize(
            {
                **content,
                "digest": header["basis_digest"],
                "retained": True,
                "basis_id": identity,
                "publication_eligible": False,
            }
        )
        try:
            verify_captured_basis(result)
        except (ValueError, TypeError, KeyError) as error:
            raise core.InvalidOperation(
                "Captured basis content or dependency digest is invalid."
            ) from error
        return result


def _retain(
    session: Session,
    tenant: str,
    census: str,
    *,
    request_id: str,
    max_subjects: int = 10,
) -> dict:
    _transaction(session)
    if (
        type(max_subjects) is not int
        or not 1 <= max_subjects <= 10
        or not isinstance(request_id, str)
        or not request_id.strip()
        or len(request_id) > 128
    ):
        raise core.InvalidOperation("Invalid captured basis request or subject limit.")
    requested = digest(
        {
            "census_id": census,
            "version": _VERSION,
            "max_subjects": max_subjects,
            "member_bytes": MEMBER_BYTES,
            "basis_bytes": BASIS_BYTES,
        }
    )
    with session.no_autoflush:
        core.get_tenant(session, tenant)
        prior = session.execute(
            select(_HEADER.c.id, _HEADER.c.request_hash).where(
                _HEADER.c.tenant_id == tenant, _HEADER.c.request_id == request_id
            )
        ).one_or_none()
        if prior is not None:
            if prior.request_hash != requested:
                raise core.InvalidOperation("Captured basis request arguments changed.")
            return _read(session, tenant, prior.id)
        from reality.services.cost_census_resolution import _resolve

        basis = _resolve(session, tenant, census, max_subjects=max_subjects)[
            "captured_basis"
        ]
        try:
            verify_captured_basis(basis)
        except ValueError as error:
            raise core.InvalidOperation(str(error)) from error
        identity = "cbs_" + uuid4().hex
        with session.begin_nested():
            session.execute(
                insert(_HEADER).values(
                    id=identity,
                    tenant_id=tenant,
                    census_id=census,
                    request_id=request_id,
                    request_hash=requested,
                    basis_version=_VERSION,
                    state="building",
                    sealed_at=None,
                    inventory_count=len(basis["inventory"]),
                    contribution_count=len(basis["contribution"]),
                    basis_digest=basis["digest"],
                    observations={
                        key: basis[key]
                        for key in ("coverage", "coverage_scope", "gaps")
                    },
                )
            )
            for family, (table, key) in _FAMILIES.items():
                for member in basis[family]:
                    row = {
                        "id": "cbm_" + uuid4().hex,
                        "tenant_id": tenant,
                        "basis_id": identity,
                        key: member[key],
                        "review_id": member["review_id"],
                        "observations": {name: member[name] for name in _OBSERVATIONS},
                    }
                    session.execute(
                        insert(table).values(**row, content_hash=digest(row))
                    )
            session.execute(
                update(_HEADER)
                .where(
                    _HEADER.c.tenant_id == tenant,
                    _HEADER.c.id == identity,
                    _HEADER.c.state == "building",
                )
                .values(state="sealed", sealed_at=now())
            )
            result = _read(session, tenant, identity)
        return result


def _replay(session: Session, tenant: str, identity: str) -> dict:
    reviews = {}
    basis = _read(session, tenant, identity, _reviews=reviews)
    from reality.services.cost_census_resolution import _resolve

    result = _resolve(session, tenant, basis["context"]["census_id"], _pinned=reviews)
    if result["captured_basis"]["digest"] != basis["digest"]:
        _invalid()
    return {**result, "captured_basis": basis}
