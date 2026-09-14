import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.services.core import create_tenant
from reality.web import api as api_module
from reality.web.app import app

ROOT = Path(__file__).resolve().parents[3]
FAMILIES = ("party", "item", "location")
OPERATIONS = ("create", "update", "deactivate", "reactivate")
INTERFACES = ("cli", "api", "web")
MATRIX = {
    (family, operation, interface)
    for family in FAMILIES
    for operation in OPERATIONS
    for interface in INTERFACES
}


def canonical_snapshot(values, *, aliases):
    ignored = {
        "id",
        "tenant_id",
        "source_record_id",
        "created_at",
        "updated_at",
    }
    return {
        key: aliases.get(value, value) if isinstance(value, str) else value
        for key, value in values.items()
        if key not in ignored
    }


def adapter_clients(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)

    def override_session():
        with factory() as api_session:
            yield api_session

    app.dependency_overrides[api_module.database_session] = override_session
    return CliRunner(), TestClient(app)


def created_id(result) -> str:
    assert result.exit_code == 0, result.stdout
    match = re.search(r"\(([^()]+)\)\s*$", result.stdout.strip())
    assert match is not None, result.stdout
    return match.group(1)


def test_declared_master_data_adapter_matrix_is_complete():
    assert len(MATRIX) == 36
    assert MATRIX == {
        (family, operation, interface)
        for family in FAMILIES
        for operation in OPERATIONS
        for interface in INTERFACES
    }


@pytest.mark.parametrize("family", FAMILIES)
def test_cli_and_api_delegate_each_family_to_shared_services(family):
    cli = (ROOT / "packages/reality-core/src/reality/cli/app.py").read_text()
    api = (ROOT / "packages/reality-core/src/reality/web/api.py").read_text()
    assert f"create_{family}(" in cli
    assert f"update_{family}(" in cli
    assert f"create_{family}(" in api
    assert f"update_{family}(" in api
    assert "set_master_data_active(" in cli
    assert "set_master_data_active(" in api


def test_canonical_snapshot_ignores_transport_noise_but_not_business_drift():
    aliases = {
        "ten_a": "tenant",
        "ten_b": "tenant",
        "loc_a": "warehouse",
        "loc_b": "warehouse",
    }
    left = canonical_snapshot(
        {
            "id": "par_a",
            "tenant_id": "ten_a",
            "name": "Acme",
            "default_location_id": "loc_a",
            "is_active": True,
        },
        aliases=aliases,
    )
    right = canonical_snapshot(
        {
            "id": "par_b",
            "tenant_id": "ten_b",
            "name": "Acme",
            "default_location_id": "loc_b",
            "is_active": True,
        },
        aliases=aliases,
    )
    assert left == right
    assert left != {**right, "name": "Different"}


