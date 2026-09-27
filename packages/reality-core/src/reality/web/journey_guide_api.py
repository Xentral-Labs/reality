"""Anonymous, read-only HTTP adapter for the Business Journey Guide."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from reality.services.business_journeys import (
    JourneyProposalError,
    answer_internal_question,
    answer_payload,
    answer_public_question,
    create_proposal,
    journey_catalog,
    journey_rewrite_provider,
    list_proposals,
    moderate_proposal,
    set_vote,
)
from reality.web.api import DatabaseSession
from reality.web.auth import CurrentUser, PlatformAdmin

router = APIRouter(prefix="/api/journey-guide", tags=["business-journey-guide"])
proposal_router = APIRouter(prefix="/api/journey-proposals", tags=["journey-proposals"])
account_router = APIRouter(
    prefix="/api/auth/journey-proposals", tags=["journey-proposals"]
)
internal_router = APIRouter(
    prefix="/api/accounts/me/journey-guide", tags=["business-journey-guide"]
)
admin_router = APIRouter(
    prefix="/api/auth/admin/journey-proposals", tags=["journey-proposals"]
)

_WINDOW_SECONDS = 60
_REQUESTS_PER_WINDOW = 20
_requests: defaultdict[str, deque[float]] = defaultdict(deque)
_requests_lock = Lock()


class PublicTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class PublicQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=2, max_length=1000)
    locale: str = Field(default="en", pattern=r"^(en|de|nl|es)$")
    history: list[PublicTurn] = Field(default_factory=list, max_length=6)


class InternalQuestion(PublicQuestion):
    pass


class ProposalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)
    business_question: str = Field(min_length=3, max_length=1000)
    expected_outcome: str = Field(min_length=3, max_length=2000)
    process_area: str = Field(min_length=3, max_length=32)
    business_context: str = Field(default="", max_length=1000)
    confirmed: StrictBool = False


class VoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed: StrictBool = False


class ModerationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        pattern=r"^(proposed|under_review|planned|in_progress|available|declined|out_of_scope)$"
    )
    public_rationale: str = Field(min_length=3, max_length=2000)
    available_journey_id: str | None = Field(default=None, pattern=r"^[A-R]\d{2}$")
    confirmed: StrictBool = False


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _admit(request: Request) -> None:
    now = time.monotonic()
    cutoff = now - _WINDOW_SECONDS
    key = _client_key(request)
    with _requests_lock:
        seen = _requests[key]
        while seen and seen[0] < cutoff:
            seen.popleft()
        if len(seen) >= _REQUESTS_PER_WINDOW:
            raise HTTPException(
                status_code=429, detail="Please wait before asking again."
            )
        seen.append(now)


@router.get("")
def public_catalog() -> dict[str, object]:
    return journey_catalog().public_payload()


@router.post("/questions")
def public_question(payload: PublicQuestion, request: Request) -> dict[str, object]:
    _admit(request)
    answer = answer_public_question(
        journey_catalog(),
        payload.question,
        locale=payload.locale,
        history=tuple(turn.model_dump() for turn in payload.history),
        provider=journey_rewrite_provider(),
    )
    return answer_payload(answer)


@internal_router.post("/questions")
def internal_question(payload: InternalQuestion, _: PlatformAdmin) -> dict[str, object]:
    return answer_internal_question(
        journey_catalog(),
        payload.question,
        locale=payload.locale,
        history=tuple(turn.model_dump() for turn in payload.history),
        provider=journey_rewrite_provider(),
    )


@proposal_router.get("")
def public_proposals(session: DatabaseSession) -> list[dict[str, object]]:
    return list_proposals(session)


@account_router.get("")
def account_proposals(
    user: CurrentUser, session: DatabaseSession
) -> list[dict[str, object]]:
    return list_proposals(session, account_id=user.id)


@account_router.post("")
def submit_proposal(
    payload: ProposalInput, user: CurrentUser, session: DatabaseSession
) -> dict[str, object]:
    try:
        return create_proposal(
            session,
            user.id,
            title=payload.title,
            business_question=payload.business_question,
            expected_outcome=payload.expected_outcome,
            process_area=payload.process_area,
            business_context=payload.business_context,
            confirmed=payload.confirmed,
        )
    except JourneyProposalError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@account_router.post("/{proposal_id}/vote")
def vote_for_proposal(
    proposal_id: str,
    payload: VoteInput,
    user: CurrentUser,
    session: DatabaseSession,
) -> dict[str, object]:
    if not payload.confirmed:
        return {"requires_confirmation": True, "proposal_id": proposal_id}
    try:
        return set_vote(session, user.id, proposal_id, active=True)
    except JourneyProposalError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@account_router.delete("/{proposal_id}/vote")
def withdraw_proposal_vote(
    proposal_id: str,
    payload: VoteInput,
    user: CurrentUser,
    session: DatabaseSession,
) -> dict[str, object]:
    if not payload.confirmed:
        return {"requires_confirmation": True, "proposal_id": proposal_id}
    try:
        return set_vote(session, user.id, proposal_id, active=False)
    except JourneyProposalError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@admin_router.post("/{proposal_id}/moderate")
def moderate_journey_proposal(
    proposal_id: str,
    payload: ModerationInput,
    admin: PlatformAdmin,
    session: DatabaseSession,
) -> dict[str, object]:
    if not payload.confirmed:
        return {
            "requires_confirmation": True,
            "proposal_id": proposal_id,
            "status": payload.status,
        }
    try:
        return moderate_proposal(
            session,
            admin.id,
            proposal_id,
            status=payload.status,
            public_rationale=payload.public_rationale,
            available_journey_id=payload.available_journey_id,
        )
    except JourneyProposalError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
