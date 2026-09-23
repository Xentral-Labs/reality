"""Seal private configuration in otherwise tenant-visible proposal records."""

import json

from cryptography.fernet import InvalidToken

from reality.security.secrets import _master_key
from reality.services.analytics.errors import AnalyticsError
from reality.services.analytics.reports import (
    change_graph_report,
    kind,
    owned,
    require_author,
)


def prepare(session, tenant_id, principal, arguments, report_kind="graph"):
    owner = require_author(session, tenant_id, principal)
    contract = kind(report_kind)
    request = contract.change_model.model_validate(arguments)
    payload = getattr(request, contract.payload_field)
    if payload:
        contract.check(payload)
    if request.report_id:
        report = owned(session, tenant_id, principal, request.report_id)
        if report.revision != request.expected_revision:
            raise AnalyticsError(
                "The report changed. Reload it before proposing a change.",
                "revision_conflict",
            )
    sealed = {
        "tenant_id": tenant_id,
        "owner_user_id": owner,
        "kind": contract.key,
        "arguments": request.model_dump(mode="json"),
    }
    token = _master_key().encrypt(json.dumps(sealed).encode()).decode()
    return {"private_report_change": token}, {
        "effect": "Change a private analytics report.",
        "requires_human_confirmation": True,
        "private": True,
    }


def reveal(session, tenant_id, principal, arguments):
    owner = require_author(session, tenant_id, principal)
    try:
        payload = json.loads(
            _master_key().decrypt(arguments["private_report_change"].encode())
        )
    except (InvalidToken, ValueError, KeyError, TypeError) as error:
        # Sealed with a key this installation no longer has. Retrying cannot
        # help, and saying "not found" would send the reader looking for a
        # proposal that is sitting right in front of them.
        raise AnalyticsError(
            "This proposal was sealed with a key this installation no longer "
            "has, so its contents cannot be shown. It can only be rejected.",
            "sealed_unreadable",
        ) from error
    if payload["tenant_id"] != tenant_id or payload["owner_user_id"] != owner:
        raise AnalyticsError(
            "Only the original author may confirm this private report change.",
            "user_context_required",
        )
    return payload["arguments"], payload.get("kind", "definition")


def execute_change(session, tenant_id, principal, arguments):
    sealed, report_kind = reveal(session, tenant_id, principal, arguments)
    if report_kind != "graph":
        # A proposal sealed by the retired generation names a kind nothing can
        # save any more. Refusing it is the only honest outcome; saving it as a
        # graph question would give it a meaning it never had.
        raise AnalyticsError(
            "This proposal was prepared by a retired analytics generation and "
            "cannot be confirmed.",
            "unknown_report_kind",
        )
    change_graph_report(session, tenant_id, principal, sealed)
    return {"private_report_changed": True}


def preview(session, tenant_id, principal, proposal_id):
    from sqlalchemy import select

    from reality.db.core import ChangeProposal
    from reality.services.core import NotFound

    proposal = session.scalar(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == tenant_id,
            ChangeProposal.id == proposal_id,
            ChangeProposal.type.in_(
                ("tool:analytics.reports.change", "tool:graph.reports.change")
            ),
        )
    )
    if proposal is None:
        raise NotFound("Report proposal not found.")
    arguments, report_kind = reveal(
        session, tenant_id, principal, json.loads(proposal.input)
    )
    report = (
        owned(session, tenant_id, principal, arguments["report_id"], deleted=True)
        if arguments.get("report_id")
        else None
    )
    return {
        "proposal_id": proposal.id,
        "status": proposal.status,
        "operation": arguments["operation"],
        "name": arguments.get("name") or (report.name if report else None),
        "definition": arguments.get("definition")
        or arguments.get("question")
        or (report.definition if report else None),
        "expected_revision": arguments.get("expected_revision"),
        "report_id": _written(session, tenant_id, principal, arguments, report),
        "kind": report_kind,
    }


