"""Fixed manifest decisions and bounded database-only settlement (spec 355)."""

import hashlib
import json
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError
from sqlalchemy import cast, select, tuple_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
    ImportJob,
    MCPAccessToken,
    SourceRecord,
    SourceStream,
)
from reality.domain.intake import (
    CONTINUATION_UNITS,
    IntakeManifest,
    canonical_json,
    content_digest,
)
from reality.services import core
from reality.services.business_locks import lock_delivery_state
from reality.services.delivery_actions import require_delivery_principal
from reality.services.finance.accounts import lock_finance
from reality.services.intake import (
    _FINANCIAL_PROFILES,
    apply_prepared_intake,
    review_intake,
)
from reality.services.memberships import Principal, require_owner

BATCH_TYPE = "tool:intake_batch_apply"


@dataclass(frozen=True)
class _ChildContext:
    session: Session
    transaction: Any
    tenant_id: str
    proposal_id: str
    authorization: dict


_child_context: ContextVar[_ChildContext | None] = ContextVar(
    "intake_batch_child", default=None
)


@contextmanager
def _child_scope(session, tenant_id, proposal_id, authorization):
    token = _child_context.set(
        _ChildContext(
            session, session.get_transaction(), tenant_id, proposal_id, authorization
        )
    )
    try:
        yield
    finally:
        _child_context.reset(token)


def _current_child_authorization(session, tenant_id, proposal_id):
    context = _child_context.get()
    if context is None:
        return None
    if (
        context.session is not session
        or context.transaction is not session.get_transaction()
        or context.tenant_id != tenant_id
        or context.proposal_id != proposal_id
    ):
        raise core.InvalidOperation(code="intake_approval_required")
    return context.authorization


def _batch(session, tenant_id, batch_id, *, lock=False):
    query = select(ChangeProposal).where(
        ChangeProposal.tenant_id == tenant_id,
        ChangeProposal.id == batch_id,
        ChangeProposal.type == BATCH_TYPE,
    )
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    row = session.scalar(query)
    if row is None:
        raise core.NotFound(code="proposal_not_found")
    return row


def _manifest(batch):
    held = json.loads(batch.input)
    manifest = IntakeManifest.model_validate(held["manifest"])
    if (
        content_digest(manifest.model_dump(mode="json", exclude_none=True))
        != held["digest"]
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    if len({entry.proposal_id for entry in manifest.entries}) != len(manifest.entries):
        raise core.InvalidOperation(code="intake_review_invalid")
    return held, manifest


def _validate_file_selection(session, tenant_id, manifest):
    selection = manifest.file_selection
    if selection is None:
        return
    source = core._tenant_record_read(
        session, SourceRecord, tenant_id, selection.source_record_id
    )
    if (
        source.source_type != "item_csv_raw"
        or source.source_artifact_id != selection.artifact_id
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    numbers = [row.row for row in selection.excluded_rows]
    for entry in manifest.entries:
        review = review_intake(session, tenant_id, entry.proposal_id)
        mapping = review["plan"]["mapping"]
        if (
            review["digest"] != entry.digest
            or review["plan"]["profile"] != "item_csv.v1"
            or mapping.get("parent_source_id") != source.id
            or mapping.get("mapping") != selection.mapping
            or mapping.get("default_unit") != selection.default_unit
        ):
            raise core.InvalidOperation(code="intake_review_invalid")
        numbers.extend(mapping["row_numbers"])
    if sorted(numbers) != list(range(2, selection.original_rows + 2)):
        raise core.InvalidOperation(code="intake_review_invalid")


def prepare_batch(
    session,
    tenant_id,
    entries,
    *,
    request_id,
    _file_selection=None,
    _artifact_selection=None,
    _commit=True,
):
    """
    BUSINESS PURPOSE:
    Retain an exact selected group without accepting source meaning.

    BUSINESS RULE intake_batch.prepare_batch:
    Freeze selected IDs and digests; exclude future arrivals and preserve request identity.
    """
    # reality-rule: intake_batch.prepare_batch
    lock_delivery_state(session, tenant_id)
    if not isinstance(request_id, str) or not 1 <= len(request_id) <= 128:
        raise core.InvalidOperation(code="intake_review_invalid")
    try:
        manifest = IntakeManifest(
            entries=entries,
            revision=1,
            file_selection=_file_selection,
            artifact_selection=_artifact_selection,
        )
    except ValidationError as error:
        raise core.InvalidOperation(code="intake_review_invalid") from error
    if len({entry.proposal_id for entry in manifest.entries}) != len(manifest.entries):
        raise core.InvalidOperation(code="intake_review_invalid")
    held = {
        "request_id": request_id,
        "manifest": manifest.model_dump(mode="json", exclude_none=True),
        "digest": content_digest(manifest.model_dump(mode="json", exclude_none=True)),
    }
    old = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.type == BATCH_TYPE,
            cast(ChangeProposal.input, JSONB)["request_id"].astext == request_id,
        )
    )
    if old is not None:
        if json.loads(old.input) != held:
            raise core.InvalidOperation(code="intake_review_stale")
        return old
    for entry in manifest.entries:
        current = review_intake(session, tenant_id, entry.proposal_id)
        if current["digest"] != entry.digest or current["status"] not in {
            "proposed",
            "executed",
        }:
            raise core.InvalidOperation(code="intake_review_stale")
    _validate_file_selection(session, tenant_id, manifest)
    from reality.services.artifact_batches import _validate_selection

    _validate_selection(session, tenant_id, manifest)
    batch = ChangeProposal(
        id=core.uid("act"),
        tenant_id=tenant_id,
        type=BATCH_TYPE,
        status="proposed",
        input=canonical_json(held),
        output=canonical_json({"next_index": 0, "results": []}),
    )
    session.add(batch)
    session.flush()
    if _commit:
        session.commit()
    return batch


