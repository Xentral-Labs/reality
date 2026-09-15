"""Code-owned job definitions. Registration never authorizes an invocation."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session


class JobError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class JobContext:
    tenant_id: str
    actor_id: str | None
    run_id: str
    scheduled_for: datetime | None
    deadline: datetime


class RecordReference(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    record_type: str = Field(min_length=1, max_length=80, pattern=r"^[a-z_]+$")
    id: str = Field(min_length=1, max_length=128)


class JobResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    counts: dict[str, int] = Field(default_factory=dict)
    references: list[RecordReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def bounded(self) -> Self:
        if len(self.model_dump_json().encode()) > 3500:
            raise JobError("result_too_large")
        return self


def require_company_owner(
    session: Session, context: JobContext, config: BaseModel | None = None
) -> None:
    # Local imports keep registry/help usable without a database configuration.
    from sqlalchemy import select

    from reality.db.core import AppUser, Tenant
    from reality.services.core import RealityError
    from reality.services.memberships import Principal, require_owner

    try:
        require_owner(session, context.tenant_id, Principal(context.actor_id))
    except RealityError as error:
        raise JobError("not_authorized") from error
    tenant = session.scalar(select(Tenant).where(Tenant.id == context.tenant_id))
    user = session.scalar(select(AppUser).where(AppUser.id == context.actor_id))
    if (
        tenant is None
        or tenant.archived_at is not None
        or user is None
        or user.status != "active"
        or user.email_verified_at is None
    ):
        raise JobError("not_authorized")


@dataclass(frozen=True)
class JobDefinition:
    name: str
    version: int
    config_model: type[BaseModel]
    authorize: Callable[[Session, JobContext, BaseModel], None]
    handler: Callable[[Session, JobContext, BaseModel], JobResult]

    def validate(self, arguments: dict) -> BaseModel:
        if (
            not isinstance(arguments, dict)
            or len(json.dumps(arguments).encode()) > 15000
        ):
            raise JobError("invalid_configuration")
        try:
            return self.config_model.model_validate(arguments)
        except ValueError as error:
            raise JobError("invalid_configuration") from error


_REGISTRY: dict[str, JobDefinition] = {}
_INITIALIZED = False


def register(definition: JobDefinition) -> None:
    if definition.name in _REGISTRY:
        raise JobError("duplicate_job_type")
    if (
        definition.config_model.model_config.get("extra") != "forbid"
        or definition.version < 1
    ):
        raise JobError("invalid_job_definition")
    _REGISTRY[definition.name] = definition


def definitions() -> dict[str, JobDefinition]:
    global _INITIALIZED
    if not _INITIALIZED:
        from reality.jobs.handlers.company_setup import INITIALIZE
        from reality.jobs.handlers.demo_data import DEMO, SETTLE
        from reality.jobs.handlers.invitations import CLEANUP
        from reality.jobs.handlers.projections import REFRESH

        register(REFRESH)
        register(CLEANUP)
        register(DEMO)
        register(SETTLE)
        register(INITIALIZE)
        _INITIALIZED = True
    return dict(_REGISTRY)


def get_definition(name: str) -> JobDefinition:
    try:
        return definitions()[name]
    except KeyError as error:
        raise JobError("unknown_job_type") from error