def _written(session, tenant_id, principal, arguments, report):
    """The report this proposal concerns, once there is one to open.

    A create carries no report ID, because the report does not exist while the
    proposal waits. Confirming writes one, and the row records the retry key the
    change was made under — so the link is already there and needs no new field.
    Offering to open a report that was since deleted is a dead end, so a deleted
    row names nothing.
    """
    from sqlalchemy import select

    from reality.db.analytics import AnalyticsReport

    if arguments["operation"] in {"create", "duplicate"}:
        # A duplicate names its source, but what confirming produced is the copy,
        # and the copy is what the reader asked for.
        owner = require_author(session, tenant_id, principal)
        return session.scalar(
            select(AnalyticsReport.id).where(
                AnalyticsReport.tenant_id == tenant_id,
                AnalyticsReport.owner_user_id == owner,
                AnalyticsReport.create_request_id == str(arguments["request_id"]),
                AnalyticsReport.deleted_at.is_(None),
            )
        )
    if report is None:
        return None
    return None if report.deleted_at is not None else report.id


# --- a requested analysis ------------------------------------------------------
#
# Sealed for the same reason a private report change is: a proposal record is
# visible to the company, and a question somebody asked is theirs. What the
# company can see is that an analysis was requested, not what was asked.


def prepare_request(session, tenant_id, principal, arguments):
    """Check the question now, and seal it for whoever confirms.

    The question is planned but not executed. Planning is what turns an unknown
    name or an edge that fans out into a refusal, and that refusal belongs here,
    at proposal time, where the asker is still looking. Executing it is the
    expensive part and the whole reason this feature exists, so it waits for the
    confirmation.
    """
    from reality.domain.traversal import Traversal
    from reality.services.analytics.cypher_surface import parse
    from reality.services.analytics.traversal import plan

    owner = require_author(session, tenant_id, principal)
    question = arguments.get("question")
    asked = (
        Traversal.model_validate(question)
        if question
        else parse(arguments.get("path") or "", arguments.get("parameters") or {})
    )
    plan(asked)
    sealed = {
        "tenant_id": tenant_id,
        "owner_user_id": owner,
        "question": asked.model_dump(mode="json", by_alias=True, exclude_none=True),
        "request_id": arguments["request_id"],
    }
    token = _master_key().encrypt(json.dumps(sealed).encode()).decode()
    return {"requested_analysis": token}, {
        "effect": (
            "Ask an analysis question. It is answered now if the company is small "
            "enough, and otherwise recorded and answered by the worker."
        ),
        "requires_human_confirmation": True,
        "private": True,
    }


def _revealed_request(session, tenant_id, principal, arguments):
    owner = require_author(session, tenant_id, principal)
    try:
        payload = json.loads(
            _master_key().decrypt(arguments["requested_analysis"].encode())
        )
    except (InvalidToken, ValueError, KeyError, TypeError) as error:
        raise AnalyticsError(
            "This proposal was sealed with a key this installation no longer "
            "has, so its contents cannot be shown. It can only be rejected.",
            "sealed_unreadable",
        ) from error
    if payload["tenant_id"] != tenant_id or payload["owner_user_id"] != owner:
        raise AnalyticsError(
            "Only the person who asked may confirm this analysis request.",
            "user_context_required",
        )
    return payload


def execute_request(session, tenant_id, principal, arguments):
    """Ask it. An answer that arrives now is an answer; otherwise it is accepted."""
    from reality.domain.traversal import Traversal
    from reality.services.analytics.requests import ask

    payload = _revealed_request(session, tenant_id, principal, arguments)
    outcome = ask(
        session,
        tenant_id,
        question=Traversal.model_validate(payload["question"]),
        user_id=principal.user_id if principal else None,
        request_id=payload["request_id"],
    )
    if outcome["state"] == "answered":
        result = outcome["answer"]
        return {
            "state": "answered",
            "rows": list(result.rows),
            "row_count": len(result.rows),
            "model_version": result.model_version,
        }
    return {"state": "accepted", "request": outcome["request"]}
