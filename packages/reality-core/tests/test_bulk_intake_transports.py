"""Spec 360 FR-011: transport selection cannot replace exact source decisions."""

import json

from sqlalchemy import select
from test_bulk_intake_admission import prepared_orders
from test_unified_source_api import client_for

from reality.db.core import Document
from reality.services import core


def test_api_prepares_exact_selection_and_retains_full_original_source(
    session, business
):
    entries = prepared_orders(session, business, 2)
    with client_for(session) as client:
        base = f"/api/tenants/{business.tenant.id}"
        response = client.post(
            f"{base}/intake-batches/prepare",
            json={"entries": entries, "request_id": "selected-api-units"},
        )
        assert response.status_code == 200, response.text
        batch_id = response.json()["id"]
        review = client.get(f"{base}/intake-batches/{batch_id}/review?limit=1").json()
        assert review["total"] == 2 and review["has_more"]
        assert review["entries"][0]["proposal_id"] == entries[0]["proposal_id"]
        original = client.get(
            f"{base}/intake-units/{entries[0]['proposal_id']}/original"
        )
        assert original.status_code == 200
        assert json.loads(original.content)["id"] == "bulk-0"
        replay = client.post(
            f"{base}/intake-batches/prepare",
            json={"entries": entries, "request_id": "selected-api-units"},
        )
        assert replay.json()["id"] == batch_id
        status = client.get(f"{base}/intake-batches/{batch_id}/status").json()
        assert status["settled"] == 0 and status["results"] == []
    assert session.scalar(select(Document)) is None


def test_api_refuses_foreign_selection_and_unbounded_pages(session, business):
    entries = prepared_orders(session, business, 1)
    foreign = core.create_tenant(session, "Foreign bulk transport")
    with client_for(session) as client:
        base = f"/api/tenants/{foreign.id}"
        response = client.post(
            f"{base}/intake-batches/prepare",
            json={"entries": entries, "request_id": "foreign-selection"},
        )
        assert response.status_code == 404
        assert (
            client.get(
                f"{base}/intake-units/{entries[0]['proposal_id']}/original"
            ).status_code
            == 404
        )
        assert (
            client.get(f"{base}/intake-batches/absent/review?limit=101").status_code
            == 422
        )
    assert session.scalar(select(Document)) is None


def test_cli_exact_confirmation_and_stop_keep_principal_and_results(
    session, business, scheduled_owner, monkeypatch, tmp_path
):
    from test_cli import runner_for

    from reality.cli import app as cli_module
    from reality.db.core import ChangeProposal
    from reality.services import intake_batches

    entries = prepared_orders(session, business, 2)
    manifest = tmp_path / "selection.json"
    manifest.write_text(json.dumps(entries))
    runner = runner_for(session, monkeypatch)
    args = ["--tenant", business.tenant.id]
    prepared = runner.invoke(
        cli_module.app,
        [
            "intake",
            "prepare-batch",
            str(manifest),
            "--request-id",
            "cli-selection",
            *args,
        ],
    )
    assert prepared.exit_code == 0, prepared.output
    review = json.loads(prepared.stdout)
    batch_id = review["batch_id"]
    missing_actor = runner.invoke(
        cli_module.app,
        ["intake", "confirm-batch", batch_id, review["digest"], "--yes", *args],
    )
    assert missing_actor.exit_code != 0
    wrong_digest = runner.invoke(
        cli_module.app,
        [
            "intake",
            "confirm-batch",
            batch_id,
            "0" * 64,
            "--user-id",
            scheduled_owner.id,
            "--yes",
            *args,
        ],
    )
    assert wrong_digest.exit_code != 0
    assert session.scalar(select(Document)) is None
    approved = runner.invoke(
        cli_module.app,
        [
            "intake",
            "confirm-batch",
            batch_id,
            review["digest"],
            "--user-id",
            scheduled_owner.id,
            "--yes",
            *args,
        ],
    )
    assert approved.exit_code == 0, approved.output
    status = json.loads(approved.stdout)
    assert status["status"] == "executing" and status["settled"] == 0
    stopped = runner.invoke(
        cli_module.app,
        ["intake", "stop-batch", batch_id, "--user-id", scheduled_owner.id, *args],
    )
    assert stopped.exit_code == 0, stopped.output
    assert json.loads(stopped.stdout)["stopped"]
    session.expire_all()
    batch = session.get(ChangeProposal, (business.tenant.id, batch_id))
    intake_batches.settle_chunk(
        session,
        business.tenant.id,
        batch_id,
        continuation_id=json.loads(batch.output)["continuation_id"],
    )
    status = intake_batches.batch_status(session, business.tenant.id, batch_id)
    assert status["counts"] == {"stopped": 2}
    assert session.scalar(select(Document)) is None