def _reviewer(session, tenant_id, authorization):
    if "agent_review" in authorization:
        from reality.services.intake_review import _current_mandate

        retained = authorization["agent_review"]
        return _current_mandate(
            session,
            tenant_id,
            retained["mandate_id"],
            retained["token_id"],
            retained["revision"],
            required_tool="intake_agent_batch_review_and_queue",
        )[2]
    principal = Principal(authorization["reviewer_user_id"])
    require_delivery_principal(session, tenant_id, principal)
    token_id = authorization.get("token_id")
    if token_id:
        token = session.scalar(
            select(MCPAccessToken)
            .where(
                MCPAccessToken.tenant_id == tenant_id,
                MCPAccessToken.id == token_id,
            )
            .execution_options(populate_existing=True)
        )
        if (
            token is None
            or token.revoked_at is not None
            or token.created_by_user_id != principal.user_id
            or not (
                {"*", "proposal_approve_and_execute"}
                & set(json.loads(token.allowed_tools))
            )
        ):
            raise core.InvalidOperation(code="intake_approval_required")
    return principal


def approve_batch(
    session,
    tenant_id,
    batch_id,
    digest,
    *,
    confirmed,
    principal,
    settling_token_id=None,
    settling_channel=None,
    _commit=True,
):
    """
    BUSINESS PURPOSE:
    Bind one actual reviewer to exact independently retained decisions.

    BUSINESS RULE intake_batch.approve_batch:
    Require exact manifest confirmation and current relevant authority before queuing.
    """
    from reality.tools.application import _record_decision

    # reality-rule: intake_batch.approve_batch
    lock_delivery_state(session, tenant_id)
    lock_finance(session, tenant_id)
    require_delivery_principal(session, tenant_id, principal)
    if principal is None or settling_channel == "chat":
        raise core.InvalidOperation(code="intake_approval_required")
    batch = _batch(session, tenant_id, batch_id, lock=True)
    held, manifest = _manifest(batch)
    if not confirmed or digest != held["digest"]:
        raise core.InvalidOperation(code="review_confirmation_required")
    if batch.status in {"executing", "executed"}:
        _reviewer(session, tenant_id, json.loads(batch.output)["authorization"])
        return batch
    if batch.status != "proposed":
        raise core.InvalidOperation(code="proposal_no_longer_available")
    for entry in manifest.entries:
        review = review_intake(session, tenant_id, entry.proposal_id)
        if review["digest"] != entry.digest:
            raise core.InvalidOperation(code="intake_review_stale")
        if (
            review["plan"]["finance_revision"] is not None
            or review["plan"]["profile"] in _FINANCIAL_PROFILES
        ):
            require_owner(session, tenant_id, principal)
    _validate_file_selection(session, tenant_id, manifest)
    from reality.services.artifact_batches import _validate_selection

    _validate_selection(session, tenant_id, manifest)
    authorization = {
        "batch_id": batch.id,
        "manifest_revision": manifest.revision,
        "manifest_digest": digest,
        "reviewer_user_id": principal.user_id,
        "token_id": settling_token_id,
        "channel": settling_channel,
        "authorized_at": core.now().isoformat(),
    }
    _reviewer(session, tenant_id, authorization)
    _record_decision(batch, principal, settling_token_id, settling_channel)
    batch.status = "executing"
    batch.output = canonical_json(
        {
            "authorization": authorization,
            "authorization_digest": content_digest(authorization),
            "next_index": 0,
            "continuation_id": core.uid("cont"),
            "results": [],
            "stopped": False,
        }
    )
    session.flush()
    from reality.services.scheduled_jobs import enqueue_intake_batch_run

    enqueue_intake_batch_run(session, tenant_id, batch.id)
    if _commit:
        session.commit()
    return batch


