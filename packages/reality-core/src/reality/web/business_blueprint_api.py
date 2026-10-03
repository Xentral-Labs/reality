"""Public generic code evidence, independent of companies and business sessions."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from reality.services.business_blueprint_source import SourceUnavailable
from reality.services.business_blueprints import discover, explain, source_for

router = APIRouter(prefix="/api/business-logic", tags=["Business logic"])
Kind = Literal["command", "tool", "action", "view", "projection", "exception"]


from reality.domain.business_blueprints import DiscoveryInput as DiscoveryQuery


class DetailQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: str = Field(default="en", max_length=5)
    brief: bool = False
    interpret: bool = True


class Admission:
    def __init__(self):
        self.lock = threading.Lock()
        self.active = threading.BoundedSemaphore(2)
        self.clients: OrderedDict[str, list[float]] = OrderedDict()

    @contextmanager
    def read(self, address: str):
        now = time.monotonic()
        with self.lock:
            times = [t for t in self.clients.get(address, []) if now - t < 60]
            if len(times) >= 30:
                raise HTTPException(
                    429,
                    "Live explanation request limit reached.",
                    headers={"Retry-After": "60"},
                )
            times.append(now)
            self.clients[address] = times
            self.clients.move_to_end(address)
            while len(self.clients) > 2048:
                self.clients.popitem(last=False)
        if not self.active.acquire(blocking=False):
            raise HTTPException(
                429,
                "Live analysis is busy. Retry shortly.",
                headers={"Retry-After": "1"},
            )
        try:
            yield
        finally:
            self.active.release()


admission = Admission()


def _bounded(value: dict) -> dict:
    import json

    if len(json.dumps(value).encode()) > 2 * 1024 * 1024:
        raise HTTPException(
            503,
            "Live explanation exceeds the response boundary; inspect a narrower entry.",
        )
    return JSONResponse(value, headers={"Cache-Control": "no-store"})


@router.get("/entries")
def entries(request: Request, query: Annotated[DiscoveryQuery, Query()]):
    with admission.read(request.client.host if request.client else "unknown"):
        return _bounded(discover(**query.model_dump()))


@router.get("/entries/{kind}/{key}")
def detail(
    request: Request, kind: Kind, key: str, query: Annotated[DetailQuery, Query()]
):
    with admission.read(request.client.host if request.client else "unknown"):
        try:
            result = explain(
                kind,
                key,
                language=query.language,
                brief=query.brief,
                interpret=query.interpret,
            )
            return _bounded(result.model_dump(mode="json"))
        except ValueError:
            raise HTTPException(404, "Business entry not found.") from None


@router.get("/entries/{kind}/{key}/source/{evidence_id}")
def source(request: Request, kind: Kind, key: str, evidence_id: str):
    if request.query_params:
        raise HTTPException(
            422, "Source reads accept only registered evidence identities."
        )
    with admission.read(request.client.host if request.client else "unknown"):
        try:
            return _bounded(source_for(kind, key, evidence_id))
        except SourceUnavailable:
            raise HTTPException(503, "Running source is unavailable.") from None
        except ValueError:
            raise HTTPException(404, "Source evidence not found.") from None
