from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.db.core import Item, Location, Party
from reality.services.core import (
    active_commitment_hold,
    create_commitment,
    create_document,
    create_tenant,
    post_sales_invoice,
    record_movement,
)


def runner_for(session, monkeypatch):
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    return CliRunner()


def test_cli_status_tenants_and_stock(session, business, monkeypatch):
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        20,
        to_location_id=business.location.id,
    )
    runner = runner_for(session, monkeypatch)

    status = runner.invoke(cli_module.app, ["status"])
    tenants = runner.invoke(cli_module.app, ["tenant", "list"])
    stock = runner.invoke(cli_module.app, ["stock", "--tenant", business.tenant.id])

    assert status.exit_code == 0
    assert "Reality V0" in status.stdout
    assert business.tenant.id in tenants.stdout
    assert "Bike Light" in stock.stdout
    assert "20" in stock.stdout


def test_cli_tenant_context_and_master_data_commands(session, business, monkeypatch):
    state = {"tenant_id": None}
    monkeypatch.setattr(
        cli_module,
        "write_current_tenant",
        lambda tenant_id: state.update(tenant_id=tenant_id),
    )
    monkeypatch.setattr(cli_module, "read_current_tenant", lambda: state["tenant_id"])
    runner = runner_for(session, monkeypatch)

    use = runner.invoke(cli_module.app, ["tenant", "use", business.tenant.id])
    current = runner.invoke(cli_module.app, ["tenant", "current"])
    party = runner.invoke(
        cli_module.app, ["party", "create", "New Customer", "customer"]
    )
    item = runner.invoke(cli_module.app, ["item", "create", "NEW-1", "New Item"])
    location = runner.invoke(cli_module.app, ["location", "create", "Second Warehouse"])

    assert use.exit_code == current.exit_code == 0
    assert business.tenant.id in current.stdout
    assert party.exit_code == item.exit_code == location.exit_code == 0


def test_cli_updates_and_changes_master_data_lifecycle(session, business, monkeypatch):
    runner = runner_for(session, monkeypatch)
    cases = [
        (
            "party",
            Party,
            business.customer.id,
            [business.customer.id, "Edited Customer", "customer"],
        ),
        (
            "item",
            Item,
            business.item.id,
            [business.item.id, "EDIT-1", "Edited Item", "--unit", "unit"],
        ),
        (
            "location",
            Location,
            business.location.id,
            [
                business.location.id,
                "Edited Warehouse",
                "--location-type",
                "warehouse",
            ],
        ),
    ]
    for command, model, record_id, update_args in cases:
        updated = runner.invoke(
            cli_module.app,
            [command, "update", *update_args, "--tenant", business.tenant.id],
        )
        deactivated = runner.invoke(
            cli_module.app,
            [command, "deactivate", record_id, "--tenant", business.tenant.id],
        )
        record = session.scalar(select(model).where(model.id == record_id))
        assert updated.exit_code == deactivated.exit_code == 0
        session.refresh(record)
        assert record is not None and record.is_active is False

        activated = runner.invoke(
            cli_module.app,
            [command, "activate", record_id, "--tenant", business.tenant.id],
        )
        session.refresh(record)
        assert activated.exit_code == 0
        assert record.is_active is True


def test_cli_runs_normal_month_for_empty_tenant(session, monkeypatch):
    tenant = create_tenant(session, "Scenario GmbH")
    runner = runner_for(session, monkeypatch)

    result = runner.invoke(
        cli_module.app, ["scenario", "run", "normal-month", "--tenant", tenant.id]
    )

    assert result.exit_code == 0
    assert "September 2026 complete" in result.stdout
    assert "receivable EUR" in result.stdout
    assert "870.0000" in result.stdout


def test_cli_posts_customer_payment_and_reports_derived_open_amount(
    session, business, monkeypatch
):
    invoice = create_document(
        session,
        business.tenant.id,
        "sales_invoice",
        "RE-CLI",
        business.customer.id,
        100,
    )
    post_sales_invoice(session, business.tenant.id, invoice.id)
    runner = runner_for(session, monkeypatch)

    paid = runner.invoke(
        cli_module.app,
        [
            "finance",
            "pay-customer",
            invoice.id,
            "40",
            "--number",
            "BANK-CLI",
            "--tenant",
            business.tenant.id,
        ],
    )
    opened = runner.invoke(
        cli_module.app,
        ["finance", "open", invoice.id, "--tenant", business.tenant.id],
    )

    assert paid.exit_code == opened.exit_code == 0
    assert "open 60" in paid.stdout
    assert "open 60" in opened.stdout


def test_cli_holds_and_releases_commitment(session, business, monkeypatch):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        1,
        "2026-09-05",
    )
    runner = runner_for(session, monkeypatch)

    held = runner.invoke(
        cli_module.app,
        [
            "commitment",
            "hold",
            commitment.id,
            "credit_check",
            "--tenant",
            business.tenant.id,
        ],
    )
    with sessionmaker(session.bind, expire_on_commit=False)() as verification:
        assert (
            active_commitment_hold(verification, business.tenant.id, commitment.id)
            is not None
        )
    released = runner.invoke(
        cli_module.app,
        [
            "commitment",
            "release-hold",
            commitment.id,
            "--tenant",
            business.tenant.id,
        ],
    )

    assert held.exit_code == released.exit_code == 0
    assert "Commitment held" in held.stdout
    assert "Released 1 hold" in released.stdout
