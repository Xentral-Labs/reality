"""Explicit real-browser proof of the demo order-to-cash stream (feature 168).

The owner creates a Sandbox company, connects and starts Demo Data, and waits for the
simulation to settle an invoice and to leave a residual and an unmatched payment, then
settles a suggested invoice by hand. It follows the simulation's own pace, so it runs for
tens of minutes to hours; CI runs it on a schedule, not on every pull request.
"""

import os
from pathlib import Path

from live_stack import PASSWORD, add_member, live_stack, migrate, run_browser_script
from sqlalchemy.orm import sessionmaker

from reality.db.core import build_engine
from reality.services import core


def test_demo_order_to_cash_stream_settles_by_hand(postgres_database, tmp_path):
    assert os.environ.get("PLAYWRIGHT_MODULE"), (
        "Set PLAYWRIGHT_MODULE for this browser test"
    )
    artifacts = (
        Path(os.environ.get("JOURNEY_ARTIFACTS", str(tmp_path))) / "demo-data-payments"
    )
    artifacts.mkdir(parents=True, exist_ok=True)
    first = int(os.environ.get("DEMO_O2C_WAIT_MINUTES", "25"))
    differences = int(os.environ.get("DEMO_O2C_DIFFERENCE_WAIT_MINUTES", "150"))
    env = migrate(postgres_database, artifacts)
    engine = build_engine(postgres_database)
    try:
        with sessionmaker(engine, expire_on_commit=False)() as session:
            # The owner works in one company and creates the Sandbox through setup.
            tenant = core.create_tenant(session, "Home company")
            add_member(session, tenant.id, "owner@example.test", "Olga Owner", "owner")
            session.commit()
    finally:
        engine.dispose()
    with live_stack(env, artifacts) as stack:
        run_browser_script(
            "demo-data-payments-browser.mjs",
            dict(
                stack["env"],
                DEMO_O2C_BASE_URL=stack["web"],
                DEMO_O2C_EMAIL="owner@example.test",
                DEMO_O2C_PASSWORD=PASSWORD,
                DEMO_O2C_WAIT_MINUTES=str(first),
                DEMO_O2C_DIFFERENCE_WAIT_MINUTES=str(differences),
                DEMO_O2C_ARTIFACTS=str(artifacts),
            ),
            artifacts,
            timeout=(first + differences + 10) * 60,
        )
    print(f"Demo order-to-cash stream verified; artifacts: {artifacts}")
