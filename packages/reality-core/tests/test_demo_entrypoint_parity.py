import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import (
    BusinessEvent,
    ChatMessage,
    ChatSession,
    Commitment,
    Document,
    DocumentLine,
    Fact,
    ImportJob,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    Reservation,
    SourceRecord,
    SourceStream,
    Tenant,
)
from reality.services.core import (
    create_party,
    create_tenant,
    ensure_demo,
    inventory_rows,
)
from reality.web import api as api_module
from reality.web.app import app

MANIFEST_VERSION = "guided-demo-v1"
SECTIONS = (
    "reference_data",
    "source",
    "evidence",
    "reality",
    "derived",
    "explanation",
)
MODELS = (
    Party,
    Item,
    Location,
    SourceRecord,
    SourceStream,
    ImportJob,
    Document,
    DocumentLine,
    Commitment,
    Reservation,
    Movement,
    Fact,
    BusinessEvent,
    ChatSession,
    ChatMessage,
    LedgerEntry,
)
NOISE = {
    "id",
    "tenant_id",
    "created_at",
    "updated_at",
    "received_at",
    "observed_at",
    "occurred_at",
    "recorded_at",
    "reserved_at",
    "sequence",
}


def clients_for(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)

    def override_session():
        with factory() as api_session:
            yield api_session

    app.dependency_overrides[api_module.database_session] = override_session
    return CliRunner(), TestClient(app)


def rows(session, model, tenant_id):
    return list(session.scalars(select(model).where(model.tenant_id == tenant_id)))


def aliases_for(session, tenant_id):
    aliases = {tenant_id: "tenant"}
    rules = (
        (Party, lambda row: f"party:{row.type}:{row.name}"),
        (Item, lambda row: f"item:{row.sku}"),
        (Location, lambda row: f"location:{row.name}"),
        (
            SourceRecord,
            lambda row: f"source:{row.source_system}:{row.external_id}:v{row.version}",
        ),
        (SourceStream, lambda row: f"stream:{row.source_system}:{row.external_id}"),
        (Document, lambda row: f"document:{row.type}:{row.number}"),
        (DocumentLine, lambda row: f"line:{row.source_line_id or row.sku}"),
        (Commitment, lambda row: f"commitment:{row.type}"),
        (Movement, lambda row: f"movement:{row.type}"),
        (ChatSession, lambda row: f"chat:{row.title}"),
    )
    for model, label in rules:
        for row in rows(session, model, tenant_id):
            aliases[row.id] = label(row)
    for model, prefix in (
        (ImportJob, "import_job"),
        (Reservation, "reservation"),
        (Fact, "fact"),
        (BusinessEvent, "event"),
        (ChatMessage, "message"),
        (LedgerEntry, "ledger"),
    ):
        ordered = sorted(rows(session, model, tenant_id), key=lambda row: row.id)
        for index, row in enumerate(ordered, 1):
            aliases[row.id] = f"{prefix}:{index}"
    return aliases


def canonical_value(value, aliases, today):
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, datetime):
        return "<timestamp>"
    # A calendar day compares as the text the manifest has always recorded, so the
    # relative-day substitution below still recognises it. `datetime` is checked
    # first because it is a `date`.
    if isinstance(value, date):
        value = value.isoformat()
    if isinstance(value, list):
        return [canonical_value(item, aliases, today) for item in value]
    if isinstance(value, dict):
        return {
            key: canonical_value(item, aliases, today)
            for key, item in sorted(value.items())
        }
    if isinstance(value, str):
        if value in aliases:
            return aliases[value]
        try:
            return canonical_value(json.loads(value), aliases, today)
        except (json.JSONDecodeError, TypeError):
            pass
        for offset in range(3):
            value = value.replace(
                (today + timedelta(days=offset)).isoformat(), f"<day+{offset}>"
            )
        for opaque_id, alias in aliases.items():
            value = value.replace(opaque_id, alias)
    return value


def canonical_rows(session, model, tenant_id, aliases, today):
    result = []
    for row in rows(session, model, tenant_id):
        values = {
            column.name: canonical_value(getattr(row, column.name), aliases, today)
            for column in row.__table__.columns
            if column.name not in NOISE
        }
        result.append(values)
    return sorted(result, key=lambda value: json.dumps(value, sort_keys=True))


def demo_manifest(session, tenant_id):
    today = datetime.now(UTC).date()
    aliases = aliases_for(session, tenant_id)
    inventory = inventory_rows(session, tenant_id)
    result = {
        "version": MANIFEST_VERSION,
        "reference_data": {
            "parties": canonical_rows(session, Party, tenant_id, aliases, today),
            "items": canonical_rows(session, Item, tenant_id, aliases, today),
            "locations": canonical_rows(session, Location, tenant_id, aliases, today),
        },
        "source": {
            "records": canonical_rows(session, SourceRecord, tenant_id, aliases, today),
            "streams": canonical_rows(session, SourceStream, tenant_id, aliases, today),
            "import_jobs": canonical_rows(
                session, ImportJob, tenant_id, aliases, today
            ),
        },
        "evidence": {
            "documents": canonical_rows(session, Document, tenant_id, aliases, today),
            "lines": canonical_rows(session, DocumentLine, tenant_id, aliases, today),
            "facts": canonical_rows(session, Fact, tenant_id, aliases, today),
        },
        "reality": {
            "commitments": canonical_rows(
                session, Commitment, tenant_id, aliases, today
            ),
            "reservations": canonical_rows(
                session, Reservation, tenant_id, aliases, today
            ),
            "movements": canonical_rows(session, Movement, tenant_id, aliases, today),
            "events": canonical_rows(session, BusinessEvent, tenant_id, aliases, today),
        },
        "derived": {
            "inventory": sorted(
                [
                    {
                        "item": aliases[row["item"].id],
                        **{
                            key: canonical_value(row[key], aliases, today)
                            for key in (
                                "physical",
                                "reserved",
                                "available",
                                "incoming",
                                "projected",
                            )
                        },
                    }
                    for row in inventory
                ],
                key=lambda value: json.dumps(value, sort_keys=True),
            ),
            "ledger_entries": len(rows(session, LedgerEntry, tenant_id)),
            "financial_state": "none",
        },
        "explanation": {
            "sessions": canonical_rows(session, ChatSession, tenant_id, aliases, today),
            "messages": canonical_rows(session, ChatMessage, tenant_id, aliases, today),
            "trace": ["source", "document", "line", "commitment", "reservation"],
        },
    }
    assert tuple(key for key in result if key != "version") == SECTIONS
    return result


