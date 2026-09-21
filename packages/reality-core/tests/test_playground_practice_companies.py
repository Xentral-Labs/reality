"""099: persistent practice companies remain private and reusable."""

import pytest
import test_playground_steps
from conftest import record_by_id
from sqlalchemy.orm import Session

from reality.db.core import AppUser, Party, PlaygroundRun, Tenant, now, uid
from reality.services.core import Conflict, InvalidOperation, NotFound
from reality.services.playground import list_runs, read_run, restart_run, start_run
from reality.services.tenant_policy import PlaygroundOperationDenied

durable_playground = test_playground_steps.durable_playground


def test_practice_companies_survive_quick_replacement(durable_playground):
    engine, owner, quick_id = durable_playground
    with Session(engine) as s:
        a = start_run(
            s,
            owner,
            "company-a",
            sandbox_kind="practice",
            company_name="  Bike Lab  ",
            confirmed=True,
        )
        b = start_run(
            s,
            owner,
            "company-b",
            sandbox_kind="practice",
            company_name="Second Lab",
            confirmed=True,
        )
        ids = a.id, b.id
        before = read_run(s, owner, a.id)
        fresh = restart_run(
            s, owner, quick_id, request_key="next-quick", confirmed=True
        )
        assert fresh.sandbox_kind == "temporary"
        assert len({a.tenant_id, b.tenant_id, fresh.tenant_id}) == 3
        for run_id in ids:
            assert read_run(s, owner, run_id)["status"] == "active"
        assert read_run(s, owner, a.id) == before
        assert before["company_name"] == "Bike Lab"
        assert s.get(Tenant, a.tenant_id).purpose == "playground"
        assert (
            record_by_id(s, Party, a.initialization_progress["parties"]["company"]).name
            == "Bike Lab"
        )
        summaries = {r["id"]: r for r in list_runs(s, owner)["runs"]}
        assert summaries[a.id]["sandbox_kind"] == "practice"
        assert summaries[a.id]["company_name"] == "Bike Lab"
        same = start_run(
            s,
            owner,
            "company-a",
            sandbox_kind="practice",
            company_name="Bike Lab",
            confirmed=True,
        )
        assert same.id == a.id
        with pytest.raises(Conflict):
            start_run(
                s,
                owner,
                "company-a",
                sandbox_kind="practice",
                company_name="Changed",
                confirmed=True,
            )
        s.rollback()
        with pytest.raises(PlaygroundOperationDenied):
            restart_run(s, owner, a.id, confirmed=True)
        s.rollback()
        assert record_by_id(s, PlaygroundRun, a.id).status == "active"
        with pytest.raises(Conflict):
            start_run(s, owner, "company-a", confirmed=True)
        s.rollback()
        other = AppUser(
            id=uid("usr"),
            email="other@example.test",
            password_hash="unused",
            status="active",
            email_verified_at=now(),
        )
        s.add(other)
        s.commit()
        with pytest.raises(NotFound):
            read_run(s, other.id, a.id)
        assert list_runs(s, other.id)["runs"] == []


@pytest.mark.parametrize(
    "kind,name",
    [
        ("practice", ""),
        ("practice", " "),
        ("practice", "a" * 121),
        ("wrong", "Company"),
        ("temporary", "Company"),
    ],
)
def test_invalid_creation_metadata_is_rejected(durable_playground, kind, name):
    engine, owner, _ = durable_playground
    with Session(engine) as s, pytest.raises(InvalidOperation):
        start_run(
            s,
            owner,
            "invalid",
            sandbox_kind=kind,
            company_name=name,
            confirmed=True,
        )


def test_creation_api_rejects_unknown_kind():
    from pydantic import ValidationError

    from reality.web.playground import StartRun

    with pytest.raises(ValidationError):
        StartRun(request_key="x", sandbox_kind="production", confirmed=True)
    assert (
        StartRun(
            request_key="x", sandbox_kind="practice", company_name="  Lab  "
        ).company_name
        == "Lab"
    )


def test_practice_companies_archive_and_restore_without_deleting(durable_playground):
    """Spec 186 FR-010..FR-012: archiving hides the company; restoring brings it back."""
    from reality.services.playground import archive_run, restore_run
    from reality.services.tenant_policy import practice_company_runs

    engine, owner, _quick_id = durable_playground
    with Session(engine) as s:
        run = start_run(
            s,
            owner,
            "archive-me",
            sandbox_kind="practice",
            company_name="Old Lab",
            confirmed=True,
        )
        assert run.tenant_id in practice_company_runs(s, owner)
        with pytest.raises(PlaygroundOperationDenied):
            archive_run(s, owner, run.id)
        s.rollback()
        with pytest.raises((NotFound, PlaygroundOperationDenied)):
            archive_run(s, "usr_nobody", run.id, confirmed=True)
        s.rollback()

        archived = archive_run(s, owner, run.id, confirmed=True)
        assert archived.status == "archived"
        assert archived.archived_at is not None
        # A second session proves the service persisted the change itself; the API
        # session never commits on its own (this is what the danger zone hit live).
        with Session(engine) as fresh:
            assert record_by_id(fresh, PlaygroundRun, run.id).status == "archived"
            assert run.tenant_id not in practice_company_runs(fresh, owner)
        assert run.tenant_id not in practice_company_runs(s, owner)
        assert s.get(Tenant, run.tenant_id).archived_at is None
        summaries = {r["id"]: r for r in list_runs(s, owner)["runs"]}
        assert summaries[run.id]["status"] == "archived"
        assert summaries[run.id]["company_name"] == "Old Lab"
        with pytest.raises(Conflict):
            archive_run(s, owner, run.id, confirmed=True)
        s.rollback()

        with pytest.raises(PlaygroundOperationDenied):
            restore_run(s, owner, run.id)
        s.rollback()
        restored = restore_run(s, owner, run.id, confirmed=True)
        assert restored.status == "active"
        assert restored.archived_at is None
        with Session(engine) as fresh:
            assert record_by_id(fresh, PlaygroundRun, run.id).status == "active"
            assert run.tenant_id in practice_company_runs(fresh, owner)
        assert run.tenant_id in practice_company_runs(s, owner)
        with pytest.raises(Conflict):
            restore_run(s, owner, run.id, confirmed=True)
        s.rollback()
