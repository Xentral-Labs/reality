"""Account-scoped company setup; all creation and recovery live in services."""

import re
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from reality.services import company_setup, free_playground
from reality.web.api import DatabaseSession
from reality.web.playground import Actor, _respond

router = APIRouter(prefix="/api/company-setup", tags=["company-setup"])


def is_account_setup_path(path: str, method: str) -> bool:
    if (method, path) in {
        ("GET", "/api/company-setup/options"),
        ("GET", "/api/company-setup/playground"),
        ("POST", "/api/company-setup/playground"),
        ("POST", "/api/company-setup"),
    }:
        return True
    return (
        bool(
            re.fullmatch(
                r"/api/company-setup/requests/[^/]+"
                + (r"/(retry|execution)" if method == "POST" else r"(/profile)?"),
                path,
            )
        )
        if method in {"GET", "POST"}
        else False
    )


class CreateCompany(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_key: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=120)
    environment: Literal["business", "sandbox"]
    content: Literal["empty", "international_demo"] = "empty"
    live_simulation: StrictBool = False
    confirmed: StrictBool = False


class Confirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: StrictBool = False


class ExecutionRequest(Confirmation):
    request_key: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=120)


@router.get("/options")
def options(actor: Actor, session: DatabaseSession):
    return _respond(lambda: company_setup.options(session, actor))


@router.post("", status_code=201)
def create(body: CreateCompany, actor: Actor, session: DatabaseSession):
    return _respond(
        lambda: company_setup.create_company(session, actor, **body.model_dump())
    )


@router.get("/requests/{request_key}")
def read(request_key: str, actor: Actor, session: DatabaseSession):
    return _respond(lambda: company_setup.read_request(session, actor, request_key))


@router.post("/requests/{request_key}/retry")
def retry(request_key: str, body: Confirmation, actor: Actor, session: DatabaseSession):
    return _respond(
        lambda: company_setup.retry_request(
            session, actor, request_key, confirmed=body.confirmed
        )
    )


@router.get("/requests/{request_key}/profile")
def profile(request_key: str, actor: Actor, session: DatabaseSession):
    return _respond(lambda: company_setup.profile(session, actor, request_key))


@router.post("/requests/{request_key}/execution", status_code=201)
def execution(
    request_key: str, body: ExecutionRequest, actor: Actor, session: DatabaseSession
):
    return _respond(
        lambda: company_setup.create_execution(
            session, actor, request_key, **body.model_dump()
        )
    )


@router.get("/playground")
def playground_status(actor: Actor, session: DatabaseSession):
    return _respond(lambda: free_playground.entry_status(session, actor))


@router.post("/playground", status_code=201)
def enter_playground(body: Confirmation, actor: Actor, session: DatabaseSession):
    return _respond(
        lambda: free_playground.enter(session, actor, confirmed=body.confirmed)
    )