def test_guided_demo_inventory_covers_every_produced_business_family(session):
    tenant = create_tenant(session, "Inventory Demo")
    ensure_demo(session, tenant)
    counts = {
        model.__tablename__: len(rows(session, model, tenant.id)) for model in MODELS
    }
    assert counts == {
        "party": 3,
        "item": 1,
        "location": 1,
        "source_record": 1,
        "source_stream": 1,
        "import_job": 1,
        "document": 1,
        "document_line": 1,
        "commitment": 2,
        "reservation": 1,
        "movement": 1,
        "fact": 0,
        "business_event": 12,
        "chat_session": 1,
        "chat_message": 2,
        "ledger_entry": 0,
    }
    assert demo_manifest(session, tenant.id)["version"] == MANIFEST_VERSION


def test_real_cli_interactive_auto_and_web_demo_entrypoints_are_equivalent(
    session, monkeypatch
):
    interactive = create_tenant(session, "Interactive Demo")
    automatic = create_tenant(session, "Automatic Demo")
    runner, client = clients_for(session, monkeypatch)
    try:
        interactive_result = runner.invoke(
            cli_module.app, ["demo", "--tenant", interactive.id], input="y\n"
        )
        automatic_result = runner.invoke(
            cli_module.app, ["demo", "--tenant", automatic.id, "--auto"]
        )
        web_result = client.post(
            "/api/v1/companies",
            json={"name": "Web Demo", "guided_demo": True},
        )
        assert interactive_result.exit_code == automatic_result.exit_code == 0
        assert web_result.status_code == 201, web_result.text

        manifests = {
            "interactive_cli": demo_manifest(session, interactive.id),
            "cli_auto": demo_manifest(session, automatic.id),
            "product_web": demo_manifest(session, web_result.json()["id"]),
        }
        assert manifests["interactive_cli"] == manifests["cli_auto"], "cli_auto"
        assert manifests["interactive_cli"] == manifests["product_web"], "product_web"
    finally:
        app.dependency_overrides.clear()


def test_demo_cancellation_empty_company_populated_tenant_and_rerun_are_safe(
    session, monkeypatch
):
    cancelled = create_tenant(session, "Cancelled Demo")
    populated = create_tenant(session, "Populated Demo")
    ensure_demo(session, populated)
    before = demo_manifest(session, populated.id)
    runner, client = clients_for(session, monkeypatch)
    try:
        cancelled_result = runner.invoke(
            cli_module.app, ["demo", "--tenant", cancelled.id], input="n\n"
        )
        assert cancelled_result.exit_code != 0
        assert rows(session, Party, cancelled.id) == []

        empty = client.post("/api/v1/companies", json={"name": "Empty Company"})
        assert empty.status_code == 201
        assert rows(session, Party, empty.json()["id"]) == []

        ensure_demo(session, populated)
        assert demo_manifest(session, populated.id) == before
    finally:
        app.dependency_overrides.clear()


def test_manifest_drift_is_reported_by_section(session):
    tenant = create_tenant(session, "Drift Demo")
    ensure_demo(session, tenant)
    expected = demo_manifest(session, tenant.id)
    item = rows(session, Item, tenant.id)[0]
    item.name = "Drifted Item"
    session.commit()
    actual = demo_manifest(session, tenant.id)
    mismatches = [
        section for section in SECTIONS if expected[section] != actual[section]
    ]
    assert mismatches == ["reference_data"]


def test_confirmed_web_population_failure_is_truthful_and_not_destructive(
    session, monkeypatch
):
    _, _ = clients_for(session, monkeypatch)

    def fail_after_one_record(api_session, tenant):
        create_party(api_session, tenant.id, "Partial Demo Company", "company")
        raise RuntimeError("injected demo population failure")

    monkeypatch.setattr(api_module, "ensure_demo", fail_after_one_record)
    client = TestClient(app, raise_server_exceptions=False)
    try:
        response = client.post(
            "/api/v1/companies",
            json={"name": "Partial Web Demo", "guided_demo": True},
        )
        assert response.status_code == 500
        tenant = session.scalar(select(Tenant).where(Tenant.name == "Partial Web Demo"))
        assert tenant is not None
        assert [party.name for party in rows(session, Party, tenant.id)] == [
            "Partial Demo Company"
        ]
    finally:
        app.dependency_overrides.clear()