def _lock_children(session, tenant_id, entries):
    ids = sorted(entry.proposal_id for entry in entries)
    proposals = list(
        session.scalars(
            select(ChangeProposal)
            .where(ChangeProposal.tenant_id == tenant_id, ChangeProposal.id.in_(ids))
            .order_by(ChangeProposal.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    )
    reviews = []
    sources = {}
    for proposal in proposals:
        try:
            review = review_intake(session, tenant_id, proposal.id)
            source = core._tenant_record_read(
                session, SourceRecord, tenant_id, review["plan"]["source_record_id"]
            )
        except core.RealityError:
            continue  # Its own child savepoint retains the precise refusal later.
        reviews.append(review)
        sources[source.id] = source

    def lock_key(source):
        identity = f"{tenant_id}\x1f{source.source_system}\x1f{source.source_type}\x1f{source.external_id}"
        return int.from_bytes(
            hashlib.sha256(identity.encode()).digest()[:8], "big", signed=True
        )

    for source in sorted(sources.values(), key=lock_key):
        core._lock_source_identity(
            session,
            tenant_id,
            source.source_system,
            source.source_type,
            source.external_id,
        )
    identities = sorted(
        {
            (row.source_system, row.source_type, row.external_id)
            for row in sources.values()
        }
    )
    list(
        session.scalars(
            select(SourceStream)
            .where(
                SourceStream.tenant_id == tenant_id,
                tuple_(
                    SourceStream.source_system,
                    SourceStream.source_type,
                    SourceStream.external_id,
                ).in_(identities),
            )
            .order_by(
                SourceStream.source_system,
                SourceStream.source_type,
                SourceStream.external_id,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    )
    job_ids = sorted({review["plan"]["import_job_id"] for review in reviews})
    list(
        session.scalars(
            select(ImportJob)
            .where(ImportJob.tenant_id == tenant_id, ImportJob.id.in_(job_ids))
            .order_by(ImportJob.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    )


def settle_chunk(session, tenant_id, batch_id, *, continuation_id, _commit=False):
    """
    BUSINESS PURPOSE:
    Settle bounded independent source decisions with the original reviewer's authority.

    BUSINESS RULE intake_batch.settle_chunk:
    Isolate known no-effect refusals; abort all provisional child effects on infrastructure failure.
    """
    # reality-rule: intake_batch.settle_chunk
    lock_delivery_state(session, tenant_id)
    lock_finance(session, tenant_id)
    batch = _batch(session, tenant_id, batch_id, lock=True)
    held, manifest = _manifest(batch)
    progress = json.loads(batch.output)
    if batch.status == "executed":
        return {"settled": 0, "terminal": True}
    if (
        batch.status != "executing"
        or progress.get("continuation_id") != continuation_id
    ):
        raise core.InvalidOperation(code="intake_review_stale")
    authorization = progress["authorization"]
    if (
        content_digest(authorization) != progress["authorization_digest"]
        or authorization["manifest_digest"] != held["digest"]
        or authorization["batch_id"] != batch.id
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    start = progress["next_index"]
    entries = manifest.entries[start : start + CONTINUATION_UNITS]
    _lock_children(session, tenant_id, entries)
    with session.begin_nested():
        for entry in entries:
            try:
                with session.begin_nested():
                    if progress["stopped"]:
                        disposition = "stopped"
                    else:
                        if "agent_review" in authorization:
                            from reality.services.intake_review import (
                                _settle_agent_batch_child,
                            )

                            with _child_scope(
                                session, tenant_id, entry.proposal_id, authorization
                            ):
                                disposition = _settle_agent_batch_child(
                                    session, tenant_id, entry.proposal_id, authorization
                                )
                        else:
                            principal = _reviewer(session, tenant_id, authorization)
                            previous = core._tenant_record_read(
                                session, ChangeProposal, tenant_id, entry.proposal_id
                            ).status
                            with _child_scope(
                                session, tenant_id, entry.proposal_id, authorization
                            ):
                                apply_prepared_intake(
                                    session,
                                    tenant_id,
                                    entry.proposal_id,
                                    entry.digest,
                                    confirmed=True,
                                    principal=principal,
                                    settling_token_id=authorization.get("token_id"),
                                    settling_channel=authorization.get("channel"),
                                    _commit=False,
                                )
                            disposition = (
                                "replayed" if previous == "executed" else "applied"
                            )
            except core.RealityError as error:
                from reality.services.intake import _retain_apply_failure

                _retain_apply_failure(session, tenant_id, entry.proposal_id, error)
                disposition = "review_required"
                progress["results"].append(
                    {
                        "proposal_id": entry.proposal_id,
                        "disposition": disposition,
                        "reason_code": error.code
                        if error.coded
                        else "invalid_operation",
                    }
                )
            else:
                progress["results"].append(
                    {"proposal_id": entry.proposal_id, "disposition": disposition}
                )
        progress["next_index"] = start + len(entries)
        progress["continuation_id"] = core.uid("cont")
        if progress["next_index"] == len(manifest.entries):
            batch.status = "executed"
            from reality.services.artifact_batches import _complete_artifact_job

            _complete_artifact_job(session, tenant_id, manifest, progress)
        batch.output = canonical_json(progress)
        session.flush()
    if _commit:
        session.commit()
    return {"settled": len(entries), "terminal": batch.status == "executed"}


def batch_status(session, tenant_id, batch_id, *, cursor=0, limit=100):
    """
    BUSINESS PURPOSE:
    Explain retained outcomes of selected source decisions.

    BUSINESS RULE intake_batch.batch_status:
    Read bounded dispositions without interpreting queue success as business acceptance.
    """
    # reality-rule: intake_batch.batch_status
    batch = _batch(session, tenant_id, batch_id)
    _, manifest = _manifest(batch)
    if (
        type(cursor) is not int
        or cursor < 0
        or type(limit) is not int
        or not 1 <= limit <= 100
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    progress = json.loads(batch.output)
    results = [
        dict(row) for row in progress.get("results", [])[cursor : cursor + limit]
    ]
    executed_ids = [
        row["proposal_id"]
        for row in results
        if row["disposition"] in {"applied", "replayed"}
    ]
    receipts = {
        row.id: json.loads(row.output)
        for row in session.scalars(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == tenant_id,
                ChangeProposal.id.in_(executed_ids),
                ChangeProposal.status == "executed",
            )
        )
    }
    for result in results:
        if result["proposal_id"] in receipts:
            result["receipt"] = receipts[result["proposal_id"]]
    return {
        "batch_id": batch.id,
        "status": batch.status,
        "total": len(manifest.entries),
        "settled": progress.get("next_index", 0),
        "results": results,
        "has_more": cursor + limit < len(progress.get("results", [])),
    }


def stop_batch(session, tenant_id, batch_id, *, principal, _commit=True):
    """
    BUSINESS PURPOSE:
    Stop further acceptance of a selected source batch while retaining results.

    BUSINESS RULE intake_batch.stop_batch:
    The original current reviewer stops future units without reversing committed children.
    """
    # reality-rule: intake_batch.stop_batch
    lock_delivery_state(session, tenant_id)
    require_delivery_principal(session, tenant_id, principal)
    batch = _batch(session, tenant_id, batch_id, lock=True)
    if batch.status == "executing":
        progress = json.loads(batch.output)
        if (
            principal is None
            or progress["authorization"]["reviewer_user_id"] != principal.user_id
        ):
            raise core.InvalidOperation(code="intake_approval_required")
        progress["stopped"] = True
        batch.output = canonical_json(progress)
        session.flush()
    if _commit:
        session.commit()
    return batch


def review_batch(session, tenant_id, batch_id, *, cursor=0, limit=100):
    """
    BUSINESS PURPOSE:
    Expose an immutable source selection for exact review.

    BUSINESS RULE intake_batch.review_batch:
    Read bounded summaries without refreshing children or including future arrivals.
    """
    # reality-rule: intake_batch.review_batch
    batch = _batch(session, tenant_id, batch_id)
    held, manifest = _manifest(batch)
    if (
        type(cursor) is not int
        or cursor < 0
        or type(limit) is not int
        or not 1 <= limit <= 100
    ):
        raise core.InvalidOperation(code="intake_review_invalid")
    entries = []
    for entry in manifest.entries[cursor : cursor + limit]:
        review = review_intake(session, tenant_id, entry.proposal_id)
        entries.append(
            {
                "proposal_id": entry.proposal_id,
                "digest": entry.digest,
                "status": review["status"],
                "source_record_id": review["plan"]["source_record_id"],
                "import_job_id": review["plan"]["import_job_id"],
                "review_reference": {
                    "tool": "intake_review",
                    "proposal_id": entry.proposal_id,
                },
                "effect_operations": [
                    effect["operation"] for effect in review["plan"]["effects"]
                ],
                "profile": review["plan"]["profile"],
                "row_count": review["plan"]["row_count"],
                "issues": review["plan"]["issues"],
            }
        )
    return {
        "batch_id": batch.id,
        "status": batch.status,
        "digest": held["digest"],
        "manifest_revision": manifest.revision,
        "total": len(manifest.entries),
        "file_selection": manifest.file_selection.model_dump(
            mode="json", exclude_none=True
        )
        if manifest.file_selection
        else None,
        "entries": entries,
        "has_more": cursor + limit < len(manifest.entries),
    }


def reject_batch(
    session,
    tenant_id,
    batch_id,
    *,
    principal,
    token_id=None,
    channel=None,
    _commit=True,
):
    """
    BUSINESS PURPOSE:
    Decline a pending source selection without applying any member.

    BUSINESS RULE intake_batch.reject_batch:
    Require current reviewer authority and reject only a still-proposed manifest.
    """
    from reality.tools.application import _record_decision

    # reality-rule: intake_batch.reject_batch
    lock_delivery_state(session, tenant_id)
    require_delivery_principal(session, tenant_id, principal)
    batch = _batch(session, tenant_id, batch_id, lock=True)
    if batch.status == "rejected":
        return batch
    if batch.status != "proposed":
        raise core.InvalidOperation(code="proposal_no_longer_available")
    _record_decision(batch, principal, token_id, channel)
    batch.status = "rejected"
    session.flush()
    if _commit:
        session.commit()
    return batch
