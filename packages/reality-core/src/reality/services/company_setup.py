"""One owner-scoped creation contract for ordinary companies and private sandboxes."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from reality.db.company_setup import OrdinaryCompanyCreation
from reality.db.core import (
    AccessApplication,
    AppUser,
    PlaygroundRun,
    Tenant,
    TenantMembership,
    now,
    uid,
)
from reality.services.core import Conflict, InvalidOperation, NotFound, create_tenant
from reality.services.tenant_policy import (
    PlaygroundOperationDenied,
    require_playground_account,
    require_playground_run,
)

PRESETS = {
    "empty": "company-empty",
    "international_demo": "international-demo",
    "execution": "atlas-execution",
}


def fingerprint(
    name: str, environment: str, content: str, live_simulation: bool = False
) -> str:
    return hashlib.sha256(
        json.dumps(
            [name, environment, content] + ([True] if live_simulation else []),
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def options(session: Session, actor_id: str) -> dict:
    user = require_playground_account(session, actor_id)
    application = session.scalar(
        select(AccessApplication).where(AccessApplication.user_id == actor_id)
    )
    return {
        "actor_id": actor_id,
        "suggested_name": application.company_name if application else "",
        "environments": (["business"] if user.status == "active" else [])
        + ["sandbox"],
        "practice_enabled": True,
        "pending": user.status != "active",
    }


def _result(
    session: Session, actor_id: str, tenant_id: str, run: PlaygroundRun | None = None
) -> dict:
    user = require_playground_account(session, actor_id)
    tenant = session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    membership = session.scalar(
        select(TenantMembership.id).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == actor_id,
            TenantMembership.role == "owner",
            TenantMembership.status == "active",
        )
    )
    if not membership or tenant is None:
        raise NotFound("Company setup not found.")
    if run:
        require_playground_run(session, run.id, actor_id)
    elif user.status != "active":
        raise NotFound("Company setup not found.")
    live_pending = bool(
        run
        and run.initialization_progress.get("creation_intent", {}).get(
            "live_simulation"
        )
        and not run.initialization_progress.get("live_setup_complete")
    )
    ready = (
        tenant.archived_at is None
        and (run is None or run.status == "active")
        and not live_pending
    )
    return {
        "tenant_id": tenant_id,
        "name": tenant.name,
        "run_id": run.id if run else None,
        "status": "ready"
        if ready
        else (
            "initialization_failed"
            if live_pending and run.status == "active"
            else (run.status if run else "archived")
        ),
        "environment": "sandbox" if run else "business",
        "error_code": "live_setup_incomplete"
        if live_pending
        else (run.initialization_error_code if run else None),
        "destination": (
            (
                f"/playground/runs/{run.id}"
                if user.status != "active" and run
                else f"/app?tenant={tenant_id}"
            )
            if ready
            else None
        ),
        "profile": run.initialization_progress.get("profile")
        if ready and run
        else None,
    }


def read_request(session: Session, actor_id: str, request_key: str) -> dict:
    require_playground_account(session, actor_id)
    receipt = session.scalar(
        select(OrdinaryCompanyCreation).where(
            OrdinaryCompanyCreation.actor_id == actor_id,
            OrdinaryCompanyCreation.request_key == request_key,
        )
    )
    if receipt:
        return _result(session, actor_id, receipt.tenant_id)
    run = session.scalar(
        select(PlaygroundRun).where(
            PlaygroundRun.owner_user_id == actor_id,
            PlaygroundRun.client_request_key == request_key,
        )
    )
    if run and run.preset_key in PRESETS.values():
        return _result(session, actor_id, run.tenant_id, run)
    raise NotFound("Company setup not found.")


def create_company(
    session: Session,
    actor_id: str,
    request_key: str,
    name: str,
    environment: str,
    content: str,
    *,
    confirmed: bool = False,
    live_simulation: bool = False,
    _initialize_inline: bool = False,
) -> dict:
    if type(live_simulation) is not bool or (
        live_simulation
        and (content != "international_demo" or environment != "sandbox")
    ):
        raise InvalidOperation(
            "Live simulation requires an international demo Sandbox."
        )
    if confirmed is not True:
        raise InvalidOperation("Confirm company creation first.")
    name = name.strip()
    if not name or len(name) > 120:
        raise InvalidOperation("Company name must contain 1 to 120 characters.")
    if not request_key or request_key != request_key.strip() or len(request_key) > 128:
        raise InvalidOperation("A request key of 1 to 128 characters is required.")
    if (
        environment not in {"business", "sandbox"}
        or content not in PRESETS
        or (environment == "business" and content != "empty")
    ):
        raise InvalidOperation("Choose an empty company or a demo Sandbox.")
    session.scalar(select(AppUser.id).where(AppUser.id == actor_id).with_for_update())
    user = require_playground_account(session, actor_id)
    digest = fingerprint(name, environment, content, live_simulation)
    receipt = session.scalar(
        select(OrdinaryCompanyCreation).where(
            OrdinaryCompanyCreation.actor_id == actor_id,
            OrdinaryCompanyCreation.request_key == request_key,
        )
    )
    run = session.scalar(
        select(PlaygroundRun).where(
            PlaygroundRun.owner_user_id == actor_id,
            PlaygroundRun.client_request_key == request_key,
        )
    )
    if receipt:
        if digest != receipt.request_fingerprint:
            raise Conflict("Request key belongs to different company choices.")
        return _result(session, actor_id, receipt.tenant_id)
    if run:
        if (
            run.initialization_progress.get("creation_intent", {}).get("fingerprint")
            != digest
        ):
            raise Conflict("Request key belongs to different company choices.")
        if run.status in {"initializing", "initialization_failed"}:
            # A repeated request replays the queued initialization, never a second one.
            # A failed initialization, a company whose profile is small enough to seed
            # in the request and an explicit retry are all recovered here instead.
            if (
                not _initialize_inline
                and run.status == "initializing"
                and run.preset_key == PRESETS["international_demo"]
                and _queue_initialization(session, run, actor_id)
            ):
                return _result(session, actor_id, run.tenant_id, run)
            run = initialize_profile(session, run.id, actor_id)
        _finish_live_setup(session, run, actor_id)
        return _result(session, actor_id, run.tenant_id, run)
    if environment == "business":
        if user.status != "active":
            raise PlaygroundOperationDenied(
                "Production admission is required for an ordinary company."
            )
        tenant = create_tenant(session, name, _commit=False)
        session.add(
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=actor_id,
                role="owner",
                status="active",
            )
        )
        session.add(
            OrdinaryCompanyCreation(
                id=uid("ccr"),
                tenant_id=tenant.id,
                actor_id=actor_id,
                request_key=request_key,
                request_fingerprint=digest,
            )
        )
        session.commit()
        return _result(session, actor_id, tenant.id)
    from reality.services.playground import start_run

    # The international profile is committed first and seeded by the worker, so the
    # request no longer carries thousands of statements (feature 199). An empty company
    # and the small execution fixture stay immediate.
    deferred = content == "international_demo" and not _initialize_inline
    run = start_run(
        session,
        actor_id,
        request_key,
        preset_key=PRESETS[content],
        preset_version=1,
        sandbox_kind="practice",
        company_name=name,
        confirmed=True,
        live_simulation=live_simulation,
        initialize=not deferred,
    )
    if deferred:
        if _queue_initialization(session, run, actor_id):
            return _result(session, actor_id, run.tenant_id, run)
        run = initialize_profile(session, run.id, actor_id)
    _finish_live_setup(session, run, actor_id)
    return _result(session, actor_id, run.tenant_id, run)


def _queue_initialization(session: Session, run: PlaygroundRun, actor_id: str) -> bool:
    """Enqueue this run's initialization once; report whether the worker owns it."""
    from reality.services import scheduled_jobs as jobs

    try:
        jobs.create_manual_run(
            session,
            run.tenant_id,
            actor_id,
            jobs.SETUP_JOB_TYPE,
            {"run_id": run.id},
            request_id=f"setup-initialize:{run.id}",
        )
    except jobs.JobError:
        # A queue that refuses the run must not cost the person their company; the
        # request initializes it itself, as it did before this feature.
        session.rollback()
        return False
    session.commit()
    return True


