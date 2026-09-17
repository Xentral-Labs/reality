"""Seal private configuration in otherwise tenant-visible proposal records."""

import json

from cryptography.fernet import InvalidToken

from reality.security.secrets import _master_key
from reality.services.analytics.errors import AnalyticsError
from reality.services.analytics.reports import (
    change_graph_report,
    change_report,
    kind,
    owned,
    require_author,
)


def prepare(session, tenant_id, principal, arguments, report_kind="definition"):
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
        raise AnalyticsError("The private report proposal cannot be read.") from error
    if payload["tenant_id"] != tenant_id or payload["owner_user_id"] != owner:
        raise AnalyticsError(
            "Only the original author may confirm this private report change.",
            "user_context_required",
        )
    return payload["arguments"], payload.get("kind", "definition")


def execute_change(session, tenant_id, principal, arguments):
    sealed, report_kind = reveal(session, tenant_id, principal, arguments)
    save = change_graph_report if report_kind == "graph" else change_report
    save(session, tenant_id, principal, sealed)
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
        "kind": report_kind,
    }
