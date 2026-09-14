from datetime import UTC, datetime

from sqlalchemy import event, func, select
from test_fact_observation import _commitment
from test_unified_source_api import client_for

from reality.db.core import Fact, uid
from reality.services.core import create_tenant, observe_fact, store_source_record


def test_fact_register_filters_before_count_keeps_observations_and_excludes_source_payload(
    session, business
):
    tid = business.tenant.id
    commitment = _commitment(session, business)
    first, _, _ = store_source_record(
        session, tid, "sample-facts", "order", "SAME", {"priority": "standard"}
    )
    second, _, _ = store_source_record(
        session, tid, "sample-facts", "order", "SAME", {"priority": "express"}
    )
    facts = [
        observe_fact(
            session,
            tid,
            source_record_id=source.id,
            subject_type="commitment",
            subject_id=commitment.id,
            predicate="order.shipping_priority",
            value=value,
            observed_at="2026-09-07T12:00:00Z",
            idempotency_key=f"read-{i}",
        )
        for i, (source, value) in enumerate(
            [(first, "standard"), (second, "express"), (second, "standard")]
        )
    ]
    foreign = create_tenant(session, "Other facts")
    before = session.scalar(
        select(func.count()).select_from(Fact).where(Fact.tenant_id == tid)
    )
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())

    event.listen(session.bind, "before_cursor_execute", capture)
    try:
        with client_for(session) as client:
            base = f"/api/tenants/{tid}/facts"
            pages = [
                client.get(base, params={"page": n, "size": 1}).json()
                for n in (1, 2, 3)
            ]
            assert [p["items"][0]["id"] for p in pages] == sorted(
                [f.id for f in facts], reverse=True
            )
            assert all(p["page"]["total"] == 3 for p in pages)
            assert (
                client.get(base, params={"page": 999, "size": 1}).json()["page"][
                    "number"
                ]
                == 3
            )
            assert (
                client.get(base, params={"q": "express"}).json()["page"]["total"] == 1
            )
            assert (
                client.get(base, params={"q": "sample-facts"}).json()["page"]["total"]
                == 3
            )
            assert (
                client.get(base, params={"subject_type": "item"}).json()["page"][
                    "total"
                ]
                == 0
            )
            assert (
                client.get(base, params={"subject_id": "missing"}).json()["page"][
                    "total"
                ]
                == 0
            )
            scoped = client.get(
                base, params={"source_record_id": second.id, "size": 1}
            ).json()
            assert scoped["page"]["total"] == 2
            assert scoped["items"][0]["source_version"] == 2
            assert scoped["items"][0]["source"] == {
                "system": "sample-facts",
                "type": "order",
                "external_id": "SAME",
            }
            assert scoped["subject_types"] == ["commitment"]
            assert scoped["subject_types_has_more"] is False
            assert (
                client.get(
                    f"/api/tenants/{foreign.id}/facts",
                    params={"source_record_id": second.id},
                ).json()["page"]["total"]
                == 0
            )
            assert client.get(base + "?size=101").status_code == 422
    finally:
        event.remove(session.bind, "before_cursor_execute", capture)
    assert not any("source_record.payload" in statement for statement in statements)
    assert not any(
        "interpretation_rule.mapping" in statement for statement in statements
    )
    assert before == session.scalar(
        select(func.count()).select_from(Fact).where(Fact.tenant_id == tid)
    )


def test_fact_inspector_links_exact_subject_and_source_without_current_truth_claim(
    session, business
):
    tid = business.tenant.id
    commitment = _commitment(session, business)
    source, _, _ = store_source_record(
        session, tid, "sample", "order", "OBS-114", {"priority": "express"}
    )
    fact = observe_fact(
        session,
        tid,
        source_record_id=source.id,
        subject_type="commitment",
        subject_id=commitment.id,
        predicate="order.shipping_priority",
        value="express",
        observed_at="2026-09-07T12:00:00Z",
        idempotency_key="inspect",
    )
    foreign = create_tenant(session, "Foreign inspection")
    with client_for(session) as client:
        path = f"/api/tenants/{tid}/inspector/fact/{fact.id}"
        data = client.get(path).json()
        assert (
            data["meaning"]
            == "This is a recorded observation, not a current-state guarantee."
        )
        links = [
            row["link"]
            for section in data["sections"]
            for row in section["rows"]
            if row["link"]
        ]
        assert {"kind": "commitment", "id": commitment.id} in links
        assert {"kind": "source_record", "id": source.id} in links
        assert (
            client.get(
                f"/api/tenants/{foreign.id}/inspector/fact/{fact.id}"
            ).status_code
            == 404
        )


def test_legacy_fact_choices_are_bounded_and_missing_source_is_not_inferred(
    session, business
):
    tid = business.tenant.id
    # Historical rows predate the current public predicate catalog; fixture setup only.
    rows = [
        Fact(
            id=uid("fct"),
            tenant_id=tid,
            subject_type=f"legacy_{i:03}",
            subject_id="historical/id",
            predicate="legacy.literal",
            value="Open <script>original</script>",
            observed_at=datetime(2026, 9, 7, tzinfo=UTC),
        )
        for i in range(101)
    ]
    session.add_all(rows)
    session.commit()
    with client_for(session) as client:
        data = client.get(f"/api/tenants/{tid}/facts?subject_type=legacy_100").json()
        assert data["page"]["total"] == 1
        assert len(data["subject_types"]) == 100
        assert data["subject_types_has_more"] is True
        assert data["items"][0]["value"] == "Open <script>original</script>"
        assert data["items"][0]["source"] is None
        inspected = client.get(
            f"/api/tenants/{tid}/inspector/fact/{rows[-1].id}"
        ).json()
        assert inspected["trail"][0]["value"] == "No linked source recorded"
        assert not any(
            row["link"] for section in inspected["sections"] for row in section["rows"]
        )