def test_api_approval_records_mixed_child_results_truthfully(
    session, business, scheduled_owner, monkeypatch
):
    from reality.db.core import ChangeProposal
    from reality.services import intake_batches
    from reality.services.memberships import Principal
    from reality.web import api as api_module

    entries = prepared_orders(session, business, 2)
    with client_for(session) as client:
        base = f"/api/tenants/{business.tenant.id}"
        batch_id = client.post(
            f"{base}/intake-batches/prepare",
            json={"entries": entries, "request_id": "mixed-results"},
        ).json()["id"]
        digest = client.get(f"{base}/intake-batches/{batch_id}/review").json()["digest"]
        assert (
            client.post(
                f"{base}/change-proposals/{batch_id}/approve",
                json={"confirmed": True, "review_token": digest},
            ).status_code
            != 200
        )
        monkeypatch.setattr(
            api_module,
            "optional_request_principal",
            lambda request: Principal(scheduled_owner.id),
        )
        approved = client.post(
            f"{base}/change-proposals/{batch_id}/approve",
            json={"confirmed": True, "review_token": digest},
        )
        assert approved.status_code == 200, approved.text
        session.expire_all()
        batch = session.get(ChangeProposal, (business.tenant.id, batch_id))
        original = core.create_commitment
        calls = 0

        def refuse_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise core.InvalidOperation(code="intake_review_stale")
            return original(*args, **kwargs)

        monkeypatch.setattr(core, "create_commitment", refuse_second)
        intake_batches.settle_chunk(
            session,
            business.tenant.id,
            batch_id,
            continuation_id=json.loads(batch.output)["continuation_id"],
        )
        status = client.get(f"{base}/intake-batches/{batch_id}/status").json()
        assert status["counts"] == {"applied": 1, "review_required": 1}
        assert len(status["results"]) == status["settled"] == 2
        assert (
            "receipt" in status["results"][0] and "receipt" not in status["results"][1]
        )
    assert len(list(session.scalars(select(Document)))) == 1


def test_api_renewal_requires_fresh_review_and_preserves_old_plan(session, business):
    from test_intake_admission import prepare

    from reality.services.intake import review_intake

    _, job, prior = prepare(session, business)
    original_plan = prior.input
    fresh_location = core.create_location(
        session, business.tenant.id, "New reviewed destination"
    )
    config = json.loads(job.input)
    config["location_id"] = fresh_location.id
    job.input = json.dumps(config)
    session.flush()
    with client_for(session) as client:
        url = f"/api/tenants/{business.tenant.id}/intake-units/{prior.id}/renew"
        request = {"job_id": job.id, "request_id": "fresh-web-meaning"}
        fresh = client.post(url, json=request)
        assert fresh.status_code == 200, fresh.text
        assert fresh.json()["id"] != prior.id
        assert client.post(url, json=request).json()["id"] == fresh.json()["id"]
        foreign = core.create_tenant(session, "Foreign source renewal")
        assert (
            client.post(
                f"/api/tenants/{foreign.id}/intake-units/{prior.id}/renew", json=request
            ).status_code
            == 404
        )
    session.expire_all()
    assert prior.input == original_plan
    assert review_intake(session, business.tenant.id, prior.id)["status"] == "stale"
    assert session.scalar(select(Document)) is None
