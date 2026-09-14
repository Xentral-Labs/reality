"""Spec 182 FR-001, FR-003, FR-004, FR-005, FR-007, FR-018: the storyline HTTP surface."""

import pytest
from fastapi.testclient import TestClient

from reality.storyline import recorder
from tests.test_http_boundary import client_for

KEY, VERSION = "order-to-close", 1


@pytest.fixture
def http(session, monkeypatch, company_setup_login):
    recorder.clear_cache()
    client = client_for(session, monkeypatch)
    actor = company_setup_login(client)
    yield client, actor
    recorder.clear_cache()


def start(client: TestClient, request_key="http-1"):
    response = client.post(
        "/api/storyline/runs",
        json={
            "key": KEY,
            "version": VERSION,
            "request_key": request_key,
            "confirmed": True,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "active", body
    return body


@pytest.mark.parametrize("retired_flag", [None, "false", "true", "", "invalid"])
def test_library_start_and_state_over_http(http, monkeypatch, retired_flag):
    if retired_flag is None:
        monkeypatch.delenv("REALITY_PLAYGROUND_ENABLED", raising=False)
    else:
        monkeypatch.setenv("REALITY_PLAYGROUND_ENABLED", retired_flag)
    client, _actor = http
    library = client.get("/api/storyline/library")
    assert library.status_code == 200
    assert library.json()["enabled"] is True
    assert [item["key"] for item in library.json()["items"]] == [
        "first-round",
        KEY,
        "purchase-to-pay",
    ]
    assert all(item["run"] is None for item in library.json()["items"])

    run = start(client)
    tenant_id = run["tenant_id"]
    state = client.get(f"/api/tenants/{tenant_id}/storyline")
    assert state.status_code == 200
    body = state.json()
    assert body["current_chapter"] == "order"
    assert body["chapters"][0]["status"] == "current"
    assert body["chapters"][0]["title"]["de"] == "Auftrag anlegen"
    listed = client.get("/api/storyline/library").json()["items"]
    started_item = next(item for item in listed if item["key"] == KEY)
    assert started_item["run"]["tenant_id"] == tenant_id

    detail = client.get(f"/api/tenants/{tenant_id}/storyline/chapters/order").json()
    assert detail["can_run"] is True
    assert all(check["holds"] for check in detail["preconditions"])
    assert detail["chapter"]["command"] == "order_create"
    assert (
        client.get(f"/api/tenants/{tenant_id}/storyline/chapters/nope").status_code
        == 404
    )


def test_a_chapter_is_prepared_confirmed_and_explained_over_http(http):
    client, _actor = http
    tenant_id = start(client)["tenant_id"]

    prepared = client.post(
        f"/api/tenants/{tenant_id}/storyline/chapters/order/prepare",
        json={"request_key": "ch-order"},
    )
    assert prepared.status_code == 200, prepared.text
    step = prepared.json()
    assert step["status"] == "pending"
    assert step["review"] is not None and step["preview_revision"]

    unconfirmed = client.post(
        f"/api/tenants/{tenant_id}/storyline/chapters/order/confirm",
        json={"step_id": step["step_id"], "preview_revision": step["preview_revision"]},
    )
    assert unconfirmed.status_code == 403

    confirmed = client.post(
        f"/api/tenants/{tenant_id}/storyline/chapters/order/confirm",
        json={
            "step_id": step["step_id"],
            "preview_revision": step["preview_revision"],
            "confirmed": True,
        },
    )
    assert confirmed.status_code == 200, confirmed.text
    done = confirmed.json()
    assert done["status"] == "done"
    assert done["receipt"]["records"]

    trace = client.get(
        f"/api/tenants/{tenant_id}/storyline/trace", params={"step_id": step["step_id"]}
    ).json()
    kinds = [item["kind"] for item in trace["items"]]
    assert kinds[:2] == ["propose", "confirm"]
    assert all(item["chapter"] == "order" for item in trace["items"])

    delta = client.get(
        f"/api/tenants/{tenant_id}/storyline/delta", params={"step_id": step["step_id"]}
    ).json()
    assert delta["events"] and delta["records"]
    assert [x["class_id"] for x in delta["exceptions"]["raised"]] == [
        "outgoing_commitment_at_risk"
    ]
    assert delta["graph"]["record"]["record_type"] == "commitment"

    marker = client.get(
        f"/api/tenants/{tenant_id}/storyline/delta",
        params={"after_sequence": done["marker"]["sequence"]},
    ).json()
    assert [e["sequence"] for e in marker["events"]] == [
        e["sequence"] for e in delta["events"]
    ]
    assert client.get(f"/api/tenants/{tenant_id}/storyline/delta").status_code == 422

    reference = client.get(
        f"/api/tenants/{tenant_id}/storyline/tool-reference/order_create"
    ).json()
    assert reference["kind"] == "command" and reference["access"] == "confirm"
    view = client.get(
        f"/api/tenants/{tenant_id}/storyline/tool-reference/view:open_items"
    )
    assert view.json()["label"]["de"] == "Offene Posten"
    dotted = client.get(
        f"/api/tenants/{tenant_id}/storyline/tool-reference/finance.settlement.apply"
    )
    assert dotted.status_code == 200 and dotted.json()["kind"] == "command"

    again = client.post(
        f"/api/tenants/{tenant_id}/storyline/chapters/order/prepare",
        json={"request_key": "ch-order-2"},
    )
    assert again.status_code == 409


def test_storyline_routes_are_private_to_the_owner_and_need_a_cookie(
    session, monkeypatch, company_setup_login, business
):
    recorder.clear_cache()
    client = client_for(session, monkeypatch)
    assert client.get("/api/storyline/library").status_code == 401
    company_setup_login(client)
    tenant_id = start(client)["tenant_id"]

    assert client.get(f"/api/tenants/{business.tenant.id}/storyline").status_code == 404

    other = client_for(session, monkeypatch)
    assert other.get(f"/api/tenants/{tenant_id}/storyline").status_code == 401
    other_login = company_setup_login
    other_login(other)  # a second session for the same account still works
    assert other.get(f"/api/tenants/{tenant_id}/storyline").status_code == 200
    recorder.clear_cache()


def test_start_errors_map_to_http_statuses(http):
    client, _actor = http
    refused = client.post(
        "/api/storyline/runs",
        json={"key": KEY, "version": VERSION, "request_key": "no-confirm"},
    )
    assert refused.status_code == 403
    unknown = client.post(
        "/api/storyline/runs",
        json={"key": "no-such", "version": 1, "request_key": "x", "confirmed": True},
    )
    assert unknown.status_code == 404
    start(client)
    conflict = client.post(
        "/api/storyline/runs",
        json={"key": KEY, "version": 2, "request_key": "y", "confirmed": True},
    )
    assert conflict.status_code == 409


def test_library_export_import_replace_and_delete(http, session):
    import json

    import yaml
    from sqlalchemy import select

    from reality.db.core import StorylinePackageRecord

    client, actor = http
    # Download of a built-in is the file as shipped; JSON is the same document.
    as_yaml = client.get(
        f"/api/storyline/library/{KEY}/{VERSION}", params={"download": "yaml"}
    )
    assert as_yaml.status_code == 200
    assert as_yaml.headers["content-disposition"].endswith('.storyline.yaml"')
    document = yaml.safe_load(as_yaml.content)
    as_json = client.get(f"/api/storyline/library/{KEY}/{VERSION}").json()
    assert as_json == document

    # Import under another key round-trips unchanged and appears only in this account.
    document["key"] = "my-story"
    body = yaml.safe_dump(document, sort_keys=False, allow_unicode=True).encode()
    created = client.post(
        "/api/storyline/library",
        params={"filename": "my-story.storyline.yaml"},
        content=body,
        headers={"Content-Type": "application/yaml"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["key"] == "my-story" and created.json()["chapters"] == 18
    library = client.get("/api/storyline/library").json()["items"]
    assert [(i["key"], i["origin"]) for i in library] == [
        ("first-round", "builtin"),
        (KEY, "builtin"),
        ("purchase-to-pay", "builtin"),
        ("my-story", "import"),
    ]
    assert client.get("/api/storyline/library/my-story/1").json() == document
    rows = session.scalars(select(StorylinePackageRecord)).all()
    assert [(r.key, r.owner_user_id) for r in rows] == [("my-story", actor.id)]

    # Same key and version: ask first, replace when told, keep the old row as history.
    again = client.post(
        "/api/storyline/library", params={"filename": "x.yaml"}, content=body
    )
    assert again.status_code == 409
    replaced = client.post(
        "/api/storyline/library",
        params={"filename": "x.yaml", "replace": "true"},
        content=body,
    )
    assert replaced.status_code == 201 and replaced.json()["replaced"] is True
    session.expire_all()
    rows = session.scalars(
        select(StorylinePackageRecord).order_by(StorylinePackageRecord.imported_at)
    ).all()
    assert [r.replaced_at is None for r in rows] == [False, True]

    # A built-in key and version cannot be shadowed; built-ins cannot be deleted.
    shadow = dict(document, key=KEY)
    assert (
        client.post(
            "/api/storyline/library",
            content=json.dumps(shadow).encode(),
            params={"filename": "s.json"},
        ).status_code
        == 409
    )
    assert client.delete(f"/api/storyline/library/{KEY}/{VERSION}").status_code == 405
    assert client.delete("/api/storyline/library/my-story/1").status_code == 204
    assert [i["key"] for i in client.get("/api/storyline/library").json()["items"]] == [
        "first-round",
        KEY,
        "purchase-to-pay",
    ]
    assert client.delete("/api/storyline/library/my-story/1").status_code == 404


def test_import_refuses_bad_packages_with_every_error_and_stores_nothing(http, session):
    import json

    from sqlalchemy import select

    from reality.db.core import StorylinePackageRecord

    client, _actor = http
    base = client.get(f"/api/storyline/library/{KEY}/{VERSION}").json()
    broken = json.loads(json.dumps(base))
    broken["key"] = "broken"
    broken["chapters"][0]["command"] = "no_such_command"
    broken["chapters"][0]["view"] = "view:nowhere"
    broken["chapters"][0]["input"]["counterparty_id"] = "$ref.parties.ghost"
    refused = client.post(
        "/api/storyline/library",
        params={"filename": "broken.json"},
        content=json.dumps(broken).encode(),
    )
    assert refused.status_code == 422
    codes = sorted(error["code"] for error in refused.json()["errors"])
    assert codes == ["unknown_command", "unknown_ref", "unknown_view"]

    assert (
        client.post(
            "/api/storyline/library",
            params={"filename": "list.yaml"},
            content=b"- a\n- b\n",
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/storyline/library",
            params={"filename": "big.json"},
            content=b"x" * 200_001,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/storyline/library",
            params={"filename": "bin.json"},
            content=b"\xff\xfe",
        ).status_code
        == 422
    )
    assert session.scalars(select(StorylinePackageRecord)).all() == []

    # A chapter naming a command the person may not confirm is a warning, not a refusal.
    warned = json.loads(json.dumps(base))
    warned["key"] = "warned"
    warned["chapters"].insert(
        1,
        {
            "key": "invite",
            "title": {"en": "Invite"},
            "situation": {"en": "s"},
            "explain": {"en": "e"},
            "command": "member_invite",
            "input": {"email": "a@example.test"},
            "next": "reference",
        },
    )
    warned["chapters"][0]["next"] = "invite"
    response = client.post(
        "/api/storyline/library",
        params={"filename": "w.json"},
        content=json.dumps(warned).encode(),
    )
    assert response.status_code == 201, response.text
    assert any(
        w["code"] == "command_requires_confirmation_you_may_lack"
        for w in response.json()["warnings"]
    )