def _finish_live_setup(
    session: Session, run: PlaygroundRun, actor_id: str, *, _commit: bool = True
) -> None:
    from reality.services import demo_data
    from reality.services.playground import _locked_owner

    _locked_owner(session, actor_id)
    run = require_playground_run(session, run.id, actor_id)
    progress = run.initialization_progress
    if (
        run.status != "active"
        or not progress.get("creation_intent", {}).get("live_simulation")
        or progress.get("live_setup_complete")
    ):
        return
    try:
        with session.begin_nested():
            proposed = demo_data.preview(session, run.tenant_id, actor_id)
            connection = demo_data.connect(
                session,
                run.tenant_id,
                actor_id,
                f"setup-connect:{run.id}",
                proposed["fingerprint"],
                confirmed=True,
                _commit=False,
            )
            demo_data.control(
                session,
                run.tenant_id,
                actor_id,
                "start",
                connection["revision"],
                f"setup-start:{run.id}",
                rate=60,
                confirmed=True,
                _commit=False,
            )
            run.initialization_progress = {**progress, "live_setup_complete": True}
            session.flush()
        if _commit:
            session.commit()
    except Exception:  # noqa: BLE001 - retain baseline and safe explicit retry after atomic rollback
        # The nested block already rolled its own writes back. A caller that owns the
        # transaction keeps it; the receipt then reports the incomplete live setup.
        if _commit:
            session.rollback()


