"""Canonical case vocabulary shared by CLI, Chat and external MCP."""

from typing import Any

from sqlalchemy.orm import Session

from reality.services import operational_cases as cases
from reality.services.case_action_guards import human_principal


def read_list(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Return the canonical bounded case list for this company.

    BUSINESS RULE tools.operational_cases.read_list.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    # reality-rule: tools.operational_cases.read_list.result
    return cases.list_cases(session, tenant_id, **arguments)


def read_case(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Return the shared current explanation for one same-company case.

    BUSINESS RULE tools.operational_cases.read_case.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    # reality-rule: tools.operational_cases.read_case.result
    return cases.explain(session, tenant_id, arguments["case_id"])


def read_object(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Return the existing case identities of a typed same-company business record.

    BUSINESS RULE tools.operational_cases.read_object.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    # reality-rule: tools.operational_cases.read_object.result
    return {
        "case_ids": cases.object_cases(
            session, tenant_id, arguments["record_type"], arguments["record_id"]
        )
    }


def read_handback(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Return the canonical exact current handback review without executing a control.

    BUSINESS RULE tools.operational_cases.read_handback.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    # reality-rule: tools.operational_cases.read_handback.result
    return cases.handback_preview(session, tenant_id, arguments["case_id"])


def takeover(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Transfer responsibility to the authenticated active member, increasing the control revision so older automated starts are revoked.

    BUSINESS RULE tools.operational_cases.takeover.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    # reality-rule: tools.operational_cases.takeover.result
    return cases.takeover(
        session,
        tenant_id,
        principal=human_principal(session, tenant_id),
        confirmed=True,
        _commit=False,
        **arguments,
    )


def handback(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Return responsibility after exact current human review, refusing unresolved sources or executing actions and preserving old action invalidation.

    BUSINESS RULE tools.operational_cases.handback.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    # reality-rule: tools.operational_cases.handback.result
    return cases.handback(
        session,
        tenant_id,
        principal=human_principal(session, tenant_id),
        confirmed=True,
        _commit=False,
        **arguments,
    )


def adopt(session: Session, tenant_id: str, arguments: dict[str, Any]):
    """
    BUSINESS PURPOSE:
    Enable coordination for newly accepted goals and an explicit bounded selection of existing outstanding goals under a real owner decision.

    BUSINESS RULE tools.operational_cases.adopt.result:
    Return only the canonical same-company result after the function's source, control and authority checks; never perform provider transport.
    """
    # reality-rule: tools.operational_cases.adopt.result
    return cases.adopt(
        session,
        tenant_id,
        principal=human_principal(session, tenant_id),
        confirmed=True,
        _commit=False,
        **arguments,
    )


def register():
    from reality.tools.application import TOOLS, Tool

    for name, description, mutating, handler in (
        (
            "operational_case_list",
            "List adopted fulfillment and announced-return cases with current responsibility.",
            False,
            read_list,
        ),
        (
            "operational_case_explain",
            "Explain one case, its work, related cases, obsolete plans and unsettled executions.",
            False,
            read_case,
        ),
        (
            "operational_case_object",
            "Discover case IDs for an existing order, commitment, return or proposal without creating work.",
            False,
            read_object,
        ),
        (
            "operational_case_handback_preview",
            "Review the exact current case state before returning responsibility to automation.",
            False,
            read_handback,
        ),
        (
            "operational_case_takeover",
            "Manually take over a case and stop further automated starts; existing executions remain visible.",
            True,
            takeover,
        ),
        (
            "operational_case_handback",
            "Return a manually owned case after exact current review and execution reconciliation.",
            True,
            handback,
        ),
        (
            "operational_case_adopt",
            "Enable new-work case coordination and explicitly select historical outstanding goals.",
            True,
            adopt,
        ),
    ):
        TOOLS[name] = Tool(name, description, mutating, handler)
