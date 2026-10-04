"""Exact retained selection for the existing stale commitment closure."""
import json

from sqlalchemy import select

from reality.domain.intake import canonical_json
from reality.services import core
from reality.services.commitment_actions import review_commitment_action

REVIEW_KEY = "_stale_closure_review"
PUBLIC_FIELDS = {"direction", "due_before", "expected_count", "reason"}


def _reference_state(session, tenant_id, arguments):
    if set(arguments) - PUBLIC_FIELDS or not PUBLIC_FIELDS <= arguments.keys():
        raise core.InvalidOperation(code="intake_review_invalid")
    if not str(arguments["reason"]).strip():
        raise core.InvalidOperation("A closure requires a reason.")
    matches = core._stale_promises(session, tenant_id, direction=arguments["direction"], due_before=arguments["due_before"])
    if len(matches) != int(arguments["expected_count"]):
        raise core.InvalidOperation("The closure no longer matches the confirmed count.")
    result = []
    for row in sorted(matches, key=lambda row: row.id):
        review = review_commitment_action(session, tenant_id, "commitment_cancel", {
            "commitment_id": row.id, "reason": arguments["reason"],
        })
        # The retained batch state uses numeric values, not identity-map-specific
        # decimal string scale or a child token derived from that presentation.
        review.pop("token")
        for field in ("quantity", "fulfilled", "open"):
            review["state"][field] = core.decimal(review["state"][field])
        for reservation in review["state"]["active_reservations"]:
            reservation["quantity"] = core.decimal(reservation["quantity"])
        for field in ("cancelled_open", "fulfilled_retained"):
            review["effect"][field] = core.decimal(review["effect"][field])
        revisions = list(session.scalars(select(core.CommitmentRevision).where(
            core.CommitmentRevision.tenant_id == tenant_id,
            core.CommitmentRevision.commitment_id == row.id,
        ).order_by(core.CommitmentRevision.id)))
        result.append({"commitment": {column.name: getattr(row, column.name) for column in row.__table__.columns},
                       "revisions": [{column.name: getattr(revision, column.name) for column in revision.__table__.columns} for revision in revisions],
                       "review": review})
    return json.loads(canonical_json(result))


def prepare_stale_closure(session, tenant_id, arguments):
    normalized = json.loads(canonical_json(arguments))
    return {**normalized, REVIEW_KEY: _reference_state(session, tenant_id, normalized)}


def require_current_stale_closure(session, tenant_id, intent):
    arguments = json.loads(intent)
    retained = arguments.pop(REVIEW_KEY, None)
    if retained is None:
        raise core.InvalidOperation(code="intake_review_invalid")
    try:
        current = _reference_state(session, tenant_id, arguments)
    except (core.InvalidOperation, core.NotFound) as error:
        raise core.InvalidOperation(code="intake_review_stale") from error
    if canonical_json(retained) != canonical_json(current):
        raise core.InvalidOperation(code="intake_review_stale")
