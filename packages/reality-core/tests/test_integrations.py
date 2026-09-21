import io
import zipfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.cli import app as cli_module
from reality.db.core import ChangeProposal, ImportJob, SourceArtifact, SourceRecord
from reality.services.core import (
    connector_shells,
    create_source_capability,
    create_source_system,
    install_connector_shell,
    integration_registry,
    set_source_capability_active,
    set_source_system_active,
)
from reality.web import app as web_module


def client_for(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(web_module, "Session", factory)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    return TestClient(web_module.app)


@pytest.mark.skip(reason="Retired server-rendered UI; covered by JSON API tests.")
def test_contextual_file_intake_streams_previews_and_requires_confirmation(
    session, business, monkeypatch, tmp_path
):
    monkeypatch.setenv("REALITY_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    client = client_for(session, monkeypatch)

    page = client.get(
        "/imports/new",
        params={"tenant": business.tenant.id, "expected_target": "bank_statement"},
    )
    assert page.status_code == 200
    assert "Import Bank statement" in page.text

    preview = client.post(
        "/imports/stage",
        data={
            "tenant": business.tenant.id,
            "expected_target": "bank_statement",
            "source_system": "bank_export",
            "source_type": "bank_statement",
            "external_id": "STATEMENT-1",
        },
        files={
            "upload": (
                "statement.csv",
                b"date,amount,party\n2026-08-29,10.00,Customer\n",
                "text/csv",
            )
        },
    )
    assert preview.status_code == 200
    assert "Map columns" in preview.text
    assert "Detected delimited text" in preview.text
    assert "AI mapping suggestions are unavailable" in preview.text
    artifact = session.query(SourceArtifact).one()
    mapped = client.post(
        "/imports/map",
        data={
            "tenant": business.tenant.id,
            "artifact_id": artifact.id,
            "expected_target": "bank_statement",
            "source_system": "bank_export",
            "source_type": "bank_statement",
            "external_id": "STATEMENT-1",
            "column_mapping": json.dumps(
                {"effective_at": "date", "amount": "amount", "party_name": "party"}
            ),
        },
    )
    assert mapped.status_code == 200
    assert "Confirmation required" in mapped.text
    proposal = session.query(ChangeProposal).filter_by(type="tool:source_ingest").one()
    assert session.query(SourceRecord).count() == 0

    confirmed = client.post(
        f"/imports/{business.tenant.id}/{proposal.id}/confirm",
        follow_redirects=False,
    )
    session.expire_all()
    assert confirmed.status_code == 303
    assert session.query(SourceArtifact).one().status == "attached"
    assert session.query(SourceRecord).one().source_artifact_id is not None
    assert session.query(ImportJob).one().status == "pending"


@pytest.mark.skip(reason="Retired server-rendered UI; covered by JSON API tests.")
def test_central_file_intake_offers_explicit_mapping_profiles(
    session, business, monkeypatch
):
    client = client_for(session, monkeypatch)

    page = client.get("/imports/new", params={"tenant": business.tenant.id})

    assert page.status_code == 200
    assert "Import data" in page.text
    assert "What does this file contain?" in page.text
    assert "Inventory snapshot" in page.text
    assert "Bank statement" in page.text
    assert "Sample import data" in page.text
    assert "reality-import-demo.zip" not in page.text


@pytest.mark.skip(reason="Retired server-rendered UI; examples belong to the frontend.")
def test_import_examples_download_from_a_fixed_allowlist(
    session, business, monkeypatch
):
    client = client_for(session, monkeypatch)

    example = client.get("/imports/examples/03_items.csv")
    assert example.status_code == 200
    assert example.headers["content-type"].startswith("text/csv")
    assert b"sku" in example.content

    package = client.get("/imports/examples/package")
    assert package.status_code == 200
    assert package.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        names = set(archive.namelist())
    assert "reality-import-demo/README.md" in names
    assert "reality-import-demo/06_bank_statement.csv" in names

    missing = client.get("/imports/examples/../../pyproject.toml")
    assert missing.status_code == 404


def test_multiple_systems_can_provide_same_source_type(session, business):
    shop_de = create_source_system(
        session, business.tenant.id, "shopify_de", "Shopify Germany"
    )
    shop_b2b = create_source_system(
        session, business.tenant.id, "shopify_b2b", "Shopify B2B"
    )

    first = create_source_capability(
        session, business.tenant.id, shop_de.id, "order", "sales_order"
    )
    second = create_source_capability(
        session, business.tenant.id, shop_b2b.id, "order", "sales_order"
    )
    set_source_capability_active(session, business.tenant.id, second.id, False)
    set_source_system_active(session, business.tenant.id, shop_b2b.id, False)

    registry = integration_registry(session, business.tenant.id)
    assert {row["system"].code for row in registry["capabilities"]} == {
        "shopify_de",
        "shopify_b2b",
    }
    assert first.is_active is True
    assert second.is_active is False
    assert shop_b2b.is_active is False


def test_mock_connector_shells_install_definitions_only(session, business):
    shells = connector_shells(session, business.tenant.id)
    assert {shell["code"] for shell in shells} >= {
        "shopify",
        "stripe",
        "shopify_payments",
        "odoo",
        "xentral",
        "weclapp",
        "billbee",
        "easybill",
        "salesforce",
        "hubspot",
        "akeneo",
        "pimcore",
    }
    system = install_connector_shell(
        session,
        business.tenant.id,
        "shopify",
        ["order"],
        "shopify_de_orders",
        "Shopify DE Orders",
    )
    registry = integration_registry(session, business.tenant.id)
    assert system.description.endswith("no connection")
    assert {row["capability"].source_type for row in registry["capabilities"]} == {
        "order"
    }
    shopify_shell = next(
        shell
        for shell in connector_shells(session, business.tenant.id)
        if shell["code"] == "shopify"
    )
    assert [instance.code for instance in shopify_shell["instances"]] == [
        "shopify_de_orders"
    ]


@pytest.mark.skip(reason="Retired server-rendered UI; covered by JSON API tests.")
def test_integrations_page_defines_sources_and_ingests_raw_payload(
    session, business, monkeypatch
):
    client = client_for(session, monkeypatch)
    tenant = business.tenant.id

    created = client.post(
        "/integrations/systems",
        data={
            "tenant": tenant,
            "code": "akeneo_main",
            "name": "Akeneo Main",
            "description": "Primary PIM",
        },
        follow_redirects=False,
    )
    assert created.status_code == 303

    page = client.get("/integrations", params={"tenant": tenant})
    assert page.status_code == 200
    assert "Akeneo Main" in page.text
    assert "Test source ingest" in page.text
    assert "Add source" in page.text
    assert "Select a system" in page.text
    assert "Shopify Payments" in page.text

    from_template = client.post(
        "/integrations/catalog/xentral",
        data={
            "tenant": tenant,
            "system_code": "xentral_orders_de",
            "system_name": "Xentral Orders DE",
            "source_types": "order",
        },
        follow_redirects=False,
    )
    assert from_template.status_code == 303
    xentral_capabilities = [
        row
        for row in integration_registry(session, tenant)["capabilities"]
        if row["system"].code == "xentral_orders_de"
    ]
    assert [row["capability"].source_type for row in xentral_capabilities] == ["order"]
    assert "RAW ONLY" not in page.text

    system_id = integration_registry(session, tenant)["systems"][0].id
    capability = client.post(
        "/integrations/capabilities",
        data={
            "tenant": tenant,
            "source_system_id": system_id,
            "source_type": "product",
            "target_type": "item",
        },
        follow_redirects=False,
    )
    assert capability.status_code == 303

    ingested = client.post(
        "/integrations/ingest",
        data={
            "tenant": tenant,
            "source_system": "akeneo_main",
            "source_type": "product",
            "external_id": "P-42",
            "payload_json": '{"id":"P-42","custom":{"color":"blue"}}',
            "context_json": "{}",
        },
        follow_redirects=False,
    )
    assert ingested.status_code == 303
    source = session.scalar(
        select(SourceRecord).where(SourceRecord.external_id == "P-42")
    )
    job = session.scalar(
        select(ImportJob).where(ImportJob.source_record_id == source.id)
    )
    assert json.loads(source.payload) == {
        "id": "P-42",
        "custom": {"color": "blue"},
    }
    assert job.status == "unmapped"

    page = client.get("/integrations", params={"tenant": tenant})
    assert "RAW ONLY" in page.text
    assert "P-42" in page.text


import json
