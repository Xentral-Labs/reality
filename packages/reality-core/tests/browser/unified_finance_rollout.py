"""Explicit real-browser proof of the finance rollout against a live stack (spec 148).

An owner proposes and confirms an operational account; the journal carries account
identities, and a partly paid customer and supplier invoice each leave 38 open.
"""

import json
import os
import time
from decimal import Decimal
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.request import Request, urlopen

from live_stack import PASSWORD, add_member, live_stack, migrate, run_browser_script
from sqlalchemy.orm import sessionmaker

from reality.db.core import build_engine
from reality.services import core
from reality.web.auth import COOKIE_NAME


def session_cookie(api: str, email: str) -> str:
    """Sign in through the API and return the session cookie the browser would hold."""
    request = Request(
        f"{api}/api/auth/login",
        data=json.dumps({"email": email, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        cookies = SimpleCookie()
        for header in response.headers.get_all("Set-Cookie") or []:
            cookies.load(header)
    return cookies[COOKIE_NAME].value


def wait_for_open_items(api: str, cookie: str, tenant_id: str) -> None:
    """Open items are a background projection (spec 179): wait until both sides show 38."""
    last = {}
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        for flow in ("receivable", "payable"):
            request = Request(
                f"{api}/api/tenants/{tenant_id}/finance/open-items?flow={flow}",
                headers={"Cookie": f"{COOKIE_NAME}={cookie}"},
            )
            with urlopen(request, timeout=20) as response:
                last[flow] = json.loads(response.read())
        if all(
            any(Decimal(str(item["open"])) == 38 for item in last[flow]["items"])
            for flow in last
        ):
            return
        time.sleep(1)
    raise AssertionError(f"Open items never showed 38: {json.dumps(last)[:1500]}")


def test_finance_rollout_on_a_live_stack(postgres_database, tmp_path):
    assert os.environ.get("PLAYWRIGHT_MODULE"), (
        "Set PLAYWRIGHT_MODULE for this browser test"
    )
    artifacts = (
        Path(os.environ.get("JOURNEY_ARTIFACTS", str(tmp_path))) / "finance-rollout"
    )
    artifacts.mkdir(parents=True, exist_ok=True)
    env = migrate(postgres_database, artifacts)
    engine = build_engine(postgres_database)
    try:
        with sessionmaker(engine, expire_on_commit=False)() as session:
            tenant = core.create_tenant(session, "Finance rollout company")
            reviewed_initialize_accounts(session, tenant.id)
            for side in ("customer", "supplier"):
                party = reviewed_create_party(
                    session, tenant.id, f"Rollout {side}", side
                )
                invoice = core.create_document(
                    session,
                    tenant.id,
                    "sales_invoice" if side == "customer" else "supplier_invoice",
                    f"{side.upper()}-ROLLOUT",
                    party.id,
                    "100",
                )
                kind = "sales" if side == "customer" else "supplier"
                getattr(core, f"post_{kind}_invoice")(session, tenant.id, invoice.id)
                getattr(core, f"post_{side}_payment")(
                    session, tenant.id, invoice.id, "62"
                )
            add_member(session, tenant.id, "owner@example.test", "Olga Owner", "owner")
            session.commit()
            tenant_id = tenant.id
    finally:
        engine.dispose()
    with live_stack(env, artifacts) as stack:
        cookie = session_cookie(stack["api"], "owner@example.test")
        wait_for_open_items(stack["api"], cookie, tenant_id)
        access = artifacts / "access.json"
        access.write_text(
            json.dumps(
                {"cookie_name": COOKIE_NAME, "cookie": cookie, "tenant_id": tenant_id}
            )
        )
        run_browser_script(
            "finance-local-rollout-browser.mjs",
            dict(
                stack["env"],
                REALITY_BROWSER_URL=stack["web"],
                FINANCE_BROWSER_ACCESS=str(access),
                FINANCE_SCREENSHOTS=str(artifacts),
            ),
            artifacts,
        )
    print(f"Finance rollout verified against a live stack; artifacts: {artifacts}")


from intake_review_support import reviewed_create_party, reviewed_initialize_accounts
