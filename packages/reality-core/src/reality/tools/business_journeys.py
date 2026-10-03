"""Application-tool adapters for the release-reviewed Business Journey Guide."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from sqlalchemy.orm import Session

from reality.db.core import AppUser
from reality.mcp.principal import current_mcp_principal
from reality.services.business_journeys import (
    create_proposal,
    set_vote,
)
from reality.services.product_advisor import (
    add_internal_journey_evidence,
    answer_product_question,
    product_advisor_provider,
)

_CURRENT_GUIDE_ACTOR: ContextVar[str | None] = ContextVar(
    "current_business_journey_actor", default=None
)


@contextmanager
def guide_actor_context(account_id: str | None) -> Iterator[None]:
    """Propagate server-verified Chat identity without exposing it as tool input."""
    token = _CURRENT_GUIDE_ACTOR.set(account_id)
    try:
        yield
    finally:
        _CURRENT_GUIDE_ACTOR.reset(token)


def business_journey_guide(
    session: Session, _tenant_id: str, arguments: dict[str, Any]
) -> dict[str, object]:
    """
    Answer a capability question without reading tenant business records.

    BUSINESS PURPOSE:
    Answer a capability question without reading tenant business records.

    BUSINESS RULE tools.business_journeys.business_journey_guide.result:
    Return answer, as prepared by the preceding checks and service calls.
    """
    principal = current_mcp_principal()
    account_id = _CURRENT_GUIDE_ACTOR.get() or (
        principal.user_id if principal else None
    )
    account = session.get(AppUser, account_id) if account_id else None
    question = str(arguments.get("question", ""))
    locale = str(arguments.get("locale", "en"))
    answer = answer_product_question(
        question,
        surface_language=locale,
        provider=product_advisor_provider(),
    )
    if account and account.is_platform_admin:
        return add_internal_journey_evidence(answer)
    # reality-rule: tools.business_journeys.business_journey_guide.result
    return answer


def business_journey_proposal_create(
    session: Session, _tenant_id: str, arguments: dict[str, Any]
) -> dict[str, object]:
    """
    Create one confirmed account proposal through the shared service.

    BUSINESS PURPOSE:
    Create one confirmed account proposal through the shared service.

    BUSINESS RULE tools.business_journeys.business_journey_proposal_create.refusal-5:
    IF no confirming account identity was supplied:
        Refuse: Journey proposal creation requires a confirming account.

    BUSINESS RULE tools.business_journeys.business_journey_proposal_create.step-7:
    Pass the stated inputs to the shared create proposal service. Its own source describes validation and record changes.
    """
    account_id = str(arguments.pop("_confirming_user_id", ""))
    # reality-rule: tools.business_journeys.business_journey_proposal_create.refusal-5
    if not account_id:
        raise ValueError("Journey proposal creation requires a confirming account.")
    # reality-rule: tools.business_journeys.business_journey_proposal_create.step-7
    return create_proposal(
        session,
        account_id,
        title=str(arguments.get("title", "")),
        business_question=str(arguments.get("business_question", "")),
        expected_outcome=str(arguments.get("expected_outcome", "")),
        process_area=str(arguments.get("process_area", "")),
        business_context=str(arguments.get("business_context", "")),
        confirmed=True,
    )


def business_journey_vote_set(
    session: Session, _tenant_id: str, arguments: dict[str, Any]
) -> dict[str, object]:
    """
    Set or withdraw one confirmed account vote through the shared service.

    BUSINESS PURPOSE:
    Set or withdraw one confirmed account vote through the shared service.

    BUSINESS RULE tools.business_journeys.business_journey_vote_set.refusal-5:
    IF no confirming account identity was supplied:
        Refuse: Journey proposal voting requires a confirming account.

    BUSINESS RULE tools.business_journeys.business_journey_vote_set.result:
    Return the result from set vote; inspect that called function for its calculation and eligibility rules.
    """
    account_id = str(arguments.pop("_confirming_user_id", ""))
    # reality-rule: tools.business_journeys.business_journey_vote_set.refusal-5
    if not account_id:
        raise ValueError("Journey proposal voting requires a confirming account.")
    # reality-rule: tools.business_journeys.business_journey_vote_set.result
    return set_vote(
        session,
        account_id,
        str(arguments.get("proposal_id", "")),
        active=bool(arguments.get("active", True)),
    )
