"""Storyline mode (spec 182): play a story package in a practice company.

A storyline run is a practice Playground run whose chapters are Playground steps.
Chapters run through the ordinary proposal path that the app, MCP and the Copilot
use in practice companies; this module adds no second write path. It owns:

- starting and resuming a run and seeding its company from the package,
- the derived chapter state (done, current, upcoming),
- preparing, confirming and rejecting a chapter under the run's mutation lock,
- branch choices and restarts,
- the reads the protocol needs (state, chapter, trace, delta, tool reference).
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

from reality.db.core import (
    ChangeProposal,
    PlaygroundRun,
    PlaygroundStep,
    StorylinePackageRecord,
    StorylineTraceEntry,
    Tenant,
    TenantMembership,
    now,
    uid,
)
from reality.services.core import (
    Conflict,
    InvalidOperation,
    NotFound,
    create_item,
    create_location,
    create_party,
    create_payment_term,
)
from reality.services.memberships import Principal
from reality.services.tenant_policy import (
    PlaygroundOperationDenied,
    require_playground_account,
    require_playground_run,
    storyline_seed_scope,
)
from reality.storyline import recorder
from reality.storyline.package import (
    Chapter,
    StorylinePackage,
    ValidationResult,
    builtin_packages,
    validate_package,
)
from reality.storyline.references import (
    ReferenceError,
    ResolutionContext,
    dig,
    is_reference,
    resolve_value,
    walk_strings,
)

logger = logging.getLogger(__name__)

PRESET_KEY = "storyline"
PRESET_VERSION = 1
PROGRESS_BYTE_BOUND = 64_000
READ_RESULT_BYTE_BOUND = 16_384


# ------------------------------------------------------------------ packages


def imported_packages(session: Session, user_id: str) -> list[StorylinePackageRecord]:
    return list(
        session.scalars(
            select(StorylinePackageRecord)
            .where(
                StorylinePackageRecord.owner_user_id == user_id,
                StorylinePackageRecord.replaced_at.is_(None),
            )
            .order_by(StorylinePackageRecord.imported_at)
        )
    )


def load_package(
    session: Session, user_id: str, key: str, version: int
) -> StorylinePackage:
    """A built-in package or one the account imported; anything else is not found."""
    for result in builtin_packages():
        if (
            result.ok
            and result.package.key == key
            and result.package.version == version
        ):
            return result.package
    row = session.scalar(
        select(StorylinePackageRecord).where(
            StorylinePackageRecord.owner_user_id == user_id,
            StorylinePackageRecord.key == key,
            StorylinePackageRecord.version == version,
            StorylinePackageRecord.replaced_at.is_(None),
        )
    )
    if row is None:
        raise NotFound("Storyline not found.")
    result: ValidationResult = validate_package(row.document)
    if not result.ok:
        raise InvalidOperation("The imported storyline no longer validates.")
    return result.package


def library(session: Session, user_id: str) -> dict[str, Any]:
    """Built-in and imported packages with the account's runs (FR-018)."""
    require_playground_account(session, user_id)
    runs = {
        run.storyline_key: run
        for run in session.scalars(
            select(PlaygroundRun).where(
                PlaygroundRun.owner_user_id == user_id,
                PlaygroundRun.storyline_key.is_not(None),
                PlaygroundRun.status == "active",
            )
        )
    }
    items = []
    for result in builtin_packages():
        if result.ok:
            items.append(_library_item(session, result.package, "builtin", None, runs))
    for row in imported_packages(session, user_id):
        result = validate_package(row.document)
        if result.ok:
            items.append(_library_item(session, result.package, "import", row, runs))
    return {"items": items, "enabled": True}


def _library_item(session, package, origin, row, runs) -> dict[str, Any]:
    run = runs.get(package.key)
    item = {
        "key": package.key,
        "version": package.version,
        "title": package.title.model_dump(exclude_none=True),
        "summary": package.summary.model_dump(exclude_none=True),
        "author": package.author.name if package.author else None,
        "chapters": len(package.chapters),
        "origin": origin,
        "imported_at": row.imported_at if row else None,
        "run": None,
    }
    if run is not None and run.storyline_version == package.version:
        progress = _progress(session, run, package)
        current = progress["current"]
        tenant = session.get(Tenant, run.tenant_id) if run.tenant_id else None
        item["run"] = {
            "run_id": run.id,
            "tenant_id": run.tenant_id,
            "status": run.status,
            "current_chapter": current,
            # Where the person is, for the library card: 1-based, None once finished.
            "position": (
                next(
                    (
                        index
                        for index, entry in enumerate(progress["path"], start=1)
                        if entry["key"] == current
                    ),
                    None,
                )
                if current
                else None
            ),
            "total": len(progress["path"]),
            "done": len(progress.get("done", ())),
            "company_name": tenant.name if tenant else None,
        }
    return item


# ------------------------------------------------------------- import / export


class ImportRefused(InvalidOperation):
    """A package that did not validate; carries every error at once (SC-008)."""

    def __init__(self, errors: list[dict[str, Any]]):
        super().__init__("The storyline package did not validate.")
        self.errors = errors


class BuiltinPackage(InvalidOperation):
    """Built-in packages are repository content; the library cannot remove them."""


def package_document(
    session: Session, user_id: str, key: str, version: int
) -> tuple[dict[str, Any], str, bytes | None]:
    """The stored document, its origin and, for built-ins, the file as shipped."""
    from reality.storyline.package import (
        FILE_SUFFIX,
        builtin_directory,
        builtin_documents,
    )

    for stem, document in builtin_documents().items():
        if document.get("key") == key and document.get("version") == version:
            path = builtin_directory() / f"{stem}{FILE_SUFFIX}"
            return document, "builtin", path.read_bytes() if path.is_file() else None
    row = session.scalar(
        select(StorylinePackageRecord).where(
            StorylinePackageRecord.owner_user_id == user_id,
            StorylinePackageRecord.key == key,
            StorylinePackageRecord.version == version,
            StorylinePackageRecord.replaced_at.is_(None),
        )
    )
    if row is None:
        raise NotFound("Storyline not found.")
    return row.document, "import", None


def export_package(
    session: Session, user_id: str, key: str, version: int, *, fmt: str = "yaml"
) -> tuple[bytes, str, str]:
    """The package as a file: built-ins verbatim, imports re-serialized (FR-018)."""
    import yaml

    require_playground_account(session, user_id)
    document, origin, raw = package_document(session, user_id, key, version)
    if fmt == "json":
        body = json.dumps(document, indent=2, ensure_ascii=False).encode()
        return body, "application/json", f"{key}.storyline.json"
    if origin == "builtin" and raw is not None:
        return raw, "application/yaml", f"{key}.storyline.yaml"
    body = yaml.safe_dump(document, sort_keys=False, allow_unicode=True).encode()
    return body, "application/yaml", f"{key}.storyline.yaml"