@pytest.mark.parametrize(
    ("family", "collection", "create_args", "create_body", "update_args", "update_body"),
    [
        (
            "party",
            "parties",
            [
                "Parity Customer",
                "customer",
                "--source-system",
                "crm",
                "--external-id",
                "CRM-026",
                "--accounting-code",
                "AR-026",
                "--credit-limit",
                "2500.50",
            ],
            {
                "name": "Parity Customer",
                "type": "customer",
                "source_system": "crm",
                "external_id": "CRM-026",
                "accounting_code": "AR-026",
                "credit_limit": "2500.50",
            },
            [
                "Edited Parity Customer",
                "supplier",
                "--source-system",
                "erp",
                "--external-id",
                "ERP-026",
                "--accounting-code",
                "AP-026",
                "--credit-limit",
                "5000",
            ],
            {
                "name": "Edited Parity Customer",
                "type": "supplier",
                "source_system": "erp",
                "external_id": "ERP-026",
                "accounting_code": "AP-026",
                "credit_limit": "5000",
            },
        ),
        (
            "item",
            "items",
            [
                "PARITY-026",
                "Parity Item",
                "--unit",
                "pcs",
                "--source-system",
                "pim",
                "--external-id",
                "PIM-026",
                "--purchase-unit",
                "box",
                "--conversion-factor",
                "10",
                "--lead-time-days",
                "3",
            ],
            {
                "sku": "PARITY-026",
                "name": "Parity Item",
                "unit": "pcs",
                "source_system": "pim",
                "external_id": "PIM-026",
                "purchase_unit": "box",
                "conversion_factor": "10",
                "lead_time_days": 3,
            },
            [
                "PARITY-026-B",
                "Edited Parity Item",
                "--unit",
                "box",
                "--source-system",
                "erp",
                "--external-id",
                "ERP-I-026",
                "--purchase-unit",
                "pallet",
                "--conversion-factor",
                "20",
                "--lead-time-days",
                "5",
            ],
            {
                "sku": "PARITY-026-B",
                "name": "Edited Parity Item",
                "unit": "box",
                "source_system": "erp",
                "external_id": "ERP-I-026",
                "purchase_unit": "pallet",
                "conversion_factor": "20",
                "lead_time_days": 5,
            },
        ),
        (
            "location",
            "locations",
            [
                "Parity Warehouse",
                "--location-type",
                "warehouse",
                "--source-system",
                "wms",
                "--external-id",
                "WMS-026",
            ],
            {
                "name": "Parity Warehouse",
                "type": "warehouse",
                "source_system": "wms",
                "external_id": "WMS-026",
            },
            [
                "Edited Parity Warehouse",
                "--location-type",
                "returns",
                "--source-system",
                "erp",
                "--external-id",
                "ERP-L-026",
            ],
            {
                "name": "Edited Parity Warehouse",
                "type": "returns",
                "source_system": "erp",
                "external_id": "ERP-L-026",
            },
        ),
    ],
)
def test_cli_and_api_produce_equivalent_authoritative_lifecycle_state(
    session,
    monkeypatch,
    family,
    collection,
    create_args,
    create_body,
    update_args,
    update_body,
):
    cli_tenant = create_tenant(session, f"{family} CLI parity")
    api_tenant = create_tenant(session, f"{family} API parity")
    runner, client = adapter_clients(session, monkeypatch)

    def cli_call(operation, *arguments):
        result = runner.invoke(
            cli_module.app,
            [family, operation, *arguments, "--tenant", cli_tenant.id],
        )
        assert result.exit_code == 0, result.stdout
        return result

    def snapshots():
        cli_response = client.get(
            f"/api/tenants/{cli_tenant.id}/{collection}/{cli_record_id}"
        )
        api_response = client.get(
            f"/api/tenants/{api_tenant.id}/{collection}/{api_record_id}"
        )
        assert cli_response.status_code == api_response.status_code == 200
        aliases = {cli_tenant.id: "tenant", api_tenant.id: "tenant"}
        return (
            canonical_snapshot(cli_response.json(), aliases=aliases),
            canonical_snapshot(api_response.json(), aliases=aliases),
        )

    try:
        cli_record_id = created_id(cli_call("create", *create_args))
        created = client.post(
            f"/api/tenants/{api_tenant.id}/{collection}", json=create_body
        )
        assert created.status_code == 201, created.text
        api_record_id = created.json()["id"]
        assert snapshots()[0] == snapshots()[1]

        cli_call("update", cli_record_id, *update_args)
        updated = client.put(
            f"/api/tenants/{api_tenant.id}/{collection}/{api_record_id}",
            json=update_body,
        )
        assert updated.status_code == 200, updated.text
        assert snapshots()[0] == snapshots()[1]

        cli_call("deactivate", cli_record_id)
        deactivated = client.patch(
            f"/api/tenants/{api_tenant.id}/{collection}/{api_record_id}/active",
            json={"is_active": False},
        )
        assert deactivated.status_code == 200, deactivated.text
        assert snapshots()[0] == snapshots()[1]

        cli_call("activate", cli_record_id)
        activated = client.patch(
            f"/api/tenants/{api_tenant.id}/{collection}/{api_record_id}/active",
            json={"is_active": True},
        )
        assert activated.status_code == 200, activated.text
        assert snapshots()[0] == snapshots()[1]
    finally:
        app.dependency_overrides.clear()


def test_existing_real_adapter_suites_cover_lifecycle_and_tenant_failures():
    cli_tests = (ROOT / "packages/reality-core/tests/test_cli.py").read_text()
    api_tests = (ROOT / "packages/reality-core/tests/test_master_data_api.py").read_text()
    assert "test_cli_updates_and_changes_master_data_lifecycle" in cli_tests
    assert "test_json_api_master_data_lifecycle" in api_tests
    assert "test_json_api_rejects_invalid_and_cross_tenant_mutations" in api_tests