def initialize_profile(
    session: Session, run_id: str, actor_id: str, *, _commit: bool = True
) -> PlaygroundRun:
    from reality.services.playground import _locked_owner

    _locked_owner(session, actor_id)
    run = require_playground_run(session, run_id, actor_id)
    if run.status in {"active", "archived"}:
        return run
    if run.preset_version != 1 or run.preset_key not in PRESETS.values():
        raise Conflict("Unsupported company profile version.")
    tenant = session.scalar(select(Tenant).where(Tenant.id == run.tenant_id))
    if tenant.archived_at:
        raise InvalidOperation("Archived company setup cannot be retried.")
    content = next(k for k, v in PRESETS.items() if v == run.preset_key)
    initial = run.initialization_progress or {
        "creation_intent": {
            "name": tenant.name,
            "environment": "sandbox",
            "content": content,
            "fingerprint": fingerprint(tenant.name, "sandbox", content),
        },
        "anchor": datetime.combine(now().date(), datetime.min.time(), UTC).isoformat(),
    }
    if set(initial) - {"creation_intent", "anchor"}:
        raise Conflict("Incomplete profile requires review.")
    run.status = "initializing"
    run.initialization_progress = initial
    session.flush()
    try:
        with session.begin_nested():
            references = {"parties": {}, "items": {}, "locations": {}}
            if content != "empty":
                from reality.services.demo_profile import seed_profile
                from reality.services.tenant_policy import _profile_scope

                with _profile_scope(session, run.id, actor_id):
                    references = seed_profile(
                        session,
                        run,
                        datetime.fromisoformat(initial["anchor"]),
                        execution=content == "execution",
                    )
            run.initialization_progress = {
                **initial,
                **references,
                "profile": {"key": content, "version": 1},
            }
            if len(json.dumps(run.initialization_progress).encode()) > 64000:
                raise InvalidOperation("Profile manifest is too large.")
            run.status, run.ready_at, run.initialization_error_code = (
                "active",
                now(),
                None,
            )
            session.flush()
    except Exception:  # noqa: BLE001 - retain safe setup identity after atomic rollback
        run.initialization_progress = initial
        run.status, run.ready_at, run.initialization_error_code = (
            "initialization_failed",
            None,
            "seed_failed",
        )
    if _commit:
        session.commit()
    return run


def profile(session: Session, actor_id: str, request_key: str) -> dict:
    result = read_request(session, actor_id, request_key)
    if result["status"] != "ready" or not result["run_id"]:
        raise InvalidOperation("A ready Sandbox profile is required.")
    run = require_playground_run(session, result["run_id"], actor_id)
    return {"tenant_id": run.tenant_id, **run.initialization_progress}


def retry_request(
    session: Session, actor_id: str, request_key: str, *, confirmed: bool = False
) -> dict:
    result = read_request(session, actor_id, request_key)
    if not confirmed:
        raise InvalidOperation("Confirm setup retry first.")
    if result["status"] == "ready":
        return result
    if (
        result["status"] not in {"initializing", "initialization_failed"}
        or not result["run_id"]
    ):
        raise Conflict("Company setup cannot be retried in its current state.")
    run = require_playground_run(session, result["run_id"], actor_id)
    intent = run.initialization_progress["creation_intent"]
    return create_company(
        session,
        actor_id,
        request_key,
        intent["name"],
        intent["environment"],
        intent["content"],
        confirmed=True,
        live_simulation=intent.get("live_simulation", False),
        # An explicit retry completes the company in the request, so a person is never
        # left waiting for a worker that is not running (feature 199).
        _initialize_inline=True,
    )


def create_execution(
    session: Session,
    actor_id: str,
    original_request_key: str,
    request_key: str,
    name: str,
    *,
    confirmed: bool = False,
) -> dict:
    baseline = profile(session, actor_id, original_request_key)
    if baseline["profile"]["key"] != "international_demo":
        raise InvalidOperation("A ready international baseline is required.")
    return create_company(
        session,
        actor_id,
        request_key,
        name,
        "sandbox",
        "execution",
        confirmed=confirmed,
    )


def _company_presentation(
    session: Session, actor_id: str, tenant_ids: list[str]
) -> dict:
    """Read labels only for requested companies with current account membership."""
    from reality.db.demo_data import DemoDataConnection

    if not tenant_ids:
        return {}
    rows = session.execute(
        select(
            Tenant.id,
            Tenant.purpose,
            PlaygroundRun.preset_key,
            DemoDataConnection.state,
        )
        .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
        .outerjoin(PlaygroundRun, PlaygroundRun.tenant_id == Tenant.id)
        .outerjoin(DemoDataConnection, DemoDataConnection.tenant_id == Tenant.id)
        .where(
            Tenant.id.in_(tenant_ids),
            TenantMembership.user_id == actor_id,
            TenantMembership.status == "active",
            Tenant.purpose == "playground",
            PlaygroundRun.owner_user_id == actor_id,
        )
    )
    return {
        tenant: {
            "company_kind": "company"
            if purpose == "business"
            else "demo"
            if preset in {"international-demo", "atlas-execution"}
            else "sandbox",
            "demo_data_state": state,
        }
        for tenant, purpose, preset, state in rows
    }