def export_draft(
    session: Session, user_id: str, run_id: str, *, fmt: str = "yaml"
) -> tuple[bytes, str, str]:
    """The run's confirmed commands as a storyline draft (FR-021)."""
    import yaml

    from reality.storyline.export import draft_document
    from reality.storyline.package import catalog_index

    require_playground_account(session, user_id)
    run = session.scalar(
        select(PlaygroundRun).where(
            PlaygroundRun.id == run_id,
            PlaygroundRun.owner_user_id == user_id,
            PlaygroundRun.storyline_key.is_not(None),
        )
    )
    if run is None:
        raise NotFound("Storyline run not found.")
    package = _package_of(session, run)
    document, _origin, _raw = package_document(
        session, user_id, run.storyline_key, run.storyline_version
    )
    rows = session.execute(
        select(StorylineTraceEntry, PlaygroundStep.lesson_step_key)
        .outerjoin(
            PlaygroundStep,
            (PlaygroundStep.id == StorylineTraceEntry.step_id)
            & (PlaygroundStep.tenant_id == StorylineTraceEntry.tenant_id),
        )
        .where(
            StorylineTraceEntry.tenant_id == run.tenant_id,
            StorylineTraceEntry.run_id == run.id,
            StorylineTraceEntry.kind == "confirm",
        )
        .order_by(StorylineTraceEntry.ordinal)
    ).all()
    draft = draft_document(
        document=document,
        package=package,
        progress=(run.initialization_progress or {}).get("storyline", {}),
        confirms=[
            {
                "name": entry.name,
                "input": entry.input,
                "result": entry.result,
                "chapter": chapter_key,
            }
            for entry, chapter_key in rows
        ],
        commands=catalog_index().commands,
    )
    stem = f"{package.key}-draft.storyline"
    if fmt == "json":
        body = json.dumps(draft, indent=2, ensure_ascii=False).encode()
        return body, "application/json", f"{stem}.json"
    body = yaml.safe_dump(draft, sort_keys=False, allow_unicode=True).encode()
    return body, "application/yaml", f"{stem}.yaml"


def import_package(
    session: Session,
    user_id: str,
    raw: bytes,
    *,
    filename: str = "",
    replace: bool = False,
) -> dict[str, Any]:
    """Validate first, store nothing on any error, replace only when asked (FR-018)."""
    from reality.storyline.package import (
        PackageTooLarge,
        PackageUnreadable,
        builtin_documents,
        checksum,
        parse_document,
        validate_package,
    )
    from reality.tools.application import MEMBERSHIP_MUTATION_TOOLS

    require_playground_account(session, user_id)
    try:
        document = parse_document(raw, filename=filename)
    except (PackageTooLarge, PackageUnreadable) as exc:
        raise ImportRefused(
            [{"path": "", "code": "unreadable", "detail": str(exc)}]
        ) from exc
    result = validate_package(document)
    if not result.ok:
        raise ImportRefused([asdict(issue) for issue in result.errors])
    package = result.package
    for builtin in builtin_documents().values():
        if (
            builtin.get("key") == package.key
            and builtin.get("version") == package.version
        ):
            raise Conflict(
                "A built-in storyline has this key and version; choose another version."
            )
    warnings = [asdict(issue) for issue in result.warnings]
    # Commands the ordinary authorization may refuse for this person are named now,
    # not discovered halfway through the story (US6-5).
    for position, chapter in enumerate(package.chapters):
        if chapter.command in MEMBERSHIP_MUTATION_TOOLS:
            warnings.append(
                {
                    "path": f"chapters[{position}].command",
                    "code": "command_requires_confirmation_you_may_lack",
                    "detail": chapter.command,
                }
            )
    existing = session.scalar(
        select(StorylinePackageRecord).where(
            StorylinePackageRecord.owner_user_id == user_id,
            StorylinePackageRecord.key == package.key,
            StorylinePackageRecord.version == package.version,
            StorylinePackageRecord.replaced_at.is_(None),
        )
    )
    if existing is not None:
        if not replace:
            raise Conflict("This storyline key and version is already in your library.")
        existing.replaced_at = now()
        session.flush()
    row = StorylinePackageRecord(
        id=uid("stp"),
        owner_user_id=user_id,
        key=package.key,
        version=package.version,
        title=package.title.pick("en")[:200],
        author=(package.author.name if package.author else None),
        checksum=checksum(document),
        document=document,
        validation={"warnings": warnings},
    )
    session.add(row)
    session.commit()
    return {
        "key": package.key,
        "version": package.version,
        "title": package.title.model_dump(exclude_none=True),
        "chapters": len(package.chapters),
        "warnings": warnings,
        "replaced": existing is not None,
    }


def delete_package(session: Session, user_id: str, key: str, version: int) -> None:
    from reality.storyline.package import builtin_documents

    require_playground_account(session, user_id)
    for builtin in builtin_documents().values():
        if builtin.get("key") == key and builtin.get("version") == version:
            raise BuiltinPackage(
                "Built-in storylines cannot be removed from the library."
            )
    row = session.scalar(
        select(StorylinePackageRecord).where(
            StorylinePackageRecord.owner_user_id == user_id,
            StorylinePackageRecord.key == key,
            StorylinePackageRecord.version == version,
            StorylinePackageRecord.replaced_at.is_(None),
        )
    )
    if row is None:
        raise NotFound("Storyline not found.")
    row.replaced_at = now()
    session.commit()


# ------------------------------------------------------------------- run start


