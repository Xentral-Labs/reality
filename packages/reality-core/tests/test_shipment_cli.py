from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from reality.cli import app as cli_module
from reality.services.shipments import record_shipment_notice


def test_shipment_cli_list_and_show_share_the_tenant_read_service(
    session, business, monkeypatch
):
    shipment, _, _ = record_shipment_notice(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
        carrier="DHL",
        tracking_number="CLI-TRACK-173",
    )
    factory = sessionmaker(session.bind, expire_on_commit=False)
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    runner = CliRunner()

    listing = runner.invoke(
        cli_module.app,
        [
            "shipment",
            "list",
            "--tenant",
            business.tenant.id,
            "--tracking",
            "TRACK-173",
            "--observation",
            "announced",
        ],
    )
    detail = runner.invoke(
        cli_module.app,
        ["shipment", "show", shipment.id, "--tenant", business.tenant.id],
    )

    assert listing.exit_code == 0, listing.stdout
    assert shipment.id in listing.stdout
    assert detail.exit_code == 0, detail.stdout
    assert "CLI-TRACK-173" in detail.stdout