def start(
    session: Session,
    user_id: str,
    *,
    key: str,
    version: int,
    request_key: str,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Start a run for a package or resume the account's active run of that key."""
    from reality.services.playground import _check_capacity, _locked_owner

    if confirmed is not True:
        raise PlaygroundOperationDenied("Confirm starting the storyline first.")
    if not request_key or request_key != request_key.strip() or len(request_key) > 128:
        raise InvalidOperation("A request key of 1 to 128 characters is required.")
    require_playground_account(session, user_id)
    _locked_owner(session, user_id)
    active = session.scalar(
        select(PlaygroundRun).where(
            PlaygroundRun.owner_user_id == user_id,
            PlaygroundRun.storyline_key == key,
            PlaygroundRun.status == "active",
        )
    )
    if active is not None and active.storyline_version != version:
        raise Conflict(
            "A run of another version of this storyline is active; restart it first."
        )
    package = load_package(session, user_id, key, version)
    if active is not None:
        return _run_view(session, active, package)
    existing = session.scalar(
        select(PlaygroundRun).where(
            PlaygroundRun.owner_user_id == user_id,
            PlaygroundRun.client_request_key == request_key,
        )
    )
    if existing is not None:
        if (existing.storyline_key, existing.storyline_version) != (key, version):
            raise Conflict("The request key belongs to a different run.")
        run = initialize(session, existing.id, user_id)
        return _run_view(session, run, package)
    _check_capacity(session, user_id)
    if session.scalar(
        select(PlaygroundRun.id).where(
            PlaygroundRun.owner_user_id == user_id,
            PlaygroundRun.status == "initializing",
        )
    ):
        raise Conflict("Resume the run that is still initializing first.")
    tenant = Tenant(
        id=uid("ten"), name=package.title.pick("en")[:120], purpose="playground"
    )
    session.add(tenant)
    session.flush()
    from reality.services.finance.accounts import _bootstrap_accounts

    _bootstrap_accounts(session, tenant.id)
    run = PlaygroundRun(
        id=uid("pgr"),
        tenant_id=tenant.id,
        owner_user_id=user_id,
        preset_key=PRESET_KEY,
        sandbox_kind="practice",
        preset_version=PRESET_VERSION,
        lesson_key=PRESET_KEY,
        lesson_version=PRESET_VERSION,
        client_request_key=request_key,
        status="initializing",
        storyline_key=key,
        storyline_version=version,
        storyline_state={},
    )
    session.add_all(
        [
            run,
            TenantMembership(
                id=uid("tmb"),
                tenant_id=tenant.id,
                user_id=user_id,
                role="owner",
                status="active",
            ),
        ]
    )
    session.commit()
    run = initialize(session, run.id, user_id)
    return _run_view(session, run, package)


def initialize(session: Session, run_id: str, user_id: str) -> PlaygroundRun:
    """Seed the company from the package inside one savepoint; fail as one unit."""
    from reality.services.playground import _locked_owner

    _locked_owner(session, user_id)
    run = require_playground_run(session, run_id, user_id)
    if run.status in {"active", "archived"}:
        return run
    tenant = session.get(Tenant, run.tenant_id)
    if tenant.archived_at is not None:
        raise PlaygroundOperationDenied("Archived storyline setup is unavailable.")
    package = load_package(
        session, run.owner_user_id, run.storyline_key, run.storyline_version
    )
    run.status = "initializing"
    run.initialization_error_code = None
    session.flush()
    started_at = now()
    failure: dict[str, Any] | None = None
    try:
        with session.begin_nested():
            seeded = _seed(session, run, user_id, package, started_at)
            progress = {
                "storyline": {
                    "key": package.key,
                    "version": package.version,
                    "start": started_at.isoformat(),
                    **seeded,
                }
            }
            if len(json.dumps(progress, default=str).encode()) > PROGRESS_BYTE_BOUND:
                raise InvalidOperation("Storyline seed references are too large.")
            run.initialization_progress = progress
            run.status, run.ready_at = "active", now()
            session.flush()
    except _SeedFailure as exc:
        failure = exc.detail
    except Exception as exc:  # noqa: BLE001 - a safe outcome after the atomic rollback
        failure = {"entry": None, "command": None, "detail": _sanitized(exc)}
    if failure is not None:
        run.status, run.ready_at = "initialization_failed", None
        run.initialization_error_code = "seed_failed"
        run.initialization_progress = {"storyline_error": failure}
    session.commit()
    recorder.clear_cache(run.tenant_id)
    if run.status == "active":
        _refresh_projections(session, run.tenant_id)
    return run


class _SeedFailure(Exception):
    def __init__(self, detail: dict[str, Any]):
        super().__init__(detail.get("detail", "seed failed"))
        self.detail = detail


def _sanitized(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {str(exc)[:300]}"


def _seed(
    session: Session,
    run: PlaygroundRun,
    user_id: str,
    package: StorylinePackage,
    started_at: datetime,
) -> dict[str, Any]:
    """Seed references and replay the history on a savepoint-joined session.

    Tool handlers commit; on a session that joins the connection's transaction with
    ``create_savepoint`` a commit only releases a savepoint, so the caller's
    ``begin_nested`` still undoes everything if one entry fails.
    """
    from sqlalchemy.orm import Session as OrmSession

    from reality.tools.application import TOOLS, _json_value

    tenant_id = run.tenant_id
    tenant_name = session.get(Tenant, tenant_id).name
    seed = package.seed
    refs: dict[str, dict[str, str]] = {
        "parties": {},
        "items": {},
        "locations": {},
        "terms": {},
    }
    inner = OrmSession(
        bind=session.connection(),
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    try:
        with storyline_seed_scope(inner, run.id, user_id):
            company = create_party(
                inner, tenant_id, tenant_name, "company", _commit=False
            )
            for name, term in seed.terms.items():
                create_payment_term(
                    inner,
                    tenant_id,
                    term.code,
                    term.name or term.code,
                    term.days,
                    discount_percent=term.discount_percent,
                    discount_days=term.discount_days,
                    _commit=False,
                )
                refs["terms"][name] = term.code.strip().upper()
            for name, party in seed.parties.items():
                term_code = ""
                if party.payment_term:
                    term_name = party.payment_term.removeprefix("$ref.terms.")
                    term_code = refs["terms"].get(term_name, "")
                refs["parties"][name] = create_party(
                    inner,
                    tenant_id,
                    party.name,
                    party.role,
                    payment_term_code=term_code,
                    _commit=False,
                ).id
            for name, location in seed.locations.items():
                refs["locations"][name] = create_location(
                    inner, tenant_id, location.name, _commit=False
                ).id
            default_location = next(iter(refs["locations"].values()), None)
            for name, item in seed.items.items():
                refs["items"][name] = create_item(
                    inner,
                    tenant_id,
                    item.sku,
                    item.name,
                    item.unit,
                    default_location_id=default_location,
                    _commit=False,
                ).id
            company_party_id = company.id
            inner.flush()
        context = ResolutionContext(
            start=started_at, refs=refs, company_party_id=company_party_id
        )
        for index, entry in enumerate(seed.history):
            try:
                arguments = resolve_value(entry.input, context)
                tool = TOOLS[entry.command]
                with storyline_seed_scope(inner, run.id, user_id):
                    output = _json_value(
                        tool.handler(inner, tenant_id, dict(arguments))
                    )
            except (
                ReferenceError,
                InvalidOperation,
                NotFound,
                Conflict,
                KeyError,
                PlaygroundOperationDenied,
            ) as exc:
                raise _SeedFailure(
                    {
                        "entry": index,
                        "command": entry.command,
                        "detail": _sanitized(exc),
                    }
                ) from exc
            if entry.as_:
                context.seed_outputs[entry.as_] = output
        inner.commit()
    finally:
        inner.close()
    return {
        "refs": refs,
        "company_party_id": company_party_id,
        "seed_outputs": context.seed_outputs,
    }


def _refresh_projections(session: Session, tenant_id: str) -> None:
    """Keep the practice company's stored views current (plan §5, analysis M7)."""
    from reality.services.projections import refresh_operational_projections

    try:
        refresh_operational_projections(session, tenant_id)
    except Exception:
        logger.exception(
            "Storyline projection refresh failed", extra={"tenant": tenant_id}
        )
        session.rollback()


# ----------------------------------------------------------------- run state


def _run_for_tenant(session: Session, user_id: str, tenant_id: str) -> PlaygroundRun:
    run = session.scalar(
        select(PlaygroundRun).where(
            PlaygroundRun.tenant_id == tenant_id,
            PlaygroundRun.owner_user_id == user_id,
            PlaygroundRun.storyline_key.is_not(None),
        )
    )
    if run is None:
        raise NotFound("This company has no storyline run.")
    return run


def _package_of(session: Session, run: PlaygroundRun) -> StorylinePackage:
    return load_package(
        session, run.owner_user_id, run.storyline_key, run.storyline_version
    )


def _steps(
    session: Session, run: PlaygroundRun
) -> list[tuple[PlaygroundStep, ChangeProposal | None]]:
    rows = list(
        session.execute(
            select(PlaygroundStep, ChangeProposal)
            .outerjoin(
                ChangeProposal,
                (ChangeProposal.id == PlaygroundStep.proposal_id)
                & (ChangeProposal.tenant_id == PlaygroundStep.tenant_id),
            )
            .where(
                PlaygroundStep.tenant_id == run.tenant_id,
                PlaygroundStep.run_id == run.id,
                PlaygroundStep.lesson_step_key.is_not(None),
            )
            .order_by(PlaygroundStep.sequence)
        )
    )
    return [(step, proposal) for step, proposal in rows]


def _step_status(step: PlaygroundStep, proposal: ChangeProposal | None) -> str:
    before = step.before_observation or {}
    if before.get("refused"):
        return "refused"
    if before.get("kind") == "read":
        return "done" if step.receipt_observation is not None else "pending"
    if proposal is None:
        return "pending"
    if proposal.status == "executed":
        return "done"
    if proposal.status == "rejected":
        return "rejected"
    return "pending"


def _progress(
    session: Session, run: PlaygroundRun, package: StorylinePackage
) -> dict[str, Any]:
    """Derive done, current and upcoming from the steps (plan §2, analysis H6)."""
    steps = _steps(session, run)
    latest: dict[str, tuple[PlaygroundStep, ChangeProposal | None]] = {}
    done: set[str] = set()
    for step, proposal in steps:
        latest[step.lesson_step_key] = (step, proposal)
        if _step_status(step, proposal) in {"done", "refused"}:
            done.add(step.lesson_step_key)
    branches = (run.storyline_state or {}).get("branches", {})
    path: list[dict[str, Any]] = []
    current: str | None = None
    key: str | None = package.chapters[0].key if package.chapters else None
    seen: set[str] = set()
    while key and key not in seen:
        seen.add(key)
        chapter = package.chapter(key)
        if chapter is None:
            break
        step, proposal = latest.get(key, (None, None))
        if key in done:
            status = "done"
        elif current is None:
            status = "current"
            current = key
        else:
            status = "upcoming"
        entry = {
            "key": key,
            "status": status,
            "kind": chapter.kind,
            "step_id": step.id if step else None,
            "step_status": _step_status(step, proposal) if step else None,
            "refused": (step.before_observation or {}).get("refused") if step else None,
            "marker": (
                {"sequence": step.marker_sequence, "at": step.marker_at}
                if step is not None and step.marker_sequence is not None
                else None
            ),
        }
        path.append(entry)
        if chapter.branches:
            chosen = branches.get(key)
            if chosen and any(branch.key == chosen for branch in chapter.branches):
                key = next(
                    branch.next for branch in chapter.branches if branch.key == chosen
                )
            else:
                key = package.default_next(key)
        else:
            key = chapter.next
    return {
        "path": path,
        "current": current,
        "done": done,
        "branches": branches,
        "latest": latest,
    }


def _run_view(
    session: Session, run: PlaygroundRun, package: StorylinePackage | None = None
) -> dict[str, Any]:
    view = {
        "run_id": run.id,
        "tenant_id": run.tenant_id if run.status in {"active", "archived"} else None,
        "status": run.status,
        "key": run.storyline_key,
        "version": run.storyline_version,
        "error": (run.initialization_progress or {}).get("storyline_error"),
        "current_chapter": None,
    }
    if run.status == "active" and package is not None:
        view["current_chapter"] = _progress(session, run, package)["current"]
    return view


def state(session: Session, user_id: str, tenant_id: str) -> dict[str, Any]:
    """Chapter list with derived status for this company's run (FR-009)."""
    run = _run_for_tenant(session, user_id, tenant_id)
    package = _package_of(session, run)
    progress = _progress(session, run, package)
    chapters = []
    for entry in progress["path"]:
        chapter = package.chapter(entry["key"])
        chapters.append(
            {
                **entry,
                "title": chapter.title.model_dump(exclude_none=True),
                # The conversation view renders past turns from the list itself,
                # so the spoken line and its explanation travel with every entry.
                "say": chapter.say.model_dump(exclude_none=True)
                if chapter.say
                else None,
                "situation": chapter.situation.model_dump(exclude_none=True),
                "explain": chapter.explain.model_dump(exclude_none=True),
                "view": chapter.view,
                "command": chapter.command,
                "branches": [
                    {
                        "key": b.key,
                        "label": b.label.model_dump(exclude_none=True),
                        "next": b.next,
                        "default": b.default,
                    }
                    for b in chapter.branches
                ],
            }
        )
    return {
        "run_id": run.id,
        "tenant_id": run.tenant_id,
        "status": run.status,
        "key": package.key,
        "version": package.version,
        "title": package.title.model_dump(exclude_none=True),
        "chapters": chapters,
        "current_chapter": progress["current"],
        "branches": progress["branches"],
        "start": (run.initialization_progress or {}).get("storyline", {}).get("start"),
    }


def _resolution_context(
    session: Session, run: PlaygroundRun, package: StorylinePackage
) -> ResolutionContext:
    stored = (run.initialization_progress or {}).get("storyline", {})
    context = ResolutionContext(
        start=datetime.fromisoformat(stored["start"]) if stored.get("start") else now(),
        refs=stored.get("refs", {}),
        company_party_id=stored.get("company_party_id"),
        seed_outputs=stored.get("seed_outputs", {}),
    )
    for step, proposal in _steps(session, run):
        if proposal is not None and proposal.status == "executed":
            context.chapter_outputs[step.lesson_step_key] = json.loads(
                proposal.output or "{}"
            )
    return context


def _preconditions(
    session: Session, run: PlaygroundRun, chapter: Chapter, context: ResolutionContext
) -> list[dict[str, Any]]:
    from reality.services.exceptions import operational_exceptions

    checks: list[dict[str, Any]] = []
    references: list[str] = []
    for source in [
        chapter.input,
        *(read.input for read in chapter.reads),
        *(read.input for read in chapter.context.values()),
    ]:
        for _path, text, _key in walk_strings(source):
            if (
                is_reference(text)
                and not text.startswith("$context.")
                and text not in references
            ):
                references.append(text)
    for reference in references:
        try:
            resolve_value(reference, context)
            holds = True
        except ReferenceError:
            holds = False
        checks.append({"kind": "reference", "name": reference, "holds": holds})
    if chapter.requires.findings_present or chapter.requires.findings_absent:
        present = {
            exception.class_id
            for exception in operational_exceptions(session, run.tenant_id)
        }
        for class_id in chapter.requires.findings_present:
            checks.append(
                {
                    "kind": "finding_present",
                    "name": class_id,
                    "holds": class_id in present,
                }
            )
        for class_id in chapter.requires.findings_absent:
            checks.append(
                {
                    "kind": "finding_absent",
                    "name": class_id,
                    "holds": class_id not in present,
                }
            )
    return checks


def chapter_detail(
    session: Session, user_id: str, tenant_id: str, key: str
) -> dict[str, Any]:
    run = _run_for_tenant(session, user_id, tenant_id)
    package = _package_of(session, run)
    chapter = package.chapter(key)
    if chapter is None:
        raise NotFound("Chapter not found.")
    progress = _progress(session, run, package)
    context = _resolution_context(session, run, package)
    preconditions = _preconditions(session, run, chapter, context)
    step, proposal = progress["latest"].get(key, (None, None))
    return {
        "chapter": _chapter_view(chapter),
        "status": next(
            (entry["status"] for entry in progress["path"] if entry["key"] == key),
            "unreachable",
        ),
        "preconditions": preconditions,
        "can_run": progress["current"] == key
        and all(check["holds"] for check in preconditions),
        "step": _step_view(step, proposal) if step is not None else None,
    }


def _chapter_view(chapter: Chapter) -> dict[str, Any]:
    return {
        "key": chapter.key,
        "kind": chapter.kind,
        "title": chapter.title.model_dump(exclude_none=True),
        "situation": chapter.situation.model_dump(exclude_none=True),
        "explain": chapter.explain.model_dump(exclude_none=True),
        "say": chapter.say.model_dump(exclude_none=True) if chapter.say else None,
        "view": chapter.view,
        "command": chapter.command,
        "input": chapter.input,
        "context": {name: read.model_dump() for name, read in chapter.context.items()},
        "reads": [read.model_dump() for read in chapter.reads],
        "primary": chapter.primary.model_dump(by_alias=True)
        if chapter.primary
        else None,
        "expect": chapter.expect.model_dump(),
        "next": chapter.next,
        "branches": [
            {
                "key": b.key,
                "label": b.label.model_dump(exclude_none=True),
                "next": b.next,
                "default": b.default,
            }
            for b in chapter.branches
        ],
    }


def _step_view(step: PlaygroundStep, proposal: ChangeProposal | None) -> dict[str, Any]:
    before = step.before_observation or {}
    return {
        "step_id": step.id,
        "chapter": step.lesson_step_key,
        "sequence": step.sequence,
        "status": _step_status(step, proposal),
        "proposal_id": proposal.id if proposal else None,
        "proposal_status": proposal.status if proposal else None,
        "preview_revision": before.get("preview_revision"),
        "review": json.loads(proposal.output)
        if proposal is not None and proposal.status == "proposed"
        else None,
        "arguments": json.loads(proposal.input)
        if proposal is not None
        else before.get("arguments"),
        "output": json.loads(proposal.output)
        if proposal is not None and proposal.status == "executed"
        else None,
        "refused": before.get("refused"),
        "context": before.get("context"),
        "marker": (
            {"sequence": step.marker_sequence, "at": step.marker_at}
            if step.marker_sequence is not None
            else None
        ),
        "receipt": step.receipt_observation,
    }


# --------------------------------------------------------------- chapter play


@contextmanager
def _locked_run(
    engine: Engine | Connection,
    user_id: str,
    tenant_id: str,
    db_session: Session | None,
) -> Iterator[tuple[Session, PlaygroundRun]]:
    from reality.db.core import Session as SessionFactory
    from reality.services.playground import _mutation_session

    if db_session is not None:
        run_id = _run_for_tenant(db_session, user_id, tenant_id).id
    else:
        with SessionFactory(bind=engine) as lookup:
            run_id = _run_for_tenant(lookup, user_id, tenant_id).id
    with _mutation_session(engine, user_id, run_id, db_session=db_session) as (
        session,
        run,
    ):
        yield session, run


def _next_sequence(session: Session, run: PlaygroundRun) -> int:
    from sqlalchemy import func

    return (
        int(
            session.scalar(
                select(func.coalesce(func.max(PlaygroundStep.sequence), 0)).where(
                    PlaygroundStep.tenant_id == run.tenant_id,
                    PlaygroundStep.run_id == run.id,
                )
            )
            or 0
        )
        + 1
    )


def _revision(step_id: str, arguments: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps({"step": step_id, "arguments": arguments}, sort_keys=True).encode()
    ).hexdigest()


def _bounded(value: Any) -> Any:
    text = json.dumps(value, default=str, sort_keys=True)
    if len(text.encode()) <= READ_RESULT_BYTE_BOUND:
        return json.loads(text)
    return {"truncated": True, "bytes": len(text.encode()), "preview": text[:2000]}


def prepare(
    engine: Engine | Connection,
    user_id: str,
    tenant_id: str,
    key: str,
    request_key: str,
    *,
    db_session: Session | None = None,
) -> dict[str, Any]:
    """Prepare the current chapter: marker, context reads, proposal or reads (FR-003)."""
    from reality.tools.application import create_change_proposal, run_read_tool

    if not request_key or request_key != request_key.strip() or len(request_key) > 128:
        raise InvalidOperation("A request key of 1 to 128 characters is required.")
    with _locked_run(engine, user_id, tenant_id, db_session) as (session, run):
        package = _package_of(session, run)
        chapter = package.chapter(key)
        if chapter is None:
            raise NotFound("Chapter not found.")
        existing = session.scalar(
            select(PlaygroundStep).where(
                PlaygroundStep.tenant_id == run.tenant_id,
                PlaygroundStep.run_id == run.id,
                PlaygroundStep.request_key == request_key,
            )
        )
        if existing is not None:
            if existing.lesson_step_key != key:
                raise Conflict("The request key belongs to another chapter.")
            proposal = (
                session.get(ChangeProposal, existing.proposal_id)
                if existing.proposal_id
                else None
            )
            return _step_view(existing, proposal)
        progress = _progress(session, run, package)
        if progress["current"] != key:
            raise Conflict("This chapter is not the current one.")
        from reality.services.playground import _require_step_capacity

        _require_step_capacity(session, run.tenant_id)
        context = _resolution_context(session, run, package)
        missing = [
            check
            for check in _preconditions(session, run, chapter, context)
            if not check["holds"]
        ]
        if missing:
            names = ", ".join(
                f"{check['name']} ({check['kind'].replace('_', ' ')})"
                for check in missing
            )
            raise Conflict(
                f"This chapter cannot run yet; missing: {names}. Restart the story with a fresh company or bring the company back to that state."
            )
        marker = recorder.capture_marker(session, run.tenant_id)
        step = PlaygroundStep(
            id=uid("pgs"),
            tenant_id=run.tenant_id,
            run_id=run.id,
            sequence=_next_sequence(session, run),
            request_key=request_key,
            proposal_id=None,
            lesson_step_key=key,
            marker_sequence=marker["marker_sequence"],
            marker_at=marker["marker_at"],
            before_observation={
                "kind": chapter.kind,
                "exceptions": marker["before_exceptions"],
                "evaluated_at": now().isoformat(),
            },
        )
        session.add(step)
        session.flush()
        scope = recorder.TraceScope(run.tenant_id, run.id, step.id, "storyline")
        with recorder.trace_scope(run.tenant_id, run.id, step_id=step.id):
            try:
                context_values: dict[str, Any] = {}
                pending = dict(chapter.context)
                while pending:
                    progressed = False
                    for name, read in list(pending.items()):
                        try:
                            arguments = resolve_value(read.input, context)
                        except ReferenceError as exc:
                            if "was not read" in str(exc):
                                continue  # depends on another context read
                            raise
                        result = run_read_tool(
                            session, run.tenant_id, read.tool, arguments
                        )
                        context.context_values[name] = (
                            dig(result, tuple(read.field.split(".")))
                            if read.field
                            else result
                        )
                        context_values[name] = _bounded(context.context_values[name])
                        del pending[name]
                        progressed = True
                    if not progressed:
                        raise ReferenceError(
                            "Context reads depend on each other: "
                            + ", ".join(sorted(pending))
                        )
                if context_values:
                    step.before_observation = {
                        **step.before_observation,
                        "context": context_values,
                    }
                if chapter.kind == "read":
                    results = []
                    for read in chapter.reads:
                        arguments = resolve_value(read.input, context)
                        result = run_read_tool(
                            session, run.tenant_id, read.tool, arguments
                        )
                        results.append(
                            {
                                "tool": read.tool,
                                "input": arguments,
                                "result": _bounded(result),
                            }
                        )
                    step.receipt_observation = {
                        "kind": "read",
                        "evaluated_at": now().isoformat(),
                        "results": results,
                    }
                    step.observed_at = now()
                    session.commit()
                    return _step_view(step, None)
                arguments = resolve_value(chapter.input, context)
                step.before_observation = {
                    **step.before_observation,
                    "arguments": arguments,
                }
                # The same review a business company runs before it proposes: a
                # held customer or an impossible quantity is refused here, at
                # preparation, and the chapter records that as its outcome.
                from reality.services.delivery_actions import eligible, review_delivery

                if eligible(chapter.command, arguments):
                    review_delivery(session, run.tenant_id, chapter.command, arguments)
                proposal = create_change_proposal(
                    session,
                    run.tenant_id,
                    chapter.command,
                    arguments,
                    actor_type="human",
                    _commit=False,
                )
            except (
                ReferenceError,
                InvalidOperation,
                NotFound,
                Conflict,
                PlaygroundOperationDenied,
            ) as exc:
                refused = {
                    "code": type(exc).__name__,
                    "detail": str(exc)[:400],
                    "at": now().isoformat(),
                    "phase": "prepare",
                }
                step.before_observation = {
                    **step.before_observation,
                    "refused": refused,
                }
                recorder.record(
                    session,
                    scope,
                    kind="error",
                    name=chapter.command or "read",
                    input=step.before_observation.get("arguments"),
                    error=f"{refused['code']}: {refused['detail']}",
                )
                session.commit()
                return _step_view(step, None)
        step.proposal_id = proposal.id
        step.before_observation = {
            **step.before_observation,
            "preview_revision": _revision(step.id, json.loads(proposal.input)),
        }
        session.commit()
        return _step_view(step, proposal)


def _owned_step(
    session: Session, run: PlaygroundRun, key: str, step_id: str
) -> tuple[PlaygroundStep, ChangeProposal | None]:
    step = session.scalar(
        select(PlaygroundStep).where(
            PlaygroundStep.tenant_id == run.tenant_id,
            PlaygroundStep.run_id == run.id,
            PlaygroundStep.id == step_id,
            PlaygroundStep.lesson_step_key == key,
        )
    )
    if step is None:
        raise NotFound("Chapter step not found.")
    proposal = (
        session.scalar(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == run.tenant_id,
                ChangeProposal.id == step.proposal_id,
            )
        )
        if step.proposal_id
        else None
    )
    return step, proposal


def confirm(
    engine: Engine | Connection,
    user_id: str,
    tenant_id: str,
    key: str,
    step_id: str,
    preview_revision: str,
    *,
    confirmed: bool = False,
    db_session: Session | None = None,
) -> dict[str, Any]:
    """Confirm a prepared chapter through the ordinary proposal executor (analysis C1)."""
    from reality.tools.application import (
        approve_and_execute_proposal,
        reject_proposal,
    )

    if confirmed is not True:
        raise PlaygroundOperationDenied("Confirm the reviewed chapter first.")
    with _locked_run(engine, user_id, tenant_id, db_session) as (session, run):
        step, proposal = _owned_step(session, run, key, step_id)
        if proposal is None:
            raise Conflict("This chapter has no proposal to confirm.")
        if proposal.status == "executed":
            return _step_view(step, proposal)
        if proposal.status == "rejected":
            raise Conflict("This chapter's proposal was rejected; prepare it again.")
        saved = (step.before_observation or {}).get("preview_revision")
        if saved is None or preview_revision != saved:
            raise Conflict("Confirmation does not match the prepared chapter.")
        token = json.loads(proposal.input).get("_delivery_review", {}).get("token")
        with recorder.trace_scope(run.tenant_id, run.id, step_id=step.id):
            try:
                approve_and_execute_proposal(
                    session,
                    run.tenant_id,
                    proposal.id,
                    confirming_principal=Principal(user_id),
                    review_token=token,
                    confirmed=True,
                )
            except (
                InvalidOperation,
                NotFound,
                Conflict,
                PlaygroundOperationDenied,
            ) as exc:
                # The system refused the command itself (a hold, a rule, a quota).
                # That is the chapter's outcome (FR-014): keep the step, close the
                # proposal, and let the story continue.
                session.rollback()
                step, proposal = _owned_step(session, run, key, step_id)
                if proposal is not None and proposal.status == "proposed":
                    # Refused before the handler ran: the chapter's outcome.
                    refused = {
                        "code": type(exc).__name__,
                        "detail": str(exc)[:400],
                        "at": now().isoformat(),
                        "phase": "confirm",
                    }
                    step.before_observation = {
                        **(step.before_observation or {}),
                        "refused": refused,
                    }
                    reject_proposal(
                        session,
                        run.tenant_id,
                        proposal.id,
                        confirming_principal=Principal(user_id),
                    )
                    session.refresh(proposal)
                    session.commit()
                    return _step_view(step, proposal)
                # The handler ran and its outcome is unknown: keep the step pending
                # and say so; the person inspects or restarts (spec 096 discipline).
                view = _step_view(step, proposal)
                view["error"] = {
                    "code": type(exc).__name__,
                    "detail": str(exc)[:400],
                    "unresolved": proposal is not None
                    and proposal.status == "executing",
                }
                return view
        session.refresh(proposal)
        step.receipt_observation = _receipt(session, run, step, proposal)
        step.observed_at = now()
        session.commit()
        _refresh_projections(session, run.tenant_id)
        return _step_view(step, proposal)


def _receipt(
    session: Session, run: PlaygroundRun, step: PlaygroundStep, proposal: ChangeProposal
) -> dict[str, Any]:
    from reality.db.core import BusinessEvent

    events = list(
        session.scalars(
            select(BusinessEvent)
            .where(
                BusinessEvent.tenant_id == run.tenant_id,
                BusinessEvent.action_id == proposal.id,
            )
            .order_by(BusinessEvent.sequence)
        )
    )
    output = json.loads(proposal.output or "{}")
    records = [
        {"family": entry.get("family"), "id": entry.get("id")}
        for entry in output.get("records", [])
        if isinstance(entry, dict)
    ]
    for field, family in (
        ("document_id", "document"),
        ("reservation_id", "reservation"),
        ("fact_id", "fact"),
        ("allocation_id", "settlement_allocation"),
    ):
        if output.get(field):
            records.append({"family": family, "id": output[field]})
    for commitment_id in output.get("commitment_ids", []) or []:
        records.append({"family": "commitment", "id": commitment_id})
    for line_id in output.get("document_line_ids", []) or []:
        records.append({"family": "document_line", "id": line_id})
    return {
        "kind": "command",
        "evaluated_at": now().isoformat(),
        "records": records,
        "event_ids": [event.id for event in events],
        "event_sequence": events[-1].sequence if events else step.marker_sequence,
    }


def reject(
    engine: Engine | Connection,
    user_id: str,
    tenant_id: str,
    key: str,
    step_id: str,
    *,
    confirmed: bool = False,
    db_session: Session | None = None,
) -> dict[str, Any]:
    from reality.tools.application import reject_proposal

    if confirmed is not True:
        raise PlaygroundOperationDenied("Confirm rejecting the chapter first.")
    with _locked_run(engine, user_id, tenant_id, db_session) as (session, run):
        step, proposal = _owned_step(session, run, key, step_id)
        if proposal is None or proposal.status != "proposed":
            raise Conflict("Only a prepared chapter can be rejected.")
        with recorder.trace_scope(run.tenant_id, run.id, step_id=step.id):
            reject_proposal(
                session,
                run.tenant_id,
                proposal.id,
                confirming_principal=Principal(user_id),
            )
        session.refresh(proposal)
        return _step_view(step, proposal)


def choose_branch(
    session: Session, user_id: str, tenant_id: str, chapter_key: str, branch_key: str
) -> dict[str, Any]:
    run = _run_for_tenant(session, user_id, tenant_id)
    require_playground_run(session, run.id, user_id, for_write=True)
    package = _package_of(session, run)
    chapter = package.chapter(chapter_key)
    if chapter is None or not any(
        branch.key == branch_key for branch in chapter.branches
    ):
        raise NotFound("Branch not found.")
    progress = _progress(session, run, package)
    if chapter_key not in progress["done"]:
        raise Conflict("Choose a branch after the chapter has run.")
    state_value = dict(run.storyline_state or {})
    branches = dict(state_value.get("branches", {}))
    branches[chapter_key] = branch_key
    run.storyline_state = {**state_value, "branches": branches}
    session.commit()
    return {
        "current_chapter": _progress(session, run, package)["current"],
        "branches": branches,
    }


def restart(
    session: Session,
    user_id: str,
    tenant_id: str,
    *,
    request_key: str,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Archive the run and start a fresh company for the same package (FR-012)."""
    from reality.services.playground import _check_capacity, _locked_owner

    if confirmed is not True:
        raise PlaygroundOperationDenied("Confirm restarting the storyline first.")
    _locked_owner(session, user_id)
    run = _run_for_tenant(session, user_id, tenant_id)
    if run.status != "active":
        raise Conflict("Only an active storyline run can be restarted.")
    _check_capacity(session, user_id)
    run.status, run.archived_at = "archived", now()
    session.flush()
    session.commit()
    recorder.clear_cache(run.tenant_id)
    return start(
        session,
        user_id,
        key=run.storyline_key,
        version=run.storyline_version,
        request_key=request_key,
        confirmed=True,
    )


# ------------------------------------------------------------------- reads


def trace(
    session: Session,
    user_id: str,
    tenant_id: str,
    *,
    step_id: str | None = None,
    after_ordinal: int = 0,
    limit: int = 200,
    free: bool = False,
) -> dict[str, Any]:
    """The run's trace; ``free`` keeps only calls made outside any chapter (FR-011)."""
    run = _run_for_tenant(session, user_id, tenant_id)
    page = recorder.read_trace(
        session,
        tenant_id,
        run.id,
        step_id=step_id,
        after_ordinal=after_ordinal,
        limit=limit,
        free=free,
    )
    chapters = {step.id: step.lesson_step_key for step, _ in _steps(session, run)}
    for item in page["items"]:
        item["chapter"] = chapters.get(item["step_id"])
    return page


def chat_evidence(
    session: Session, user_id: str, tenant_id: str, message_id: str
) -> dict[str, Any]:
    """Recorded calls for one reply and later decisions on the same proposals."""
    from sqlalchemy import or_

    from reality.db.core import ChatMessage, StorylineTraceEntry

    run = _run_for_tenant(session, user_id, tenant_id)
    message = session.scalar(
        select(ChatMessage).where(
            ChatMessage.id == message_id,
            ChatMessage.tenant_id == tenant_id,
            ChatMessage.role == "assistant",
        )
    )
    if message is None:
        raise NotFound("Chat message not found.")
    base = (
        StorylineTraceEntry.tenant_id == tenant_id,
        StorylineTraceEntry.run_id == run.id,
    )
    association = session.scalar(
        select(StorylineTraceEntry)
        .where(
            *base,
            StorylineTraceEntry.name == "chat.reply",
            StorylineTraceEntry.input["message_id"].as_string() == message_id,
        )
        .order_by(StorylineTraceEntry.ordinal.desc())
        .limit(1)
    )
    if association is None:
        return {"available": False, "items": [], "has_more": False}
    saved = association.result or {}
    ids = saved.get("trace_ids", [])[:128]
    direct = list(
        session.scalars(
            select(StorylineTraceEntry).where(
                *base,
                StorylineTraceEntry.id.in_(ids),
                StorylineTraceEntry.name != "chat.reply",
            )
        )
    )
    proposals = {row.proposal_id for row in direct if row.proposal_id}
    rows = list(
        session.scalars(
            select(StorylineTraceEntry)
            .where(
                *base,
                StorylineTraceEntry.name != "chat.reply",
                or_(
                    StorylineTraceEntry.id.in_(ids),
                    StorylineTraceEntry.proposal_id.in_(proposals),
                ),
            )
            .order_by(StorylineTraceEntry.ordinal)
            .limit(501)
        )
    )
    return {
        "available": True,
        "items": [{**recorder.entry_view(row), "chapter": None} for row in rows[:500]],
        "has_more": bool(
            saved.get("has_more") or len(direct) != len(ids) or len(rows) > 500
        ),
    }


def delta(
    session: Session,
    user_id: str,
    tenant_id: str,
    *,
    step_id: str | None = None,
    after_sequence: int | None = None,
    after_at: datetime | None = None,
    record: str | None = None,
    ordinal: int | None = None,
) -> dict[str, Any]:
    from reality.db.core import StorylineTraceEntry
    from reality.storyline.delta import read_delta

    run = _run_for_tenant(session, user_id, tenant_id)
    before: list[str] = []
    primary: tuple[str, str] | None = None
    if ordinal is not None:
        # A confirmation outside any chapter carries its own marker (free play).
        entry = session.scalar(
            select(StorylineTraceEntry).where(
                StorylineTraceEntry.tenant_id == run.tenant_id,
                StorylineTraceEntry.run_id == run.id,
                StorylineTraceEntry.ordinal == ordinal,
            )
        )
        if entry is None or entry.marker_sequence is None:
            raise NotFound("No marker recorded for this call.")
        after_sequence, after_at = entry.marker_sequence, entry.marker_at
        before = list(entry.before_exceptions or [])
    if step_id is not None:
        step = session.scalar(
            select(PlaygroundStep).where(
                PlaygroundStep.tenant_id == run.tenant_id,
                PlaygroundStep.run_id == run.id,
                PlaygroundStep.id == step_id,
            )
        )
        if step is None:
            raise NotFound("Chapter step not found.")
        after_sequence, after_at = step.marker_sequence, step.marker_at
        before = list((step.before_observation or {}).get("exceptions") or [])
        chapter = _package_of(session, run).chapter(step.lesson_step_key or "")
        if chapter is not None and chapter.primary and step.proposal_id:
            proposal = session.get(ChangeProposal, step.proposal_id)
            if proposal is not None and proposal.status == "executed":
                try:
                    record_id = dig(
                        json.loads(proposal.output or "{}"),
                        tuple(chapter.primary.from_.removeprefix("output.").split(".")),
                    )
                    primary = (chapter.primary.record_type, str(record_id))
                except ReferenceError:
                    primary = None
    if after_sequence is None:
        raise InvalidOperation("A marker (step_id or after_sequence) is required.")
    if record and ":" in record:
        record_type, _, record_id = record.partition(":")
        primary = (record_type, record_id)
    return read_delta(
        session,
        tenant_id,
        after_sequence=int(after_sequence),
        after_at=after_at,
        before_exceptions=before,
        primary=primary,
    )


def tool_reference(name: str, language: str = "en") -> dict[str, Any]:
    """One tool or view explained from the catalogs (FR-007, analysis M4)."""
    from reality.catalogs import (
        load_catalog_labels,
        load_operational_exception_catalog,
        runtime_application_catalog,
    )
    from reality.mcp.catalog import tool_definitions
    from reality.tools.application import TOOLS

    labels = load_catalog_labels()
    catalog = runtime_application_catalog()
    if name.startswith("view:"):
        key = name.removeprefix("view:")
        views = {
            view["key"]: view
            for workspace in catalog.get("workspaces", [])
            for view in workspace.get("views", [])
        }
        view = views.get(key)
        if view is None:
            raise NotFound("View not found.")
        return {
            "key": key,
            "kind": "view",
            "label": {"en": view.get("label", key), **labels["views"].get(key, {})},
            "description": view.get("description", ""),
            "access": "read",
            "parameters": [],
            "projections": [view["projection"]] if view.get("projection") else [],
            "docs_path": f"/tool-usage/views#view-{key}",
        }
    if name.startswith("exception:"):
        class_id = name.removeprefix("exception:")
        entry = next(
            (
                c
                for c in load_operational_exception_catalog().classes
                if c["id"] == class_id
            ),
            None,
        )
        if entry is None:
            raise NotFound("Exception class not found.")
        return {
            "key": class_id,
            "kind": "exception",
            "label": {"en": entry["label"], **labels["exceptions"].get(class_id, {})},
            "description": entry.get("description", ""),
            "clears_through": entry.get("clears_through", ""),
            "severity": entry.get("severity"),
            "docs_path": f"/tool-usage/exceptions#exception-{class_id}",
        }
    tool = TOOLS.get(name)
    if tool is None:
        raise NotFound("Tool not found.")
    guidance = catalog.get("capability_guidance") or {}
    mcp_name = next(
        (
            mcp
            for mcp, entry in guidance.items()
            if (entry or {}).get("application_tool") == name
        ),
        None,
    )
    definition = next(
        (
            d
            for d in tool_definitions()
            if d.name == (mcp_name or f"{name}_propose") or d.name == name
        ),
        None,
    )
    command = next(
        (
            c
            for c in catalog.get("commands", [])
            if c.get("service") == name or name in (c.get("tools") or [])
        ),
        None,
    )
    schema = definition.input_schema if definition else {}
    parameters = [
        {
            "name": key,
            "type": (spec.get("type") if isinstance(spec.get("type"), str) else "any")
            if isinstance(spec, dict)
            else "any",
            "required": key in (schema.get("required") or []),
            "description": spec.get("description", "")
            if isinstance(spec, dict)
            else "",
        }
        for key, spec in (schema.get("properties") or {}).items()
    ]
    return {
        "key": name,
        "kind": "command" if tool.mutating else "read",
        "label": {
            "en": definition.label if definition else name,
            **labels["commands"].get(name, {}),
        },
        "description": (definition.description if definition else tool.description),
        "access": "confirm" if tool.mutating else "read",
        "parameters": parameters,
        "projections": list((command or {}).get("writes") or []),
        "docs_path": f"/tool-usage/commands#command-{name}",
    }
